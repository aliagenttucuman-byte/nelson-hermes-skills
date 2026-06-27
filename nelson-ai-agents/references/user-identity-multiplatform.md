# Identidad Multi-Plataforma para JARVIS / Agentes del Equipo Nelson

Referencia técnica para reconocer al mismo usuario desde cualquier canal
(WhatsApp, Telegram, Microsoft Teams, Slack) y cargar su memoria Holographic
de forma unificada. Spec completa en `~/brainstorming/2026-05-29-user-identity-memory/`.

---

## Problema

Cada plataforma genera un ID distinto para el mismo usuario humano:

| Plataforma | Campo clave | Estabilidad |
|------------|-------------|-------------|
| WhatsApp (Baileys) | `from` (ej: `5493812345678@s.whatsapp.net`) | Estable |
| Telegram | `message.from.id` (entero) | Estable |
| Teams | `activity.from.aadObjectId` (UUID Azure AD) | ⚠️ Ver abajo |
| Slack | `event.user` | Estable |

### Microsoft Teams — pitfall crítico

Teams tiene **dos** identificadores diferentes:
- `from.id` — formato `29:1XXXXX`, inestable entre tenants y reinstalaciones
- `from.aadObjectId` — UUID de Azure Active Directory, inmutable mientras exista la cuenta ✅

**Siempre usar `aadObjectId` para Teams.** También capturar `channelData.tenant.id` para soporte multi-tenant.

---

## Solución: Tres capas

### Capa 1 — Identity Map

Archivo `~/.hermes/identity_map.json`:

```json
{
  "version": "1.0",
  "users": {
    "nelson": {
      "canonical_id": "nelson",
      "display_name": "Nelson Acosta (Tony Stark)",
      "role": "owner",
      "aliases": {
        "whatsapp": ["5493812345678@s.whatsapp.net"],
        "telegram": [8896858194],
        "teams": ["<aadObjectId-uuid>"]
      }
    }
  }
}
```

### Capa 2 — IdentityResolver (Python)

```python
# identity/resolver.py
import json
from pathlib import Path

class IdentityResolver:
    def __init__(self, map_path="~/.hermes/identity_map.json"):
        self.map_path = Path(map_path).expanduser()
        self._load()

    def _load(self):
        with open(self.map_path) as f:
            data = json.load(f)
        # Construir índice inverso: (platform, raw_id) -> canonical_id
        self._index: dict[tuple, str] = {}
        for canonical_id, user in data["users"].items():
            for platform, ids in user.get("aliases", {}).items():
                for raw_id in ids:
                    self._index[(platform, str(raw_id))] = canonical_id

    def resolve(self, platform: str, raw_id: str) -> str | None:
        """Devuelve canonical_id o None si el usuario no está registrado."""
        return self._index.get((platform, str(raw_id)))

    def is_pending(self, platform: str, raw_id: str) -> bool:
        """True si está en lista de pendientes de aprobación."""
        # TODO: implementar pending_approvals.json
        return False
```

### Capa 3 — Hook en gateway de mensajes

```python
# En el handler de mensajes entrantes (WhatsApp, Telegram, Teams):
resolver = IdentityResolver()

def handle_message(platform: str, raw_id: str, message: str):
    canonical_id = resolver.resolve(platform, raw_id)

    if canonical_id is None:
        # Usuario desconocido → notificar al owner
        notify_owner_pending(platform, raw_id, message)
        return "Hola! Tu solicitud de acceso fue enviada al administrador."

    # Usuario conocido → cargar memoria Holographic
    context = fact_store.probe(canonical_id)
    response = jarvis.reply(message, user_context=context)
    
    # Guardar nuevo hecho si aplica
    if new_fact := extract_fact(message):
        fact_store.add(content=new_fact, tags=canonical_id)
    
    return response
```

---

## Flujos

### Primera vez (usuario nuevo)
```
mensaje → resolve() → None
→ agregar a pending_approvals.json
→ notificar a owner (Nelson) por WhatsApp
→ Nelson aprueba → crear canonical_id → agregar alias
```

### Sesión posterior (usuario conocido)
```
mensaje → resolve() → canonical_id
→ fact_store.probe(canonical_id) → contexto histórico
→ JARVIS responde con contexto cargado
→ fact_store.add() si hay nuevo hecho
```

### Usuario ya conocido llega desde canal nuevo
```
"soy Nelson, mi Telegram es @nelson_acosta"
→ verificar identidad (Nelson confirma desde canal conocido)
→ agregar nuevo alias al canonical_id existente
→ actualizar identity_map.json
```

---

## SIE (Superlinked Inference Engine) como potenciador

SIE es un servidor de inferencia open source que mejora tres puntos del pipeline:

| Componente | Rol | Modelo sugerido |
|------------|-----|-----------------|
| `extract` (GLiNER) | Extrae entidades auto de cada mensaje → taggeo automático en Holographic | urchade/gliner_multi-v2.1 |
| `encode` (BGE-M3) | Embeddings densos + sparse para reemplazar HRR básico | BAAI/bge-m3 |
| `score` (BGE-reranker) | Reranking de hechos antes de armar el prompt | BAAI/bge-reranker-v2-m3 |

Deploy en ai-server:
```bash
# CPU (sin GPU)
docker run -d --name sie-server -p 8080:8080 \
  ghcr.io/superlinked/sie-server:latest-cpu-default

# Verificar
curl http://localhost:8080/health
```

---

## Activar Holographic como provider de memoria

```bash
hermes config set memory.provider holographic
hermes memory status
```

Con Holographic activo, `fact_store.probe("canonical_id")` devuelve TODOS los
hechos acumulados del usuario en TODAS las sesiones y TODOS los canales.

---

## Fases de implementación

| Fase | Qué | Esfuerzo |
|------|-----|----------|
| 1 | `identity_map.json` manual + Holographic activo | 1-2 hs |
| 2 | `identity/resolver.py` + hook en gateway de Hermes | 4-6 hs |
| 3 | PR a Hermes + comandos nativos `hermes identity add/link/list` | 2-3 días |

---

*Referencia generada 2026-05-29 — Sesión de arquitectura JARVIS*
