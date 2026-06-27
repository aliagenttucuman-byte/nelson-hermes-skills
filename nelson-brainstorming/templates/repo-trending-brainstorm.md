# {NOMBRE_REPO} — Posible Brainstorming

> **Fecha:** {YYYY-MM-DD}
> **Status:** 💡 IDEA — {esperar madurez / listo para spike / vigilar}
> **Trigger:** Tony preguntó si vale la pena.
> **Repo upstream:** https://github.com/{org}/{repo} ({LICENSE}, {stars}k ⭐ en {edad})
> **Modelo/Paper (si aplica):** {HF link}, {arxiv link}

## TL;DR

{Resumen de 4-6 líneas: qué hace, por qué importa, veredicto inicial (self-host viable o no).}

## Arquitectura / Stack

- **Lenguaje:** {Python / TS / etc}
- **Modelo base / runtime:** {detalle}
- **Dependencias críticas:** {torch X.Y, CUDA Z, etc}
- **Tamaño:** {modelo + deps}

## Hardware vs ai-server actual

| Recurso | Necesita | Tenemos | Veredicto |
|---|---|---|---|
| VRAM | {X GB} | 4 GB GTX 1650 | {✅/⚠️/❌} |
| RAM | {X GB} | 13 GB | {} |
| Disco | {X GB} | 126 GB libres | {} |
| CUDA | {X.Y} | 12.2 instalado | {} |

## Qué Entra y Qué No

### ✅ Self-hosteable HOY en ai-server

{lista o tabla con modelos/configs que entran}

### ❌ NO entra (requiere más recursos)

{lista de lo que requiere RunPod/Lambda on-demand}

## Cómo encaja en el stack del equipo Nelson

| Skill / Proyecto actual | Cómo encaja {repo} |
|---|---|
| `nelson-{skill}` | {detalle} |
| AlegentAI / ForestAI | {casos de uso} |
| LAN/LATAM (M365) | {si aplica} |
| Expreso Bisonte | {si aplica} |

## Hipótesis de Valor

```
CREEMOS QUE
  {hipótesis técnica + comercial}
RESULTARÁ EN
  {output concreto vendible o útil}
CRITERIOS DE ACEPTACIÓN
  - {criterio 1 verificable}
  - {criterio 2 verificable}
  - {criterio 3 verificable}
```

## Plan de Acción Propuesto (2 Fases)

### Fase 1 — VIGILAR (semanas 0-{N})

Monitorear:
- Releases en GitHub
- Issues cerradas / nuevas relacionadas con {limitación principal}
- Aparición de {quantización / soporte español / etc} oficial
- Benchmarks públicos vs {alternativas actuales}

**Trigger para pasar a Fase 2:** {condiciones concretas}.

### Fase 2 — SPIKE (cuando Fase 1 dispare)

Opciones de ejecución:

**A) Self-hosted en ai-server** — si {condiciones}
**B) RunPod / Lambda on-demand** — para validar calidad sin tocar ai-server
**C) API hosted del proveedor** — solo para PoC sin compromiso

## Pitfalls Identificados

- {Pitfall técnico 1}
- {Pitfall de licencia / privacidad}
- {Pitfall de mantenimiento / madurez}

## Comparativa vs Alternativas Actuales

| Solución | Calidad | Velocidad | VRAM | Self-host viable |
|---|---|---|---|---|
| {Alternativa actual del stack} | | | | ✅ ya en producción |
| **{Este repo}** | | | | {} |

## Próximos Pasos

1. {Acción concreta inmediata si Tony aprueba}
2. {Si va Fase 1 → crear cron-job watcher}
3. {Si va Fase 2 → crear skill operativa `nelson-{nombre}`}

## Referencias

- Repo: {URL}
- Modelo: {HF URL si aplica}
- Paper: {arxiv si aplica}
- Skills relacionadas: `nelson-{skill1}`, `nelson-{skill2}`

## Status del Brainstorming

- [x] Idea capturada
- [x] Hardware analizado
- [x] Plan de 2 fases propuesto
- [ ] Tony aprueba próxima acción
- [ ] Spike iniciado
- [ ] Veredicto VALIDATED / PARTIAL / INVALIDATED
