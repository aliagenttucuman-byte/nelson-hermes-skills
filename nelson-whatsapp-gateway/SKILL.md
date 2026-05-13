---
name: nelson-whatsapp-gateway
description: WhatsApp Gateway con Baileys para el equipo Nelson. Envía mensajes a cualquier número desde scripts Python/Node.js sin depender de la conexión nativa de Hermes.
category: software-development
tags: [whatsapp, baileys, messaging, gateway, nodejs, automation]
related_skills: [nelson-automation-n8n, nelson-external-communication]
---

# WhatsApp Gateway (Baileys)

> **Trigger:** Cada vez que Tony necesita enviar mensajes de WhatsApp desde un script propio a números arbitrarios, fuera del flujo nativo de Hermes.

## Propósito

Baileys es una librería Node.js no oficial que se conecta a WhatsApp Web. Una vez vinculado, expone una mini API HTTP que cualquier script Python puede consumir para enviar mensajes a cualquier número.

Alternativas evaluadas:
- **WhatsApp Business API (Meta)**: oficial pero burocrática. Requiere negocio verificado, número fijo, y pago por mensaje.
- **Baileys**: no oficial, sin costo por mensaje, más flexible. Es la opción preferida del equipo.

## Instalación

```bash
mkdir -p whatsapp-gateway && cd whatsapp-gateway
npm init -y
npm install @whiskeysockets/baileys qrcode
```

Requiere Node.js 18+.

## Flujo de conexión

### Paso 1: Generar código de emparejamiento o QR

Baileys ofrece dos métodos de vinculación:

1. **Código de emparejamiento (preferido)**: 8 dígitos numéricos. El usuario va a WhatsApp → ⋮ → Dispositivos vinculados → Vincular con número de teléfono, e ingresa el código.
2. **QR**: se guarda como imagen PNG. El usuario escanea con la cámara del celular.

Ver `references/connect-example.js` para el script completo.

### Paso 2: Vincular

El script genera el código/QR y queda esperando. Una vez vinculado desde el celular, la sesión se guarda en `auth/` (MultiFileAuthState). De ahí en más, reconexiones son automáticas.

### Paso 3: Exponer API HTTP

Una vez conectado, se levanta un servidor Express (u otro framework) que escucha endpoints tipo:

```
POST /send
{
  "number": "5493816240691",
  "message": "Hola desde el gateway"
}
```

## Pitfalls

- **Códigos expiran en ~40 segundos**. El usuario debe ingresarlo inmediatamente. Si expira, hay que matar el proceso, limpiar `auth/` y reiniciar.
- **WhatsApp tiene límite de 4 dispositivos vinculados**. Si el usuario ya tiene 4, debe desvincular alguno antes de intentar de nuevo.
- **Si falla el código de emparejamiento, hacer fallback a QR**. Algunas cuentas no admiten pairing code y requieren QR.
- **No usar `printQRInTerminal` en Baileys moderno**. Está deprecado. Escuchar el evento `connection.update` con `qr` y generar la imagen manualmente con `qrcode`.
- **Si da "Connection Failure" / "not logged in"**: limpiar `auth/` y reiniciar el proceso. El state corrupto bloquea reconexiones.
- **El QR se guarda en archivo PNG** porque el usuario puede no estar mirando la terminal (GNOME, otras apps abiertas). Abrir automáticamente con `xdg-open` si es posible.
- **NO usar `&` o `nohup` en comandos de terminal Hermes**. Hermes bloquea backgrounding en foreground commands. Usar `execute_code` con `subprocess.Popen(..., start_new_session=True)` para levantar el servidor, luego verificar con health checks separados.
- **Health check con Python `urllib`** en vez de `curl` desde terminal cuando el servidor corre en background — más fiable dentro del entorno de Hermes.

## API HTTP completa (Express)

Una vez conectado Baileys, exponer endpoints:

