# RAG PoC — Comparativa de Storage Local
## Demo Package para Pablo

**Fecha:** 2026-05-14
**Autor:** Equipo Nelson (Tony/JARVIS)
**Estado:** Funcionando — 3 variantes deployadas en paralelo

---

## Que es esto

Un sistema de **Chat con Documentos** (RAG) que permite subir PDFs y hacer preguntas sobre ellos. Es 100% local (corre en nuestro servidor) pero accesible desde cualquier celular o PC gracias a túneles de Cloudflare.

**Caso de uso:** Un empleado sube el manual de RRHH de la empresa, y después puede preguntar "¿Cuántos días de licencia por paternidad me corresponden?" y el sistema responde con la información exacta del documento, citando la fuente.

---

## Las 3 Versiones (Deployadas en Paralelo)

Cada versión usa un **backend de almacenamiento distinto** para guardar los PDFs. Esto nos permite comparar y elegir la mejor opción según el cliente.

| Variante | Tecnología | Persistencia | Ideal para |
|----------|-----------|--------------|------------|
| **FLoCI-AWS** | Emulador S3 de AWS | ❌ Memoria (se pierde al reiniciar) | Testear código AWS antes de migrar |
| **MinIO** | Servidor S3 real local | ✅ Disco (persiste reinicios) | Stack local estable, producción on-premise |
| **FLoCI-Azure** | Emulador Azure Blob Storage | ⚠️ Hybrid (memoria + flush cada 5s) | Clientes con infraestructura Azure |

---

## URLs de Acceso (Funcionando Ahora)

| Variante | Interfaz Web | API Backend |
|----------|-------------|-------------|
| **FLoCI-AWS** | https://bonds-backgrounds-light-audit.trycloudflare.com | https://ham-brian-growth-gnome.trycloudflare.com |
| **MinIO** | https://thoroughly-depends-hurricane-afterwards.trycloudflare.com | https://mailed-yarn-scratch-write.trycloudflare.com |
| **FLoCI-Azure** | https://truly-reactions-tubes-likely.trycloudflare.com | https://roberts-cure-electoral-wall.trycloudflare.com |

> **Nota:** Estas URLs son temporales (túneles de Cloudflare). Si se reinicia el servidor, las URLs cambian. El método para regenerarlas está documentado en la skill `nelson-rag-pipeline`.

---

## Como Probarlo (Flujo End-to-End)

### Paso 1: Abrir la UI
Elegí cualquiera de las 3 URLs de Frontend arriba. Todas se ven igual.

### Paso 2: Subir un Documento
- Hacé clic en "Subir documento"
- Seleccioná un PDF (por ejemplo, un manual de RRHH o un contrato)
- El sistema lo procesa automáticamente: extrae el texto, lo divide en fragmentos, genera embeddings y lo guarda en la base vectorial

**Documentos de prueba ya cargados en las 3 versiones:**
- `documento_rrhh_prueba.pdf` — Manual de RRHH ficticio
- `ia-ejemplo.pdf` — Guía de conceptos básicos de IA

### Paso 3: Hacer una Pregunta
- Escribí tu pregunta en el chat
- Ejemplos que funcionan bien:
  - "¿Cuántos días de licencia por paternidad le corresponden a un padre?"
  - "¿Qué beneficios tiene un empleado con 10 años de antigüedad?"
  - "¿Cuál es la política de home office?"

### Paso 4: Ver la Respuesta con Fuentes
- El sistema responde con la información encontrada
- Debajo de la respuesta aparece la **fuente** (qué documento y qué fragmento usó)
- Esto permite verificar que no está inventando nada

---

## Arquitectura Técnica

```
Usuario (celular/PC)
    |
    v
Cloudflare Tunnel (URL pública)
    |
    v
[Frontend React]  ←  Vite + Tailwind CSS
    |
    |  fetch()  |
    v           v
[Backend FastAPI]  ←  Python 3.12
    |
    +-----------+-----------+
    |           |           |
    v           v           v
[Storage]  [Vector DB]  [LLM]
S3/MinIO   Qdrant      OpenCode Zen
Azure      (768 dims)  gpt-5.4-nano
           embeddings  nomic-embed-text
           (Ollama)    (fallback: Ollama llama3.2:3b)
```

**Todo corre en nuestro servidor Linux local.** El único componente externo es OpenCode Zen para el LLM de generación (gpt-5.4-nano, el más barato disponible). Los túneles de Cloudflare dan acceso remoto.

