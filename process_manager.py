import psutil

for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
    try:
        bilgi = proc.info
        if bilgi['memory_percent'] and bilgi['memory_percent'] > 1.0:
            print(f"PID: {bilgi['pid']:<6} | Adı: {bilgi['name']:<25} | RAM: %{bilgi['memory_percent']:.2f}")
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        continue