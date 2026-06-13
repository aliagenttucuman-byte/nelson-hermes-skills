# Troubleshooting: Gateway Caído (Puerto 3001 No Responde)

Secuencia de diagnóstico validada en junio 2026.

## Síntoma

- `curl http://localhost:3001/health` no responde o devuelve `{"status":"disconnected"}`.
- El bridge de Hermes en puerto 3000 sigue funcionando (`connected`).
- Mensajes automatizados no llegan a contactos externos.

## Paso 1: Verificar proceso

```bash
lsof -i :3001 || ss -tlnp | grep 3001
ps aux | grep -E "node.*server\.js|baileys" | grep -v grep
```

Si no hay proceso escuchando en 3001, el gateway está muerto.

## Paso 2: Verificar dependencias Node

```bash
cd /ruta/al/whatsapp-gateway
ls node_modules 2>/dev/null || echo "FALTAN node_modules"
ls package.json 2>/dev/null || echo "FALTA package.json"
```

Si faltan, instalar:
```bash
npm init -y
npm install @whiskeysockets/baileys express qrcode
```

## Paso 3: Verificar auth corrupto (si el proceso existe pero dice disconnected)

Revisar logs del gateway. Si aparece:
- `Bad MAC`
- `No matching sessions found for message`
- `stream errored out (conflict, type: replaced)`

Entonces el directorio `auth/` está corrupto o desincronizado.

## Paso 4: Limpiar auth y re-vincular

```bash
# 1. Parar cualquier proceso node en el directorio del gateway
pkill -f "node.*whatsapp-gateway"

# 2. Borrar sesión corrupta
rm -rf /ruta/al/whatsapp-gateway/auth/*

# 3. Generar QR nuevo
node connect.js
```

Escaneá el QR que se guarda en `qr.png`. Una vez conectado, `connect.js` sale solo.

## Paso 5: Levantar server.js permanente

```bash
node server.js
```

Verificar:
```bash
curl -s http://localhost:3001/health   # Debe responder {"status":"connected"}
curl -s -X POST http://localhost:3001/send \
  -H "Content-Type: application/json" \
  -d '{"to":"549...", "message":"Test"}'
```

## Secuencia rápida (todo en uno)

```bash
cd /ruta/al/whatsapp-gateway
pkill -f "node.*whatsapp-gateway"
rm -rf auth/*
node connect.js &
sleep 8
curl -s http://localhost:3001/health
```

> Nota: `connect.js` espera conexión y sale solo tras 5 segundos. Después de eso se puede arrancar `server.js` para la API permanente.
