# Comparación FLoCI vs MinIO — Hallazgos de Sesión (Mayo 2026)

## Contexto
Se ejecutó una comparación directa: mismo pipeline RAG, solo cambiando el backend S3 (MinIO → FLoCI). El objetivo era validar si FLoCI podía reemplazar a MinIO en el stack local.

## URLs de la prueba
- Frontend (FLoCI): https://bonds-backgrounds-light-audit.trycloudflare.com
- Backend (FLoCI): https://ham-brian-growth-gnome.trycloudflare.com
- Frontend (MinIO): https://thoroughly-depends-hurricane-afterwards.trycloudflare.com
- Backend (MinIO): https://mailed-yarn-scratch-write.trycloudflare.com

## Resultado de la comparación

| Aspecto | MinIO | FLoCI |
|---------|-------|-------|
| Qué es | S3 real local | Emulador AWS (S3 + 30 servicios) |
| Puerto | 9000 | 4566 |
| API | S3-compatible | AWS S3 real |
| Persistencia | Sí (volumen Docker) | No por defecto (en memoria) |
| Requiere cuenta AWS | No | No |
| Cambios en código Python | 0 (boto3 funciona con ambos) | 0 |
| Docker network | Funciona directo | Requiere recreación completa |
| Overhead | Menor | Mayor (Quarkus native) |

## Problemas encontrados con FLoCI

### 1. Docker Compose network (crítico)
**Síntoma**: El contenedor `floci` arrancaba pero el backend fallaba con:
```
botocore.exceptions.EndpointConnectionError: Could not connect to the endpoint URL: "http://floci:4566/rag-documents"
curl: (6) Could not resolve host: floci
```
**Causa**: Al reemplazar el servicio `minio` por `floci` en un `docker-compose.yml` existente y hacer `docker compose up -d`, Docker no conectó automáticamente `floci` a la red `default` del proyecto.

**Verificación**:
```bash
docker network inspect <proyecto>_default
# FLoCI no aparecía en la lista de contenedores conectados
```

**Fix**: `docker compose down && docker compose up -d` (recreación completa, no restart). Esto forza a Docker Compose a recrear la red y conectar todos los servicios.

### 2. Persistencia de datos
FLoCI arrancó con `Storage mode: memory` (default). Al hacer `docker compose down`, se perdieron todos los PDFs subidos. MinIO con volumen Docker conservaba los archivos.

**Fix para persistencia**: Agregar a `docker-compose.yml`:
```yaml
  floci:
    environment:
      - SERVICES=s3
      - PERSISTENCE=1   # <-- agregar esto
    volumes:
      - floci-data:/app/data   # <-- montar en /app/data, no /data
```

### 3. PDFs de prueba no extraíbles
Se generaron 3 PDFs de ejemplo con ReportLab (`guia_fastapi.pdf`, `manual_seguridad_it.pdf`, `faq_inteligencia_artificial.pdf`). `pdfplumber` extrajo texto vacío de todos ellos.

**Causa**: ReportLab Canvas renderiza texto como paths vectoriales, no como objetos de texto seleccionables.

**Fix**: Para testing de RAG, usar PDFs reales exportados desde Word/Google Docs, nunca ReportLab Canvas. Verificar extractabilidad con:
```bash
python3 -c "import pdfplumber; pdf = pdfplumber.open('test.pdf'); print(len(pdf.pages[0].extract_text() or ''))"
# Si devuelve 0, el PDF no es text-extractable
```

**Síntoma en el RAG**: El PDF se sube exitosamente a S3, pero `GET /stats` muestra que los chunks no aumentaron. Las preguntas sobre ese documento responden "No encontré información relevante".

## Problemas encontrados al correr ambos en paralelo

### 4. Stacks Docker Compose colisionan si comparten directorio
**Síntoma**: Al intentar levantar FLoCI y MinIO simultáneamente desde el mismo directorio con `docker compose -f docker-compose.yml` y `docker compose -f docker-compose.minio.yml`, Docker Compose detectaba los contenedores como parte del mismo proyecto y los reemplazaba en lugar de crear nuevos.

**Causa**: Docker Compose usa el nombre del directorio como nombre de proyecto por defecto. Ambos comandos desde el mismo directorio = mismo proyecto = misma red = colisión.

**Fix**: Crear directorios separados para cada versión (ej: `rag-poc/` y `rag-poc-minio/`), copiar `backend/` y `frontend/` a ambos, y levantar desde cada directorio. Docker Compose asigna nombres de proyecto distintos automáticamente.

**Puertos usados en la prueba paralela**:
| Servicio | FLoCI | MinIO |
|----------|-------|-------|
| Backend API | 8000 | 8001 |
| Frontend UI | 8080 | 8081 |
| S3 | 4566 | 9002 |
| Qdrant | 6333 | 6335 |

## Lo que funcionó bien
- **API boto3**: Sin cambios. El mismo código `boto3.client("s3", endpoint_url=...)` funciona con FLoCI y MinIO indistintamente.
- **Cloudflare tunnel `--protocol http2`**: Más estable que QUIC default cuando se ejecutan múltiples túneles simultáneos.
- **Qdrant persistió**: Los chunks originales se mantuvieron en el volumen Qdrant entre reinicios.
- **Demos simultáneas**: Ambas versiones (FLoCI + MinIO) estuvieron accesibles públicamente vía Cloudflare al mismo tiempo.

## Veredicto
- **MinIO**: Recomendado para stack local estable y demos. Persistencia nativa, menor overhead, menos sorpresas de networking.
- **FLoCI**: Útil solo si se planea migrar futuro a AWS y se quiere testear compatibilidad exacta de la API S3. Para un PoC local, agrega complejidad innecesaria (volatilidad de memoria, problemas de red, mayor consumo de recursos).

## Comandos útiles para reproducir

```bash
# Levantar con FLoCI
cd /home/server/brainstorming/2026-05-13-rag-poc
docker compose down
docker compose up -d

# Levantar con MinIO (directorio separado)
cp -r backend frontend /home/server/brainstorming/2026-05-13-rag-poc-minio/
cd /home/server/brainstorming/2026-05-13-rag-poc-minio
docker compose -f docker-compose.yml up -d

# Verificar FLoCI responde
curl http://localhost:4566/

# Verificar MinIO responde
curl http://localhost:9002/minio/health/live

# Subir PDF y probar
curl -s -X POST -F "file=@documento.pdf" http://localhost:8000/upload  # FLoCI
curl -s -X POST -F "file=@documento.pdf" http://localhost:8001/upload  # MinIO

# Stats
curl -s http://localhost:8000/stats
curl -s http://localhost:8001/stats

# Pregunta
curl -s -X POST -H "Content-Type: application/json" -d '{"question":"¿...?"}' http://localhost:8000/ask
curl -s -X POST -H "Content-Type: application/json" -d '{"question":"¿...?"}' http://localhost:8001/ask

# Túneles Cloudflare (http2 para estabilidad)
cloudflared tunnel --url http://localhost:8000 --protocol http2
cloudflared tunnel --url http://localhost:8080 --protocol http2
cloudflared tunnel --url http://localhost:8001 --protocol http2
cloudflared tunnel --url http://localhost:8081 --protocol http2
```
