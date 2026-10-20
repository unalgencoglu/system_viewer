from flask import Flask, render_template, jsonify
import psutil

app = Flask(__name__)

def get_cpu_model():
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":")[1].strip()
    except Exception:
        pass
    return "Bilinmeyen İşlemci"

@app.route("/api/cpu")
def  api_cpu():
    cpu_usage = psutil.cpu_percent(interval=0.5)
    cpu_model = get_cpu_model()
    core_count = psutil.cpu_count(logical=True)

    return jsonify({
        "percent": cpu_usage,
        "model": cpu_model,
        "cores": core_count
    })

@app.route("/")
def anasayfa():
    return render_template('index.html')

@app.route("/ayarlar")
def ayarlar():
    return render_template('ayarlar.html')

if __name__ == '__main__':
    app.run(debug=True)