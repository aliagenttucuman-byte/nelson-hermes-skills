# Playbook: ForestAI PoC (ForestAI-PoC)

> **Servicio:** ForestAI PoC — Inventario forestal con drones e image analytics
> **Puertos:** 3010 (frontend, Docker nginx) | 8010 (backend FastAPI) | 5433 (PostGIS) | 6380 (Redis)
> **Compose:** `/home/server/proyectos/forestai-poc/docker-compose.yml`
> **Owner:** Diego (PoC activa) / Beto (arquitectura) / Tony (decisiones de negocio)
> **Stack:** React + Vite (compilado a dist) + FastAPI + Celery + PostGIS + Redis + MinIO

## Señales de alarma típicas

Reportadas por Pablo, por clientes, o detectadas en monitoreo:
- "La página no carga, queda en blanco"
- "Subí una ortofoto y dice error 500"
- "El NDVI no aparece, demora eternidad"
- "El túnel no anda"
- Health check `:8010/health` retorna no-200 o cuelga
- Container en estado `Restarting` o `Exit 1`

## Triage paso a paso (ejecutar en orden, sin saltearse)

```bash
# 1. Conectarse al server
ssh server@100.110.8.13

# 2. Estado de containers
docker ps -a --filter "name=forestai" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}"

# Salida esperada: 5 containers UP (backend, celery, frontend, db, redis)
# Patológicos: Exit 1, Restarting, "unhealthy"
```

```bash
# 3. Health check del backend (puerto interno del container)
docker exec forestai-poc-backend-1 curl -sf http://localhost:8000/health
# Si no responde, ver logs
docker logs --tail 100 forestai-poc-backend-1
```

```bash
# 4. Verificar dependencias (PostGIS y Redis)
docker exec forestai-poc-db-1 pg_isready -U forestai
# Esperado: "accepting connections"
docker exec forestai-poc-redis-1 redis-cli ping
# Esperado: "PONG"
```

```bash
# 5. Recursos del host
docker stats --no-stream forestai-poc-backend-1 forestai-poc-celery-1
df -h /home/server/proyectos
free -h
```

```bash
# 6. Si hay tunnel Cloudflare activo, verificar que la URL siga viva
# Logs en /tmp/cf_forestai.log
tail -20 /tmp/cf_forestai.log
# Si el log está vacío o el proceso murió, ver § Reinicio de tunnel
```

## Mitigación por escenario

### Escenario A: Backend unhealthy / reiniciando

**Síntoma:** `forestai-poc-backend-1` en estado `Restarting` o no responde a /health.

```bash
# Ver la causa del restart
docker logs --tail 50 forestai-poc-backend-1

# Causa frecuente: conexión a PostGIS perdida al startup
# Solución: reiniciar también la DB para que el backend re-conecte
cd /home/server/proyectos/forestai-poc/
docker compose restart db
sleep 10
docker compose restart backend celery

# Verificar recuperación
sleep 5
curl -s http://localhost:8010/health
```

### Escenario B: Frontend muestra cambios viejos (BUG CONOCIDO)

**Síntoma:** Tony o Mercedes hicieron cambios en `frontend/src/` pero el browser muestra la versión vieja.

**Pitfall crítico:** el container `forestai-poc-frontend-1` sirve un **dist estático**. Los cambios en código fuente NO se reflejan automáticamente. Ver `nelson-server-services` § "Docker container ForestAI ≠ código fuente".

```bash
# Solución obligatoria
cd /home/server/proyectos/forestai-poc/frontend
npm run build
docker cp dist/. forestai-poc-frontend-1:/usr/share/nginx/html/

# Pedir al usuario Ctrl+Shift+R en el browser
```

### Escenario C: PostGIS no arranca

**Síntoma:** `forestai-poc-db-1` en estado `Exit 1` o loop de restart.

