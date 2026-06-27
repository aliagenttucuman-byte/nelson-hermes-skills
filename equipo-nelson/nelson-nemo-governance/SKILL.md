---
name: nelson-nemo-governance
description: >
  Plataforma de Gobierno y Tuning de NemoHermes para clientes enterprise (YPF).
  Zero Trust, SSO EntraID, RBAC, versionado de skills/prompts/MCPs/tools, workflow
  de aprobación, PII scanner, cruce de datos entre áreas con aprobación dual.
tags: [nelson, ypf, nemohermes, governance, enterprise, sso, rbac, zero-trust]
category: equipo-nelson
---

# NemoHermes Governance Platform

## Trigger

- Cliente enterprise tiene NemoHermes ya implementado y necesita gobierno sin devs
- Múltiples áreas/VPs quieren usar agentes con aislamiento y control
- Necesidad de versionar prompts/skills con trazabilidad completa
- Requisito de SSO corporativo (EntraID, Okta, etc.)

## Contexto de Origen

Desarrollado para YPF (jun 2026). NemoHermes es una capa de routing de capacidades
NVIDIA (vLLM, NIM, Whisper) que corre sobre DGX Spark. La plataforma de gobierno
se acopla sobre eso para que VPs y analistas puedan operar sin intervención de IT.

Repo NemoHermes: https://github.com/Hmbown/NemoHermes

## Arquitectura en 5 Capas

```
Usuarios (VPs, Analistas, Admin)
        ↓ EntraID SSO
Capa 1 — Autenticación (Zero Trust)
  JWT Token + RBAC + Namespace por área + Audit Log
        ↓
Capa 2 — Panel de Gobierno (UI sin código)
  Editor Prompts │ Catálogo Skills │ MCPs │ Tools
  Workflow Aprobación │ Dashboard KPIs │ PII Scanner
        ↓
Capa 3 — Registry Versionado
  Skills Registry │ Prompt Templates │ MCP Registry │ Tools
  Git interno │ Azure Key Vault (secrets)
        ↓
Capa 4 — NemoHermes Core
  Routing Engine │ Capability Registry │ Hermes Agent
  FastAPI :9000 │ React UI
        ↓
Capa 5 — Infraestructura
  PostgreSQL │ Redis │ vLLM/NIM │ Qdrant │ Key Vault │ GCP
  Tailscale (Zero Trust Network)
```

## Esquema Dinámico

### Skill
```yaml
skill:
  id: "fin-001"
  area: "Finanzas"
  owner: "vp-finanzas@cliente.com"
  version: "2.1.0"
  estado: "approved"  # draft | review | approved | deprecated | rejected
  permisos:
    lectura: ["finanzas", "presidencia"]
    ejecucion: ["finanzas"]
  contenido: |
    # Sin datos hardcodeados — usar variables {{periodo}}, {{unidad}}
```

### Prompt Template
```yaml
prompt_template:
  variables:
    - nombre: "periodo"
      tipo: "string"
  contenido: |
    Analizá {{unidad_negocio}} para {{periodo}}...
  pii_check: passed   # PII Scanner obligatorio antes de aprobar
```

### MCP
```yaml
mcp:
  tipo: "readonly"
  datos_prohibidos: ["datos_personales", "salarios"]
  autenticacion: "azure-key-vault/token-name"
  permisos_por_rol:
    VP: readwrite
    Analista: readonly
    ReadOnly: denied
```

## Workflow de Aprobación

```
Author crea/modifica → PII Scanner automático
  ↓ datos sensibles → rechaza + notifica
  ↓ OK → estado: review → notifica Admin
Admin aprueba → Git commit automático (tag versión) → deploy
Admin rechaza → vuelve a draft con comentarios
Todo queda en Audit Log inmutable
```

## Matriz de Permisos

| Acción | ReadOnly | Analista | VP | Admin |
|--------|----------|----------|-----|-------|
| Ver skills del área | ✅ | ✅ | ✅ | ✅ |
| Ver skills otras áreas | ❌ | ❌ | ❌ | ✅ |
| Crear skill (draft) | ❌ | ✅ | ✅ | ✅ |
| Aprobar skill | ❌ | ❌ | ❌ | ✅ |
| Crear MCP | ❌ | ❌ | ✅ | ✅ |
| Cruce de datos | ❌ | ❌ | ✅* | ✅ |

*VP puede solicitar — requiere aprobación de ambas VPs + Admin

## Cruce de Datos entre Áreas

- Los datos NUNCA salen de su namespace de origen
- El agente tiene acceso de lectura temporal a ambos namespaces
- Requiere aprobación de VP origen + VP destino + Admin
- Se crea namespace temporal con TTL (ej: 30 días)
- Todo el acceso queda en Audit Log

## Stack Tecnológico

| Componente | Tecnología |
|------------|-----------|
| Auth | Microsoft EntraID + MSAL |
| Backend | FastAPI (Python) |
| Frontend | React + TypeScript |
| Editor prompts | Monaco Editor / TipTap |
| DB | PostgreSQL (skills, prompts, audit) |
| Cache | Redis (permisos) |
| Versionado | Git bare repo interno |
| Secrets | Azure Key Vault |
| Vector search | Qdrant |
| PII Scanner | Microsoft Presidio |
| Infra | GCP + Terraform |
| Red | Tailscale Zero Trust |

## Roadmap (16 semanas)

- **Fase 1 (4 sem):** EntraID + RBAC + modelo datos + Git versionado
- **Fase 2 (4 sem):** Panel React + editor prompts + workflow aprobación + PII Scanner
- **Fase 3 (3 sem):** MCPs + Tools + Dashboard KPIs + Key Vault
- **Fase 4 (3 sem):** Cruce de datos + Audit log + Rate limiting
- **Fase 5 (2 sem):** Deploy GCP + Tailscale + piloto 2 VPs + docs usuario final

## Entregables

- `references/nemo-governance-ypf.md` — documentación completa para YPF
- Diagrama PNG: `/tmp/nemo-governance/nemo-governance.png`
- Doc MD: `/tmp/nemo-governance/NEMO_HERMES_GOVERNANCE.md`

## Pitfalls

1. **Exclusividad de PI en NDA Globant** — si el cliente usa Globant como intermediario,
   la cláusula 4 de PI puede reclamar el código desarrollado. Agregar carve-out de IP preexistente antes de firmar.
2. **SWIFT bancario** — Lead Bank SWIFT es LEADUS42 (sin XXX al llenar formularios).
   No confiar en LEIBUS44 que circula en internet — verificar en app o swift.com.
3. **Namespaces temporales** — deben tener TTL explícito y cleanup automático. Sin TTL
   los cruces de datos quedan abiertos indefinidamente.
4. **PII Scanner** — usar Microsoft Presidio con modelos en español para detectar CUIL,
   DNI, direcciones argentinas además de los patrones anglosajones por defecto.
