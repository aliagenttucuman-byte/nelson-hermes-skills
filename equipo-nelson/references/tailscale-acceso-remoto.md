# Tailscale — Acceso Remoto al Servidor

## Estado actual

- **Tailscale instalado:** `/usr/bin/tailscale`
- **IP del servidor:** `100.122.52.55`
- **Hostname:** `ai-server`
- **Estado del daemon:** `active` + `enabled` (arranca con el sistema)
- **Cuenta propietaria:** `pabloeorellana@` — OJO: la red está bajo la cuenta de Pablo

## Cómo conectarse por SSH

```bash
# Por IP
ssh server@100.122.52.55

# Por hostname (si Tailscale DNS está activo)
ssh server@ai-server
```

## Dispositivos en la red Tailscale

| Hostname | IP | OS | Estado |
|----------|----|----|--------|
| ai-server | 100.122.52.55 | Linux | online |
| casasrv01 | 100.111.193.67 | Windows | offline |
| macbook-air-de-pablo-2 | 100.75.252.68 | macOS | offline |
| soportecampus | 100.67.36.92 | Windows | offline |

## Alerta: red bajo cuenta de Pablo

La red Tailscale está registrada bajo la cuenta de `pabloeorellana@`. Esto significa:
- Pablo tiene control administrativo de la red
- Si Pablo elimina el servidor de la red, Nelson pierde acceso remoto
- **Recomendación pendiente:** evaluar si conviene migrar a una cuenta propia de Nelson o mantener acceso garantizado de otra forma (usuario admin adicional en la red)

## Verificar estado

```bash
tailscale status
tailscale ip
```
