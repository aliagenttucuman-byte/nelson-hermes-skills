---
name: nelson-skill-authoring
description: Workflow para crear skills nelson-* nuevas en ~/.hermes/skills/ cuando hay un gap operativo (skill faltante, decisión recurrente, o trabajo terminado que merece ser capturable). Una skill por sesión, terminada y archivada, antes de abrir la siguiente. Plantilla estándar probada con 4 skills reales (incident-response, multi-tenancy, project-tracking, backup-dr) creadas el 2026-06-07 en una sola sesión de 4 turnos.
version: 1.0.0
author: JARVIS
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [skills, authoring, nelson, workflow, brainstorming, roadmap, process]
    category: software-development
    related_skills: [nelson-brainstorming, nelson-meta-orchestrator, nelson-task-memory, hermes-agent-skill-authoring, writing-plans]
---

# nelson-skill-authoring

> **Trigger:** Nelson pide arrancar/crear/diseñar una skill nueva para el equipo, o el sistema detecta un gap recurrente sin skill que lo cubra. NO usar para in-repo skills de hermes-agent (eso es `hermes-agent-skill-authoring`).

## Principio rector

> "Comer de a poco. No arrancar todo junto. Una skill por sesión, terminada y archivada, antes de abrir la siguiente."

El backlog vive en `~/brainstorming/YYYY-MM-DD-skills-faltantes-roadmap-v2/README.md` (ver `references/roadmap-convention.md`). Antes de crear una skill, chequear ese roadmap. Si no existe, recrearlo desde la memoria de sesiones (vino perdiéndose 2+ semanas en mayo 2026).

## El workflow probado (5 pasos)

### Paso 1 — Confirmar el gap

Pregunta filtro antes de empezar: **¿Esta skill se va a usar más de una vez?**

- Si la respuesta es "una vez" o "no estoy seguro" → no es skill, es un doc. Archivá en brainstorming y seguí.
- Si la respuesta es "sí, varias" → seguí.

Anunciá el plan en 1 mensaje: "Arranco con [nombre]. Chequeo contexto existente, después la armo." Nelson respondió con "Dale" las 3 veces; ese es el ritmo.

### Paso 2 — Investigar antes de escribir (regla del 3-minuto)

Antes de tocar el teclado, en paralelo:

1. **Skills existentes relevantes**: `search_files` en `~/.hermes/skills/` con palabras clave del dominio. Si hay peer, **extender en vez de crear** (ver § Cuándo NO crear).
2. **Roadmap / backlog**: leer el README de `~/brainstorming/.../skills-faltantes-roadmap-v2/` para ver si ya está marcada 🟡.
3. **Sesiones históricas relevantes**: `session_search` con 2-3 keywords del dominio para no repetir investigación ya hecha. Las sesiones de cron semanal (formato `cron_*`) suelen tener el contexto reconstruido.

Esto evita: duplicar trabajo, pisar convenciones del equipo, olvidar el stack real (ej: si la skill asume Postgres 14 y el server corre 16).

### Paso 3 — Diseñar la estructura (5 preguntas de diseño)

Antes de escribir SKILL.md, responder:

1. **¿Quién la va a cargar?** (Diego/Ops, Gino/Luigi/Gestión, Nelson/Técnico, un agente IA). El dueño cambia el tono y el nivel de detalle.
2. **¿Cuándo se carga?** (en medio de un incidente, en sprint planning, on-demand para crear tenant). El trigger va en la primera línea del frontmatter.
3. **¿Tiene capas?** (DB + API + CLI + UI). Si tiene 2+ capas, probablemente tiene templates separados, no un solo SKILL.md monolítico.
4. **¿Es defensiva o productiva?** Defensiva = commandos, runbooks, checklists (incident-response). Productiva = decisiones de arquitectura, patrones, scripts (multi-tenancy). El tono es distinto.
5. **¿Hay decisión de arquitectura bloqueante?** Si la skill implica elegir entre opciones (schema separado vs row-level, planilla vs servicio, etc.), esa decisión va en § 3 de SKILL.md, no escondida en el medio. Nelson valida mejor cuando la decisión está al frente.

