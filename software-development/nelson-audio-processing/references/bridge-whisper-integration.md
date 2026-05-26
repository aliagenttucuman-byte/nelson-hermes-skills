# Integracion Bridge WhatsApp + Whisper Daemon

## Problema Original
Los audios de WhatsApp llegaban como `[audio received]` sin transcripcion. El bridge de Baileys guardaba el archivo en cache pero no lo transcribia antes de entregarlo al agente.

## Solucion Implementada

### 1. Whisper Daemon (`/home/server/whisper_daemon.py`)

Mantiene el modelo cargado en GPU para transcripciones rapidas (<1s despues del primer arranque).

```python
#!/usr/bin/env python3
import json, socket, os, sys
import whisper

HOST = "127.0.0.1"
PORT = 5001
MODEL = "small"  # base es insuficiente para espanol argentino
DEVICE = "cuda"

def log(msg):
    print(f"[whisper-daemon] {msg}", flush=True)

log(f"Cargando modelo Whisper {MODEL} en {DEVICE}...")
model = whisper.load_model(MODEL, device=DEVICE)
log("Modelo listo. Escuchando en {}:{}".format(HOST, PORT))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    while True:
        conn, addr = s.accept()
        with conn:
            data = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
            try:
                req = json.loads(data.decode().strip())
                path = req.get("path", "")
                if not os.path.exists(path):
                    resp = {"error": f"File not found: {path}"}
                else:
                    result = model.transcribe(path, language="es")
                    resp = {"text": result["text"]}
            except Exception as e:
                resp = {"error": str(e)}
            conn.sendall(json.dumps(resp).encode())
```

**Arranque:**
```bash
# Debe mantenerse SIEMPRE corriendo
python3 /home/server/whisper_daemon.py &

# Verificar
curl -s http://127.0.0.1:5001/health 2>/dev/null || python3 -c "import socket; s=socket.socket(); s.connect(('127.0.0.1',5001)); s.close()"
```

### 2. Modificaciones al Bridge (`bridge.js`)

En el handler de mensajes de audio (`messages.upsert`), despues de descargar el archivo, se conecta al daemon y transcribe:

```javascript
// Despues de writeFileSync(filePath, buf);
const transcript = await transcribeAudio(filePath);
if (transcript) {
    body = transcript;
}
```

**Funcion `transcribeAudio`:**
```javascript
async function transcribeAudio(filePath) {
  return new Promise((resolve) => {
    const client = net.createConnection({ host: '127.0.0.1', port: 5001 }, () => {
      client.write(JSON.stringify({ path: filePath }));
      client.end();
    });
    let data = '';
    client.on('data', (chunk) => { data += chunk; });
    client.on('end', () => {
      try {
        const resp = JSON.parse(data);
        if (resp.text) {
          resolve(resp.text.trim());
        } else {
          console.error('[bridge] Whisper daemon error:', resp.error);
          resolve(null);
        }
      } catch (e) {
        console.error('[bridge] Failed to parse whisper response:', e.message);
        resolve(null);
      }
    });
    client.on('error', (err) => {
      console.error('[bridge] Whisper daemon connection error:', err.message);
      resolve(null);
    });
    setTimeout(() => { client.destroy(); resolve(null); }, 10000);
  });
}
```

### 3. Problema Conocido: `fetch failed` de Baileys

Tras reiniciar el bridge, Baileys puede fallar al descargar audios con `fetch failed`.

**Causa:** La sesion de Baileys necesita completar el sync inicial de historial antes de poder descargar media de los servidores de WhatsApp.

**Sintoma en logs:**
```
[bridge] Failed to download audio: fetch failed
```

**Solucion:**
- Esperar 30-60 segundos despues de reiniciar el bridge antes de enviar audios
- O reiniciar el bridge completo (kill + restart) despues de esperar un minuto
- El daemon de Whisper no se ve afectado; el problema es puramente de Baileys descargando la media

## Flujo de Datos

```
Usuario manda audio por WhatsApp
         |
         v
  Baileys recibe mensaje
         |
         v
  Bridge.js descarga a /home/server/.hermes/audio_cache/aud_<hash>.ogg
         |
         v
  Bridge.js conecta a whisper daemon (127.0.0.1:5001)
         |
         v
  Whisper transcribe con modelo cargado en GPU
         |
         v
  Bridge.js entrega texto al gateway de Hermes
         |
         v
  Agente recibe texto transcrito (no [audio received])
```
