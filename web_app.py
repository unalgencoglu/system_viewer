from flask import Flask, render_template, jsonify, abort, request

# Veriler collector paketinden gelir: Linux'ta /proc okunur, Windows'ta psutil kullanılır.
from collector import get_system_info, get_system_stats, get_processes, get_process_detail, control_process

app = Flask(__name__)


@app.route("/api/system")
def api_system():
    return jsonify(get_system_info())


@app.route("/api/stats")
def api_stats():
    return jsonify(get_system_stats())


@app.route("/api/processes")
def api_processes():
    return jsonify(get_processes())


@app.route("/api/process/<int:pid>")
def api_process(pid):
    detail = get_process_detail(pid)
    if detail is None:
        abort(404)
    return jsonify(detail)


@app.route("/api/process/<int:pid>/action", methods=["POST"])
def api_process_action(pid):
    """
    Gövde (JSON): {"action": "terminate" | "kill" | "suspend" | "resume" | "nice", "nice": 10}
    """
    body = request.get_json(silent=True) or {}
    ok, message = control_process(pid, body.get("action"), body.get("nice"))
    return jsonify({"ok": ok, "message": message}), (200 if ok else 400)


@app.route("/")
def anasayfa():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
