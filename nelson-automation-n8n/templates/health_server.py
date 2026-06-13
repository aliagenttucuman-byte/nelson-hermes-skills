#!/usr/bin/env python3
"""
Mini health check server para n8n monitor — puerto 9099
Usar cuando n8n necesita chequear recursos del sistema operativo.
n8n v2.20.6 no tiene executeCommand — este server es el workaround validado.

Levantar:
    python3 health_server.py &

Desde n8n: HTTP Request GET http://172.17.0.1:9099/
"""
import subprocess, json, psutil
from http.server import HTTPServer, BaseHTTPRequestHandler


def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, timeout=5).strip()
    except:
        return "0"


def safe_int(val):
    try:
        return int(val.split()[0])
    except:
        return 0


def get_metrics():
    # interval=None es CRÍTICO — interval=1 bloquea el HTTP thread
    cpu  = str(round(psutil.cpu_percent(interval=None), 1))
    ram  = str(round(psutil.virtual_memory().percent, 1))
    disk = str(round(psutil.disk_usage("/").percent, 1))

    # Servicios del equipo Nelson — ajustar según proyecto
    forestai = run("docker ps --filter name=forestai-poc --filter status=running --format '{{.Names}}' | wc -l")
    bisonte  = run("ss -tlnp 2>/dev/null | grep ':9000' | wc -l")
    whatsapp = run("ss -tlnp 2>/dev/null | grep ':3001' | wc -l")

    alerts = []
    try:
        if float(cpu) > 80: alerts.append(f"CPU: {cpu}% > 80%")
        if float(ram) > 85: alerts.append(f"RAM: {ram}% > 85%")
        if float(disk) > 80: alerts.append(f"Disco: {disk}% > 80%")
    except:
        pass
    if safe_int(forestai) == 0: alerts.append("ForestAI Docker CAIDO")
    if safe_int(bisonte)  == 0: alerts.append("Expreso Bisonte :9000 CAIDO")
    if safe_int(whatsapp) == 0: alerts.append("WhatsApp Gateway :3001 CAIDO")

    return {
        "status": "alert" if alerts else "ok",
        "alerts": alerts,
        "metrics": {"cpu": cpu, "ram": ram, "disk": disk},
        "services": {
            "forestai_docker": safe_int(forestai),
            "bisonte_9000":    safe_int(bisonte),
            "whatsapp_3001":   safe_int(whatsapp),
        }
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def do_GET(self):
        data = json.dumps(get_metrics()).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 9099), Handler)
    print("Health server en :9099")
    server.serve_forever()
