---
name: nelson-automation-n8n
title: Automatizacion con n8n
published: true
description: n8n como motor de automatizacion para el equipo Nelson. Workflows para procesar datos, integrar APIs, webhooks, scheduled jobs y conectar con el stack existente (FastAPI, RAG, LLMs).
category: software-development
author: JARVIS
tags: [n8n, automation, workflow, webhook, cron, integration]
---

# Automatizacion con n8n - Equipo Nelson

## Descripcion

n8n es la plataforma de automatizacion elegida para el equipo Nelson. Corre en Docker local, se conecta con las APIs del equipo, bases de datos, LLMs y servicios externos.

## Instalacion

### Docker Compose (ya instalado)

Ver template listo para copiar en [`templates/docker-compose.yml`](templates/docker-compose.yml).

```yaml
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_SECURE_COOKIE=false
      - GENERIC_TIMEZONE=America/Argentina/Buenos_Aires
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - n8n-network

volumes:
  n8n_data:

networks:
  n8n-network:
    driver: bridge
```

**Importante:** `N8N_SECURE_COOKIE=false` es obligatorio para acceder via HTTP (no HTTPS). Sin esta variable, n8n rechaza las cookies en navegadores modernos.

### Primera ejecucion: crear usuario owner

En versiones recientes de n8n, `N8N_BASIC_AUTH` fue eliminado. La primera vez que se accede a http://localhost:5678, n8n pide crear un usuario owner/admin. Completar el formulario con los datos del usuario (email, nombre, password). Este usuario sera el unico administrador.

### Comandos utiles

```bash
# Levantar
cd ~/n8n-docker && sudo docker compose up -d

# Ver logs
sudo docker logs -f n8n

# Backup datos
sudo docker exec n8n tar czf /tmp/n8n-backup.tar.gz /home/node/.n8n
sudo docker cp n8n:/tmp/n8n-backup.tar.gz ~/backups/
```

## Workflows tipicos para el equipo

### 1. Webhook -> Procesar -> Guardar en DB

**Caso de uso:** Recibir datos de un formulario o API externa.

```
Webhook (POST) -> Code Node (validar) -> PostgreSQL Insert -> Response
```

### 2. Scheduled Job -> Scraping -> Notificacion

**Caso de uso:** Monitorear paginas de clientes, precios, disponibilidad.

```
Cron (cada hora) -> HTTP Request -> Code Node (parsear) -> If (cambio?) -> Telegram/Slack
```

### 3. Documento -> RAG Pipeline

**Caso de uso:** Subir documento a n8n, procesarlo con el pipeline RAG del equipo.

```
Webhook (archivo) -> HTTP Request (a API de document-processing) -> Qdrant Insert -> Slack confirmacion
```

### 4. Alerta -> LLM -> Accion

**Caso de uso:** Recibir alerta de sistema, analizar con LLM, ejecutar accion.

```
Webhook (alerta) -> HTTP Request (a Ollama/Gemma) -> Switch (clasificacion) -> Accion correspondiente
```

## Credenciales comunes

| Servicio | Tipo | Configuracion |
|----------|------|---------------|
| PostgreSQL | Postgres | host: db, port: 5432 |
| Qdrant | HTTP Request | host: localhost:6333 |
| Ollama | HTTP Request | host: host.docker.internal:11434 |
| Telegram | Telegram | Bot Token |
| SMTP | SMTP | Para emails |

## Integracion con el stack del equipo

### Conectar n8n con Ollama (LLMs locales)

1. En n8n crear nodo HTTP Request
2. Method: POST
3. URL: `http://host.docker.internal:11434/api/generate`
4. Body (JSON):
```json
{
  "model": "llama3.2:3b",
  "prompt": "{{ $json.texto }}",
  "stream": false
}
```

### Conectar n8n con APIs del equipo

Las APIs FastAPI del equipo se acceden desde n8n via:
- `http://host.docker.internal:8000` (backend)
- `http://host.docker.internal:8080` (frontend)

## Plan de Automatización de la Consultora (Workfows Prioritarios)

Este plan documenta los workflows clave para transformar la consultora en una máquina de automatización. Principio: si una tarea se repite más de 2 veces por semana, debe estar automatizada.

### Workflows Prioritarios

