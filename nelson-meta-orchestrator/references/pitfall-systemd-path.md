# Pitfall: PATH incompleto en subprocesses dentro de servicios systemd

## Sintoma

El endpoint SSE devuelve HTTP 200 pero no llegan chunks al frontend.
El cliente queda "procesando" indefinidamente sin recibir ningun dato.

## Causa raiz

Uvicorn corriendo bajo systemd no hereda el PATH del usuario.
Binarios instalados en `~/.local/bin` o dentro de venvs no se encuentran
cuando se los llama por nombre simple en `asyncio.create_subprocess_exec`.

El subprocess se lanza sin lanzar excepcion pero produce stdout vacio
porque el binario no existe en el PATH reducido del servicio.

## Solucion

Usar rutas absolutas en todo `create_subprocess_exec` dentro de servicios systemd:

```python
# MAL - falla silenciosamente bajo systemd
proc = await asyncio.create_subprocess_exec("hermes", "-z", prompt, ...)
proc = await asyncio.create_subprocess_exec("edge-tts", "--voice", ...)

# BIEN - rutas absolutas
proc = await asyncio.create_subprocess_exec(
    "/home/server/.local/bin/hermes", "-z", prompt, ...
)
proc = await asyncio.create_subprocess_exec(
    "/home/server/.hermes/hermes-agent/venv/bin/edge-tts", "--voice", ...
)
```

## Alternativa

Agregar la variable PATH en el archivo .service:

```ini
[Service]
Environment=PATH=/home/server/.local/bin:/home/server/.hermes/hermes-agent/venv/bin:/usr/local/bin:/usr/bin:/bin
```

## Debug rapido

Si un SSE devuelve 200 vacio, verificar con:

```bash
# Testear el binario con el mismo usuario del servicio
sudo -u server /ruta/al/binario --version

# Ver que PATH tiene el servicio
sudo systemctl show nelson-meta-orchestrator | grep Environment
```