### Paso 4 — Estructura estándar probada (la plantilla)

Las 3 skills creadas el 2026-06-07 (incident-response, multi-tenancy, project-tracking) salieron de esta misma plantilla. Funciona porque:

- **Frontmatter estricto** con `metadata.hermes.tags` y `related_skills` para que el loader las relacione entre sí
- **Trigger en bloque quote al inicio** — el agente o Nelson sabe en 5 segundos si esta skill es para su caso
- **Principio rector** (1 línea) — lo que la skill considera innegociable
- **§ § claras por capa o por fase** — no por tema genérico
- **Templates separados** del SKILL.md principal para no inflar el archivo
- **Pitfalls al final** numerados, con mitigación concreta, no "tener cuidado"

Tamaños que probaron funcionar:
- SKILL.md: 12-30 KB (incident-response 12.5, multi-tenancy 27, project-tracking 20)
- Templates: 1-5 archivos, total <20 KB
- Ejemplos: 1-2 archivos, 4-8 KB (solo si la skill es abstracta y necesita mostrar producto terminado, ej: project-tracking)

### Paso 5 — Archivar y propagar

Al terminar la skill, en este orden estricto:

1. **Actualizar el SKILL.md si hace falta** (un pitfall aprendido durante el armado, un comando que no anduvo)
2. **Crear carpeta de brainstorming** `~/brainstorming/YYYY-MM-DD-nombre-skill/` con README.md de 50-100 líneas que documente: qué se hizo, decisiones tomadas, qué NO se hizo, próximos pasos
3. **Actualizar el ROADMAP** centralizado: marcar la skill como 🟢 Hecha en la tabla, agregar línea al histórico
4. **Anunciar cierre con recap conciso** (no más de 12-15 líneas, ver § Ritmo de entrega)

Si el ROADMAP no existe o está perdido, recrearlo (ya pasó en mayo 2026). Es trabajo de 1 minuto que paga siempre.

## Cuándo NO crear una skill nueva

- **Ya hay una skill que cubre la clase** → extender esa. Ej: si la nueva skill fuera "incident-response-sev1" sin ser distinta en estructura, no crear.
- **Es un comando suelto** → guardar en `references/` de la skill que gobierna esa clase de tarea.
- **Es un doc de un solo uso** → archivo en brainstorming, no skill.
- **Es work-in-progress** → crear la skill al cerrar, no al empezar. Espera al producto terminado.

## El ritmo de entrega (lo que Nelson espera)

Probado en 3 sesiones consecutivas el 2026-06-07. Cada skill se entregó con este patrón:

```
1. Mensaje corto de plan: 1-2 líneas
   "Arranco con [skill]. Chequeo contexto existente, después la armo."

2. Trabajo (investigación + creación):
   - skill_view de skills vecinas
   - search_files / session_search
   - write_file de SKILL.md + templates
   - patch del ROADMAP
   - write_file del README de brainstorming

3. Recap conciso de cierre (12-15 líneas WhatsApp-friendly):
   - Qué se creó (lista corta)
   - Decisión clave (si hay)
   - Roadmap actualizado (1 línea)
   - Próxima candidata (1 línea con pregunta)
```

**Lo que NO hacer:**
- ❌ **Pedir confirmación con `clarify` cuando la decisión se puede tomar con defaults sensatos.** `clarify` no está disponible en el entorno de WhatsApp (confirmado el 2026-06-07 al intentar usarlo en multi-tenancy: la herramienta devolvió "Clarify tool is not available in this execution context"). **Solución: tomar la decisión por defecto, documentarla explícitamente, y permitir que el usuario la revierta.** Ej: para multi-tenancy, en vez de clarificar, recomendé row-level + RLS como default y lo dejé al frente de la skill para que Tony pudiera rechazar.
- ❌ Tablas truncadas, contenido cortado, listas demasiado largas
- ❌ Volver a explicar el contexto que ya está en la sesión
- ❌ Empezar la siguiente skill sin chequear el ROADMAP
- ❌ Crear la skill en formato "one-session-one-skill" con el nombre del día → es exactamente el anti-patrón que la consigna de curator skills combate

