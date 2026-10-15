# Burada hangi fonksiyonun ne işe yaradığı ve nasıl kullanıldığı yer alıyor.

# cpu_percent():
interval ile verilen süre içinde
CPU'nun kullanım yüzdesini verir

psutil.cpu_percent(interval=1) örneğin 1 saniye

# cpu_count():
Sistemin kaç çekirdeği olduğunu gösterir

psutil.cpu_count(logical=True) logical=True sanal çekirdekleri de gösterir

-------------
------------------
# virtual_memory():
Kapsamlı istatistikleri verir

psutil.virtual_memory()

# Bazı alt fonksiyonları:
x = psutil.virtual_memory()

x.total -> Sistemdeki toplam fiziksel RAM miktarı (Byte cinsinden verilir)

x.available -> Sistemdeki herhangi bir ek işleme maruz kalmadan 
               kullanılabilecek gerçek bellek miktarıdır
               (swap alanı olmadan kullanılabilecek alan) 

x.used -> O anda kullanılan bellek miktarıdır

x.free -> Tamamen boş duran bellek alanı

x.percent -> Sistemin genel doluluk oranıdır
------------------
-------------

-------------
------------------
# proccess_iter():
Processleri yazan bir fonksiyondur, bu fonksiyon bazı parametreler alabilir

# Verilebilecek parametreler:
'pid' process id, 'name' process'in dosya adı, 'status' process'in durumu
'cpu_percent' process'in işlemci kullanım yüzdesi
'memory_percent' process'in toplam RAM'e göre yüzdesi
'memory_info' fiziksel RAM ve sanal bellek kullanım detayları ...

psutil.process_iter(['pid', 'name', 'cpu_percent' ...])
[:5] -> 5 tanesini döner
------------------
-------------