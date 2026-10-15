""" Burası what_happend.md dosyasında yer alanların uygulamasıdır """

import psutil

islemler = {
    "cpu_kullanimi": psutil.cpu_percent(interval=1),
    "cekirdek_sayisi": psutil.cpu_count(logical=True),
    "bellek": psutil.virtual_memory()
}

for baslik, deger in islemler.items():
    print(f"{baslik} -> {deger}")

for proc in list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']))[:2]:
    try:
        print(f"PID: {proc.info['pid']}\n"
              f"Process İsmi: {proc.info['name']}\n"
              f"İşlemci Yüzdeliği: {proc.info['cpu_percent']}\n"
              f"Process'in Yüzdesi: {proc.info['memory_percent']}\n"
              f"RAM detayları: {proc.info['memory_info']}"
              )
    except(psutil.NoSuchProcess, psutil.AccessDenied):
        pass