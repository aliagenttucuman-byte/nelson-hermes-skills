---
name: nelson-spec-driven-workflow
description: "Flujo completo de Spec-Driven Development para el equipo Nelson. Skill maestra que orquesta las 8 fases del ciclo SDD adaptado a nuestra consultora."
version: 1.0.0
author: Equipo Nelson (Tony + JARVIS)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [spec-driven-development, sdd, workflow, nelson, fastapi, react, docker]
    related_skills: [nelson-project-constitution, spec-driven-development, writing-plans, subagent-driven-development, requesting-code-review, nelson-code-quality, nelson-project-bootstrap, nelson-pricing-model]
---

# Nelson Spec-Driven Workflow

Skill maestra que documenta el flujo completo de **Spec-Driven Development (SDD)** adaptado para la consultora de Nelson.

## Origen

Este flujo está basado en la metodología de [GitHub Spec Kit](https://github.com/github/spec-kit), pero **adaptado a nuestro stack y estructura de 2 equipos**. No dependemos del repositorio externo: usamos nuestras propias skills.

## Flujo de 8 Fases

```
┌─────────────────────────────────────────────────────────────────┐
│  NELSON SPEC-DRIVEN DEVELOPMENT (SDD)                          │
│                                                                │
│  1. CONSTITUCIÓN  ──→  Principios del proyecto                │
│  2. SPECIFICAR    ──→  Qué construir (OpenAPI)                │
│  3. CLARIFICAR    ──→  Revisar ambigüedades                   │
│  4. PLANEAR       ──→  Cómo construir (tech stack)            │
│  5. ESTIMAR       ──→  Costos reales antes de codear         │
│  6. ANALIZAR      ──→  Coherencia spec→plan→estimación       │
│  7. TAREAS        ──→  Breakdown para agentes                 │
│  8. CHECKLIST     ──→  Validar antes de codear                │
│  9. IMPLEMENTAR   ──→  Ejecutar con agentes                   │
└─────────────────────────────────────────────────────────────────┘
```

## Fases Detalladas

### 1. CONSTITUCIÓN → `nelson-project-constitution`

**Quién:** Tony (líder) + Beto (arquitecto)

**Qué hace:** Define los principios fundacionales del proyecto antes de escribir una línea de código.

**Salida:** `CONSTITUTION.md` con:
- Stack permitido (Python 3.12, FastAPI, React 19, Docker)
- Estándares de calidad (type hints, tests, docs)
- Reglas de negocio clave
- Principios UX (móvil-first, accesibilidad)
- Restricciones (presupuesto, tiempo, compliance)

**Regla:** Sin CONSTITUTION, no hay proyecto. Es la "constitución" que todos los agentes deben respetar.

---

### 2. SPECIFICAR → `spec-driven-development`

**Quién:** Beto (arquitecto backend)

**Qué hace:** Define QUÉ se construye. No cómo, no con qué tech. Solo el QUÉ.

**Salida:**
- `specs/openapi.yaml` — API contract
- `specs/user-stories.md` — User stories con criterios de aceptación
- `specs/data-model.md` — Entidades y relaciones

**Regla de Nelson:** OpenAPI PRIMERO, código DESPUÉS. Si no hay spec, no se codea.

---

#### Formato de User Stories del equipo Nelson

Nelson usa el esquema **CREEMOS QUE / RESULTARÁ EN / CRITERIOS DE ACEPTACIÓN**. Es el formato obligatorio para todas las HU del equipo (tanto para I+D+I como para el equipo Central).

```markdown
## HU-XX — [Título breve]

**CREEMOS QUE** al [construir/implementar/agregar X],
lograremos [beneficio esperado para el usuario o el sistema].

**RESULTARÁ EN** [descripción del artefacto o comportamiento concreto que se entrega].

**CRITERIOS DE ACEPTACIÓN:**
- Dado [contexto], cuando [acción], entonces [resultado observable]
- Dado [contexto], cuando [acción], entonces [resultado observable]
- [Criterio no-funcional: tiempo, límite, comportamiento en fallo]
- [Criterio de continuidad: qué pasa si algo falla parcialmente]
```

**Reglas del formato:**
- El "CREEMOS QUE" arranca con una hipótesis validable, no con una descripción técnica
- El "RESULTARÁ EN" describe el entregable concreto (módulo, pipeline, PNG, endpoint)
- Los criterios de aceptación usan lenguaje "Dado/Cuando/Entonces" (BDD-style) para los comportamientos funcionales, y lenguaje directo para los no-funcionales (tiempos, límites)
- Mínimo 4 criterios por HU: al menos 2 funcionales, 1 no-funcional (performance/tiempo), 1 de resiliencia (qué pasa si falla)

**Separación pipeline vs renderización:**
Cuando una HU describe tanto la extracción/procesamiento de datos COMO la visualización, separarlas en dos HUs distintas:
- HU de **motor/pipeline**: captura datos, parsea, produce DataFrames o estructuras limpias
- HU de **renderización/UI**: toma los datos limpios y genera gráficos, reportes, imágenes

Esto aplica especialmente en proyectos tipo PowerBI → WhatsApp, donde el "extraer querydata y parsear DSR" es independiente del "generar PNG con matplotlib". Beneficio: cada HU es testeable por separado y el motor es reutilizable por otras HUs de visualización.

**Ejemplo real (spike PowerBI → WhatsApp):**

```markdown
## HU-01 — Extracción de datos desde tablero Power BI público

CREEMOS QUE al construir un mecanismo que intercepte automáticamente las llamadas
internas de un embed público de Power BI usando un browser headless, lograremos
extraer los datos reales del tablero sin necesitar credenciales Azure AD ni acceso
a la API corporativa de Microsoft.

RESULTARÁ EN un módulo Python reutilizable que, dada una URL pública de Power BI,
capture y parsee el formato DSR interno devolviendo un DataFrame estructurado.

CRITERIOS DE ACEPTACIÓN:
- Dado una URL pública válida, cuando se ejecuta el módulo, entonces se capturan
  todos los archivos querydata emitidos por el tablero (mínimo 1)
- Dado el JSON DSR capturado, cuando se ejecuta el parser, entonces se obtiene un
  DataFrame con columnas nombradas correctamente y sin datos vacíos
- El proceso completa en menos de 45 segundos incluyendo la carga del browser
- El módulo funciona en modo caché: si los JSON ya existen, los reutiliza sin
  lanzar el browser (ejecución en menos de 3 segundos)
- El módulo acepta cualquier URL pública de Power BI sin cambios de código
```

---

### 3. CLARIFICAR → Integrado en `spec-driven-development`

**Quién:** Tony valida, Beto ajusta

**Qué hace:** Revisa que no haya ambigüedades. Pregunta tipo:
- "¿Y si el usuario no tiene permiso?"
- "¿Qué pasa con datos vacíos?"
- "¿Hay límites de paginación?"

**Salida:** Sección "Clarificaciones" agregada al spec.

**Regla:** Una ambigüedad en el spec = 10 horas de rework. Mejor clarificar ahora.

---

### 4. PLANEAR → `writing-plans`

**Quién:** Beto diseña, Ricky (backend dev) y Nico (frontend dev) revisan

**Qué hace:** Define CÓMO se construye. Tech stack, arquitectura, dependencias, orden de implementación.

**Salida:** `PLAN.md` con:
- Arquitectura de componentes
- Dependencias y versiones
- Orden de implementación (qué primero, qué después)
- Riesgos y mitigaciones
- Estimación de esfuerzo

---

### 5. ESTIMAR → `nelson-pricing-model`

**Quién:** JARVIS genera, Tony valida, Pablo usa para negociar

**Qué hace:** Define los costos reales del proyecto antes de tocar código.

**Salida:** `ESTIMACION.md` con:
- Costo de desarrollo (horas × personas × $30/hora)
- Costo de infraestructura cloud mensual
- Costo de LLM (tokens)
- Suscripción mensual recurrente
- Plan de pagos por hitos

> **Para proyectos RAG (PoC → Producción):** Usar los 3 paquetes estándar del equipo (Essential $21.600, Professional $26.400, Enterprise $30.000) como punto de partida en vez de estimar desde cero. Ver `nelson-pricing-model` → "Paquetes Estándar para RAG".

**Regla de Nelson:** Sin ESTIMACION.md aprobada, no se implementa. Tony decide si los números son viables antes de gastar horas de desarrollo.

**Modelo de negocio:**
- **Desarrollo:** se cobra one-time ($30/hora)
- **Software:** incluido en desarrollo, sin costo de licencia
- **Suscripción mensual:** infra + soporte + mantenimiento

---

### 6. ANALIZAR → `nelson-spec-analyzer`

**Quién:** JARVIS (o Alma en modo QA)

**Qué hace:** Revisa coherencia entre spec, plan y estimación.

**Chequeos:**
- ¿El plan cubre TODAS las user stories del spec?
- ¿Hay funcionalidades en el plan que NO están en el spec? (over-engineering)
- ¿Faltan endpoints en el OpenAPI para alguna user story?
- ¿El data model soporta todas las entidades del spec?
- ¿La estimación cubre TODO el plan? ¿Hay tareas sin estimar?

**Salida:** Reporte de gaps. Si hay gaps, volver a fase 2, 4 o 5.

**Regla:** Si el analyzer encuentra gaps, NO se pasa a implementación.

---

### 7. TAREAS → `subagent-driven-development`

**Quién:** JARVIS orquesta, agentes ejecutan

**Qué hace:** Convierte el plan en tareas concretas para cada agente.

**Salida:** `TASKS.md` con:
- Tareas asignadas a cada agente (Beto, Ricky, Nico, Diego, Alma)
- Dependencias entre tareas (qué bloquea a qué)
- Tareas paralelizables marcadas con [P]
- Criterios de done por tarea

---

### 8. CHECKLIST → `requesting-code-review` + `nelson-code-quality`

**Quién:** Alma (QA) + JARVIS

**Qué hace:** Validación final antes de tocar código.

**Checklist:**
- [ ] ¿Todas las user stories tienen tests definidos?
- [ ] ¿El OpenAPI spec está validado (sin errores de sintaxis)?
- [ ] ¿Hay manejo de errores definido?
- [ ] ¿La seguridad está considerada (auth, CORS, rate limiting)?
- [ ] ¿La documentación está planificada?
- [ ] ¿El stack elegido es compatible con nuestro entorno (GPU 4GB, 13GB RAM)?
- [ ] ¿La estimación está aprobada por Tony?
- [ ] ¿Pablo tiene los números para cotizar al cliente?

**Regla:** Si falta algún check, se completa antes de implementar.

---

### 9. IMPLEMENTAR → `subagent-driven-development`

**Quién:** Todos los agentes en paralelo

**Qué hace:** Ejecuta el plan.

**Orden:**
1. Beto: Scaffolding + models + schemas (base del backend)
2. Ricky: Endpoints + servicios + lógica de negocio
3. Nico: Componentes + pages + consumo de API
4. Diego: Dockerfiles + docker-compose + CI/CD
5. Alma: Tests + QA + revisión final

**Regla:** Cada agente trabaja en su rama. PR obligatorio para mergear a main.

---

## Diferencias con GitHub Spec Kit

| Aspecto | GitHub Spec Kit | Nelson SDD |
|---|---|---|
| Dependencias | CLI `specify`, Node.js, Python | Solo nuestras skills |
| Templates | `.specify/templates/` | Nuestras skills + `~/brainstorming/templates/` |
| Integración | 30+ agentes externos | Nuestros 5 agentes IA + JARVIS |
| Presets | Externos (community) | Nuestros presets internos |
| Storage | `.specify/` en cada repo | Skills globales + `brainstorming/` |

## ¿Cuándo usar este flujo?

**SIEMPRE** para:
- Nuevos proyectos de cliente
- Features mayores (>3 días de trabajo)
- Integraciones con sistemas externos
- Refactors arquitectónicos

**NO es necesario** para:
- Bugfixes simples
- Ajustes de UI menores
- Tareas de mantenimiento
- Spikes y experimentos (I+D+I usa flujo simplificado, ver abajo)

---

## Flujo Simplificado para I+D+I (Experimentación)

El equipo I+D+I (Tony + 2 agentes) trabaja con un flujo **ultra-liviano** para validar hipótesis rápido.

### Diferencias clave

| Aspecto | Equipo Central (producción) | Equipo I+D+I (experimentos) |
|---|---|---|
| **Fases** | 8 fases completas | 3 fases: Spec → Plan → Implementar |
| **Constitución** | CONSTITUTION.md formal | README.md con stack y objetivo |
| **OpenAPI** | Especificación completa | Endpoints clave en texto plano |
| **Tests** | 80% cobertura, unit + integración | Solo si ayudan a validar la hipótesis |
| **Documentación** | Completa + ADRs | README.md + notas breves |
| **Code review** | PR obligatorio con review | Push directo a main |
| **Analyzer** | JARVIS/Alma revisan antes de codear | Tony revisa después de codear |
| **Stack backend** | **Python (FastAPI)** | **Python (libre: FastAPI, Flask, Django, etc.)** |
| **Stack frontend** | **React (Vite)** | **React (libre: Next.js, Remix, etc.)** |
| **Tiempo máximo** | Deadline del cliente | 2-3 días máximo por experimento |
| **Definition of Done** | Código + tests + docs + PR + deploy + OK Tony | "Funciona para demo" + Tony vió el video/screenshot |

### ¿Qué puede variar en I+D+I?

Dentro de **Python + React**, el equipo I+D+I puede experimentar con:

- **Backend:** FastAPI vs Flask vs Django vs Litestar. Async vs sync. Diferentes ORMs (SQLAlchemy vs Tortoise vs Prisma). Diferentes vector DBs.
- **Frontend:** Vite vs Next.js vs Remix. Diferentes state managers (Zustand vs Jotai vs Redux Toolkit). Diferentes UI kits (Shadcn vs Chakra vs Mantine).
- **Infra:** Docker vs Podman. Diferentes observability tools. Diferentes deployment strategies.

**Lo que NO puede variar:** El lenguaje backend es Python. El framework frontend es React. Punto.

### Flujo I+D+I en 3 pasos

```
1. ESPECIFICAR (30 min)
   Tony describe la idea.
   JARVIS escribe README.md con:
   - ¿Qué queremos probar?
   - Stack a usar (puede ser experimental)
   - Criterio de éxito (¿qué resultado valida la hipótesis?)

2. PLANEAR (30 min)
   JARVIS + agentes I+D+I hacen plan ultra-breve:
   - 3-5 tareas máximo
   - Sin estimaciones detalladas
   - Stack flexible ("probamos Svelte en vez de React")

3. IMPLEMENTAR (1-2 días)
   Codear rápido, sin tests salvo que sean necesarios.
   Push directo. Sin PRs. Sin reviews.
   Si no funciona en 2 días: descartar o pivotar.

4. DEMO (15 min)
   Tony ve el resultado.
   Si le gusta → documentar como PoC para posible promoción al equipo Central.
   Si no → archivar en ~/brainstorming/ con nota "no válido".
```

### Reglas I+D+I

- **2 días máximo** por experimento. Si no funciona, se corta.
- **Sin culpa:** Un experimento que falla NO es un fracaso. Es información.
- **Stack base fijo:** Backend Python, Frontend React. Siempre.
- **Variaciones permitidas:** Dentro de Python/React se puede probar frameworks, librerías, ORMs, state managers, UI kits, etc.
- **Sin tests obligatorios:** Solo si ayudan a validar la hipótesis.
- **Sin documentación pesada:** README + notas. Nada más.
- **Promoción:** Si un experimento funciona y Tony quiere llevarlo a producción, se "congela" y el equipo Central lo rebuild desde cero con el flujo completo de 8 fases.

### Ejemplo I+D+I — ForestAI (inventario forestal con drones, 2026-05-19)

```
Tony: "Quiero hacer una PoC de inventario forestal con imágenes de drone — conteo por especie, biomasa, edad"

JARVIS:
  1. README.md: "ForestAI PoC — hipótesis: image analytics clásico (sin ML) puede detectar y clasificar árboles desde ortofotos"
  2. Plan: FastAPI + Rasterio/OpenCV + Celery + React + MapLibre GL JS
  3. Criterio de éxito: 6 puntos concretos (upload → mapa → click → resumen → export → async)
  4. Implementar en 2 días sin ML, sin OpenDroneMap (usuario sube ortofoto ya procesada)

Tony: "Perfecto, usemos esto como caso de prueba para el flujo I+D+I"
(Se ejecuta el flujo completo de la sesión: README → spec → plan → implementar)
```

Ver referencia de dominio: `nelson-brainstorming/references/forestai-inventario-forestal-drones.md`

---

### Ejemplo I+D+I — Zustand vs React Query

```
Tony: "Quiero probar si Zustand es más simple que React Query para estado global"

JARVIS:
  1. README.md: "Experimento Zustand vs React Query — hipótesis: menos boilerplate"
  2. Plan: scaffold React + Zustand, migrar feature de auth, comparar líneas de código
  3. Implementar en 1 día (React + Python backend mock)
  4. Demo a Tony con comparación de código

Tony: "Me gusta. 30% menos código. Anoten esto para evaluar en producción."

(El experimento se archiva. Si en 3 meses decide adoptar Zustand, el equipo Central lo implementa formalmente con flujo completo.)
```

## Próximas Skills a Crear

1. `nelson-project-constitution` — Fase 1 ✅
2. `nelson-pricing-model` — Fase 5 ✅
3. `nelson-spec-analyzer` — Fase 6
4. `nelson-sdd-templates` — Templates de spec, plan, tasks, estimación

## Ejemplo de Uso

```
Tony: "JARVIS, nuevo proyecto: app de reservas para restaurantes"

JARVIS:
  1. Carga `nelson-spec-driven-workflow`
  2. Fase 1: Genera CONSTITUTION.md con stack, calidad, reglas
  3. Fase 2: Beto escribe OpenAPI spec (user stories, endpoints, data model)
  4. Fase 3: Clarificar con Tony ("¿Qué pasa si cancelan?")
  5. Fase 4: Planear con stack FastAPI + React + PostgreSQL
  6. Fase 5: Estimar costos con `nelson-pricing-model` (dev + infra + suscripción)
  7. Fase 6: Analizar coherencia spec→plan→estimación
  8. Fase 7: Tareas para cada agente
  9. Fase 8: Checklist de calidad
  10. Fase 9: Implementar en paralelo
```

## Notas

- Cada proyecto nuevo crea su propio `CONSTITUTION.md` y `specs/`
- Los templates viven en `~/brainstorming/templates/`
- El flujo completo queda documentado en esta skill
- Equipo I+D+I puede experimentar variaciones, pero el equipo Central sigue este flujo al pie de la letra
