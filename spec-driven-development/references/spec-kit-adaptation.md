# Spec Kit (GitHub) → Adaptación Nelson

**Fecha:** 2026-05-14
**Origen:** Análisis de https://github.com/github/spec-kit
**Estado:** Referencia estratégica — pendiente implementación progresiva

---

## Resumen

Spec Kit es un toolkit open-source de GitHub para Spec-Driven Development. En vez de adoptar su repo, mapeamos sus 8 fases a nuestras skills existentes y las 3 skills nuevas que necesitamos crear.

---

## Mapeo Fases → Skills Nelson

| # | Fase Spec Kit | Qué hace | Skill Nelson equivalente | Estado |
|---|---------------|----------|-------------------------|--------|
| 1 | `/speckit.constitution` | Principios del proyecto, calidad, stack, reglas de negocio | **`nelson-project-constitution`** (nueva) | ❌ No existe |
| 2 | `/speckit.specify` | Definir QUÉ construir (user stories, reqs) | `spec-driven-development` (OpenAPI primero) | ✅ Existe |
| 3 | `/speckit.clarify` | Clarificar requerimientos vagos | Integrar en `spec-driven-development` | ❌ Parcial |
| 4 | `/speckit.plan` | Plan técnico con stack elegido | `writing-plans` + `nelson-project-bootstrap` | ✅ Existe |
| 5 | `/speckit.analyze` | Revisar coherencia spec→plan→tasks | **`nelson-spec-analyzer`** (nueva) | ❌ No existe |
| 6 | `/speckit.tasks` | Breakdown de tareas accionables | `subagent-driven-development` (2-stage review) | ✅ Existe |
| 7 | `/speckit.checklist` | Quality checklist antes de implementar | `requesting-code-review` + `nelson-code-quality` | ✅ Existe |
| 8 | `/speckit.implement` | Ejecutar el plan | `subagent-driven-development` (delegate_task) | ✅ Existe |

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

## Skills NUEVAS a crear (3)

### 1. `nelson-project-constitution`
Genera el `CONSTITUTION.md` de un proyecto: principios, calidad mínima, stack permitido, reglas de negocio. Cada proyecto nuevo arranca con esto. Es como el README de la metodología.

**Contenido típico:**
- Stack permitido (ej: Python 3.12, FastAPI, React 19, Docker)
- Calidad mínima (type hints estrictos, 80% coverage, pre-commit)
- Reglas de negocio (ej: "todo endpoint debe tener rate limiting")
- UX principles (responsive, accesibilidad mínima)
- Performance targets (TTFB < 200ms, bundle < 500KB)

### 2. `nelson-spec-analyzer`
Revisa coherencia entre:
- Spec (qué se pidió) vs Plan (cómo se va a hacer)
- Plan vs Tasks (todo está cubierto?)
- Detecta over-engineering antes de codear

**Preguntas que responde:**
- ¿Cada user story del spec tiene tareas en el plan?
- ¿Hay dependencias circulares en las tareas?
- ¿El plan propone librerías que no están en el stack aprobado?
- ¿Hay endpoints en el spec que no aparecen en el plan?

### 3. `nelson-spec-driven-workflow` (SKILL MAESTRA)
Documenta el flujo completo 1→8. Carga las skills necesarias en orden. Es la "skill de skills".

**Uso:**
```
Tony: "empezamos proyecto X"
→ JARVIS carga `nelson-spec-driven-workflow`
→ Paso 1: generar CONSTITUTION.md
→ Esperar OK de Tony
→ Paso 2: generar spec OpenAPI
→ ...etc
```

---

## Lecciones de Spec Kit para adoptar

**1. Templates versionados**
Spec Kit usa `.specify/templates/` con overrides por proyecto. Nosotros podemos tener `templates/constitution-template.md` y `templates/spec-template.md` en cada proyecto.

**2. Comandos slash para agentes**
Spec Kit define `/speckit.constitution`, `/speckit.specify`, etc. Nosotros podemos usar frases clave:
- `"JARVIS, constitution para proyecto X"` → genera principios
- `"JARVIS, specify"` → genera spec OpenAPI
- `"JARVIS, analyze"` → revisa coherencia spec/plan

**3. Research antes de planear**
Spec Kit tiene un paso `research.md` donde el agente investiga la tech stack antes de implementar. Esto evita proponer librerías obsoletas. Lo podemos integrar en `writing-plans`.

**4. Cross-artifact analysis**
`/speckit.analyze` revisa que el plan cubra todo el spec. Es como un code review antes de escribir código. Nuestro `nelson-spec-analyzer` haría eso.

**5. Extensiones y presets**
Spec Kit permite extensiones (nuevos comandos) y presets (customizar templates). El equipo I+D+I puede crear extensiones custom que luego el equipo Central estandariza.

---

## Roadmap de adopción sugerido

| Fase | Acción | Equipo | Tiempo |
|------|--------|--------|--------|
| 1 | Crear `nelson-spec-driven-workflow` (skill maestra) | JARVIS + Tony | 1h |
| 2 | Crear `nelson-project-constitution` | JARVIS + Tony | 1h |
| 3 | Probar flujo completo con un PoC de I+D+I | I+D+I | 1 proyecto |
| 4 | Refinar según feedback | JARVIS + Tony | 30min |
| 5 | Integrar `nelson-spec-analyzer` | JARVIS | 1h |
| 6 | Adoptar en equipo Central para proyectos reales | Central | Proyecto 1 |
| 7 | Documentar lecciones y actualizar skills | JARVIS | 30min |

---

## Notas

- No adoptamos el repo de Spec Kit ni sus dependencias (uv, specify-cli)
- Solo adoptamos la **metodología** y la **estructura de fases**
- Todo se implementa con nuestras skills existentes + 3 nuevas
- El objetivo es formalizar lo que ya hacemos, no reemplazarlo