## Patrones confirmados (4 skills creadas el 2026-06-07)

Lección transversal, no documentada en la v1: además de las 5 preguntas de diseño, hay decisiones que se repiten en cada skill nueva y vale la pena chequearlas antes de empezar.

### Patrón A — ¿Hay skill adyacente para extender, no crear?

Antes de crear `nelson-X`, preguntarse: ¿hay una skill vecina cuya extensión cubriría este gap con menos fricción? Ejemplos confirmados:

- `nelson-project-tracking` se pensó como servicio nuevo (Full). Se terminó haciendo "Medio: extender `nelson-task-memory` con 3 tablas". Razón: skill adyacente ya tiene DB, API, CLI, y un dashboard en camino. Construir encima = 1 día de Ricky, no 1-2 sprints.
- `nelson-multi-tenancy` no se extendió a una skill existente porque no había ninguna que tocara el tema. Se creó nueva.
- `nelson-backup-dr` se vinculó a `nelson-incident-response` (la skill de runbooks referencia backup-dr explícitamente). No se extendió incident-response porque es un dominio distinto.

**Regla:** si la skill nueva agrega un dominio **distinto** a una existente, crear nueva. Si agrega **funcionalidad del mismo dominio**, extender la existente.

### Patrón B — Estructura de carpetas según el dominio

| Skill | SKILL.md | templates/ | scripts/ | playbooks/ | runbooks/ | examples/ |
|-------|----------|-----------|----------|-----------|-----------|-----------|
| incident-response | ✅ | ✅ 4 (postmortem + 3 mensajes) | — | ✅ 1 (forestai) | — | — |
| multi-tenancy | ✅ | ✅ 3 (ADR + 2 .py) | — | — | — | — |
| project-tracking | ✅ | ✅ 5 (board + retro + reporte + T-shirt + script) | — | — | — | ✅ 1 (burndown) |
| backup-dr | ✅ | — | ✅ 8 (todos los .sh ejecutables) | — | ✅ (vacio, creado para crecer) | — |

**Lección:** la estructura nace del **tipo de output** de la skill, no de un template fijo:
- Defensiva con runbooks → `playbooks/` o `runbooks/`
- Productiva con scripts ejecutables → `scripts/` (no docs)
- Productiva con código boilerplate → `templates/*.py`
- Abstracta que necesita mostrar producto terminado → `examples/`

### Patrón C — Sync a GitHub end-to-end con `gh` CLI (workflow completo)

El `sync-to-repo.sh` del repo `nelson-hermes-skills` corre automáticamente (cron) y deja commits sin pushear localmente. El 2026-06-07 había 2 commits pendientes del 6 y 30 de mayo. Cuando intenté pushear mis 4 skills, GitHub push protection detectó un **LinkedIn Client Secret** en uno de esos commits viejos.

**El problema:** el push a `main` se rechazó por `GH013`. El secret no es tuyo, pero el commit queda en la cadena. El `gh` CLI es la herramienta correcta para resolverlo end-to-end sin pedirle a Tony que abra la UI.

**La solución probada (paso a paso, 8 pasos, ~10 min):**

```bash
# 1. Sincronizar skills locales al repo
bash ./sync-new-skills.sh   # o sync-to-repo.sh actualizado

# 2. Verificar divergencias con remoto
cd /home/server/repos/nelson-hermes-skills
git status
git log --oneline origin/main..HEAD

# 3. Intentar push directo a main — si FALLA con GH013, hay secrets
git push 2>&1 | tail -10
# Si ves: "remote rejected] main -> main (push declined due to repository rule violations)"
#       "GITHUB PUSH PROTECTION - Push cannot contain secrets"
# → el push a main está bloqueado, ir a branch

# 4. Crear branch limpio desde origin/main
git fetch origin
git checkout -b feat/<nombre-descriptivo>-<YYYY-MM-DD>
git reset --hard origin/main

# 5. Cherry-pick solo el commit propio encima
git cherry-pick <SHA-de-tu-commit>
# Si hay conflict en memories/ (archivos ignorados por .gitignore):
git checkout --theirs memories/MEMORY.md memories/USER.md
git add memories/MEMORY.md memories/USER.md
git cherry-pick --continue --no-edit

# 6. Push del branch (no de main)
git push -u origin feat/<nombre-descriptivo>-<YYYY-MM-DD>

# 7. Crear PR + merge + cleanup con gh CLI
gh pr create --base main --head feat/<nombre-descriptivo>-<YYYY-MM-DD> \
  --title "feat: <título corto>" \
  --body "..."  # resumen + decisiones + stats

gh pr merge <PR-number> --squash --delete-branch
# --squash: 1 commit por feature en main (limpio para próximos backups)
# --delete-branch: borra el branch remoto al mergear

# 8. Sincronizar local y limpiar referencias
git fetch origin
git checkout main
git reset --hard origin/main
git remote prune origin   # limpia refs a branches remotos borrados
```