---

## Stack Completo

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Frontend | React + Vite + Tailwind CSS | React 19, Vite 6 |
| Backend | FastAPI + Python | 3.12 |
| Storage | FLoCI / MinIO / FLoCI-Azure | Latest |
| Vector DB | Qdrant | Latest |
| LLM | OpenCode Zen (cloud) | gpt-5.4-nano |
| Embeddings | Ollama (local) | nomic-embed-text |
| Infra | Docker Compose | Latest |
| Acceso remoto | Cloudflared | Quick tunnels |

---

## Comparativa Detallada

| Característica | FLoCI-AWS | MinIO | FLoCI-Azure |
|----------------|-----------|-------|-------------|
| Protocolo | S3 (AWS API real) | S3 (nativo 100%) | Azure Blob Storage |
| SDK Python | boto3 | boto3 | azure-storage-blob |
| Puerto | 4566 | 9002/9003 | 4577 |
| Startup | ~5 segundos | ~2 segundos | ~100 milisegundos |
| Persistencia | ❌ Memoria | ✅ Disco | ⚠️ Hybrid |
| Docker Image | `floci/floci` | `minio/minio` | `floci/floci-az` |
| Documentos de prueba | 2 PDFs | 2 PDFs | 2 PDFs |
| Chunks indexados | 40 | 40 | 40 |

---

## Decisiones para el Cliente

| Si el cliente... | Recomendamos |
|------------------|--------------|
| Ya usa AWS o planea migrar | **FLoCI-AWS** (testear ahora, migrar después) |
| Quiere on-premise / no define cloud | **MinIO** (más estable, persistente) |
| Ya usa Azure | **FLoCI-Azure** (misma API, migración trivial) |
| Necesita ultra-baja latencia en startup | **FLoCI-Azure** (~100ms) |
| Necesita que los datos sobrevivan reinicios | **MinIO** |

---

## Lecciones Aprendidas (Pitfalls)

1. **PDFs generados con código no sirven:** Los PDFs creados con ReportLab (librería Python) no tienen texto seleccionable. El sistema los sube pero no puede extraer texto. **Solución:** Usar PDFs exportados desde Word, Google Docs, o escaneados con OCR.

2. **Frontend apuntando a localhost:** Si la UI no muestra documentos, el 90% de las veces es porque el frontend intenta hablar con `localhost:8000` en vez de la URL pública del backend. **Solución:** Actualizar `VITE_API_URL` en el docker-compose y recrear el contenedor.

3. **Dos stacks en paralelo:** Si se corren dos versiones desde el mismo directorio, Docker Compose las mezcla. **Solución:** Usar directorios separados o el flag `-p nombre-proyecto`.

4. **Qdrant sin `curl`:** La imagen oficial de Qdrant no tiene `curl` ni `wget`. Los healthchecks con `curl` fallan. **Solución:** Usar healthcheck con `python3 -c "import urllib.request..."` o simplemente no usar `condition: service_healthy`.

---

## Costos

| Componente | Costo |
|-----------|-------|
| Servidor Linux local | $0 (ya lo tenemos) |
| Ollama (LLM local) | $0 (corre en nuestra GPU) |
| OpenCode Zen (LLM cloud) | ~$0.0001/1K tokens (~$0.01/mes estimado) |
| Qdrant (Vector DB local) | $0 (open source) |
| FLoCI / MinIO | $0 (open source) |
| Cloudflare tunnels | $0 (quick tunnels, sin cuenta) |
| **Total** | **$0** |

---

## Próximos Pasos (Para Discutir con Pablo)

- [ ] Validar que Pablo puede acceder a las 3 URLs desde su celular
- [ ] Decidir con qué variante seguimos (MinIO recomendado para producción)
- [ ] Definir el primer cliente piloto (¿YPF? ¿Consultora?)
- [ ] Evaluar si necesitamos autenticación (usuarios/login) antes de entregar
- [ ] Evaluar si necesitamos persistencia en base relacional (PostgreSQL) para metadatos

---

## Documentación Técnica del Equipo

- Skill: `nelson-cloud-storage-comparison` — Comparativa de emuladores cloud
- Skill: `nelson-document-qa` — Sistema RAG completo
- Skill: `nelson-rag-pipeline` — Pipeline de chunking, embeddings, retrieval
- Repositorio: `github.com/aliagenttucuman-byte/nelson-hermes-skills`
