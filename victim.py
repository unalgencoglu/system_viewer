import time
import os

print(f"[Hedef Süreç Başladı] PID: {os.getpid()}")
sayac = 0

while True:
    sayac += 1
    print(f"Hedef çalışıyor... Adım: {sayac}")
    time.sleep(1)