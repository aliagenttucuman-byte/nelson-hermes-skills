# Telegram Gateway — Setup y Pairing (Nelson / JARVIS)

## Contexto
Nelson quería que terceros (ej. Pablo, socio) pudieran hablar con JARVIS sin exponer el número personal de Nelson. Telegram resuelve esto limpiamente.

## Bot activo
- **Username:** @Jarvis_Alegent_bot
- **Nombre:** Jarvis
- **ID:** 8903482496
- **Modo:** polling (no webhook)
- **Fecha de activación:** 2026-05-22

## Proceso de setup completo

### 1. Crear bot con BotFather
```
Telegram → @BotFather → /newbot
→ Nombre: Jarvis Alegent Bot (o similar)
→ Username: Jarvis_Alegent_bot
→ Token: (guardado en .env)
```

### 2. Configurar en Hermes
```bash
# Agregar token al .env (estaba comentado por defecto)
sed -i 's/# TELEGRAM_BOT_TOKEN=/TELEGRAM_BOT_TOKEN=<TOKEN>/' ~/.hermes/.env

# Verificar
grep "TELEGRAM_BOT_TOKEN" ~/.hermes/.env | grep -v "^#"
```

### 3. Reiniciar gateway
```bash
systemctl --user restart hermes-gateway
sleep 10
hermes gateway status
```
El restart puede tardar hasta 60-90 segundos si hay agentes activos (draining).

### 4. Verificar conexión
```bash
grep -i "telegram" ~/.hermes/logs/gateway.log | tail -10
# Señal de éxito:
# INFO gateway.platforms.telegram: [Telegram] Connected to Telegram (polling mode)
# INFO gateway.run: ✓ telegram connected
```

### 5. Obtener nombre del bot (confirmación)
```bash
python3 -c "
import urllib.request, json, re
token = open('/home/server/.hermes/.env').read()
match = re.search(r'TELEGRAM_BOT_TOKEN=([^\n]+)', token)
if match:
    t = match.group(1)
    res = urllib.request.urlopen(f'https://api.telegram.org/bot{t}/getMe').read()
    print(json.loads(res)['result'])
"
```

## Flujo de pairing para nuevos usuarios

Cuando alguien le escribe al bot por primera vez:

```bash
# Ver solicitudes pendientes
hermes pairing list

# Salida ejemplo:
# Platform  Code      User ID     Name           Age
# telegram  65N8SWBB  8896858194  Nelson Acosta  1m ago

# Aprobar (IMPORTANTE: incluir plataforma como primer arg)
hermes pairing approve telegram 65N8SWBB

# ❌ INCORRECTO (falla):
hermes pairing approve 65N8SWBB
```

## Notas de privacidad
- El bot NO expone el número de teléfono de Nelson
- Los usuarios de Telegram solo ven el nombre y username del bot
- Nelson controla quién tiene acceso via el flujo de pairing
- Cada usuario aprobado queda persistido — no necesita re-aprobación
