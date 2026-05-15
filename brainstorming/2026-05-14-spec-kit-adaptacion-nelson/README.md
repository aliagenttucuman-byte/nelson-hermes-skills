# Spec Kit → Adaptación Nelson
## Metodología SDD propia, sin dependencias externas

**Fecha:** 2026-05-14
**Estado:** Diseño de adaptación

---

## Fases Spec Kit → Nuestras Skills

| Fase Spec Kit | Qué hace | Nuestra skill equivalente | Estado |
|---|---|---|---|
| `/speckit.constitution` | Principios del proyecto, calidad, stack | **NUEVA:** `nelson-project-constitution` | ❌ No existe |
| `/speckit.specify` | Definir QUÉ construir (user stories, reqs) | `spec-driven-development` (OpenAPI primero) | ✅ Existe |
| `/speckit.clarify` | Clarificar requerimientos vagos | **NUEVA:** integrar en `spec-driven-development` | ❌ Parcial |
| `/speckit.plan` | Plan técnico con stack elegido | `writing-plans` + `nelson-project-bootstrap` | ✅ Existe |
| `/speckit.analyze` | Revisar coherencia spec→plan→tasks | **NUEVA:** `nelson-spec-analyzer` | ❌ No existe |
| `/speckit.tasks` | Breakdown de tareas accionables | `subagent-driven-development` (2-stage review) | ✅ Existe |
| `/speckit.checklist` | Quality checklist antes de implementar | `requesting-code-review` + `nelson-code-quality` | ✅ Existe |
| `/speckit.implement` | Ejecutar el plan | `subagent-driven-development` (delegate_task) | ✅ Existe |

---

## Flujo Adaptado "Nelson SDD"

```
1. CONSTITUCIÓN → `nelson-project-constitution`
   "Creemos los principios: calidad, testing, UX, performance, stack base"

2. SPECIFICAR → `spec-driven-development`
   "Definimos QUÉ se construye: OpenAPI specs, user stories, data model"

3. CLARIFICAR → (integrado en spec-driven-development)
   "Revisamos si falta algo, si hay ambigüedades, si los reqs son completos"

4. PLANEAR → `writing-plans`
   "Breakdown técnico: archivos, dependencias, orden de implementación"

5. ANALIZAR → `nelson-spec-analyzer`
   "Revisar que el plan cubra TODO lo del spec. Nada de over-engineering."

6. TAREAS → `subagent-driven-development`
   "Convertir plan en tareas concretas para cada agente (Beto, Ricky, Nico...)"

7. CHECKLIST → `requesting-code-review` + `nelson-code-quality`
   "Validar antes de implementar: ¿tests? ¿docs? ¿seguridad? ¿performance?"

8. IMPLEMENTAR → `subagent-driven-development`
   "Beto diseña → Ricky codea backend → Nico codea frontend → Diego dockeriza → Alma testea"
```

---

## Skills NUEVAS a crear

### 1. `nelson-project-constitution`
Genera el `CONSTITUTION.md` de un proyecto: principios, calidad mínima, stack permitido, reglas de negocio. Cada proyecto nuevo arranca con esto. Es como el README de la metodología.

### 2. `nelson-spec-analyzer`
Revisa coherencia entre:
- Spec (qué se pidió) vs Plan (cómo se va a hacer)
- Plan vs Tasks (todo está cubierto?)
- Detecta over-engineering antes de codear

### 3. `nelson-spec-driven-workflow` (SKILL MAESTRA)
Documenta el flujo completo 1→8. Carga las skills necesarias en orden. Es la "skill de skills".

---

## ¿Qué opinas?

¿Empezamos creando `nelson-project-constitution` y `nelson-spec-analyzer`? O preferís que primero actualice `spec-driven-development` para que incluya clarificación y análisis?
