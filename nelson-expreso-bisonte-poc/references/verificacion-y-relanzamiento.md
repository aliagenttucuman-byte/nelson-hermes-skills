# Verificación y relanzamiento — corrige supuestos viejos de la SKILL.md

## Lo que cambió respecto al "estado verificado 2026-06-17"

El cuadro original decía que backend :9000 y spa_proxy :9090 "sobreviven entre sesiones". **Falso en la práctica.** Solo Postgres :5435 sobrevive (corre en Docker via `docker-compose.db.yml`). Backend y proxy son procesos foreground que se mueren si la sesión que los lanzó termina o el server reinicia.

Pendiente: moverlos a systemd siguiendo `nelson-systemd-services`. Mientras tanto, asumir que hay que relanzarlos en cada sesión nueva.

## Verificación correcta (endpoints que existen)

```bash
# Backend :9000 — NO tiene /health ni / → ambos devuelven 404 aunque el backend esté sano.
# Usar /docs (Swagger) o un endpoint real del API.
curl -s -o /dev/null -w "backend: %{http_code}\n" http://localhost:9000/docs   # → 200

# SPA proxy :9090 — sirve la SPA en /
curl -s -o /dev/null -w "spa:     %{http_code}\n" http://localhost:9090/        # → 200

# Postgres :5435
ss -lntp | grep :5435    # debe estar LISTEN
```

### PITFALL: 404 en `/` del backend NO significa "caído"

Si `curl http://localhost:9000/` devuelve 404, el backend probablemente está sano — FastAPI no tiene root handler. Confirmar con `/docs`. Solo `000` (connection refused) indica que está realmente caído.

## Relanzar los 3 servicios (Postgres ya corre)

Usar `terminal(background=true)` para cada proceso (no `nohup` / `disown` — Hermes los rechaza):

```bash
# 1. Backend FastAPI
cd /home/server/proyectos/excel-merger-poc/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 9000

# 2. SPA proxy (en otra sesión background)
cd /home/server/proyectos/excel-merger-poc
python3 spa_proxy.py
```

Verificar después de ~5s con el bloque de curls de arriba. El backend tarda más en estar listo que el proxy.

## Path real del código

El proyecto se llama "Expreso Bisonte" pero el repo local está en `/home/server/proyectos/excel-merger-poc/` (el nombre quedó del PoC original). El backend FastAPI vive en `backend/app/main.py` — el módulo correcto para uvicorn es `app.main:app` ejecutado desde `backend/`.
