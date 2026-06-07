---
name: nelson-project-tracking
description: Sistema liviano de tracking de proyectos para el equipo Nelson. Estimación (T-shirt size + horas), registro de tiempo, velocity y burndown calculado. Construido sobre nelson-task-memory — sin servicio nuevo. Pensado para Gino (gestión) y Luigi (economía), y también para tracking de los agentes IA del equipo.
version: 1.0.0
author: JARVIS
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [project-tracking, estimation, velocity, burndown, time-tracking, sprint, nelson, gino, luigi]
    category: software-development
    requires_toolsets: [terminal]
---

# nelson-project-tracking

> **Trigger:** Gino o Luigi piden "cuánto nos llevó esto" o "a este ritmo, ¿cuándo terminamos?". También cuando Nelson arranca un sprint nuevo o cierra una PoC y quiere ver velocity del equipo. Antes de medir: leer § 2 (qué medir) y § 3 (cómo se estima).

## Principio rector

> "Lo que no se mide, no se mejora. Pero lo que se mide mal, te hace tomar decisiones peores que no medir nada."

Tres planos, en este orden:
1. **Estimación** — antes de empezar, ¿cuánto creemos que va a llevar?
2. **Ejecución** — durante el trabajo, ¿cuánto nos está llevando realmente?
3. **Visualización** — al final del ciclo, ¿qué nos dicen los números?

Si falta cualquiera de los tres, el dato no sirve.

## 1. Por qué sobre nelson-task-memory y no servicio nuevo

| Opción | Pros | Contras | Cuándo |
|--------|------|---------|--------|
| Extender `nelson-task-memory` (esta skill) | Reutiliza la DB, los endpoints y el `cli` que ya existen. Una sola fuente de verdad. Sin deploy nuevo. | El esquema es genérico, no específico de proyectos. Menos rico que Linear/Jira. | **Cuando tenés 1-10 proyectos activos y querés ver números reales en <1 día.** ← acá estamos |
| Servicio nuevo (`nelson-tracker`) | API propia de Project/Sprint/Task, UI dedicada, intégraciones. | 1-2 sprints de trabajo, deploy, mantenimiento. | Cuando Gino/Luigi pidan features de项目管理 real (capacity planning, dependencias entre tickets, OKRs) |
| Linear / Jira / Notion DB | Madurez, integrations, mobile app, features out-of-the-box. | Costo, dependencia externa, data fuera de nuestro control. | Cuando haya 3+ personas dedicadas a gestión |

**Decisión para 2026:** extender `nelson-task-memory` con 3 tablas (`projects`, `sprints`, `time_entries`) + 2 endpoints + un dashboard HTML simple. Sin deploy nuevo.

## 2. Qué medir (los números que Gino y Luigi necesitan)

### Lo mínimo para empezar (semana 1)

| Métrica | Para qué sirve | Cómo se calcula |
|---------|----------------|-----------------|
| **Estimación por tarea** | Saber qué tarea es grande antes de empezar | T-shirt size o horas estimadas al crear la tarea |
| **Tiempo real por tarea** | Comparar con la estimación | Suma de `time_entries` por task_id |
| **Velocity del sprint** | "¿A este ritmo, cuándo terminamos?" | Story points o horas completadas por sprint |
| **Burndown del sprint** | Visualmente: ¿vamos bien o nos atrasamos? | Gráfico de horas restantes vs ideal line |
| **Ratio estimado/real** | Mejorar futuras estimaciones | Promedio de `(real - estimado) / estimado` por tarea |

### Lo que NO medir (al menos no en v1)

- Cycle time per subtask → requiere workflow state machine, lo agregamos en v2
- Lead time vs cycle time → mismo motivo
- Bugs escapados, NPS del cliente, etc. → eso son métricas de producto, no de项目管理

## 3. Cómo se estima (lo más simple que funcione)

### Opción A: T-shirt size (recomendada para arrancar)

Sin números, sin peleas. 5 valores: `XS`, `S`, `M`, `L`, `XL`.

| Talla | Horas reales esperadas | Ejemplo |
|-------|------------------------|---------|
| `XS` | <2h | Cambiar config, fix chico |
| `S` | 2-4h | Tarea de un día, bien definida |
| `M` | 0.5-1 día | Feature chica con un endpoint |
| `L` | 1-2 días | Feature mediana, toca 2-3 archivos |
| `XL` | >2 días | **Rompéla en subtareas** |

