---
name: nelson-scheduled-jobs
description: "Tareas recurrentes automatizadas para el equipo Nelson. Cron jobs de Hermes, scripts Python de scraping/monitoring, y state management para evitar duplicados."
category: software-development
tags: [cron, automation, rss, scraping, scheduled-tasks, hermes]
related_skills: [nelson-automation-n8n, nelson-brainstorming, blogwatcher]
---

# Scheduled Jobs — Tareas Recurrentes Automatizadas

> **Trigger:** Cuando Tony (Nelson) necesita una tarea que corra automáticamente en intervalos fijos (diario, 2x día, semanal) y entregue resultados por WhatsApp.

## Stack preferido

- **Hermes cron jobs** para scheduling nativo (no dependencias externas)
- **Python stdlib** (`urllib`, `xml.etree.ElementTree`, `json`) para scraping — evita instalar dependencias
- **State file JSON** para deduplicación entre corridas
- **Scripts shell en `~/.hermes/scripts/`** como entrypoint del cron

## Workflow de creación

```
1. Definir fuentes / URLs / lógica de negocio
2. Crear script Python con manejo de estado (seen_articles.json)
3. Probar manualmente: python3 scripts/mi_script.py
4. Crear wrapper shell en ~/.hermes/scripts/
5. Registrar cron job Hermes: schedule + deliver=origin + no_agent=true
6. Verificar próxima ejecución y output
```

## Reglas de oro

1. **Scripts Python van en `~/brainstorming/YYYY-MM-DD-proyecto/scripts/`** — sigue convención brainstorming
2. **Wrapper shell va en `~/.hermes/scripts/`** — Hermes exige path relativo desde ahí
3. **Siempre usar `no_agent: true`** para jobs puros de datos — evita gastar tokens de LLM
4. **State file en `data/seen_*.json`** — fuera del repo, persistente entre sesiones
5. **Keywords de filtrado configurables** — no mandar todo, solo lo relevante para el equipo

## Integración con WhatsApp Gateway

Si el job necesita enviar resultados por WhatsApp a múltiples números (ej: resumen de noticias, alertas):

1. Asegurar que el WhatsApp Gateway esté corriendo en `localhost:3001`
2. Desde el script Python, usar `urllib.request` para pegarle a los endpoints del gateway:
   - `POST /send` — un número
   - `POST /send-batch` — múltiples números con delay configurable
3. Ver `nelson-whatsapp-gateway` para el servidor y el script helper `send_whatsapp.py`

Ejemplo de envío desde un job Python:
```python
import json, urllib.request

def send_whatsapp(to: str, message: str):
    data = json.dumps({"to": to, "message": message}).encode()
    req = urllib.request.Request(
        "http://localhost:3001/send",
        data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    urllib.request.urlopen(req, timeout=10)
```

## Pitfalls

- **NO usar path absoluto en cron job** — Hermes rechota. Usar solo nombre del script en `~/.hermes/scripts/`
- **NO olvidar `chmod +x`** en el wrapper shell
- **NO parsear RSS con regex** — usar `xml.etree.ElementTree` (stdlib)
- **NO confiar en que un feed siempre responde** — wrappear cada fetch en try/except y continuar
- **Si el job depende de un servicio en background** (ej: WhatsApp Gateway en :3001), verificar health check antes de enviar. Si no está disponible, loguear el error y continuar — no crashear el job.
- **NO usar `&` ni `nohup` en terminal Hermes** para levantar servicios. Usar `execute_code` + `subprocess.Popen(start_new_session=True)` o arrancar el servicio fuera del cron job.

## Templates

- `templates/rss-aggregator.py` — script base para monitorear feeds RSS/Atom con filtro de keywords. Ver comentarios inline para adaptar FEEDS y HIGHLIGHT_KEYWORDS.

## Referencias

- `references/hermes-cron-setup.md` — paso a paso para registrar cron jobs nativos de Hermes, formatos de schedule, y troubleshooting.

## Comandos útiles

```bash
# Listar jobs activos
hermes jobs list

# Ver logs de un job
hermes jobs logs <job-id>
```
