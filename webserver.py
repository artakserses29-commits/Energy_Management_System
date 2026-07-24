import json
import os
import mimetypes
import socket
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from config.settings import FLASK_HOST, FLASK_PORT
from core.shared_state import set_mode
from data.database import Database

HERE = Path(__file__).parent
STATIC_DIR = HERE / "web" / "static"
TEMPLATES_DIR = HERE / "web" / "templates"
LOCALES_DIR = HERE / "web" / "locales"

db = Database()


def load_template(name, lang="fr"):
    path = TEMPLATES_DIR / name
    if not path.exists():
        return "<h1>404</h1>"
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    locale_file = LOCALES_DIR / f"{lang}.json"
    locale = {}
    if locale_file.exists():
        with open(locale_file, "r", encoding="utf-8") as f:
            locale = json.load(f)

    for key, val in locale.items():
        html = html.replace("{{ locale." + key + " }}", val)

    html = html.replace("{{ lang }}", lang)

    js_files = []
    for js_name in ["dashboard.js", "charts.js", "socket-client.js"]:
        js_path = STATIC_DIR / "js" / js_name
        if js_path.exists():
            js_files.append(js_path.read_text(encoding="utf-8"))

    html = html.replace("</body>", f"<script>{''.join(js_files)}</script></body>")
    return html


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.route()
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def do_POST(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len) if content_len else b"{}"
            data = json.loads(body) if body else {}
            self.route_post(data)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def route(self):
        path = self.path.split("?")[0]

        if path == "/":
            html = load_template("dashboard.html")
            self.send_html(html)

        elif path == "/lang/fr":
            self.send_file(LOCALES_DIR / "fr.json", "application/json")
        elif path == "/lang/en":
            self.send_file(LOCALES_DIR / "en.json", "application/json")

        elif path == "/api/status":
            etat, mesures = db.get_status_snapshot()
            status = {
                "current_state": etat.get("source_active", "solaire"),
                "mode": etat.get("mode", "auto"),
                "manual_source": None,
                "relay_states": {
                    "solaire": etat.get("source_active") == "solaire",
                    "batterie": etat.get("source_active") == "batterie",
                    "jirama": etat.get("source_active") == "jirama",
                    "groupe": etat.get("source_active") == "groupe",
                },
            }
            self.send_json({"status": status, "mesures": mesures})

        elif path.startswith("/api/mesures"):
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            source = qs.get("source", [None])[0]
            limit = int(qs.get("limit", [50])[0])
            if source:
                data = db.get_recent_mesures(source, limit)
            else:
                data = {}
                for s in ("solaire", "batterie", "jirama", "groupe", "consommation"):
                    data[s] = db.get_recent_mesures(s, limit)
            self.send_json(data)

        elif path == "/api/etats":
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            limit = int(qs.get("limit", [50])[0])
            self.send_json(db.get_recent_etats(limit))

        elif path == "/api/evenements":
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            limit = int(qs.get("limit", [50])[0])
            self.send_json(db.get_evenements(limit))

        elif path == "/api/previsions":
            self.send_json(db.get_previsions(5))

        elif path == "/api/derniere-prevision":
            self.send_json(db.get_derniere_prevision())

        elif path.startswith("/static/"):
            rel = path[len("/static/"):]
            filepath = STATIC_DIR / rel
            self.send_file(filepath)

        else:
            self.send_html("<h1>404</h1>", 404)

    def route_post(self, data):
        path = self.path.split("?")[0]
        if path == "/api/mode":
            mode = data.get("mode", "auto")
            source = data.get("source")
            set_mode(mode, source)
            db.insert_evenement("mode", f"Mode: {mode} source: {source}", "info")
            self.send_json({"success": True})
        else:
            self.send_json({"error": "not found"}, 404)

    def send_html(self, html, status=200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, filepath, mime=None):
        filepath = Path(filepath)
        if not filepath.exists() or not filepath.is_file():
            self.send_html("<h1>404</h1>", 404)
            return
        if mime is None:
            mime, _ = mimetypes.guess_type(str(filepath))
            if mime is None:
                mime = "application/octet-stream"
        body = filepath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "max-age=3600")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[HTTP] {args[0]} {args[1]} {args[2]}")


def run_server(host="127.0.0.1", port=5000):
    server = HTTPServer((host, port), Handler)
    print(f"Serveur web: http://{host}:{port}")
    print(f"Ouvrez http://127.0.0.1:{port} dans votre navigateur.")
    print("Ctrl+C pour arreter.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("Serveur arrete.")


if __name__ == "__main__":
    run_server()