**Regla:** si alguien dice "XL", hay que romper la tarea antes de aceptarla. Si no se puede romper, es un proyecto, no una tarea.

**Para velocity:** asignar puntos fibonacci por talla: `XS=1, S=2, M=3, L=5, XL=8`. La suma del sprint es la velocity planeada. La suma de los completados es la velocity real.

### Opción B: Horas estimadas (cuando ya hay confianza)

Después de 2-3 sprints con T-shirt, los agentes/equipo empiezan a tener intuición. Ahí podés pasar a horas explícitas.

| Rango | Estimación |
|-------|-----------|
| <2h | Tarea individual de un agente |
| 2-8h | Feature bien acotada |
| 1-3 días | Feature que toca varias capas |
| >3 días | Proyecto, no tarea |

**Regla:** estimación pesimista + 30%. Si decís "2 días", en realidad son 2.5. Es mejor sub-estimar a la baja y sorprender que sobre-estimar y fallar.

### Opción C: Planning poker (cuando hay equipo y debate)

Para Gino/Luigi que trabajan con Nelson: cada uno tira su carta (1, 2, 3, 5, 8, 13), se discute el más alto y el más bajo, se re-tira. 15-30 min por sprint planning. **No lo hagas para tareas individuales**, solo en el planning.

### Decisión recomendada para 2026

**T-shirt size para todo.** Después de 2-3 sprints, si los números son estables, migrar a horas estimadas. Planning poker solo para el sprint planning con Gino/Luigi/Nelson.

## 4. El modelo de datos (extensión de nelson-task-memory)

Tres tablas nuevas. Se agregan con una migración Alembic-style en `init_db()` — todo idempotente.

### Tabla `projects`

```sql
CREATE TABLE IF NOT EXISTS projects (
    id              TEXT PRIMARY KEY,        -- UUID
    slug            TEXT UNIQUE NOT NULL,    -- "expreso_bisonte", "forestai"
    name            TEXT NOT NULL,
    description     TEXT,
    owner           TEXT,                    -- "gino", "luigi", "nelson", "jarvis"
    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN ('active', 'paused', 'completed', 'cancelled')),
    start_date      TEXT,                    -- ISO 8601
    target_end_date TEXT,                    -- ISO 8601 (opcional)
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_owner  ON projects(owner);
```

### Tabla `sprints`

```sql
CREATE TABLE IF NOT EXISTS sprints (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,                -- "Sprint 1", "MVP Q3"
    goal        TEXT,
    start_date  TEXT NOT NULL,
    end_date    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'planned'
                CHECK(status IN ('planned', 'active', 'completed', 'cancelled')),
    capacity_hours REAL,                      -- horas totales disponibles del equipo
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sprints_project ON sprints(project_id);
CREATE INDEX IF NOT EXISTS idx_sprints_status  ON sprints(status);
```

### Relación task ↔ sprint ↔ project

```sql
-- Agregar columnas a la tabla tasks existente (idempotente)
ALTER TABLE tasks ADD COLUMN project_id TEXT REFERENCES projects(id) ON DELETE SET NULL;
ALTER TABLE tasks ADD COLUMN sprint_id   TEXT REFERENCES sprints(id)   ON DELETE SET NULL;
ALTER TABLE tasks ADD COLUMN estimate    TEXT CHECK(estimate IN ('XS','S','M','L','XL'));  -- T-shirt size
ALTER TABLE tasks ADD COLUMN estimate_points INTEGER;  -- 1, 2, 3, 5, 8
ALTER TABLE tasks ADD COLUMN estimate_hours   REAL;    -- estimación explícita en horas
ALTER TABLE tasks ADD COLUMN due_date         TEXT;     -- ISO 8601

CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_sprint   ON tasks(sprint_id);
```

### Tabla `time_entries`

```sql
CREATE TABLE IF NOT EXISTS time_entries (
    id          TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user        TEXT NOT NULL,                -- "nelson", "jarvis", "ricky", etc.
    started_at  TEXT NOT NULL,                -- ISO 8601
    ended_at    TEXT NOT NULL,                -- ISO 8601
    hours       REAL NOT NULL,                -- calculado: (ended - started) / 3600
    description TEXT,                         -- qué se hizo en este tramo
    billable    INTEGER DEFAULT 1,            -- 0/1, default facturable
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_time_entries_task    ON time_entries(task_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_user    ON time_entries(user);
CREATE INDEX IF NOT EXISTS idx_time_entries_started ON time_entries(started_at);
```

