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
- **`pip` no existe en el sistema — usar `python3 -m pip`** para instalar dependencias. El comando `pip` sin más da "command not found". Siempre invocar como `python3 -m pip install ...`.
- **Actualizar delivery de un cron job existente**: `hermes cron` no tiene subcomando `update` desde CLI — usar el tool `cronjob` con `action=update`, `job_id=<id>`, y `deliver=origin,whatsapp:<número>`. Funciona con múltiples destinos separados por coma.
- **DDG News rate limit 403**: Si se llaman más de 2-3 búsquedas sin pausa, devuelve `403 Ratelimit`. Fix: `time.sleep(0.5)` entre búsquedas. También el paquete fue renombrado de `duckduckgo_search` a `ddgs` — puede aparecer RuntimeWarning. Usar `python3 -m pip install ddgs` para la versión nueva.
- **RSS de referentes (MiduDev, Brais Moure, Fazt)**: Sus URLs `/rss.xml` dan 404. Hay que buscar el feed real de cada uno antes de agregar a REFERENTS. Investigar si usan Substack, FeedBurner, o YouTube RSS.
- **Multi-delivery en cronjob**: Para que un cron job entregue a múltiples contactos de WhatsApp, usar el tool `cronjob` con `action=update`, `job_id=<id>`, y `deliver=origin,whatsapp:<num1>,whatsapp:<num2>,...`. Los números van con código de país completo sin `+` (ej: `5493816240691`). Actualizar todos los jobs relevantes por separado si hay más de uno.
- **NO listar números externos en `deliver:` de cron jobs**: El bridge nativo de Hermes falla con `jidDecode` para cualquier número que no esté previamente en la sesión del bot. El error `Cannot destructure property 'user' of 'jidDecode(...)' as it is undefined` significa exactamente eso. Patrón correcto: `deliver: origin` en el cron (solo para Nelson), y el propio prompt del cron llama al gateway Baileys (`localhost:3001`) vía `send_whatsapp.py` para los externos (Gabi, Pablo, Faku). Ver `nelson-whatsapp-gateway` para el script helper y el patrón completo.
- **Dos cron jobs duplicados**: Si hay dos jobs con el mismo propósito, consolidar en uno y borrar el viejo con `cronjob action=remove`. No dejar jobs dobles corriendo en horarios solapados — aumenta carga y genera confusión en logs.
- **Hermes cron job: bug reasoning_details con OpenCode Go + Kimi K2.6**: Si los jobs fallan con `HTTP 400: Extra inputs are not permitted, field: reasoning_details`, el provider OpenCode Go está enviando campos de razonamiento que el endpoint rechaza. Fix: cambiar a provider `anthropic` con `hermes config set model.provider anthropic` y `hermes config set model.default claude-sonnet-4-20250514`. Reiniciar la sesión para que tome efecto.

## Templates

- `templates/rss-aggregator.py` — script base para monitorear feeds RSS/Atom con filtro de keywords. Ver comentarios inline para adaptar FEEDS y HIGHLIGHT_KEYWORDS.
- `templates/linkedin-oauth2-server.py` — servidor FastAPI OAuth2 para LinkedIn (AlegentAI). Scopes, redirect URI, y flujo completo para obtener access_token.

---

## Pipeline LinkedIn — AlegentAI (publicación automatizada)

Para publicar posts en LinkedIn desde la cuenta personal de Nelson (aliagenttucuman@gmail.com) usando la API oficial v2 con OAuth2.

### App registrada

- **Nombre:** Alegent AI investigations
- **Client ID:** 77djcvwzhlbcak
- **Producto aprobado:** Share on LinkedIn ✅ — scope `w_member_social` ✅
- **Credenciales:** `/home/server/brainstorming/2026-05-31-linkedin-feed-pipeline/auth/.env`
- **Tokens:** `/home/server/brainstorming/2026-05-31-linkedin-feed-pipeline/auth/tokens.json`

### Flujo OAuth2 (una sola vez)

```bash
cd ~/brainstorming/2026-05-31-linkedin-feed-pipeline
python3 server.py
# Levantar túnel CF:
cloudflared tunnel --url http://localhost:8090 2>&1 | tee /tmp/cf_linkedin.log &
# Obtener URL del túnel → abrir en browser → Autorizar en LinkedIn
```

Tras autorizar, el token se guarda en `auth/tokens.json` con `access_token` (válido 60 días) y `person_id`.

### Publicar un post

```python
from publisher import publish_post
result = publish_post("Texto del post con #hashtags")
```

### Endpoint de publicación (UGC Posts v2)

```
POST https://api.linkedin.com/v2/ugcPosts
Authorization: Bearer {access_token}
X-Restli-Protocol-Version: 2.0.0

{
  "author": "urn:li:person:{person_id}",
  "lifecycleState": "PUBLISHED",
  "specificContent": {
    "com.linkedin.ugc.ShareContent": {
      "shareCommentary": {"text": "..."},
      "shareMediaCategory": "NONE"
    }
  },
  "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
}
```

### PITFALL CRÍTICO — Scopes LinkedIn

LinkedIn valida ESTRICTAMENTE los scopes contra los productos aprobados.
**Solo pedir `w_member_social`** — nada más para esta app.

```python
SCOPES = "w_member_social"   # CORRECTO

# INCORRECTO — causa invalid_scope_error inmediato:
SCOPES = "openid profile email w_member_social"
SCOPES = "w_member_social r_liteprofile r_emailaddress"
```

Para obtener `person_id` sin `r_liteprofile`: hardcodearlo en `tokens.json` o sacarlo de la URL del perfil LinkedIn.

### PITFALL — Redirect URI con Cloudflare Tunnel

Cloudflare genera URL nueva en cada restart → Redirect URI debe actualizarse:

1. `python3 server.py` en :8090
2. `cloudflared tunnel --url http://localhost:8090` → capturar URL
3. Actualizar `.env` `LINKEDIN_REDIRECT_URI`
4. Actualizar LinkedIn Developer → Auth → Authorized Redirect URLs
5. Reiniciar server.py

### Otros pitfalls LinkedIn

- **Client Secret formato WPL_AP1**: `WPL_AP1.xxxxx.xxx==` es el valor correcto, aunque no parezca hex. Usarlo tal cual.
- **Procesos zombie con scopes viejos**: `pkill -9 -f "server.py" && fuser -k 8090/tcp` antes de relanzar.
- **Endpoint de perfil**: con `r_liteprofile` usar `/v2/me` (campos: `localizedFirstName`, `id`). Con OpenID usar `/v2/userinfo`.
- **Rate limits**: ~100 posts/día (API básica). Para producción: 1-3 posts/día.

Ver `references/linkedin-oauth2-pitfalls.md` para el registro completo de errores de la sesión 2026-05-31.
Ver `templates/linkedin-oauth2-server.py` para el servidor OAuth2 completo.

## References

- `references/hermes-cron-setup.md` — paso a paso para registrar cron jobs nativos de Hermes, formatos de schedule, y troubleshooting.
- `references/ai-news-aggregator-case.md` — caso real completo: RSS aggregator de IA con envío automático por WhatsApp Gateway, estructura de archivos, cron job, y lecciones aprendidas.
- `references/ai-news-aggregator-v2-design.md` — diseño del agregador v2 completo: 8 fases (RSS labs, DDG, Google News, Reddit, Dev.to, Referentes, YouTube RSS, GitHub Trending), scoring, formato del mensaje externo, cron job ID y pitfalls por fuente.

## Comandos útiles

```bash
# Listar jobs activos
hermes jobs list

# Ver logs de un job
hermes jobs logs <job-id>
```
