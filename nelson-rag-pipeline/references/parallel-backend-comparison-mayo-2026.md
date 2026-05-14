# Sesion: Deploy Triple de Backends RAG en Paralelo (FLoCI-AWS, MinIO, FLoCI-Azure)
## Fecha: 2026-05-14
## Contexto: Comparativa tangible para stakeholder (Pablo)

## Resumen
Se deployaron 3 instancias completas del PoC RAG (frontend + backend + storage + qdrant + ollama) en paralelo, cada una usando un backend de storage distinto. Todas expuestas via Cloudflare tunnels para acceso remoto desde celular.

## Stacks Deployados

| Stack | Directorio | Backend Port | Frontend Port | Qdrant Port | Storage Port |
|-------|-----------|--------------|---------------|-------------|----------------|
| FLoCI-AWS | `~/brainstorming/2026-05-13-rag-poc` | 8000 | 8080 | 6333 | 4566 |
| MinIO | `~/brainstorming/2026-05-13-rag-poc-minio` | 8001 | 8081 | 6335 | 9002/9003 |
| FLoCI-Azure | `~/brainstorming/2026-05-14-rag-floci-azure` | 8002 | 8082 | 6337 | 4577 |

## URLs Publicas (Cloudflare Quick Tunnels)

| Stack | Frontend | Backend |
|-------|----------|---------|
| FLoCI-AWS | bonds-backgrounds-light-audit.trycloudflare.com | ham-brian-growth-gnome.trycloudflare.com |
| MinIO | thoroughly-depends-hurricane-afterwards.trycloudflare.com | mailed-yarn-scratch-write.trycloudflare.com |
| FLoCI-Azure | truly-reactions-tubes-likely.trycloudflare.com | roberts-cure-electoral-wall.trycloudflare.com |

> Nota: URLs temporales, cambian al reiniciar cloudflared.

## Documentos de Prueba
- `documento_rrhh_prueba.pdf` (manual RRHH ficticio)
- `ia-ejemplo.pdf` (guia conceptos IA)

## Resultados de la Comparativa

| Caracteristica | FLoCI-AWS | MinIO | FLoCI-Azure |
|----------------|-----------|-------|-------------|
| Persistencia | Memoria (se pierde) | Disco (persiste) | Hybrid (flush 5s) |
| Startup | ~5s | ~2s | ~100ms |
| SDK | boto3 | boto3 | azure-storage-blob |
| Chunks indexados | 40 | 40 | 40 |
| Respuesta a query RRHH | Correcta + sources | Correcta + sources | Correcta + sources |

## Problemas Encontrados y Fixes

1. **Frontend MinIO mostraba "No hay documentos"**: VITE_API_URL apuntaba a localhost en vez de URL publica del backend. Fix: actualizar env var y recrear contenedor con `--force-recreate`.
2. **Docker Compose mezclaba contenedores**: Al correr dos stacks desde el mismo directorio base, Docker Compose usaba el mismo nombre de proyecto. Fix: usar directorios separados o flag `-p nombre-proyecto`.
3. **FLoCI pierde datos al reiniciar**: FLoCI corre en memoria por defecto. Fix documentado: para persistencia agregar `PERSISTENCE=1` y volumen en `/app/data`.

## Demo Package
Se creo un README.md de presentacion para Pablo en `~/brainstorming/2026-05-14-rag-floci-azure/README.md` con flujo end-to-end, arquitectura, tabla comparativa y guia de conversacion.

Template reutilizable: `nelson-cloud-storage-comparison/templates/demo-package-README.md`

## Lecciones para Futuras Demos Comparativas
- Siempre usar directorios separados para cada stack en paralelo
- Siempre actualizar VITE_API_URL antes de mostrar la UI a alguien externo
- Siempre verificar que los documentos de prueba tengan texto extraible (no ReportLab Canvas)
- Siempre dejar un documento de presentacion README.md en el directorio del brainstorming

## Skill Actualizada
- `nelson-cloud-storage-comparison`: se agrego seccion "Demo para Stakeholders" y template demo-package-README.md
- `nelson-rag-pipeline`: se agrego este reference
