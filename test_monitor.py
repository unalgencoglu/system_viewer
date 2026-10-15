import psutil
import time

print("---SİSTEM BİLGİLERİ ALINIYOR---")

cpu_kullanimi = psutil.cpu_percent(interval=1) #interval=1, 1 saniye boyunca CPU kullanımını ölçer
cekirdek_sayisi = psutil.cpu_count(logical=True) #Sistemdeki çekirdek sayısını verir
print(f"Mantıksal Çekirdek Sayısı: {cekirdek_sayisi}")
print(f"Toplam CPU Kullanımı: %{cpu_kullanimi}")

bellek = psutil.virtual_memory() #Toplam fiziksel bellek, boş alan ve yüzdelik kullanım oranını çeker

"""
    Linux bize bu bilgileri Byte cinsinden
    verdiği için bunu GigaByte'a çeviriyoruz
    1024 ** 3 = 1024 * 1024 * 1024
"""

toplam_gb = bellek.total / (1024 ** 3)
kullanilan_gb = bellek.used / (1024 ** 3)
print(f"Toplam RAM: {toplam_gb:.2f} GB")
print(f"Kullanılan RAM: {kullanilan_gb:.2f} GB (%{bellek.percent})") #bellek.percent RAM'in doluluk oranını doğrudan verir

print("--- ÇALIŞAN İLK 5 SÜREÇ ---")
"""
    Burada psutil.process_iter ile linuxta çalışan tüm processleri 
    gezen bir döngü kuruyoruz, fakat burada performanslı olması için 
    yalnızca pid, name ve cpu_percent bilgilerini alıyoruz
"""
for proc in list(psutil.process_iter(['pid', 'name', 'cpu_percent']))[:5]: 
    try:
        print(f"PID: {proc.info['pid']} | İsim: {proc.info['name']}")
    except(psutil.NoSuchProcess, psutil.AccessDenied):
        pass

"""
    Süreçler sürekli değişim halinde olduğu için taradığımız süreç kapandığı
    zaman programın bozulmaması için bir try - except kontrolü kurduk
    NoSuchProcess -> Süreç bulunamadı
    AccessDenied -> Erişim engeli olursa 
"""