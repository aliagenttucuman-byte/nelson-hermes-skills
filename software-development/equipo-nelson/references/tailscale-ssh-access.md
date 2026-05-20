# Acceso Remoto al Servidor via Tailscale + SSH

## Estado actual (Mayo 2026)
- Servidor `ai-server` está en la red Tailscale de la cuenta `aliagenttucuman@gmail.com`
- IP Tailscale del servidor: `100.110.8.13`
- Windows de Nelson (nelsondev): `100.76.143.33`
- SSH activo via socket (systemd), puerto 22

## Desde Windows
1. Instalar Tailscale (ya instalado en nelsondev)
2. Conectar con cuenta `aliagenttucuman@gmail.com`
3. Abrir PowerShell: `ssh server@100.110.8.13`
4. Contraseña: `srv2026`

Alias opcional en `C:\Users\<usuario>\.ssh\config`:
```
Host ai-server
    HostName 100.110.8.13
    User server
```
Luego: `ssh ai-server`

## Desde Android
1. Instalar **Tailscale** (Play Store) → login con `aliagenttucuman@gmail.com`
2. Instalar **JuiceSSH** o **Termius** (ambos gratuitos, JuiceSSH más simple)
3. Nueva conexión SSH:
   - Host: `100.110.8.13`
   - Usuario: `server`
   - Contraseña: `srv2026`
   - Puerto: 22

## Pitfalls
- **SSH inactivo:** `sudo systemctl start ssh` — el servicio está configurado via socket (activo aunque aparezca "inactive")
- **Timeout de conexión:** Verificar que Tailscale esté conectado en el cliente. Si la IP del cliente no aparece en `tailscale status`, no está en la red.
- **Cuenta equivocada:** La red Tailscale original era de `pabloeorellana@`. Se migró a `aliagenttucuman@`. Si alguien se conecta con la cuenta de Pablo, no verá el servidor.
- **Reasignar el servidor a otra cuenta Tailscale:**
  ```bash
  sudo tailscale logout
  sudo tailscale up  # abre URL para autenticar
  # Visitar la URL en el navegador y loguear con la cuenta deseada
  ```
