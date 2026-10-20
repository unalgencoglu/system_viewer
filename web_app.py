from flask import Flask, render_template, jsonify
import platform
import psutil, time

app = Flask(__name__)

def uptime_str():
    saniye = int(time.time() - psutil.boot_time())
    return f"{saniye // 3600}s {saniye % 3600 // 60}dk"

def get_os_info():
    sistem = platform.system()  
    if sistem == "Linux":
        try:
            r = platform.freedesktop_os_release()  
            ad = r.get("PRETTY_NAME", "Linux")     
        except OSError:
            ad = "Linux"
        return f"{ad} · {platform.release()}"      
    if sistem == "Windows":
        build = int(platform.version().split(".")[2])
        surum = "11" if build >= 22000 else platform.release()
        return f"Windows {surum} (build {build})"
    return f"{sistem} {platform.release()}"

def get_cpu_model():
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHİNE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            )
            return winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except Exception:
            return platform.processor() or "Bilinmeyen İşlemci"
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":")[1].strip()
    except Exception:
        pass
    return "Bilinmeyen İşlemci"

@app.route("/api/system")
def api_system():
    os_info = get_os_info()
    uptime = uptime_str()

    return jsonify({
        "os": os_info, 
        "uptime": uptime
    })

@app.route("/api/stats")
def  api_cpu():
    cpu_usage = psutil.cpu_percent(interval=None)
    cpu_model = get_cpu_model()
    core_count = psutil.cpu_count(logical=True)
    per_core = psutil.cpu_percent(interval=None, percpu=True)

    mem = psutil.virtual_memory()
    total_gb = round(mem.total / (1024 ** 3), 2)
    used_gb = round(mem.used / (1024 ** 3), 2)
    ram_percent = mem.percent

    return jsonify({
        "cpu": {
            "percent": cpu_usage,
            "model": cpu_model,
            "cores": core_count,
            "per_core": per_core
        },
        "ram": {
            "percent": ram_percent,
            "used_gb": used_gb,
            "total_gb": total_gb
        }
    })

@app.route("/")
def anasayfa():
    return render_template('index.html')

@app.route("/ayarlar")
def ayarlar():
    return render_template('ayarlar.html')

if __name__ == '__main__':
    app.run(debug=True)