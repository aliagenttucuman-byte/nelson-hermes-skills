---
name: nelson-brainstorming
description: Archivado de brainstorming y documentos de proyecto para Nelson Acosta. Crea carpetas con fecha, README.md obligatorio, y templates reutilizables.
category: software-development
tags: [brainstorming, documentation, project-management, sdd, specs]
related_skills: [nelson-project-bootstrap, spec-driven-development, writing-plans]
---

# Brainstorming & Documentación de Proyectos

> **Trigger:** Cada vez que Tony (Nelson) propone una idea de negocio, proyecto nuevo, feature, o refinamiento de arquitectura. También cuando se genera un SDD, spec OpenAPI, análisis financiero o modelo de dominio.

## Convención de Carpetas

Todo brainstorming, SDD, spec o documento de proyecto se guarda en:

```
~/brainstorming/
├── YYYY-MM-DD-nombre-del-proyecto/
│   ├── README.md              # Resumen ejecutivo (obligatorio)
│   ├── SDD.md                 # Software Design Document (si aplica)
│   ├── openapi.yaml           # Spec API (si aplica)
│   ├── financiero.md          # Modelos VAN/TIR/costos (si aplica)
│   ├── diagramas/             # PNG/SVG/Excalidraw
│   ├── notas/                 # Ideas sueltas, links, referencias
│   ├── spike-nombre/          # Spikes / experimentos (si aplica)
│   │   ├── SPIKE-CONCLUSION.md  # Verdict del spike (VALIDATED/PARTIAL/INVALIDATED)
│   │   └── test_*.py          # Script de prueba del spike
│   └── decisiones.md          # Decisiones clave tomadas
│
└── templates/
    ├── sdd-template.md
    ├── brainstorming-README.md
    └── spike-conclusion-template.md
```

## Spikes dentro de un Brainstorming

> **Vault Obsidian:** `~/brainstorming/` tiene `.obsidian/`. Skills kepano instaladas en `~/.hermes/skills/` y `~/brainstorming/.claude/skills/`: obsidian-markdown, obsidian-cli, obsidian-bases, json-canvas, defuddle.

Cuando un brainstorming incluye spikes (experimentos throwaway), se guardan en subcarpetas:

```
~/brainstorming/2025-05-13-idi-consultora/
├── README.md
├── spike-notebooklm/
│   ├── SPIKE-CONCLUSION.md   # Verdict: INVALIDATED + razones
│   └── test_notebooklm.py    # Script reproducible
└── arduino-iot-opciones.md
```

Cada spike DEBE tener:
- `SPIKE-CONCLUSION.md` con verdict claro (VALIDATED / PARTIAL / INVALIDATED)
- Script reproducible que permita re-ejecutar o entender el experimento
- Referencia en el README principal del proyecto
## Reglas de Oro

1. **UNA CARPETA POR SESIÓN/PROYECTO** — Nunca archivos sueltos en `~/`
2. **Fecha obligatoria** al inicio: `YYYY-MM-DD-`
3. **README.md siempre** — Resumen de 10-15 líneas para que cualquiera entienda de qué trata sin abrir otros archivos
4. **SDD separado del README** — El README es resumen; el SDD es el documento técnico completo
5. **Versionado** — Si hay cambios mayores, copiar a nueva carpeta con `_v2`

## Flujo de Trabajo Automático

Cuando Tony inicia un brainstorming:

```
1. Detectar tema/proyecto
2. Crear carpeta: mkdir -p ~/brainstorming/YYYY-MM-DD-{nombre}/
3. Generar documento(s) dentro de esa carpeta (SDD, specs, etc.)
4. Crear README.md usando template (ver templates/brainstorming-README.md)
5. Si es proyecto activo → considerar symlink a ~/proyectos/activos/
```

## Pitfalls

