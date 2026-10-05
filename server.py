#!/usr/bin/env python3
"""
Layer 2 & 4 Server: server.py
Lightweight HTTP & REST API server for the AI News Dashboard.
Serves static frontend assets, API endpoints (/api/articles, /api/bookmark, /api/sync),
and bridges deterministic pipeline execution with user interactivity.
"""

import os
import sys
import json
import subprocess
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
STORAGE_FILE = os.path.join(BASE_DIR, "data", "articles.json")

def get_articles_data() -> dict:
    if not os.path.exists(STORAGE_FILE):
        # Run pipeline once if storage doesn't exist
        subprocess.run([sys.executable, os.path.join(BASE_DIR, "run_pipeline.py")], check=False)
    
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": str(e), "articles": []}
    return {"articles": [], "total_articles": 0, "last_sync": datetime.now(timezone.utc).isoformat()}

def toggle_bookmark(article_id: str, is_saved: bool) -> dict:
    if not os.path.exists(STORAGE_FILE):
        return {"success": False, "error": "Storage file not found"}

    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        found = False
        saved_at = datetime.now(timezone.utc).isoformat() if is_saved else None

        for art in data.get("articles", []):
            if art["id"] == article_id:
                art["is_saved"] = is_saved
                art["saved_at"] = saved_at
                found = True
                break

        if found:
            temp_file = STORAGE_FILE + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_file, STORAGE_FILE)
            return {"success": True, "id": article_id, "is_saved": is_saved, "saved_at": saved_at}
        else:
            return {"success": False, "error": f"Article {article_id} not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

class DashboardRequestHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_HEAD(self):
        self.do_GET(head_only=True)

    def do_GET(self, head_only=False):
        parsed = urlparse(self.path)
        path = parsed.path

        # REST API: GET /api/articles
        if path == "/api/articles":
            data = get_articles_data()
            payload = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if not head_only:
                self.wfile.write(payload)
            return

        # Serve DesignGuidelines assets (glitter_logo, designlogo, etc.)
        if path.startswith("/DesignGuidelines/") or path in ("/glitter_logo.png", "/designlogo.png", "/designlogo_transparent.png"):
            filename = os.path.basename(path)
            logo_path = os.path.join(BASE_DIR, "DesignGuidelines", filename)
            if not os.path.exists(logo_path):
                logo_path = os.path.join(WEB_DIR, filename)
            if os.path.exists(logo_path) and os.path.isfile(logo_path):
                mime_type, _ = mimetypes.guess_type(logo_path)
                if not mime_type:
                    mime_type = "image/png"
                with open(logo_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                if not head_only:
                    self.wfile.write(content)
                return

        # Static assets inside web/
        if path == "/" or path == "":
            rel_file = "index.html"
        else:
            rel_file = path.lstrip("/")

        file_path = os.path.join(WEB_DIR, rel_file)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "application/octet-stream"
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            if not head_only:
                self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()
            if not head_only:
                self.wfile.write(b"404 Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b"{}"

        try:
            req_json = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            req_json = {}

        # REST API: POST /api/bookmark
        if path == "/api/bookmark":
            article_id = req_json.get("id")
            is_saved = bool(req_json.get("is_saved", False))
            if not article_id:
                res = {"success": False, "error": "Missing article id"}
            else:
                res = toggle_bookmark(article_id, is_saved)
            payload = json.dumps(res).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        # REST API: POST /api/sync
        if path == "/api/sync":
            print("[*] Triggering manual pipeline sync via API...")
            try:
                proc = subprocess.run(
                    [sys.executable, os.path.join(BASE_DIR, "run_pipeline.py")],
                    capture_output=True,
                    text=True,
                    check=False
                )
                success = (proc.returncode == 0)
                data = get_articles_data()
                res = {
                    "success": success,
                    "returncode": proc.returncode,
                    "stdout": proc.stdout[-500:] if proc.stdout else "",
                    "data": data
                }
            except Exception as e:
                res = {"success": False, "error": str(e)}

            payload = json.dumps(res).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        self.send_response(404)
        self.end_headers()

def run(port=PORT):
    server_address = ("", port)
    httpd = HTTPServer(server_address, DashboardRequestHandler)
    print(f"[+] AI News Dashboard Server running at http://localhost:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Stopping server.")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run(port)
