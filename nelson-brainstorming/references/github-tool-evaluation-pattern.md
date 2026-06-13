# Patrón: Evaluación de Herramientas de Terceros (GitHub)

Estructura estándar para documentar la evaluación de un repo de GitHub cuando Nelson pregunta "¿nos sirve?".

Guardar como: `~/brainstorming/YYYY-MM-DD-{nombre-herramienta}-evaluacion/README.md`

---

## Plantilla

```markdown
# Brainstorming: {Nombre Herramienta} — Evaluación de Integración

**Fecha:** YYYY-MM-DD  
**Origen:** Solicitud de Nelson (Tony Stark) — investigar si {herramienta} sirve para el stack AlegentAI.  
**Decisión:** {Veredicto global} — {una línea}

---

## Qué es

{2-3 oraciones}.  
**Autor:** {autor}  
**Repo:** https://github.com/{owner}/{repo}  
**Web:** {url si aplica}  
**⭐ Stars:** {N} | **License:** {MIT/Apache/etc.} | **Lang:** {TypeScript/Python/etc.}

---

## Stack Tecnológico

| Capa | Tecnología | Compatibilidad Stack Nelson |
|------|------------|----------------------------|
| Backend | {tech} | { ✅ / ❌ / ⚖️ } |
| Frontend | {tech} | { ✅ / ❌ / ⚖️ } |
| Base de datos | {tech} | { ✅ / ❌ / ⚖️ } |
| LLM Framework | {tech} | { ✅ / ❌ / ⚖️ } |
| Auth | {tech} | { ✅ / ❌ / ⚖️ } |

---

## Features Principales

1. **{Feature 1}** — {breve descripción}
2. **{Feature 2}** — {breve descripción}
3. **{Feature 3}** — {breve descripción}

---

## Análisis de Integración

### Meta-Orchestrator
- { ✅ / ❌ / ⚖️ } {Justificación de 1-2 líneas}

### ForestAI (FastAPI + React + PostgreSQL/PostGIS)
- { ✅ / ❌ / ⚖️ } {Justificación de 1-2 líneas}

### Expreso Bisonte (Pipeline Excel 1:1)
- { ✅ / ❌ / ⚖️ } {Justificación de 1-2 líneas}

### Futura App / Línea de Producto Nueva
- { ✅ / ❌ / ⚖️ } {Justificación de 1-2 líneas}

---

## Componentes Potencialmente Reutilizables

| Componente | Valor | Complejidad de Porte |
|------------|-------|----------------------|
| {componente} | {alta/media/baja} | {estimación} |

---

## Requisitos para Futuro Uso (si se decide integrar/portar)

- {requisito técnico 1}
- {requisito técnico 2}
- {requisito técnico 3}

---

## Próximos Pasos (Sujetos a Prioridad de Nelson)

1. {Spike/acción sugerida}
2. {Validación}
3. {Decisión de integrar o descartar}

---

## Criterios de Activación (¿Cuándo revisitar este doc?)

- Nelson dice: "{trigger phrase}"
- {Otro trigger de negocio/técnico}
```

---

## Ejemplos Concretos

### CopilotKit (SDK agente embebido)
- Veredicto: NO integrar. Es un ecosistema completo con runtime GraphQL propio.
- Joya escondida: `useAgent` hook + Generative UI para futura app con copilot integrado.
- Activación: cuando Nelson dice "quiero una app con copilot integrado".

### Open Notebook (alternativa a Notebook LM)
- Veredicto: NO integrar. Producto completo con SurrealDB + Next.js, incompatible.
- Joya escondida: generación de podcasts multi-speaker (1-4 speakers) con perfiles custom.
- Activación: cuando Nelson dice "quiero que ForestAI genere resúmenes en audio formato conversación".

---

## Veredictos Estándar

| Emoji | Significado | Cuándo usar |
|-------|-------------|-------------|
| ✅ | SÍ — integrar/portar | Caso ideal, no hay overkill |
| ❌ | NO — descartar | Incompatible, duplica, overkill |
| ⚖️ | MEDIO — spike primero | Prometedor pero con riesgos/adicional |
| ⚡ | JOYA ESCONDIDA | Feature/componente aislado vale la pena recordar |

**Regla de oro:** Ser honesto. Nelson prefiere un "NO, overkill" directo que una evaluación ambigua.
