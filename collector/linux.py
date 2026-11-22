"""
Linux toplayıcı: tüm bilgileri doğrudan /proc dosya sisteminden okur.

/proc gerçek bir disk klasörü değildir. Çekirdek (kernel) bu dosyaları biz
okuduğumuz anda kendi veri yapılarından (süreç tablosu, bellek sayaçları ...)
üretir. Yani burada okunan her şey, çekirdeğin süreçler hakkında tuttuğu
bilginin (PCB - Process Control Block) bize açılan bir penceresidir.

Kullanılan dosyalar:
    /proc/stat              -> toplam ve çekirdek başına CPU süreleri, açılış zamanı
    /proc/meminfo           -> genel bellek durumu
    /proc/cpuinfo           -> işlemci modeli
    /proc/uptime            -> sistem ne kadar süredir açık
    /proc/<pid>/stat        -> süreç durumu, CPU süresi, thread sayısı, bellek
    /proc/<pid>/status      -> aynı bilgilerin okunabilir hali, kullanıcı (Uid)
    /proc/<pid>/fd/         -> sürecin açık dosya tanımlayıcıları
    /proc/<pid>/exe         -> çalıştırılabilir dosyanın yolu (sembolik link)
    /proc/<pid>/cmdline     -> süreci başlatan komut
"""
import os
import pwd
import signal
import time

from .base import bytes_to_gb, format_uptime

PROC = "/proc"

# Çekirdek CPU sürelerini "jiffy" (tik) cinsinden verir. Saniyede kaç tik
# olduğunu ve bir bellek sayfasının kaç byte olduğunu sistemden soruyoruz.
CLK_TCK = os.sysconf("SC_CLK_TCK")      # genelde 100
PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")  # genelde 4096

# Süreç durum harfleri (/proc/<pid>/stat 3. alan)
STATES = {
    "R": "running",      # çalışıyor veya çalışmaya hazır (kuyrukta)
    "S": "sleeping",     # bir olayı bekliyor, uyandırılabilir
    "D": "disk sleep",   # G/Ç bekliyor, sinyalle uyandırılamaz
    "Z": "zombie",       # bitti ama ebeveyni çıkış kodunu henüz almadı
    "T": "stopped",      # sinyalle durduruldu (Ctrl+Z, SIGSTOP)
    "t": "tracing stop", # hata ayıklayıcı tarafından durduruldu
    "I": "idle",         # boşta bekleyen çekirdek thread'i
    "X": "dead",
}


def _read(path):
    with open(path) as f:
        return f.read()


# --------------------------------------------------------------------------
# Genel CPU
# --------------------------------------------------------------------------

def _read_cpu_times():
    """
    /proc/stat'ın başındaki satırlar:
        cpu  user nice system idle iowait irq softirq steal guest guest_nice
        cpu0 ...
        cpu1 ...
    Değerler açılıştan beri birikmiş süredir (jiffy).
    Dönüş: [(toplam, boşta), ...]. İlk eleman tüm sistem, sonrakiler çekirdekler.
    """
    times = []
    for line in _read(f"{PROC}/stat").splitlines():
        if not line.startswith("cpu"):
            break
        values = [int(x) for x in line.split()[1:]]
        # guest süreleri zaten user/nice içinde sayıldığı için ilk 8 sütunu alıyoruz
        total = sum(values[:8])
        idle = values[3] + values[4]  # idle + iowait
        times.append((total, idle))
    return times


_prev_cpu = None


def _cpu_percents():
    """
    Biriken süreler tek başına bir şey söylemez, iki ölçüm arasındaki farka bakarız:
        CPU% = (Δtoplam - Δboşta) / Δtoplam × 100
    Önceki ölçümü saklayıp her çağrıda yenisiyle karşılaştırıyoruz.
    """
    global _prev_cpu
    now = _read_cpu_times()
    if _prev_cpu is None:          # ilk çağrı: karşılaştıracak ölçüm yok
        _prev_cpu = now
        time.sleep(0.1)
        now = _read_cpu_times()

    percents = []
    for (t1, i1), (t2, i2) in zip(_prev_cpu, now):
        d_total = t2 - t1
        d_busy = d_total - (i2 - i1)
        percents.append(round(d_busy / d_total * 100, 1) if d_total > 0 else 0.0)
    _prev_cpu = now
    return percents[0], percents[1:]