**Variación end-to-end (cuando Tony dice "Hace vos todo"):** correr los pasos 7-8 con `gh` en vez de pedirle que abra el PR desde la UI. El merge queda atribuido a la cuenta `aliagenttucuman-byte` (Tony), no a JARVIS, porque `gh` usa los credenciales del usuario. Funciona porque el `gh` CLI está autenticado en el server con la cuenta de Tony (`gh auth status` lo confirma).

**Lección para la skill:** si vas a sincronizar skills a un repo con sync automático + push protection, **siempre branch primero**, nunca push directo a main. El branch es seguro aunque haya secrets viejos en main local. Y si Tony aprueba el workflow end-to-end, `gh` CLI te deja hacer PR + merge + cleanup en un solo turno.

### Patrón C-bis — Cleanup de secrets pre-existentes en main local

Cuando `git reset --hard origin/main` saca de la historia local los commits con secrets, **los archivos problemáticos pueden no existir en el remoto** (si los commits viejos nunca llegaron a origin). Verificar antes de hacer `git filter-branch`:

```bash
# Verificar si los archivos con secret están en origin
git ls-tree -r origin/main | grep -i <patron-archivo>

# Si NO hay matches → los archivos están solo en commits locales descartados
# El reset los borró de la historia. No hace falta filter-branch.

# Si SÍ hay matches → los archivos están en el remoto también
# Hay que editar + commit + push con --force, o esperar al cron de limpieza
```

**Caso del 2026-06-07:** los 2 archivos de LinkedIn con el secret (`nelson-automation-n8n/references/linkedin-api-oauth2.md` y `nelson-scheduled-jobs/references/linkedin-oauth2-pitfalls.md`) estaban en commits locales del 30 mayo y 6 junio que nunca llegaron a `origin/main`. Después del `git reset --hard origin/main`, los archivos desaparecieron del working tree y la historia. Verificado con `git grep`: cero ocurrencias del secret en el repo actual.

**Lección:** antes de hacer `git filter-repo` o force-push destructivo, verificá que el secret realmente esté en origin. Si está solo en local y se descarta, no hay nada que limpiar.

### Patrón D — Convención de ubicación de skills (inconsistencia activa, 2026-06-07)

**Estado actual (inconsistencia):** las skills del equipo Nelson viven en **dos lugares** distintos en `~/.hermes/skills/`:

- `~/.hermes/skills/nelson-X/` (raíz) — donde quedaron las 4 skills creadas el 2026-06-07 (incident-response, multi-tenancy, project-tracking, backup-dr)
- `~/.hermes/skills/software-development/nelson-X/` (subcarpeta) — donde están las demás (skill-authoring, task-memory, etc.) y la peer `nelson-skill-authoring` que está editando ahora

**El problema:** el `sync-to-repo.sh` del repo busca en `software-development/` por default. Si la skill nueva se crea en raíz, hay que agregarla al array del script manualmente o no la sincroniza.

**Regla temporal (mientras se decide la convención definitiva):**