```bash
# Ver el error
docker logs --tail 100 forestai-poc-db-1

# Causa frecuente: volumen corrupto o incompatibilidad de versión
# Mitigación rápida (acepta pérdida de datos — solo si es PoC)
cd /home/server/proyectos/forestai-poc/
docker compose down db
docker volume rm forestai-poc_postgis_data
docker compose up -d db
# Esperar 20-30s a que inicialice PostGIS
docker exec forestai-poc-db-1 pg_isready -U forestai
# Restaurar desde backup si existe (cuando nelson-backup-dr esté listo)
```

**Si es producción con datos reales: NO ejecutar el `volume rm` sin consultar con Diego/Tony.**

### Escenario D: Celery worker colgado

**Síntoma:** jobs de procesamiento NDVI/máscaras se quedan en "pending" eternamente.

```bash
# Reiniciar celery sin tocar el resto
cd /home/server/proyectos/forestai-poc/
docker compose restart celery

# Si persiste, ver la cola de Redis
docker exec forestai-poc-redis-1 redis-cli LLEN celery
# Si la cola tiene miles de items viejos, limpiarla
docker exec forestai-poc-redis-1 redis-cli FLUSHDB
docker compose restart celery
```

### Escenario E: Tunnel Cloudflare caído

**Síntoma:** URL `*.trycloudflare.com` dejó de responder, pero localhost sí anda.

```bash
# Matar el túnel viejo
pkill -9 cloudflared

# Relanzar
cloudflared tunnel --url http://localhost:3010 2>&1 | tee /tmp/cf_forestai.log &
sleep 15
NEW_URL=$(grep -o 'https://[a-z0-9\-]*\.trycloudflare\.com' /tmp/cf_forestai.log | head -1)
echo "Nueva URL: $NEW_URL"

# Comunicar a Pablo / cliente
# Actualizar este valor en la memoria del agente (siguiente turno de JARVIS)
```

### Escenario F: Disco lleno

**Síntoma:** containers crashean, logs dicen "No space left on device".

```bash
df -h
# Si /home está al 100%:
docker system df  # ver cuánto ocupan los containers/images
docker image prune -a  # PELIGRO: borra imágenes sin usar
docker volume prune   # PELIGRO: borra volúmenes huérfanos
# Considerar mover ortofotos viejas a storage frío
du -sh /home/server/proyectos/forestai-poc/data/* | sort -h | tail
```

## Verificación post-mitigación

Checklist obligatorio después de cada intervención:

- [ ] `curl http://localhost:8010/health` retorna 200 con status="ok"
- [ ] `docker ps` muestra los 5 containers UP
- [ ] Frontend carga en el browser (pedirle a Tony o usar curl + check del HTML)
- [ ] Si hay tunnel activo, la URL pública responde
- [ ] Un usuario real (Pablo o el cliente) confirma que puede hacer su flujo completo
- [ ] Logs del último minuto no muestran errores nuevos

## Escalamiento

| Sev | Trigger | Acción |
|-----|---------|--------|
| Sev-1 | ForestAI caído y cliente en reunión/demostración ahora | Tony + Diego, respuesta <5 min, comunicar a Pablo |
| Sev-2 | ForestAI caído sin cliente activo, o degradación severa | Diego + owner técnico, <30 min |
| Sev-3 | Frontend muestra UI rara, ortofoto carga lento, NDVI impreciso | Ticket + plan, <4h |
| Sev-4 | Mejora visual,文案, color | Backlog |

## Post-mortem

Si Sev-1 o Sev-2: obligatorio en 24h. Usar `templates/postmortem.md`.

## Referencias

- Skill: `nelson-server-services` (mapa de puertos, pitfall del dist)
- Skill: `nelson-monitoring-observability` (health checks y logging)
- Skill: `nelson-cloudflare-tunnel-deploy` (deploy de tunnel)
- Compose: `/home/server/proyectos/forestai-poc/docker-compose.yml`
- Logs: `docker logs <container>` o `docker compose logs -f`