def _cpu_model():
    try:
        for line in _read(f"{PROC}/cpuinfo").splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return "Bilinmeyen İşlemci"


def _boot_time():
    """/proc/stat içindeki 'btime' satırı: açılış anı (Unix zamanı, saniye)."""
    for line in _read(f"{PROC}/stat").splitlines():
        if line.startswith("btime"):
            return int(line.split()[1])
    return 0


# --------------------------------------------------------------------------
# Genel bellek
# --------------------------------------------------------------------------

def _read_meminfo():
    """
    /proc/meminfo satırları 'MemTotal:  8048232 kB' biçimindedir.
    Hepsini byte'a çevirip sözlüğe koyuyoruz.
    """
    info = {}
    for line in _read(f"{PROC}/meminfo").splitlines():
        key, value = line.split(":", 1)
        info[key] = int(value.split()[0]) * 1024
    return info


def _memory():
    m = _read_meminfo()
    total = m["MemTotal"]
    # MemAvailable: takasa (swap) gitmeden yeni programlara verilebilecek bellek.
    # Önbellek (cache) gerektiğinde boşaltılabildiği için "kullanılan" sayılmaz.
    available = m.get("MemAvailable", m["MemFree"] + m.get("Buffers", 0) + m.get("Cached", 0))
    used = total - available
    return total, used


# --------------------------------------------------------------------------
# Sistem bilgisi
# --------------------------------------------------------------------------

def get_system_info():
    name = "Linux"
    try:
        for line in _read("/etc/os-release").splitlines():
            if line.startswith("PRETTY_NAME="):
                name = line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    kernel = _read(f"{PROC}/sys/kernel/osrelease").strip()
    uptime_seconds = float(_read(f"{PROC}/uptime").split()[0])
    return {"os": f"{name} · {kernel}", "uptime": format_uptime(uptime_seconds)}


def get_system_stats():
    total_percent, per_core = _cpu_percents()
    mem_total, mem_used = _memory()
    return {
        "cpu": {
            "percent": total_percent,
            "model": _cpu_model(),
            "cores": len(per_core),
            "per_core": per_core,
        },
        "ram": {
            "percent": round(mem_used / mem_total * 100, 1),
            "used_gb": bytes_to_gb(mem_used),
            "total_gb": bytes_to_gb(mem_total),
        },
    }


# --------------------------------------------------------------------------
# Süreçler
# --------------------------------------------------------------------------

def _list_pids():
    """Her çalışan süreç için /proc altında PID numarasıyla bir klasör vardır."""
    return [int(d) for d in os.listdir(PROC) if d.isdigit()]


def _parse_stat(pid):
    """
    /proc/<pid>/stat tek satırdır, alanlar boşlukla ayrılır:
        1234 (python3) S 1 1234 1234 0 -1 ...
    Süreç adı boşluk veya parantez içerebilir; bu yüzden SON ')' karakterinden
    bölüyoruz. 'man 5 proc' içindeki n. alan, aşağıdaki listede f[n-3]'tür.
    """
    data = _read(f"{PROC}/{pid}/stat")
    left, right = data.rsplit(")", 1)
    f = right.split()
    return {
        "name": left.split("(", 1)[1],
        "state": f[0],                    # 3  durum harfi
        "ppid": int(f[1]),                # 4  ebeveyn PID
        "utime": int(f[11]),              # 14 kullanıcı modunda geçen CPU süresi (jiffy)
        "stime": int(f[12]),              # 15 çekirdek modunda geçen CPU süresi (jiffy)
        "nice": int(f[16]),               # 19 öncelik (-20 en yüksek, 19 en düşük)
        "threads": int(f[17]),            # 20 thread sayısı
        "starttime": int(f[19]),          # 22 açılıştan kaç jiffy sonra başladı
        "vsize": int(f[20]),              # 23 sanal bellek (byte)
        "rss": int(f[21]) * PAGE_SIZE,    # 24 RAM'deki sayfa sayısı -> byte
    }