#### 1. Onboarding de Nuevo Proyecto
**Trigger:** Tony dice "empezamos proyecto X" o email con subject "[NUEVO PROYECTO]"
**Acciones:**
1. Crear carpeta `~/brainstorming/YYYY-MM-DD-nombre-proyecto/`
2. Generar `README.md` con template estándar
3. Crear repo en GitHub (si aplica)
4. Generar scaffold con `nelson-project-bootstrap`
5. Enviar confirmación a Tony por WhatsApp
**Tiempo ahorrado:** ~30 min/proyecto

#### 2. Reporte Semanal Automático
**Trigger:** Lunes 9:00 AM (America/Argentina)
**Acciones:**
1. Contar commits de la semana
2. Listar proyectos activos
3. Verificar estado de servicios (RAGs, Ollama, n8n)
4. Generar resumen breve
5. Enviar a Pablo por WhatsApp
**Tiempo ahorrado:** ~45 min/semana

#### 3. Monitoreo de Servicios + Alerta
**Trigger:** Cada 5 minutos (ya implementado como cronjob `rag-health-monitor`)
**Acciones:**
1. Revisar /health de cada RAG
2. Si caído: reiniciar contenedor automáticamente
3. Si sigue caído: alerta escalonada (Tony → Pablo)
**Mejoras con n8n:** Dashboard visual, historial de uptime, MTTR

#### 4. Nuevo Lead/Prospecto
**Trigger:** Formulario web o email a contacto
**Acciones:**
1. Extraer datos del lead
2. Guardar en Airtable/Notion (CRM)
3. Notificar a Luigi
4. Enviar auto-reply al prospecto

#### 5. Backup Automático de Skills y Memoria
**Trigger:** Sábados 2:00 AM
**Acciones:**
1. Ejecutar `sync-to-repo.sh`
2. Ejecutar `git push`
3. Si falla: reintentar o notificar a Tony

#### 6. Recolección de Tech News
**Trigger:** Diario 9:00 AM y 6:00 PM
**Acciones:**
1. Scrapear fuentes IA
2. Generar resumen con TTS
3. Enviar a Tony por WhatsApp
**Estado:** ✅ Ya implementado (cronjob `ai-news-aggregator`)

#### 7. Recordatorio de Pagos
**Trigger:** 5 días antes de vencimiento
**Acciones:**
1. Revisar Airtable/Notion de facturación
2. Enviar recordatorio al cliente
3. Si vence sin pago: escalar a Luigi y Pablo

### Roadmap de Implementación

| Fase | Workflows | Esfuerzo | Impacto |
|------|-----------|----------|---------|
| Fase 1 (esta semana) | Monitoreo + Reporte semanal | 2-3h | Alto |
| Fase 2 (próxima semana) | Onboarding + Backup auto | 3-4h | Alto |
| Fase 3 (próximo mes) | Leads + Facturación + Dashboard | 5-6h | Medio |

## Cuándo usar n8n vs cronjobs de Hermes

**Regla práctica:** Si el workflow conecta 3 o más sistemas distintos, usar n8n. Si es un script simple con un trigger de tiempo, usar cronjob de Hermes — es más directo y sin overhead.

| Tarea | Herramienta correcta | Motivo |
|-------|---------------------|--------|
| Backup semanal de skills a GitHub | Cronjob Hermes | Script simple, un solo sistema |
| Monitoreo de servicios + reinicio | Cronjob Hermes | Script bash, no requiere integraciones |
| Tech news diario | Cronjob Hermes | Ya implementado, funciona |
| Reporte semanal para Pablo | n8n | GitHub + WhatsApp + estado servicios = 3+ sistemas |
| Gestión de leads | n8n | Email + CRM + WhatsApp + cliente = 4+ sistemas |
| Onboarding de proyecto | n8n | GitHub + WhatsApp + filesystem + Gino = multi-sistema |

**Pitfall:** No usar n8n para tareas que un cronjob Hermes resuelve en 30 minutos. El overhead de configurar un workflow visual no se justifica para automatizaciones simples.

## Buenas practicas

- **Siempre** usar error handlers en cada workflow
- **Nunca** hardcodear credenciales, usar n8n credentials store
- **Backup** semanal de `n8n_data` volume
- **Versionar** workflows exportandolos a JSON y guardandolos en Git
- **Documentar** cada workflow con descripcion clara

## Troubleshooting

| Problema | Solucion |
|----------|----------|
| n8n no arranca | `sudo docker logs n8n` |
| No llegan webhooks | Verificar firewall, puerto 5678 |
| No conecta a localhost | Usar `host.docker.internal` |
| Workflow lento | Verificar recursion infinita |