- **Docker container ≠ código fuente**: En ForestAI el frontend compilado vive en el container `forestai-poc-frontend-1` (puerto 3010). El tunnel CloudFlare apunta al container, NO al directorio de código. Después de cada `npm run build` hay que hacer: `docker cp ~/proyectos/forestai-3d/frontend/dist/. forestai-poc-frontend-1:/usr/share/nginx/html/`. Sin este paso los cambios no se ven aunque el build sea exitoso.
- **NO guardar specs en `~/` suelto**
- **Imagen no visible en WhatsApp desde path largo:** Si el `MEDIA:` apunta a un path profundo como `~/brainstorming/.../output/reporte.png` y Nelson no ve la imagen, copiarla a `/tmp/reporte.png` y reenviar desde ahí. Workaround confiable cuando el path incluye carpetas muy anidadas.
- **sync-to-repo.sh necesita actualización manual:** El array `SKILLS=()` en `/home/server/repos/nelson-hermes-skills/sync-to-repo.sh` no se actualiza automáticamente. Cada vez que se crea una skill nueva con `skill_manage action=create`, agregarla al array antes del próximo sync o la skill no se pushea al repo GitHub.
- **NO guardar specs en `~/` suelto**
- **NO mezclar README con SDD** — El README debe caber en una pantalla; el SDD puede ser largo
- **NO olvidar la fecha** — Sin fecha no se sabe qué brainstorming es el más reciente
- **NO usar nombres genéricos** como `proyecto-nuevo`; ser específico: `fleet-optimizer`, `rag-documentos`
- **NO intentar correr apps GUI en el servidor headless** — Obsidian, VS Code, etc. son apps de escritorio. Si Tony pide una herramienta visual, la respuesta correcta es: preparar el vault/config en el servidor y sincronizarlo a su Windows vía Syncthing + Tailscale (ver `references/syncthing-vault-sync.md`)

## Comandos Útiles

```bash
# Listar brainstormings recientes
ls -lt ~/brainstorming/ | head -20

# Buscar en todos los brainstormings
grep -r "VAN" ~/brainstorming/ --include="*.md"

# Último brainstorming
cd ~/brainstorming/$(ls -t ~/brainstorming/ | head -1)
```

## Coding Challenges

Cuando Nelson pide documentar la resolución de un coding challenge, crear en brainstorming:

```
~/brainstorming/YYYY-MM-DD-coding-challenges-{plataforma}/
├── README.md          ← tabla de challenges + flujo de trabajo
└── nombre-problema.py ← solución con docstring (enunciado + tests inline)
```

Usar `nelson-coding-challenges` skill para el flujo completo de resolución.

## Análisis de Mercado / Estimativo de Ganancias

Cuando Tony pide "¿es viable esto en Argentina?" o "cuánto podríamos ganar", el flujo es:

1. **Investigar el mercado existente** — buscar competidores internacionales (US, Europa, Israel primero)
2. **Estimar el universo total** en Argentina por segmento (hoteles, countries, clubes, etc.)
3. **Calcular escenarios** al 1%, 2% y 5% de penetración de mercado
4. **Identificar gaps** — precio, soporte local, normativas — son el diferencial siempre
5. **Modelo de negocio**: precio de integración + mantenimiento anual recurrente

Formato de respuesta para estimativo:
- Base total del mercado
- % objetivo → número de clientes
- Ingreso por instalación (one-time)
- Ingreso por mantenimiento (recurrente anual)
- Total año 1
- Tabla de escenarios (conservador / base / optimista)

## Empaquetado para Terceros (GUIA_REPLICAR.md + ZIP)

Cuando Nelson dice "armame todo para pasarle a alguien" o "quiero que otra persona lo replique", el flujo es:

1. Revisar el script principal + outputs existentes en el brainstorming
2. Generar `GUIA_REPLICAR.md` en la carpeta del spike/proyecto con:
   - Prereqs (Python + libs con versión)
   - Estructura de carpetas esperada
   - Fuente de datos (URL exacta)
   - Pasos numerados para correr
   - Resultado esperado (captura/descripción)
   - Pitfalls con solución
   - Sección "Adaptar a otro dataset" si aplica
3. Generar el ZIP con `python3 zipfile` (zip binary no disponible en el servidor):
   ```python
   import zipfile, os
   with zipfile.ZipFile('paquete.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
       zipdir('directorio-a-empaquetar', zf)
   ```
4. Incluir en el ZIP: script principal, datos de ejemplo, outputs de muestra, requirements.txt, README.md, carpeta docs/ con las guías
5. Entregar el ZIP con `MEDIA:/ruta/al/paquete.zip`

**No incluir** en el ZIP: archivos `.env`, credenciales, datasets >50MB, archivos temporales o `__pycache__`.

## Spikes de Datos Energéticos (Argentina)

Para spikes que consuman datos de la Secretaría de Energía Argentina (datos.gob.ar), ver `references/datos-energia-argentina.md` para endpoints probados, quirks del API, y patrón de pipeline completo (descarga → KPIs → reporte imagen → WhatsApp).