1. **Crear siempre en `~/.hermes/skills/software-development/nelson-X/`** para que el sync-to-repo.sh la tome sin tocar el array. El costo: 1 nivel más de profundidad.
2. **Si la skill es claramente de devops** (ej: backup-dr, incident-response, server-services), se puede crear en raíz. Justificación: el sync-to-repo.sh ya acepta esas (server-services está en raíz). Pero requiere patch manual del array.
3. **Patch obligatorio del array al cierre** (ver "Errores recurrentes" #8).

**Decisión definitiva pendiente (housekeeping):** elegir una convención y migrar las que están en el lugar incorrecto. No resuelto al 2026-06-07. No bloqueante: las 4 skills nuevas ya están en main del repo.

### Patrón F — Preferencia del usuario: "Hace vos todo" cuando ya dio el OK (confirmado 2026-06-07)

Después de armar las 4 skills y de proponer "Opción A: mergeás el PR desde la UI", Tony respondió **"Hace vos todo"**. Eso significa:

- Si ya hay aprobación implícita (ej: "dale sync al repo"), no volver a pedirle que abra URLs o clickee botones.
- Usar el `gh` CLI autenticado en el server (con la cuenta de Tony) para PR + merge + cleanup.
- Reportar al final con el link al PR mergeado y el estado del repo (no esperar confirmación de que lo mergeó).

**Implicación para el workflow:** el Patrón C original (manual, "esperando merge de Tony") es el fallback. **El Patrón C actualizado (con `gh` CLI) es el preferred path** cuando el usuario ya dijo "dale". La señal es: si Tony respondió "Dale" / "Avancemos" / "Hace vos todo" / "Sí" en el último turno, hacer el merge end-to-end.

**Excepción:** si el merge tiene consecuencias no obvias (force-push, rewrite de historia, delete de branches remotos de terceros), pedir confirmación una vez antes. `gh pr merge --squash --delete-branch` es seguro y reversible (el commit sigue en el historial de GitHub aunque el branch se borre), pero cosas como `--force-with-lease` o `git filter-branch` necesitan OK explícito.

### Patrón G — "Pasada que no actualiza nada" es oportunidad perdida (regla de review)

Confirmado el 2026-06-07 en un turno de review explícito ("review the conversation and update memory/skills"). **Cada sesión debe producir al menos un update** (skill patch, memoria nueva, o document de brainstorming). "Nothing to save" no es el default, es la excepción cuando genuinamente no hay señal.

**Cómo aplicar este patrón cuando Tony pide "review the conversation":**

1. **Memoria primero** — ¿hay preferencias durables, hechos del entorno, o contexto del usuario que no estén ya en MEMORY/USER? Si sí, patch (con `replace` si excede el límite, no `add`).
2. **Skills consultadas/creadas en la sesión** — ¿alguna tiene una lección nueva? Patch con `skill_manage action='patch'`.
3. **Output reusable de la sesión** (ej: documento de valuación) — si se repite la clase de tarea, crear skill umbrella o `references/<topic>.md` en una skill existente.
4. **Gaps reconocidos** — si la skill consultada no tenía la info que necesitaste, agregarla ahora. Patch.
5. **Pitfalls transversales** — si algo se rompió (herramienta faltante, decisión revertida), el fix va en la skill que gobierna esa tarea, no en memoria.

**Anti-patrones del review:**
- ❌ Decir "Nothing to save" sin haber revisado memoria + skills + output de la sesión
- ❌ Agregar entradas redundantes a memoria cuando la info ya está en una skill
- ❌ Crear skill nueva one-off cuando hay peer que se puede extender
- ❌ Hardcodear la lección en el SKILL.md si pertenece a `references/` (knowledge bank denso)

**Lección del 2026-06-07:** la sesión produjo 4 skills nuevas + 1 documento de valuación (17KB) + 1 sync a repo. En el review explícito posterior, la pregunta correcta no fue "qué guardo en memoria" sino **"qué skill me faltó en algún momento de las 4 sesiones anteriores y ahora sé que la necesito"**. La respuesta: una vista consolidada "equipo + portfolio" de valuación, que se agregó como output documentado en `nelson-startup-benchmarking` (ver § VALUACION-CONSOLIDADA en esa skill).

### Patrón E — El ROADMAP se pierde. Recrearlo SIEMPRE.

En mayo 2026 el `ROADMAP_SKILLS.md` original se perdió. Durante 3 semanas (17, 24, 31 mayo) el cron semanal intentó leerlo y no pudo. El 7 de junio se recreó como `2026-06-07-skills-faltantes-roadmap-v2/README.md` y desde entonces ha funcionado.

**Lección:** el ROADMAP centralizado es un punto único de falla. Si se pierde, **recrearlo en el momento** que se detecta (no esperar a "tener tiempo"). El template vive implícito en el formato de la v2 — secciones: Principio rector, Estados, Backlog por área, TOP 3 críticas, Reglas de uso, Histórico, Sesiones de referencia.

## Pitfall nuevo (junio 2026): sync a GitHub con push protection

Ver Patrón C arriba para la solución. Resumen en una línea: **branch + cherry-pick del commit propio + push del branch**, nunca push directo a main cuando hay secrets viejos en la cadena local.

## Frontmatter estándar (la receta)

```yaml
---
name: nelson-<area>-<acción>     # lowercase, hyphens, ≤64 chars
description: <1-2 líneas con trigger class, no la tarea de hoy>
version: 1.0.0
author: JARVIS
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [<3-6 tags, primero el dominio, después la acción>]
    category: software-development        # o devops, data-science, etc.
    related_skills: [<skills que se cargan junto, no todas las del equipo>]
---
```

`description`写法 clave: empieza con el **trigger class**, no con la tarea de hoy. Ej bueno: *"Patrones de aislamiento multi-tenant para el stack del equipo Nelson (FastAPI + SQLAlchemy + PostgreSQL + Qdrant + Redis). Tres estrategias comparadas..."*. Ej malo: *"Skill creada el 2026-06-07 para..."*.

## Errores recurrentes (los 9 que ya cometí)

1. **Investigar poco → skill genérica.** "Cómo hacer X" sin saber el stack real del equipo. Siempre `search_files` + `session_search` primero.
2. **SKILL.md >40 KB → inflar con cosas que son templates.** Mover a `templates/`, dejar solo el cómo-y-porqué en SKILL.md.
3. **No archivar en brainstorming** → sesión perdida. Después de 2 semanas nadie recuerda por qué se creó la skill. El README de brainstorming es el "ticket" de la decisión.
4. **Olvidar el ROADMAP** → el backlog queda desactualizado y el próximo cron semanal no sabe qué fue. Patch siempre al cierre.
5. **Pitfalls como advertencias genéricas** ("tener cuidado con X"). Los buenos pitfalls son **específicos y accionables**: "Si usás `pip` directo en el server, no anda → usar `python3 -m pip`". Diferencia: 1 minuto vs 30 minutos para el próximo.
6. **No marcar en el ROADMAP lo que NO se hizo.** Si la skill documenta algo que queda como trabajo futuro, decirlo explícito en el brainstorming README. La promesa implícita "se hizo" se cobra sola más tarde.
7. **Crear la skill al inicio del trabajo, no al cierre.** La tentación es crear el SKILL.md apenas se empieza a investigar. Mal: el agente en otra sesión carga una skill a medio hacer. Bien: la skill nace cuando el producto está cerrado y validado.
8. **Olvidar el sync-to-repo.sh al cerrar.** El script del repo `nelson-hermes-skills` tiene un array hardcodeado de skills. Si la nueva no se agrega, las próximas sync automáticas no la llevan al repo. **Patch obligatorio del array al cierre** (ver Patrón D).
9. **Intentar usar `clarify` para decisiones de diseño.** Confirmado el 2026-06-07: la herramienta no está disponible en el entorno de WhatsApp. Cuando hay que elegir entre opciones (ej: row-level vs schema separado), **tomar la decisión por defecto con justificación explícita al frente del SKILL.md**, no pedir aclaración. Patrón opuesto: preguntar algo que el contexto ya respondió es ruido.
10. **Usar `skill_manage(action='create', category='software-development')` y olvidarse del .gitignore.** Confirmado el 2026-06-27: el flag `category=X` mete la skill en `~/.hermes/skills/X/nelson-foo/`, pero TODAS las categorías públicas (`software-development/`, `creative/`, `research/`, `devops/`, etc.) están en `.gitignore` del repo `nelson-hermes-skills` — son workspace temporal del curator, no se commitean. **La skill queda en disco pero NO va al repo aunque hagas git add.** Fix: después del create, `mv ~/.hermes/skills/software-development/nelson-foo ~/.hermes/skills/nelson-foo` para llevarla a la raíz, que SÍ se trackea. Verificar con `git check-ignore -v` si dudás. Alternativa: omitir el `category` en el create — la skill nace directamente en la raíz.

## Cómo se ve un cierre de sesión exitoso (template de recap para WhatsApp)

```
[NOMBRE-SKILL] creada en ~/.hermes/skills/<path>/ (X KB, N archivos)
- SKILL.md — [qué cubre, 1 línea]
- templates/<archivo> — [qué es]
- examples/<archivo> — [si aplica, qué muestra]

[Si hay decisión de diseño clave]
Decisión: [1 línea con la elección y por qué]

Roadmap actualizado: [skill-1, skill-2, skill-3] → 🟢 Hechas.
Siguiente candidata: [nombre] (1 línea de por qué).

¿Seguimos con [próxima]?
```

Mantenerlo abajo de 15 líneas. WhatsApp corta mensajes largos visualmente.

## Sidecar de brainstorming: High-Value Observations

Cuando en una evaluación de librería/herramienta aparece una observación filtrada — una pieza concreta de un proyecto archivado que vale la pena mirar más adelante — el lugar correcto es el sidecar `~/brainstorming/HIGH-VALUE-OBSERVATIONS.md`, NO una skill nueva. El schema de entradas, los patrones de ejemplo y el ciclo de vida (NO borrar, mover a Completadas, migrar a proyecto real) están en `references/high-value-observations-convention.md`.

Regla operativa: si lo que detectás cabe en una entrada de sidecar con schema de 8 campos, va al sidecar. Si requiere un workflow multi-paso, una skill recurrente, o un set de templates, va a skill nueva. La duda "¿es skill o sidecar?" se resuelve con la pregunta filtro del Paso 1: **¿se va a usar más de una vez?** Si la observación no se va a usar más de una vez ni como skill ni como template, es sidecar.

## Push al repo GitHub de skills

Después de crear o modificar skills, sincronizar al repo `~/repos/nelson-hermes-skills`:

```bash
# Copiar skills nuevas/modificadas
cp -r ~/.hermes/skills/equipo-nelson/nombre-skill ~/repos/nelson-hermes-skills/equipo-nelson/
cp ~/.hermes/skills/nombre-skill/SKILL.md ~/repos/nelson-hermes-skills/nombre-skill/SKILL.md

# Commit y push
cd ~/repos/nelson-hermes-skills
git add -A
git commit -m "feat: skills nuevas sesion YYYY-MM-DD — nombre1, nombre2"
git push origin main
```

PITFALL: el array `SKILLS=()` en `sync-to-repo.sh` no se actualiza automáticamente — el método manual con `cp` + `git add -A` es más confiable.

## Referencias

- `references/roadmap-convention.md` — formato estándar del ROADMAP, cómo recrearlo si se pierde, lecciones de la pérdida de mayo 2026
- `references/skill-validator-checklist.md` — pre-flight check antes de declarar la skill "lista" (frontmatter, tamaño, peer-review mental)
- `references/high-value-observations-convention.md` — sub-protocolo del sidecar de brainstorming: cuándo guardar observaciones filtradas de evals y cómo (schema de 8 campos, patrones de ejemplo, ciclo de vida). Ex-skill `nelson-high-value-observations` consolidada acá.
- `templates/skill-authoring-readme.md` — README de brainstorming que se usa al cerrar una skill nueva
- `templates/recap-message.md` — plantilla del mensaje de cierre para WhatsApp
- `nelson-brainstorming` — la skill vecina que archiva docs; esta skill archiva skills
- `hermes-agent-skill-authoring` — la otra skill de authoring, esa es para in-repo (no confundir)
- `nelson-meta-orchestrator` — la skill que coordina qué agente hace qué; las skills creadas acá alimentan el catálogo que el orchestrator conoce