```
GET  /health          -> {"status": "connected"}
POST /send            -> {"to": "549...", "message": "Hola"}
POST /send-batch      -> {"recipients": [{"to": "...", "message": "..."}], "delayMs": 2000}
```

Ver `references/whatsapp-api-server.js` para el servidor completo listo para copiar.

## Script Python helper

Ver `references/send_whatsapp.py` — script standalone que consume la API local sin dependencias externas (solo stdlib). Soporta envío individual y batch a múltiples números.

Ejemplo de uso desde cualquier script del equipo:
```bash
python3 send_whatsapp.py --to 5493816240691 --message "Hola desde el equipo!"
python3 send_whatsapp.py --to 5493816240691,5493811234567 --message "Broadcast!" --batch --delay 2000
```

## Arrancar el servidor en background (patrón Hermes)

Hermes no permite `&` ni `nohup` en comandos de terminal. El patrón correcto:

```python
import subprocess
proc = subprocess.Popen(
    ["node", "server.js"],
    cwd="/ruta/al/gateway",
    stdout=open("/tmp/wa-server.log", "w"),
    stderr=subprocess.STDOUT,
    start_new_session=True
)
```

Luego verificar estado con `urllib.request.urlopen("http://localhost:3001/health")`.

## Auto-arranque con systemd (recomendado)

Para que el gateway se levante solo al encender la PC y se reinicie si falla:

1. Crear `~/.config/systemd/user/whatsapp-gateway.service`:

```ini
[Unit]
Description=WhatsApp Gateway (Baileys)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/server/brainstorming/.../whatsapp-gateway
ExecStart=/usr/bin/node server.js
Restart=on-failure
RestartSec=5
Environment=NODE_ENV=production

[Install]
WantedBy=default.target
```

2. Verificar que `linger` está habilitado para el usuario (`/var/lib/systemd/linger/server` debe existir; si no, `sudo loginctl enable-linger server`).

3. Recargar, habilitar e iniciar:

```bash
systemctl --user daemon-reload
systemctl --user enable whatsapp-gateway.service
systemctl --user start whatsapp-gateway.service
```

**Comandos útiles:**
```bash
systemctl --user status whatsapp-gateway   # Ver estado
systemctl --user restart whatsapp-gateway  # Reiniciar
systemctl --user stop whatsapp-gateway     # Parar
```

> **Pitfall:** Si hay un proceso viejo escuchando en el puerto 3001, el nuevo servicio puede quedar en estado "disconnected". Matar el proceso anterior con `kill <PID>` o `pkill -f "node server.js"` y reiniciar el servicio.

## Directorio de contactos

En el script Python helper, mantener un diccionario `CONTACTS` para resolver nombres a números. Esto permite que scripts y comandos usen nombres en lugar de números crudos.

```python
CONTACTS = {
    "pablo": "5493816240691",
    "pablo terian": "5493816240691",
    "terian": "5493816240691",
    "mi socio": "5493816240691",
}
```

Cuando Tony agregue un nuevo contacto del equipo, sumarlo a este diccionario y guardar en memoria de usuario el nombre + número.

## Integración: envío automático desde scripts Python

Cualquier script Python puede enviar mensajes integrando la función `send_whatsapp`:

```python
def send_whatsapp(to: str, message: str):
    data = json.dumps({"to": to, "message": message}).encode("utf-8")
    req = request.Request(
        "http://localhost:3001/send",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

Ejemplo de uso: el AI News Aggregator genera un resumen y al finalizar llama `send_whatsapp` para cada destinatario en `WHATSAPP_RECIPIENTS`.

## Referencias

- `references/connect-example.js` — Script Node.js completo de conexión con QR + código de emparejamiento.
- `references/whatsapp-api-server.js` — Servidor Express completo con endpoints `/send` y `/send-batch`.
- `references/send_whatsapp.py` — Script Python helper para consumir la API sin dependencias.
