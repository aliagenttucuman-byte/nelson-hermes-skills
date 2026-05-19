# Sincronización de Vault/Carpeta vía Syncthing + Tailscale

> Contexto: Tony quiere usar Obsidian (app GUI) en su Windows, pero el vault de notas vive en el servidor Linux headless. La solución es Syncthing sobre la red Tailscale.

## Arquitectura

```
┌─────────────────┐         Tailscale VPN         ┌─────────────────┐
│   Windows       │ ◄────────────────────────────► │  Servidor Linux │
│  (nelsondev)    │    Syncthing  TCP 22000       │  (ai-server)    │
│                 │                               │                 │
│  Obsidian GUI   │                               │  Syncthing      │
│    ┌──────┐     │                               │    ┌──────┐     │
│    │Vault │◄────┼──── Syncthing sync ───────────┼───►│Vault │     │
│    └──────┘     │                               │    └──────┘     │
└─────────────────┘                               └─────────────────┘
```

## Por qué no SSHFS-Win

SSHFS-Win es caprichoso en Windows moderno. Requiere WinFsp + SSHFS-Win y a menudo falla al conectar vía `\\sshfs\...`. Syncthing es más robusto y bidireccional automático.

## Setup en el Servidor Linux

```bash
# 1. Descargar Syncthing binary
mkdir -p ~/Applications
curl -L -o syncthing.tar.gz "https://github.com/syncthing/syncthing/releases/download/v1.29.4/syncthing-linux-amd64-v1.29.4.tar.gz"
tar -xzf syncthing.tar.gz
mv syncthing-linux-amd64-v*/syncthing ~/syncthing
rm -rf syncthing*

# 2. Generar config inicial (ejecutar una vez para que genere device ID)
~/syncthing -no-browser -home="$HOME/.config/syncthing"
# matar con Ctrl+C después de 5 segundos

# 3. Obtener device ID
cat ~/.config/syncthing/config.xml | grep -o 'device id="[^"]*"' | head -1
# Ejemplo: ZY6VMV5-5N45Y5N-XXUC4FN-DVD3XWO-OFUSUM6-AKMX4PE-JCITVFR-6AC5AAW

# 4. Exponer GUI en Tailscale IP (opcional, para acceso web remoto)
# Editar config.xml: cambiar <address>127.0.0.1:8384</address> a <address>0.0.0.0:8384</address>

# 5. Ejecutar como background process
~/syncthing -no-browser -home="$HOME/.config/syncthing"
```

## Setup en Windows

1. Descargar **Synctrayz** o **Syncthing Windows** desde https://syncthing.net/downloads/
2. Ejecutar, obtener Device ID desde el panel web (http://localhost:8384 → Actions → Show ID)
3. Agregar el ID del servidor como remote device → aparece petición de conexión en el servidor
4. En el servidor, aceptar la conexión y compartir la carpeta deseada
5. En Windows, aceptar la carpeta compartida y elegir ruta local de destino

## Configuración de carpeta en el servidor (config.xml)

```xml
<folder id="brainstorming" label="Brainstorming I+D+I" path="/home/server/brainstorming"
        type="sendreceive" rescanIntervalS="60" fsWatcherEnabled="true">
    <device id="ID-DEL-SERVIDOR"/>
    <device id="ID-DEL-WINDOWS"/>
</folder>
```

## URLs de acceso

- Panel web local: http://localhost:8384
- Panel web del servidor vía Tailscale: http://100.110.8.13:8384

## Troubleshooting

| Síntoma | Causa probable | Fix |
|---|---|---|
| "unshared" en la carpeta | El dispositivo Windows no está en `<folder><device>` | Agregar el device ID de Windows a la lista de devices de la carpeta en config.xml |
| Devices no se ven | Global announce deshabilitado o redes separadas | Ambos dispositivos en misma red Tailscale, o habilitar relays |
| Config inválida al editar a mano | Device ID mal formateado o longitud incorrecta | Usar ID exacto que genera Syncthing, nunca inventar |