def _read_status(pid):
    """/proc/<pid>/status: 'Anahtar:\\tdeğer' satırları."""
    status = {}
    for line in _read(f"{PROC}/{pid}/status").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            status[key] = value.strip()
    return status


_users = {}


def _username(uid):
    if uid not in _users:
        try:
            _users[uid] = pwd.getpwuid(uid).pw_name
        except KeyError:
            _users[uid] = str(uid)
    return _users[uid]


def _count_fds(pid):
    """Açık dosya sayısı = /proc/<pid>/fd klasöründeki girdi sayısı."""
    try:
        return len(os.listdir(f"{PROC}/{pid}/fd"))
    except (PermissionError, FileNotFoundError):
        return None   # başka kullanıcının süreci: erişim yok


def _snapshot():
    """Tüm süreçlerin stat bilgisi + o anki toplam CPU süresi."""
    total = _read_cpu_times()[0][0]
    procs = {}
    for pid in _list_pids():
        try:
            procs[pid] = _parse_stat(pid)
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue   # süreç biz okurken kapandı
    return total, procs


# Bir önceki ölçüm. Anahtar (pid, başlama zamanı): PID'ler tekrar kullanılabildiği
# için aynı numaralı yeni bir süreci eskisiyle karıştırmamak gerekiyor.
_prev_total = None
_prev_proc = {}
_last_cpu = {}


def get_processes():
    """
    Süreç CPU yüzdesi de iki ölçüm farkıyla hesaplanır:
        CPU% = Δ(utime + stime) / Δ(toplam CPU süresi) × 100
    Δtoplam bütün çekirdeklerin toplamı olduğu için sonuç tüm sisteme göre
    yüzdedir (0-100). 'top' ise tek çekirdeğe göre gösterir (400% olabilir).
    """
    global _prev_total, _prev_proc, _last_cpu

    total, procs = _snapshot()
    if _prev_total is None:
        _prev_total = total
        _prev_proc = {(p, s["starttime"]): s["utime"] + s["stime"] for p, s in procs.items()}
        time.sleep(0.2)
        total, procs = _snapshot()

    d_total = total - _prev_total
    mem_total = _read_meminfo()["MemTotal"]

    result = []
    new_prev = {}
    new_cpu = {}
    for pid, s in procs.items():
        jiffies = s["utime"] + s["stime"]
        key = (pid, s["starttime"])
        new_prev[key] = jiffies
        before = _prev_proc.get(key, jiffies)   # yeni başlayan süreç: 0 göster
        cpu = round((jiffies - before) / d_total * 100, 1) if d_total > 0 else 0.0
        new_cpu[pid] = cpu

        try:
            user = _username(os.stat(f"{PROC}/{pid}").st_uid)
        except FileNotFoundError:
            continue

        result.append({
            "pid": pid,
            "name": s["name"],
            "state": s["state"],
            "state_name": STATES.get(s["state"], s["state"]),
            "user": user,
            "cpu": cpu,
            "mem": round(s["rss"] / mem_total * 100, 2),
            "rss": s["rss"],
            "threads": s["threads"],
            "open_files": _count_fds(pid),
        })

    _prev_total, _prev_proc, _last_cpu = total, new_prev, new_cpu
    return result


def _list_fds(pid):
    """
    /proc/<pid>/fd içindeki her girdi bir dosya tanımlayıcısıdır (0 stdin,
    1 stdout, 2 stderr, ...) ve gerçekte neyi gösterdiğine dair sembolik linktir.
    """
    base = f"{PROC}/{pid}/fd"
    try:
        names = os.listdir(base)
    except (PermissionError, FileNotFoundError):
        return None

    files = []
    for name in sorted(names, key=int):
        try:
            target = os.readlink(f"{base}/{name}")
        except OSError:
            continue
        if target.startswith("socket:"):
            kind = "socket"
        elif target.startswith("pipe:"):
            kind = "pipe"
        elif target.startswith("anon_inode:"):
            kind = "anon_inode"
        elif target.startswith("/dev/"):
            kind = "device"
        else:
            kind = "file"
        files.append({"fd": int(name), "path": target, "type": kind})
    return files


