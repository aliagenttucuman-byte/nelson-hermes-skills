"""
spa_proxy.py — Mini-proxy para SPA + API separadas.

Sirve el frontend dist (con SPA fallback a index.html) y proxyea /api/* al backend.
Un solo puerto → un solo tunnel de Cloudflare. Sin Docker, sin nginx, sin caddy.

Uso:
    # 1. Editar las 3 constantes de arriba (FRONTEND_DIST, BACKEND_URL, PORT)
    # 2. Levantar:
    python3 spa_proxy.py &
    # 3. Tunnel:
    cloudflared tunnel --url http://localhost:9090 2>&1 | tee /tmp/cf_proyecto.log &

Cuándo usar: ver nelson-cloudflare-tunnel-deploy, sección "Patrón Alternativo 2".
"""
import http.server
import socketserver
import urllib.request
import urllib.error
import os
import sys

# === CONFIGURAR ACÁ ===
FRONTEND_DIST = "/home/server/proyectos/MI-PROYECTO/frontend/dist"
BACKEND_URL = "http://localhost:9000"  # puerto del backend uvicorn
PORT = 9090  # puerto donde escuchará el proxy
# =====================

INDEX_HTML = os.path.join(FRONTEND_DIST, "index.html")


class SPAProxyHandler(http.server.SimpleHTTPRequestHandler):
    """Sirve archivos del dist con SPA fallback. Proxyea /api/* al backend."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIST, **kwargs)

    # --- Frontend: servir dist con SPA fallback ---
    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy("GET")
            return
        # SPA fallback: si el path no existe como archivo del dist, servir index.html
        rel = self.path.lstrip("/").split("?")[0]
        if rel and not os.path.exists(os.path.join(FRONTEND_DIST, rel)):
            self.path = "/index.html"
        return super().do_GET()

    # --- API: proxy al backend ---
    def do_POST(self):
        if self.path.startswith("/api/"):
            self._proxy("POST")
            return
        self.send_error(404)

    def do_PUT(self):
        if self.path.startswith("/api/"):
            self._proxy("PUT")
            return
        self.send_error(404)

    def do_DELETE(self):
        if self.path.startswith("/api/"):
            self._proxy("DELETE")
            return
        self.send_error(404)

    def do_PATCH(self):
        if self.path.startswith("/api/"):
            self._proxy("PATCH")
            return
        self.send_error(404)

    def do_OPTIONS(self):
        # CORS preflight
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def _proxy(self, method):
        """Proxy transparente al backend."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        target = BACKEND_URL + self.path
        req = urllib.request.Request(target, data=body, method=method)
        # Reenviar headers (excluir Host y Content-Length que urllib maneja)
        for h, v in self.headers.items():
            if h.lower() not in ("host", "content-length"):
                req.add_header(h, v)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = resp.read()
                self.send_response(resp.status)
                for h, v in resp.headers.items():
                    if h.lower() not in ("transfer-encoding", "content-encoding", "connection"):
                        self.send_header(h, v)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        except urllib.error.HTTPError as e:
            payload = e.read() if e.fp else b""
            self.send_response(e.code)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            err = f'{{"detail":"proxy error: {e}"}}'.encode()
            self.send_header("Content-Length", str(len(err)))
            self.end_headers()
            self.wfile.write(err)

    def log_message(self, format, *args):
        # Log compacto y legible
        sys.stderr.write(f"[spa-proxy] {self.address_string()} {format % args}\n")


if __name__ == "__main__":
    if not os.path.isdir(FRONTEND_DIST):
        print(f"ERROR: FRONTEND_DIST no existe: {FRONTEND_DIST}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(INDEX_HTML):
        print(f"ERROR: falta index.html en {FRONTEND_DIST} — ¿hiciste npm run build?", file=sys.stderr)
        sys.exit(1)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), SPAProxyHandler) as httpd:
        print(f"✓ SPA proxy listening on 0.0.0.0:{PORT}")
        print(f"  Frontend dist: {FRONTEND_DIST}")
        print(f"  Backend:       {BACKEND_URL}")
        print(f"  Routes:        /api/* → backend, /* → SPA fallback")
        print(f"  Tunnel:        cloudflared tunnel --url http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
