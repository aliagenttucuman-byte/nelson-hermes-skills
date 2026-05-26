# Sesion: RAG PoC con FLoCI y MinIO en paralelo + Cloudflare
## Fecha: 2026-05-14
## Contexto: Comparar FLoCI vs MinIO como backend S3 para PoC RAG

## Objetivo
El usuario (Tony/Nelson) queria desplegar dos versiones del mismo PoC RAG en paralelo:
1. **FLoCI** (emulador AWS, en memoria)
2. **MinIO** (S3 real local, persistente)

Ambas expuestas por Cloudflare para que el usuario las compare desde su celular.

## URLs finales
- **FLoCI**: https://bonds-backgrounds-light-audit.trycloudflare.com
- **MinIO**: https://thoroughly-depends-hurricane-afterwards.trycloudflare.com

## Problemas encontrados y fixes

### 1. Frontend MinIO mostraba "No hay documentos"
**Causa raiz**: El `docker-compose.minio.yml` tenia `VITE_API_URL=http://localhost:8001`. Cuando el usuario abria la UI desde Cloudflare, su navegador intentaba conectar a `localhost:8001` (su propia maquina), no al backend.

**Fix**: Actualizar la env var del frontend para que apunte a la URL publica del backend:
```yaml
frontend:
  environment:
    - VITE_API_URL=https://mailed-yarn-scratch-write.trycloudflare.com
```
Y recrear el contenedor con `--force-recreate` (no alcanza con `restart`).

**Verificacion**: `docker inspect <frontend>` debe mostrar la env var correcta. Tambien, desde el navegador (F12 -> Network), las llamadas a `/documents` deben ir a la URL publica.

### 2. Docker Compose mezclaba contenedores de FLoCI y MinIO
**Causa raiz**: Se ejecuto `docker compose -f docker-compose.minio.yml up -d` desde el mismo directorio `/home/server/brainstorming/2026-05-13-rag-poc/`. Docker Compose uso el nombre de proyecto `2026-05-13-rag-poc` para ambos stacks, causando que el segundo reemplazara/recreate los contenedores del primero.

**Fix**: Usar `-p` para forzar nombre de proyecto distinto:
```bash
docker compose -p rag-floci -f docker-compose.yml up -d
docker compose -p rag-minio -f docker-compose.minio.yml up -d
```

**Sintoma de diagnostico**: Al hacer `docker compose up` del segundo stack, se ve `Recreating` en lugar de `Creating` para servicios que ya existian, y despues los contenedores del primer stack desaparecen de `docker ps`.

### 3. FLoCI pierde datos al reiniciar
FLoCI corre en memoria por defecto. Al reiniciar el contenedor, el bucket y los objetos se pierden. MinIO con volumen Docker (`minio-data`) sobrevive reinicios.

Para persistir FLoCI: agregar `PERSISTENCE=1` y volumen en `/app/data`.

## Estado final de ambos stacks

| Stack | Frontend | Backend | S3 | Qdrant | Docs | Chunks |
|-------|----------|---------|----|--------|------|--------|
| FLoCI | bonds-backgrounds-light-audit | ham-brian-growth-gnome | 4566 (memoria) | 6333 | 2 PDFs | 138 |
| MinIO | thoroughly-depends-hurricane-afterwards | mailed-yarn-scratch-write | 9002 (disco) | 6335 | 2 PDFs | 40 |

Nota: la diferencia en chunks (138 vs 40) se debe a que FLoCI fue reindexado completo en una pasada anterior con chunk size diferente o mas documentos.

## Verificacion de funcionamiento
```bash
# Backend responde
curl https://mailed-yarn-scratch-write.trycloudflare.com/health
curl https://ham-brian-growth-gnome.trycloudflare.com/health

# Documentos visibles
curl https://mailed-yarn-scratch-write.trycloudflare.com/documents
curl https://ham-brian-growth-gnome.trycloudflare.com/documents

# CORS ok
curl -X OPTIONS -H "Origin: https://thoroughly-depends-hurricane-afterwards.trycloudflare.com" \
  -H "Access-Control-Request-Method: POST" \
  https://mailed-yarn-scratch-write.trycloudflare.com/ask
```

## Lecciones aprendidas
1. Siempre verificar `docker inspect <frontend> | grep VITE_API_URL` despues de cambiar env vars.
2. Nunca confiar en `docker restart` para aplicar cambios de env vars en Docker Compose. Usar `--force-recreate`.
3. Para stacks paralelos, usar `-p` con nombre de proyecto explicito o directorios separados.
4. Cuando un usuario dice "No hay documentos" en una UI expuesta por tunnel, el 90% de las veces es porque el frontend apunta a `localhost`.
5. FLoCI es util para testear compatibilidad AWS, pero MinIO es mas estable para demos persistentes.
