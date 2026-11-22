"""
Windows toplayıcı: Windows'ta /proc olmadığı için şimdilik psutil kullanır.
psutil arka planda WinAPI'yi çağırır (CreateToolhelp32Snapshot,
GetProcessMemoryInfo, GetProcessTimes ...). Vakit kalırsa bu fonksiyonlar
ctypes ile doğrudan çağrılacak.

Dönen veri linux.py ile birebir aynı biçimdedir (bkz. base.py).
"""
import os
import platform
import time

import psutil

from .base import bytes_to_gb, format_uptime

STATES = {
    psutil.STATUS_RUNNING: ("R", "running"),
    psutil.STATUS_STOPPED: ("T", "stopped"),
}


def _cpu_model():
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
        )
        return winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
    except OSError:
        return platform.processor() or "Bilinmeyen İşlemci"


def get_system_info():
    build = int(platform.version().split(".")[2])
    version = "11" if build >= 22000 else platform.release()
    return {
        "os": f"Windows {version} (build {build})",
        "uptime": format_uptime(time.time() - psutil.boot_time()),
    }


# psutil.cpu_percent(interval=None) önceki ölçümü her thread için ayrı saklar.
# Flask her isteği yeni bir thread'de işlediği için her çağrı "ilk ölçüm" sayılır
# ve hep 0 döner. Bu yüzden Linux tarafındaki gibi farkı kendimiz hesaplıyoruz:
#     CPU% = (Δtoplam - Δboşta) / Δtoplam × 100
_prev_cpu = None


def _read_cpu_times():
    times = [psutil.cpu_times()] + psutil.cpu_times(percpu=True)
    return [(sum(t), t.idle) for t in times]


def _cpu_percents():
    global _prev_cpu
    now = _read_cpu_times()
    if _prev_cpu is None:
        _prev_cpu = now
        time.sleep(0.1)
        now = _read_cpu_times()
    percents = []
    for (t1, i1), (t2, i2) in zip(_prev_cpu, now):
        d_total = t2 - t1
        d_busy = d_total - (i2 - i1)
        percents.append(round(max(0.0, d_busy / d_total * 100), 1) if d_total > 0 else 0.0)
    _prev_cpu = now
    return percents[0], percents[1:]


def get_system_stats():
    mem = psutil.virtual_memory()
    total_percent, per_core = _cpu_percents()
    return {
        "cpu": {
            "percent": total_percent,
            "model": _cpu_model(),
            "cores": len(per_core),
            "per_core": per_core,
        },
        "ram": {
            "percent": mem.percent,
            "used_gb": bytes_to_gb(mem.total - mem.available),
            "total_gb": bytes_to_gb(mem.total),
        },
    }


# psutil süreç CPU yüzdesini iki çağrı arasındaki farktan hesaplar; bu yüzden
# aynı Process nesnelerini saklamamız gerekiyor.
_procs = {}
_last_cpu = {}
_cores = psutil.cpu_count() or 1


def _state(p):
    return STATES.get(p.status(), ("S", "sleeping"))


def get_processes():
    result = []
    alive = {}
    for p in psutil.process_iter():
        p = _procs.get(p.pid, p)
        try:
            with p.oneshot():
                # psutil tek çekirdeğe göre verir, Linux tarafıyla aynı olsun diye bölüyoruz
                cpu = round(p.cpu_percent(None) / _cores, 1)
                mem = p.memory_info()
                state, state_name = _state(p)
                try:
                    user = p.username()
                except psutil.AccessDenied:
                    user = "?"
                try:
                    open_files = p.num_handles()
                except psutil.AccessDenied:
                    open_files = None
                result.append({
                    "pid": p.pid,
                    "name": p.name(),
                    "state": state,
                    "state_name": state_name,
                    "user": user,
                    "cpu": cpu,
                    "mem": round(p.memory_percent(), 2),
                    "rss": mem.rss,
                    "threads": p.num_threads(),
                    "open_files": open_files,
                })
            alive[p.pid] = p
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    _procs.clear()
    _procs.update(alive)
    _last_cpu.clear()
    _last_cpu.update({p["pid"]: p["cpu"] for p in result})
    return result