## Git — Pitfalls del Repo Brainstorming

El repo `~/brainstorming` tiene contenido mixto: proyectos corridos con Docker como root generan archivos `__pycache__` de owner root que **bloquean git checkout/rebase** con:

```
error: The following untracked working tree files would be overwritten
Permission denied
```

**Workaround si git rebase queda trabado por archivos de root:**

```bash
# 1. Borrar el state de rebase manualmente
rm -rf ~/brainstorming/.git/rebase-merge ~/brainstorming/.git/REBASE_HEAD

# 2. Recuperar el commit SHA de los commits locales
git -C ~/brainstorming reflog --oneline | head -10

# 3. Forzar push del commit local directamente (sin checkout)
git -C ~/brainstorming push origin <SHA>:main --force

# 4. Restaurar HEAD al branch
git -C ~/brainstorming symbolic-ref HEAD refs/heads/main
```

**Prevención:** el `.gitignore` ya excluye `__pycache__/`. Si hay archivos de root ya trackeados:
```bash
git rm -r --cached -f path/a/__pycache__/
```

Agregar siempre al `.gitignore` del repo:
```
node_modules/
__pycache__/
*.pyc
auth/
.env
```

La carpeta `auth/` de Baileys contiene tokens de sesión de WhatsApp — **nunca subir al repo**.

## Project Charter

Cuando Nelson propone una iniciativa con socio externo (modelo CEO/COO con participación societaria), generar un **Project Charter** formal aplicando la metodología de Pablo:

- PMI / ISO 21502 / PRINCE2 / Agile
- Formato: 2-3 páginas, tablas, secciones enumeradas
- Estructura: Contexto → Mandato → Alcance → RACI → Cronograma → Presupuesto → Riesgos → Estructura Societaria → KPIs → Próximos Pasos
- Hipótesis de valor siempre en formato: `CREEMOS QUE... RESULTARÁ EN... CRITERIOS DE ACEPTACIÓN...`
- Participación societaria estándar: Nelson 40-45% (tecnología), Socio 55-60% (dominio + clientes)
- Formalización: sweat equity en MVP → SAS al primer cliente pago
- Guardar como `PROJECT-CHARTER-v2.md` en la carpeta del proyecto
- Entregar a Nelson como **PDF** (no .md — WhatsApp no renderiza markdown)
  → usar el patrón WeasyPrint documentado en `nelson-documentation`

Ver template: `templates/project-charter-template.md`

## Análisis Técnico de Proyectos (Codebase Review)

Cuando Nelson trae un repo o PoC para analizar, el patrón más efectivo es:

1. **Particionar el codebase en 3 grupos** y lanzar 3 subagentes en paralelo con `delegate_task` (ver `subagent-driven-development/references/parallel-codebase-analysis.md`)
2. **Consolidar** los resultados en una página HTML standalone con tabs
3. Servir el HTML en `~/brainstorming/YYYY-MM-DD-proyecto/frontend/public/` (se sirve por el servidor de la plataforma educativa o por un simple `python -m http.server`)
4. Exponer con Cloudflare Tunnel y mandar la URL por WhatsApp

**Template HTML base:** `templates/analysis-page.html` — dark mode, tabs, CSS completo, listo para copiar y reemplazar placeholders.

**Estructura de tabs recomendada:**
- 📐 Descripción — contexto de negocio, dataset/datos clave, stats
- 🏗️ Arquitectura — flujos con `.arch-box/.arch-arrow`, stack tecnológico
- 🤖 Core/Modelo — algoritmos, métricas, features, flujo de inferencia
- ✅ Aciertos — lo que se hizo bien con justificación técnica
- ⚠️ Problemas — bugs con severidad (`.prio-high/.prio-med/.prio-low`), código incorrecto ❌ + correcto ✅
- 🚀 Mejoras — roadmap con código concreto, impacto y esfuerzo estimado

**Expansión iterativa:** Si Nelson pide más detalle, lanzar 2 subagentes paralelos de expansión (uno por grupo de tabs), hacen patches sobre el archivo existente. La página puede crecer de 53KB a 124KB en una pasada sin regenerar todo.

## Evaluaciones de Repos Open-Source (Patrón "eval")

Cuando Nelson dice "qué opinas de https://github.com/..." o "veamos este repo" sobre un proyecto open-source externo (NO un PoC propio), el flujo de archivo es:

