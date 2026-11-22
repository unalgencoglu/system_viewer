# Process Controller

Linux ve Windows üzerinde çalışan süreçleri ve kaynak kullanımını izleyen,
süreçleri web arayüzünden yönetmeyi sağlayan bir performans izleyici.
İşletim Sistemleri dersi projesi.

## Amaç

İşletim sisteminin süreçleri nasıl yönettiğini ve kaynak kullanımı
bilgisini nasıl tuttuğunu öğrenmek; bu bilgiyi toplayıp gösteren bir
izleme aracı geliştirmek.

Bu yüzden Linux'ta veriler hazır bir kütüphaneden alınmaz, doğrudan
çekirdeğin sunduğu **`/proc`** dosya sisteminden okunur:

| Bilgi | Kaynak |
|---|---|
| Süreç listesi | `/proc/<pid>/` klasörleri |
| Durum, CPU süresi (utime, stime), thread, bellek | `/proc/<pid>/stat` |
| Kullanıcı, RSS, sanal bellek | `/proc/<pid>/status` |
| Açık dosyalar | `/proc/<pid>/fd/` |
| Genel CPU kullanımı | `/proc/stat` |
| Genel bellek | `/proc/meminfo` |

CPU yüzdesi iki ölçüm arasındaki farktan hesaplanır:

```
CPU% = Δ(sürecin CPU süresi) / Δ(toplam CPU süresi) × 100
```

Süreç kontrolü Linux'ta sinyallerle (`kill()`) ve `setpriority()` sistem
çağrısıyla yapılır. Windows'ta `/proc` olmadığı için aynı bilgiler
`psutil` (arka planda WinAPI) ile toplanır.

## Özellikler

- Canlı CPU ve RAM kartları, grafikler, çekirdek başına kullanım
- Süreç tablosu: PID, isim, kullanıcı, durum (R, S, D, Z, T), CPU %, RAM %, açık dosya sayısı
- Tabloda arama ve sütuna göre sıralama
- Süreç detayı: dosya yolu, komut, PPID, nice, başlama zamanı, RSS / VMS, açık dosyalar
- Süreç kontrolü: duraklat, devam ettir, sonlandır, zorla kapat, öncelik (nice) değiştir
- Açık / koyu tema

## Kurulum ve çalıştırma

Python 3.10 veya üzeri gerekir.

### Linux (Kali, Ubuntu)

```bash
python3 -m venv venv
source venv/bin/activate
pip install flask
python web_app.py
```

`venv` oluşturulamazsa önce `sudo apt install python3-venv` çalıştırın.

Başka kullanıcılara ait süreçlerin açık dosyalarını görmek ve onları
yönetmek için root yetkisi gerekir:

```bash
sudo venv/bin/python web_app.py
```

### Windows

```bat
python -m venv venv
venv\Scripts\activate.bat
pip install flask psutil
python web_app.py
```

Sistem süreçlerini yönetmek için terminali yönetici olarak açın.

Sunucu çalıştıktan sonra tarayıcıda **http://127.0.0.1:5000** adresine gidin.

## Proje yapısı

```
collector/
  __init__.py   # işletim sistemine göre toplayıcıyı seçer
  base.py       # ortak veri biçimi ve yardımcı fonksiyonlar
  linux.py      # /proc okuyan toplayıcı ve sinyalle süreç kontrolü
  windows.py    # psutil ile toplayıcı
web_app.py      # Flask sunucusu ve API
templates/      # HTML şablonları
static/         # CSS ve JavaScript
```

## API

| Yöntem | Adres | Açıklama |
|---|---|---|
| GET | `/api/system` | İşletim sistemi ve çalışma süresi |
| GET | `/api/stats` | CPU ve RAM kullanımı |
| GET | `/api/processes` | Süreç tablosu |
| GET | `/api/process/<pid>` | Süreç detayı ve açık dosyalar |
| POST | `/api/process/<pid>/action` | Süreç kontrolü. Gövde: `{"action": "suspend" \| "resume" \| "terminate" \| "kill" \| "nice", "nice": 10}` |