def get_process_detail(pid):
    try:
        p = _procs.get(pid) or psutil.Process(pid)
        with p.oneshot():
            mem = p.memory_info()
            state, state_name = _state(p)

            def safe(fn, default=None):
                try:
                    return fn()
                except psutil.AccessDenied:
                    return default

            files = safe(p.open_files)
            return {
                "pid": pid,
                "name": p.name(),
                "state": state,
                "state_name": state_name,
                "user": safe(p.username, "?"),
                "ppid": p.ppid(),
                "exe": safe(p.exe),
                "cmdline": " ".join(safe(p.cmdline, [])),
                "nice": _nice_from_class(safe(p.nice)),
                "threads": p.num_threads(),
                "cpu": _last_cpu.get(pid, 0.0),
                "mem": round(p.memory_percent(), 2),
                "rss": mem.rss,
                "vms": mem.vms,
                "start_time": p.create_time(),
                "files": None if files is None else
                         [{"fd": f.fd, "path": f.path, "type": "file"} for f in files],
            }
    except psutil.NoSuchProcess:
        return None


# --------------------------------------------------------------------------
# Süreç kontrolü
# --------------------------------------------------------------------------
# Windows'ta sinyal yoktur. psutil şu WinAPI çağrılarını kullanır:
#   terminate / kill -> TerminateProcess
#   suspend / resume -> NtSuspendProcess / NtResumeProcess
#   nice             -> SetPriorityClass (Windows sayı değil "öncelik sınıfı" kullanır)


def _priority_class(nice):
    """Linux nice değerini (-20..19) en yakın Windows öncelik sınıfına çevirir."""
    if nice <= -15:
        return psutil.HIGH_PRIORITY_CLASS
    if nice < 0:
        return psutil.ABOVE_NORMAL_PRIORITY_CLASS
    if nice == 0:
        return psutil.NORMAL_PRIORITY_CLASS
    if nice < 15:
        return psutil.BELOW_NORMAL_PRIORITY_CLASS
    return psutil.IDLE_PRIORITY_CLASS


def _nice_from_class(priority_class):
    """Arayüz her iki sistemde aynı ölçeği göstersin diye sınıfı nice değerine çevirir."""
    return {
        psutil.REALTIME_PRIORITY_CLASS: -20,
        psutil.HIGH_PRIORITY_CLASS: -15,
        psutil.ABOVE_NORMAL_PRIORITY_CLASS: -5,
        psutil.NORMAL_PRIORITY_CLASS: 0,
        psutil.BELOW_NORMAL_PRIORITY_CLASS: 10,
        psutil.IDLE_PRIORITY_CLASS: 19,
    }.get(priority_class)


def control_process(pid, action, nice=None):
    if pid in (0, 4) or pid == os.getpid():   # 0: System Idle, 4: System
        return False, "Bu süreç korunuyor (sistem süreci veya uygulamanın kendisi)."
    try:
        p = psutil.Process(pid)
        if action == "terminate":
            p.terminate()
            return True, "Sonlandırma isteği gönderildi."
        if action == "kill":
            p.kill()
            return True, "Süreç zorla kapatıldı."
        if action == "suspend":
            p.suspend()
            return True, "Süreç duraklatıldı."
        if action == "resume":
            p.resume()
            return True, "Süreç devam ettirildi."
        if action == "nice":
            nice = int(nice)
            if not -20 <= nice <= 19:
                return False, "Nice değeri -20 ile 19 arasında olmalı."
            p.nice(_priority_class(nice))
            return True, "Öncelik sınıfı değiştirildi."
        return False, f"Bilinmeyen işlem: {action}"
    except psutil.NoSuchProcess:
        return False, "Süreç bulunamadı (kapanmış olabilir)."
    except psutil.AccessDenied:
        return False, "Yetki yok. Uygulamayı yönetici olarak çalıştırmanız gerekebilir."
    except (TypeError, ValueError):
        return False, "Geçersiz nice değeri."