```
~/brainstorming/YYYY-MM-DD-{nombre-repo}-eval/
└── README.md   # TL;DR + veredicto ejecutivo + tabla comparativa
```

**Estructura recomendada del README** (basada en casos reales: hands-on-ai-engineering, headroom, whisper, react-doctor):

1. **TL;DR** (3-5 líneas) — Qué es, decisión, por qué
2. **Veredicto ejecutivo** (tabla rápida: calidad, docs, madurez, actividad, licencia, riesgos)
3. **Recomendación** — INTEGRAR / SPIKE / ARCHIVADO, con razón principal
4. **Métricas del repo** — stars, forks, último commit, license (vía `curl https://api.github.com/repos/...`)
5. **Qué hace** — diagrama de arquitectura (ASCII) + modos de uso si los tiene
6. **Componentes clave** — bulleted list de las piezas más importantes
7. **Lo que vale / lo que no vale para el equipo** — comparativa con lo que ya tenemos
8. **Comparativa con stack actual** — tabla de 3 columnas (repositorio | nuestra skill/herramienta | gaps)
9. **Plan de spike opcional** (si aplica) — setup, métricas a capturar, criterios de éxito
10. **Decisión** — sección final con la decisión concreta
11. **Referencias** — links al repo, docs, model card, benchmarks

**Cuándo archivar en brainstorming vs integrar directo a skill:**

- **Eval simple / descartar rápido** → `~/brainstorming/YYYY-MM-DD-...-eval/README.md` (1 commit)
- **Vale la pena usar en el equipo** → patchear la skill correspondiente (ej. `nelson-frontend-stack` para react-doctor, `nelson-llm-generation` para LLMs nuevos) + nota en el README
- **Pieza standalone interesante** → spike corto de 1-2 días, linkear desde el README

**Patrón de commit:**
```bash
git add 2026-06-06-{nombre}-eval/
git commit -m "eval: {nombre-repo} ({autor}) — {veredicto corto}

{N-stars}, {license}, activo. Veredicto: {INTEGRAR|SPIKE|ARCHIVADO}.
Razón principal: {1-2 líneas}.

{2-3 bullets con lo más importante}"
```

**Importante:** NO subir PRs upstream para cambios sobre repos free-tier externos. Los hallazgos se mantienen en `nelson-brainstorming` y las skills.

**Diferencia vs Evaluación Rápida:**
- **Evaluación rápida** (este skill, sección anterior): veredicto ejecutivo en 5-10 min, archivado como `-eval/`, sin tocar código
- **Codebase review** (esta sección): análisis técnico profundo en horas, HTML con tabs, recomendaciones de mejora con código

## Regenerar roadmaps / archivos perdidos desde sesión search

Cuando un archivo crítico (ROADMAP, INDEX, lista de pendientes) se perdió del disco y el meta-orquestador lleva varias sesiones intentándolo leer sin éxito, NO seguir dando error: **regenerar** desde `session_search`.

Patrón aplicado el 2026-06-07 con `~/brainstorming/2026-05-15-skills-faltantes-roadmap/ROADMAP_SKILLS.md` (perdido 2+ semanas):

1. Detectar el archivo por nombre o por síntoma (sesiones cron/agent lo buscan y no aparece).
2. `search_files` en la ruta original → 0 resultados.
3. `session_search query="ROADMAP" OR "<keyword del archivo>"` → varias sesiones relevantes (la original que lo creó + las que intentaron leerlo después).
4. Reconstruir el contenido desde los summaries de esas sesiones, agregándole fecha de regeneración y nota "este archivo reemplaza al original perdido".
5. Guardar en carpeta nueva con sufijo `-v2`: `~/brainstorming/YYYY-MM-DD-<nombre>-v2/README.md`.
6. Si el archivo era un roadmap de skills pendientes, **arrancar inmediatamente la primera skill del TOP** (con el OK del usuario) para que el roadmap no quede en el limbo otra vez.

**Por qué:** un roadmap regenerado que no se ejecuta vuelve a perderse en 2 semanas. La regeneración y la primera acción tienen que ser la misma sesión.

## Exploración de Repos GitHub Trending (patrón "mira esto, jarvis?")

Cuando Nelson manda un link de repo GitHub con la pregunta corta tipo "mira esto, jarvis?" o "qué te parece esto?", el flujo es:

1. **Inspeccionar repo via API**: stars, license, fecha creación, lenguaje, descripción, topics, tamaño, open issues
2. **Leer README** (probar `main` Y `master` — muchos repos chinos/asiáticos usan `master`)
3. **Listar archivos clave**: `requirements.txt`, `config.json`, `model.safetensors`, tamaños reales con `curl -sIL ... | grep content-length`
4. **Validar fit con hardware del ai-server** (GTX 1650 4GB VRAM, 13GB RAM, CPU only fallback) — verificar SIEMPRE con `nvidia-smi` y `free -h` la primera vez en la sesión
5. **Mapear contra skills/proyectos existentes del equipo** (AlegentAI, ForestAI, Expreso Bisonte, LAN/LATAM)
6. **Veredicto en 3 categorías**:
   - ✅ Self-hosteable HOY en ai-server
   - ⚠️ Self-hosteable con caveats (cuantización, RunPod, etc.)
   - ❌ No viable hoy — vigilar madurez

Si Nelson dice "guarda esto como brainstorming" / "anotemos brainstorming", crear carpeta `~/brainstorming/YYYY-MM-DD-{nombre-repo}-spike/` con README que use el **template `templates/repo-trending-brainstorm.md`**. Estructura: TL;DR → Hardware fit → Casos de uso para equipo Nelson → Hipótesis CREEMOS/RESULTARÁ → Plan 2 fases (VIGILAR + SPIKE) → Pitfalls → Próximos pasos → Status checkboxes.

Pitfall importante: **NO crear skill operativa** desde un repo trending hasta validar Fase 1 (vigilancia 2-4 semanas) y Fase 2 (spike concreto). Hasta entonces es solo brainstorming.

## Fusión de Documentos para Propuestas Comerciales

Cuando Nelson pide "fusionar estos 2 documentos en propuesta para X", el flujo validado es:

1. **Identificar los 2 docs exactos** — preguntar paths si no son obvios, listar candidatos
2. **Preguntar 4 cosas ANTES de escribir**:
   - Audiencia: ¿interna o para enviar a prospecto?
   - Caminos de negocio: ¿cuántos y cuáles (A/B/C)?
   - Formato/tono: Project Charter PMI vs deck visual; PDF directo vs MD primero
   - Sweat equity: ¿se mantiene número total y se desglosa por roles?
3. **Si pide desglose de sweat equity**: pedir nombres+roles del equipo (4 personas típico: Arquitecto, Líder Técnico, Analista Funcional, QA). Repartir horas con coherencia técnica (Líder Técnico la mayoría, QA y AF cantidades menores).
4. **3 caminos comerciales estándar para propuestas AlegentAI**:
   - **A — Sociedad con equity mayoritario AlegentAI** (60-65%)
   - **B — Cliente paga desarrollo** (100% IP AlegentAI, servicio)
   - **C — Híbrido / activos valorizables como aporte** (paridad o cuasi-paridad)
5. **Cada camino con hipótesis CREEMOS / RESULTARÁ / CRITERIOS DE ACEPTACIÓN**
6. **Sin nombres propios de prospectos por defecto** — usar "el prospecto" / "prospecto forestal regional" salvo que Nelson autorice
7. **Output dual**: MD editable + PDF profesional usando `nelson-documentation/scripts/generar_pdf_weasyprint.py`
8. **Copia a `/tmp/`** antes de mandar por WhatsApp (pitfall conocido de paths largos)

Ver template: `templates/propuesta-comercial-3-caminos.md`

## Archivos de Soporte