def _kb(value):
    """status dosyasındaki '342512 kB' değerini byte'a çevirir."""
    return int(value.split()[0]) * 1024 if value else 0


def get_process_detail(pid):
    try:
        s = _parse_stat(pid)
        status = _read_status(pid)
        cmdline = _read(f"{PROC}/{pid}/cmdline").replace("\0", " ").strip()
    except (FileNotFoundError, ProcessLookupError):
        return None

    try:
        exe = os.readlink(f"{PROC}/{pid}/exe")
    except OSError:
        exe = None   # çekirdek thread'i veya erişim yok

    uid = int(status["Uid"].split()[0])   # gerçek, etkin, kayıtlı, dosya sistemi
    mem_total = _read_meminfo()["MemTotal"]
    rss = _kb(status.get("VmRSS"))        # çekirdek thread'lerinde bu satırlar yok

    return {
        "pid": pid,
        "name": status.get("Name", s["name"]),
        "state": s["state"],
        "state_name": STATES.get(s["state"], s["state"]),
        "user": _username(uid),
        "ppid": s["ppid"],
        "exe": exe,
        "cmdline": cmdline,
        "nice": s["nice"],
        "threads": s["threads"],
        "cpu": _last_cpu.get(pid, 0.0),
        "mem": round(rss / mem_total * 100, 2),
        "rss": rss,
        "vms": _kb(status.get("VmSize")),
        "start_time": _boot_time() + s["starttime"] / CLK_TCK,  # Unix zamanı
        "files": _list_fds(pid),
    }


# --------------------------------------------------------------------------
# Süreç kontrolü
# --------------------------------------------------------------------------
#
# Linux'ta bir sürece dışarıdan müdahale etmenin yolu ona SİNYAL göndermektir
# (kill() sistem çağrısı). Çekirdek sinyali sürecin PCB'sine işler; süreç
# sıradaki çalışma anında sinyali işler ya da çekirdek doğrudan uygular.
#
#   SIGTERM (15) -> "lütfen kapan": süreç yakalayıp temizlik yapabilir
#   SIGKILL (9)  -> çekirdek süreci hemen bitirir, yakalanamaz
#   SIGSTOP (19) -> süreç durdurulur, durumu T (stopped) olur, yakalanamaz
#   SIGCONT (18) -> durdurulmuş süreç kaldığı yerden devam eder
#
# Öncelik (nice) setpriority() sistem çağrısıyla değiştirilir. Zamanlayıcı
# (CFS) düşük nice değerli süreçlere daha çok CPU zamanı verir. Normal kullanıcı
# nice değerini sadece artırabilir (önceliği düşürebilir); azaltmak root ister.

SIGNALS = {
    "terminate": signal.SIGTERM,
    "kill": signal.SIGKILL,
    "suspend": signal.SIGSTOP,
    "resume": signal.SIGCONT,
}


def control_process(pid, action, nice=None):
    """
    Dönüş: (başarılı mı, mesaj). Hata durumunda mesaj kullanıcıya gösterilir.
    """
    if pid in (0, 1) or pid == os.getpid():
        return False, "Bu süreç korunuyor (init veya uygulamanın kendisi)."

    try:
        if action in SIGNALS:
            os.kill(pid, SIGNALS[action])
            return True, f"{SIGNALS[action].name} sinyali gönderildi."
        if action == "nice":
            nice = int(nice)
            if not -20 <= nice <= 19:
                return False, "Nice değeri -20 ile 19 arasında olmalı."
            os.setpriority(os.PRIO_PROCESS, pid, nice)
            return True, f"Nice değeri {nice} yapıldı."
        return False, f"Bilinmeyen işlem: {action}"
    except ProcessLookupError:
        return False, "Süreç bulunamadı (kapanmış olabilir)."
    except PermissionError:
        return False, "Yetki yok. Başka kullanıcının süreci için veya önceliği artırmak için root gerekir."
    except (TypeError, ValueError):
        return False, "Geçersiz nice değeri."