## 5. API nueva (extender `nelson-task-memory`)

### Endpoints de projects

```
POST   /projects/                  crear
GET    /projects/                  listar (filtros: status, owner)
GET    /projects/{id}              detalle
PATCH  /projects/{id}              actualizar
DELETE /projects/{id}              borrar (cascade a sprints, NO a tasks)
```

### Endpoints de sprints

```
POST   /projects/{project_id}/sprints                  crear
GET    /projects/{project_id}/sprints                  listar
GET    /sprints/{id}                                   detalle
PATCH  /sprints/{id}                                   actualizar
POST   /sprints/{id}/close                             cerrar sprint, snapshot de métricas
```

### Endpoints de estimación (sobre tasks existentes)

```
PATCH  /tasks/{id}/estimate                            body: {estimate: "M", points: 3, hours: 6}
```

### Endpoints de time tracking

```
POST   /tasks/{id}/time/start                          body: {description: "..."}
POST   /tasks/{id}/time/stop                           cierra el entry activo
POST   /tasks/{id}/time/log                            body: {started_at, ended_at, description}  (registro manual)
GET    /tasks/{id}/time                                lista de entries de la tarea
GET    /reports/time?user=&project=&from=&to=         reporte filtrable
GET    /reports/burndown?sprint_id=                    datos para el gráfico
GET    /reports/velocity?project_id=&last_n=          velocity de últimos N sprints
```

### Ejemplo: cierre de sprint devuelve snapshot

```json
{
  "sprint": {"id": "...", "name": "Sprint 3", "start_date": "...", "end_date": "..."},
  "metrics": {
    "planned_points": 21,
    "completed_points": 18,
    "planned_hours": 56,
    "actual_hours": 64.5,
    "tasks_planned": 8,
    "tasks_completed": 6,
    "tasks_carried_over": 2,
    "velocity_points": 18,
    "velocity_hours_per_point": 3.58,
    "estimation_accuracy": 0.87
  },
  "by_task": [
    {"id": "...", "goal": "...", "estimate": "M", "points": 3, "estimated_h": 6, "actual_h": 7.5, "status": "done"},
    ...
  ]
}
```

## 6. CLI para Gino y Luigi (extender el `tasks` CLI)

```bash
# === PROYECTOS ===
projects new "Expreso Bisonte" --slug expreso_bisonte --owner gino
projects list
projects list --owner gino
projects show expreso_bisonte
projects pause expreso_bisonte

# === SPRINTS ===
sprints new expreso_bisonte --name "Sprint 1 MVP" --weeks 2 --capacity 80
sprints list expreso_bisonte
sprints start <sprint_id>
sprints close <sprint_id>   # calcula métricas finales

# === ESTIMACIÓN ===
tasks estimate <task_id> --size M --points 3 --hours 6
tasks assign <task_id> --sprint <sprint_id> --project expreso_bisonte

# === TIME TRACKING ===
tasks start <task_id>                 # crea time entry activo
tasks start <task_id> --desc "implementando endpoint"
tasks stop                            # cierra el entry activo del usuario actual
tasks log <task_id> --hours 2 --desc "review de código" --at 2026-06-07T15:00
tasks log <task_id> --from "2026-06-07T09:00" --to "2026-06-07T12:30" --desc "implementación"

# === REPORTES ===
reports time --user nelson --last 30
reports time --project expreso_bisonte --last 7
reports burndown <sprint_id>          # ASCII en consola o HTML
reports velocity expreso_bisonte --last 6
reports accuracy                      # ratio estimado/real por usuario
```

## 7. El dashboard mínimo (HTML estático)

Sin React, sin Vite, sin nada que mantener. Un solo HTML que pega a la API.

`/home/server/nelson/task-memory/dashboard/index.html` (servido por el mismo FastAPI).

Paneles:

1. **Active projects** (cards): nombre, owner, días restantes, % avance
2. **Burndown del sprint activo**: línea de horas restantes + línea ideal
3. **Velocity trend**: bar chart de últimos 6 sprints
4. **Top 5 tareas con mayor overrún**: estimada vs real
5. **Tabla de tareas activas**: estimate, logged hours, % spent, days remaining

Para los gráficos: Chart.js vía CDN, sin build, sin node_modules. Si Gino/Luigi piden más, ahí sí React.

## 8. Flujo de trabajo de un sprint (paso a paso)

### Sprint Planning (1h, con Gino/Luigi/Nelson)

1. Revisar tareas del backlog (sin sprint asignado).
2. Para cada tarea, estimar T-shirt size en grupo.
3. Sumar puntos. Si supera la `capacity_points` (típicamente 2x la velocity del sprint anterior), recortar.
4. Asignar tareas al sprint con `tasks assign <task_id> --sprint <sprint_id>`.
5. Documentar el goal del sprint en `sprints new`.

### Daily / durante el sprint

1. Cada agente/ persona registra tiempo con `tasks start` / `tasks stop` (o `tasks log` retroactivo).
2. Si una tarea resulta más grande que su estimate, **avisar al grupo** y re-estimar.
3. El burndown se actualiza solo (la API lo calcula en `/reports/burndown`).

### Cierre de sprint (30 min, con Gino/Luigi/Nelson)

1. `sprints close <sprint_id>` — genera snapshot automático.
2. Revisar 3 números:
   - **Velocity** (completado vs planeado) → ¿coincide con la histórica?
   - **Accuracy** (real vs estimado) → ¿mejoramos o empeoramos?
   - **Carry-over** (tareas que no entraron) → ¿hay un patrón?
3. Anotar 1-2 cosas que aprendimos en el goal del próximo sprint.
4. Opcional: usar el template `retrospectiva-sprint.md` para capturar acuerdos.

## 9. Plantillas

(Ver carpeta `templates/`)

- `estimacion-t-shirt.md` — guía rápida de T-shirt size con ejemplos del equipo Nelson
- `sprint-board.md` — board imprimible para usar en planning si Gino/Luigi no miran la API
- `retrospectiva-sprint.md` — template de retro con las 4Ls (Liked, Learned, Lacked, Longed for)
- `reporte-cliente-mensual.md` — formato que Luigi puede mandar a clientes
- `scripts/onboard_sprint.py` — crea project + sprint + asigna tareas en un solo comando
- `scripts/close_sprint.py` — cierra sprint + genera snapshot + imprime resumen

## 10. Migración desde "no medir"

La mayoría de los proyectos del equipo Nelson hoy **no tienen tracking de tiempo**. La transición no es traumática:

1. **Semana 0:** crear el `project` para cada cliente activo. No asignar tareas todavía.
2. **Semana 1:** en el próximo sprint, empezar a estimar con T-shirt size. **No trackear tiempo todavía**, solo estimación.
3. **Semana 2:** trackear tiempo con `tasks start` / `tasks stop` solo en el proyecto piloto (ej: ForestAI).
4. **Semana 3:** al cerrar el primer sprint con medición, mirar el burndown. **No concluir nada todavía** — son pocos datos.
5. **Semana 4-5:** segundo sprint con medición. Comparar con el primero. Ahí sí se puede hablar de velocity.
6. **Mes 2 en adelante:** la velocity de 2-3 sprints se estabiliza, se puede planear con más confianza.

**Anti-patrón:** empezar trackeando tiempo en 5 proyectos a la vez. La fricción de `tasks start` mata la adopción. Empezar con 1 proyecto, demostrar valor, expandir.

## 11. Anti-patrones y pitfalls