- `references/forestai-geotiff-sources.md` — Fuentes públicas de GeoTIFF forestales para PoCs de inventario forestal: NeonTreeEvaluation, ReforesTree, OpenAerialMap. Incluye comandos de descarga directa y limitaciones Argentina.
- `templates/repo-trending-brainstorm.md` — Template README para brainstorming de repos GitHub trending con plan de 2 fases (VIGILAR + SPIKE).
- `templates/propuesta-comercial-3-caminos.md` — Template para propuestas comerciales AlegentAI con 3 caminos (Sociedad / Cliente paga / Híbrido) + sweat equity desglosado por roles.
- `references/external-eval-patterns.md` — Patrones de extracción de metadata de fuentes externas: endpoints API exactos (HF, GitHub, arxiv, npm, PyPI), comandos curl one-liner, campos JSON importantes, y pitfalls por fuente. Para aplicar el patrón de Evaluación Rápida.
- `templates/brainstorming-README.md` — Template copiable para README de cada sesión
- `templates/sdd-template.md` — Template para Software Design Documents
- `templates/spike-conclusion-template.md` — Template para documentar verdict de spikes
- `templates/agenda-regreso-template.md` — Template para agenda de regreso de vacaciones/licencia
- `references/fleet-optimizer-example.md` — Ejemplo concreto de SDD completo con VAN/TIR y OpenAPI
- `references/cookie-extraction-epiphany.md` — Técnica para extraer cookies de GNOME Web/Epiphany y convertir a formato Playwright
- `references/syncthing-vault-sync.md` — Cómo sincronizar un vault Obsidian entre servidor Linux y Windows vía Tailscale + Syncthing
- `templates/project-charter-template.md` — Template reutilizable para Project Charter (CEO/COO + participación societaria + metodología PM de Pablo)
- `templates/reporte-energia-argentina.py` — Script completo: descarga → KPIs → reporte PNG dark mode (petróleo y gas por empresa)
- `templates/coding-challenge-template.py` — Template base para documentar coding challenges con enunciado en docstring, type hints, y casos de prueba inline
- `templates/analysis-page.html` — Template HTML standalone dark mode con tabs para análisis técnico de proyectos (Descripción/Arquitectura/Core/Aciertos/Problemas/Mejoras)
- `references/html-project-analysis-page.md` — Patrón operativo: cómo construir la página con delegate_task paralelo, CSS reutilizable, servidor 0.0.0.0 + Cloudflare expose
- `nelson-ai-vision/references/drowning-detection-market.md` — Análisis de mercado completo para sistema de detección de ahogamiento en piletas
- `templates/poc-ai-quickstart.md` — Template README para PoCs con IA (hipótesis CREEMOS QUE, HU formato Nelson, plan 3-5 tareas, smoke test con proxy FreeLLMAPI). Companion de la skill `nelson-poc-ai-quickstart`.
- `references/forestai-inventario-forestal-drones.md` — Stack validado, repos GitHub, datasets, técnicas sin ML, criterios de éxito PoC ForestAI (2026-05-19)
- `references/github-repo-selfhost-evaluation.md` — Recipe para evaluar repos GitHub que Tony comparte ("¿se puede self-hostear?"): stats del repo, tamaño del modelo, match con hardware ai-server (GTX 1650 4GB), formato de respuesta, cuándo guardar como brainstorming vs spike directo
- `references/knowhere-analysis.md` — Análisis de Ontos-AI/knowhere: knowledge graph + RAG, veredicto 🟡 robar idea (síntesis multi-fuente y extracción de triplas), no adoptar directo

## Skills nuevas — workflow hermano

Esta skill archiva **documentos de proyecto** (SDD, specs, análisis, spikes). Cuando lo que se está creando es una **skill nueva para el equipo Nelson** (`nelson-*`), el workflow vive en `nelson-skill-authoring` — incluye su propia plantilla de README de brainstorming y la convención del ROADMAP. No mezclemos: brainstorming para docs, skill-authoring para skills.

## Vault de Obsidian

El vault de Obsidian de Nelson vive en `~/brainstorming/` (misma carpeta de brainstorming). Confirmado por `.obsidian/` presente ahí.

Las skills de kepano para Obsidian están instaladas en:
- `~/brainstorming/.claude/skills/` — para Claude Code
- `~/.hermes/skills/` — para JARVIS/Hermes

Skills instaladas (kepano/obsidian-skills):
- `obsidian-markdown` — Obsidian Flavored Markdown con wikilinks, callouts, properties
- `obsidian-bases` — Obsidian Bases (.base) con views, filters, formulas
- `json-canvas` — JSON Canvas (.canvas) con nodes y edges
- `obsidian-cli` — CLI de Obsidian para desarrollo de plugins
- `defuddle` — extrae markdown limpio de páginas web, ahorra tokens

Para instalar/actualizar:
```bash
git clone https://github.com/kepano/obsidian-skills.git /tmp/obsidian-skills
cp -r /tmp/obsidian-skills/skills/* ~/brainstorming/.claude/skills/
cp -r /tmp/obsidian-skills/skills/* ~/.hermes/skills/
```
- `nelson-ai-vision/references/drowning-detection-market.md` — Análisis de mercado completo para sistema de detección de ahogamiento en piletas
- `references/forestai-inventario-forestal-drones.md` — Stack validado, repos GitHub, datasets, técnicas sin ML, criterios de éxito PoC ForestAI (2026-05-19)