## Pitfalls

1. **Docker requiere sudo.** Si el usuario no esta en el grupo `docker`, todos los comandos necesitan `sudo`. Usar: `echo 'PASSWORD' | sudo -S docker compose up -d` para evitar prompts interactivos.

2. **`docker compose up -d` es un proceso largo.** Algunas herramientas de terminal lo detectan como foreground process. Si falla, usar `background=true` o separar en: `docker compose pull` (foreground) y luego `docker compose up -d` (background).

3. **Primera vez tarda.** La primera ejecucion descarga la imagen (~400MB). No interrumpir. Verificar progreso con `sudo docker logs -f n8n`.

4. **Verificacion post-instalacion.** Siempre correr el script de verificacion despues de levantar: [`scripts/verify-n8n.sh`](scripts/verify-n8n.sh). Comprueba que el container esta Up, el health endpoint responde `{"status":"ok"}`, y la home page devuelve HTTP 200.

5. **NO instalar nodos custom dentro del contenedor Docker.** Instalar paquetes como `n8n-nodes-opencode` via `npm install` dentro del container genera problemas de permisos (root vs node). El contenedor corre como usuario `node` pero `npm install` como `root` deja archivos inaccesibles. Solucion: **usar el nodo HTTP Request nativo de n8n** en lugar de nodos custom. Es mas simple y no requiere instalacion.

6. **Simplificar cuando el usuario lo pida.** Si el usuario dice "simplifica" o muestra frustracion con pasos complejos, reducir a la solucion minima viable. No explicar teorias extensas ni dar multiples opciones. Ir directo a lo que funciona.

## Integracion con OpenCode (via HTTP Request)

Ver workflow listo para importar: [`templates/opencode-workflow.json`](templates/opencode-workflow.json).

En lugar del nodo custom problematico, usar el nodo **HTTP Request** nativo:

1. OpenCode server debe estar corriendo en el host: `opencode serve --port 4096`
2. Desde n8n, crear nodo HTTP Request:
   - Method: `POST`
   - URL: `http://host.docker.internal:4096/api/v1/chat`
   - Body (JSON):
```json
{
  "prompt": "={{ $json.body.prompt }}"
}
```
3. Procesar la respuesta con un nodo Code o Set.

Ejemplo de workflow:
```
Webhook (prompt) -> HTTP Request (OpenCode) -> Code (parsear respuesta) -> Response
```

## Benchmarks de LLMs locales (equipo Nelson)

Hardware de referencia: NVIDIA GTX 1650 Mobile 4GB VRAM, 13GB RAM.

| Modelo | Parametros | Tamanio GGUF | VRAM usada | Tiempo respuesta* | Recomendacion |
|--------|-----------|-------------|------------|-------------------|---------------|
| llama3.2:3b | 3B | ~2.0 GB | ~2.0 GB | ~4.3s | ✅ Uso diario |
| qwen2.5:3b | 3B | ~1.9 GB | ~1.9 GB | ~6.3s | ✅ Uso diario |
| gemma3:1b | 1B | ~800 MB | ~800 MB | ~2.7s | ✅ Rapido, basico |
| gemma3:4b | 4B | ~3.3 GB | ~2.4 GB | ~6.3s | ✅ Mas capacidad |
| gemma4-e2b IQ2_M | 2.3B efectivos | 2.62 GB | ~2.9 GB | ~55s | ⚠️ Thinking mode, lento |
| gemma4-e4b Q2_K | 4B efectivos | 4.46 GB | >4 GB | N/A | ❌ No entra en 4GB VRAM |

*Tiempo medido con la misma pregunta: "Ventajas de Docker en 2 oraciones". Cuantizacion mas agresiva = mas lento.

**Conclusion para el equipo:** Usar llama3.2:3b o qwen2.5:3b para automatizaciones rapidas en n8n. Gemma 4 E2B solo si se necesita explicitamente el thinking mode y se tolera la latencia.

**Para importar modelos custom a Ollama (ej: Gemma 4 desde Hugging Face):** ver [`references/ollama-custom-gguf-import.md`](references/ollama-custom-gguf-import.md).

## Recursos

- URL local: http://localhost:5678
- Documentacion: https://docs.n8n.io/
- Workflow templates: https://n8n.io/workflows/
