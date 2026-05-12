# Docker Setup — Entorno de Nelson

## Comandos correctos

```bash
# Docker Compose V2 (espacio, no guión)
docker compose up --build -d
docker compose down
docker compose ps

# NUNCA usar docker-compose (obsoleto en este entorno)
```

## Permisos

- Usuario `server` NO está en grupo `docker`
- Requiere `sudo` para todo comando docker
- Clave sudo: `srv2026`

## Puertos usados en el proyecto base

| Servicio | Puerto host |
|----------|-------------|
| Backend (FastAPI) | 8000 |
| Frontend (React+Vite vía nginx) | 8080 |
| PostgreSQL | 5432 |

> Nota: El puerto 3000 está ocupado en este servidor, por eso el frontend usa 8080.

## Troubleshooting

**Error: `permission denied while trying to connect to the docker API`**
→ Usar `sudo docker compose ...`

**Error: `failed to bind host port 0.0.0.0:3000/tcp: address already in use`**
→ Cambiar puerto en `docker-compose.yml` (ej: `8080:80`)

**Error de rate limit al instalar skills del hub**
→ IDs truncados en la tabla. Usar `hermes skills inspect <identifier>` para ver el ID exacto, o instalar desde URL directa.
