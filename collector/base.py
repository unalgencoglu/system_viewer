"""
Toplayıcıların (linux.py ve windows.py) ortak sözleşmesi.

İki toplayıcı da aşağıdaki fonksiyonları sağlar ve AYNI şekilde
sözlük (dict) döndürür. Böylece Flask ve arayüz hangi işletim sisteminde
çalıştığını bilmek zorunda kalmaz.

get_system_info() -> {
    "os": str,            # "Kali GNU/Linux Rolling · 6.11.2-amd64"
    "uptime": str,        # "3s 12dk"
}

get_system_stats() -> {
    "cpu": {"percent": float, "model": str, "cores": int, "per_core": [float]},
    "ram": {"percent": float, "used_gb": float, "total_gb": float},
}

get_processes() -> [ {
    "pid": int, "name": str, "state": str, "user": str,
    "cpu": float,         # tüm sisteme göre % (0-100)
    "mem": float,         # toplam RAM'e göre %
    "rss": int,           # fiziksel bellek, byte
    "threads": int,
    "open_files": int | None,   # None = erişim yok
}, ... ]

get_process_detail(pid) -> {
    yukarıdakilere ek olarak:
    "ppid", "exe", "cmdline", "nice", "vms", "start_time",
    "files": [ {"fd": int, "path": str, "type": str} ] | None
} ya da süreç yoksa None

control_process(pid, action, nice=None) -> (bool, str)
    action: "terminate" | "kill" | "suspend" | "resume" | "nice"
    Başarılı mı ve kullanıcıya gösterilecek mesaj.
"""


def bytes_to_gb(n):
    return round(n / (1024 ** 3), 2)


def format_uptime(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600}s {seconds % 3600 // 60}dk"