1. **Medir para castigar.** "Ves, llevás 4 horas y la estimación era 2h." → la gente infla estimaciones o esconde trabajo. La medición es para mejorar el sistema, no para juzgar personas.
2. **Olvidar el "done"** en `tasks done`. Una tarea que nunca se marca como done se queda abierta para siempre y distorsiona todas las métricas. Regla: si el trabajo terminó, marcá done aunque la estimación haya quedado corta.
3. **Sumar horas sin contexto.** Que el agente IA haya tardado 3 horas no significa que el humano tardaría 3 horas. Si vas a comparar humano vs IA, marcalo explícitamente.
4. **Velocity como KPI individual.** La velocity es del equipo/sprint, no de una persona. Mostrarla por persona genera incentivos equivocados.
5. **Correr detrás del burndown.** Si vas atrasado a mitad de sprint, recortar YA, no esperar al cierre. El burndown no es para enterarse al final.
6. **Horas reales ≠ horas productivas.** Reuniones, contexto, espera de review. Si medís solo tiempo en la tarea, subestimás el costo total del proyecto. Para Luigi es importante trackear también tiempo de overhead.
7. **Sprints eternos.** Si un sprint dura más de 4 semanas, ya no es un sprint. Acortá o partí en milestones internos.
8. **Sprints semanales con equipo chico.** Si el equipo son 2-3 personas, sprint semanal es muy ruidoso (1 día malo te descuadra todo). Sprint de 2 semanas es el sweet spot para equipo chico.
9. **"Vamos a trackingear desde ahora" sin definir qué es una tarea.** La gente anota cosas distintas: un issue, una reunión, un día entero. Definir antes qué cuenta como task y qué no.
10. **Re-estimar a la baja cuando estás atrasado.** "Bueno, en realidad eran 2 horas" — no. La estimación original es la que vale para aprender. Si la cambias retroactivamente, el sistema nunca mejora.
11. **No distinguir tiempo del agente vs humano.** Un agente IA puede tener `tasks start` y `tasks stop`, pero su "hora" no es igual a la hora de Gino. Para reportes de costos Luigi, mantener el flag.
12. **Confundir capacidad con disponibilidad.** "Tengo 40 horas esta semana" no es 40 horas de capacidad real. Descontar reuniones, support, overhead. Regla: capacidad real = horas disponibles × 0.6.

## 12. Cómo se ve un reporte de burndown (ejemplo real)

```
Sprint: ForestAI MVP v1 (2026-06-02 → 2026-06-15)
Capacity: 80h (Nelson 30h + Gino 25h + Ricky 25h)
Planned: 56h (18 puntos)

Día          Ideal    Real    Restante
─────────────────────────────────────
1 (06-02)    52.0     50.5    55.5
2 (06-03)    48.0     49.0    54.0
3 (06-04)    44.0     47.0    52.0
4 (06-05)    40.0     42.0    48.0
5 (06-06)    36.0     38.0    44.0
6 (06-07)    32.0     35.0    41.0   ← estás acá
7 (06-08)    28.0     ??      ??
8 (06-09)    24.0
9 (06-10)    20.0
10 (06-11)   16.0
11 (06-12)   12.0
12 (06-13)   8.0
13 (06-14)   4.0
14 (06-15)   0.0

Estado: atrasado 3h sobre la línea ideal. Decisión a mitad de sprint.
```

## 13. Definiciones y vocabulario compartido

| Término | Definición operativa para el equipo Nelson |
|---------|---------------------------------------------|
| **Tarea** | Unidad de trabajo asignable a 1 agente/persona, completable en <2 días |
| **Subtarea** | Hija de una tarea, scope más chico |
| **Sprint** | Período de 2 semanas con capacidad fija y goal definido |
| **Capacidad** | Horas reales disponibles (disponibilidad × 0.6) |
| **Velocity** | Puntos fibonacci completados al cierre del sprint |
| **Burndown** | Gráfico de trabajo restante vs tiempo |
| **Accuracy** | Promedio de `min(estimado, real) / max(estimado, real)`. 1.0 = perfecto |
| **Carry-over** | Tarea planeada para el sprint que pasó al siguiente |
| **Overhead** | Tiempo que no es tarea directa: reuniones, support, espera |
| **T-shirt size** | XS / S / M / L / XL como estimación cualitativa |
| **Story point** | Número fibonacci (1,2,3,5,8,13) que representa tamaño relativo |
| **Owner** | Persona responsable última del proyecto (Gino, Luigi, Nelson) |
| **Assigned** | Persona/agente que ejecuta la tarea en este momento |

## Referencias

- `nelson-task-memory` — DB, API y CLI base que esta skill extiende
- `nelson-meta-orchestrator` — los agentes IA también trackean su tiempo por task
- `nelson-financial-dashboard` — skill hermana, la construimos después con los datos de tiempo
- `nelson-retrospective` — skill hermana, usa los snapshots de sprint
- `templates/` — T-shirt size, board imprimible, retro template, scripts
