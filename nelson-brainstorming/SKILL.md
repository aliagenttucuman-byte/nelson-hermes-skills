---
name: nelson-brainstorming
description: Archivado de brainstorming y documentos de proyecto para Nelson Acosta. Crea carpetas con fecha, README.md obligatorio, y templates reutilizables. Cubre evaluaciones rápidas de repos/modelos/productos externos.
category: software-development
tags: [brainstorming, documentation, project-management, sdd, specs, repo-eval]
related_skills: [nelson-project-bootstrap, spec-driven-development, writing-plans]
---

# Brainstorming & Documentación de Proyectos

> **Trigger:** Cada vez que Tony (Nelson) propone una idea de negocio, proyecto nuevo, feature, o refinamiento de arquitectura. También cuando se genera un SDD, spec OpenAPI, análisis financiero o modelo de dominio. Y cuando Nelson manda un link externo (HF, GitHub, paper) y pregunta "¿qué opinas?" / "¿nos sirve?".

## Convención de Carpetas

Todo brainstorming, SDD, spec o documento de proyecto se guarda en:

```
~/brainstorming/
├── YYYY-MM-DD-nombre-del-proyecto/    # Proyectos propios de Nelson
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
├── YYYY-MM-DD-{nombre}-eval/   # Evaluaciones de repos/modelos/productos externos
│   └── README.md              # Veredicto ejecutivo + match con proyectos
│
└── templates/
    ├── sdd-template.md
    ├── brainstorming-README.md
    ├── external-eval-README.md
    └── spike-conclusion-template.md
```

## Patrón: Evaluación de Repos Externos ("¿qué opinas de esto?")

Cuando Nelson trae un repo de GitHub para evaluar, el flujo es:

1. `curl -sL https://raw.githubusercontent.com/{owner}/{repo}/main/README.md` para leer el README
2. `curl -s https://api.github.com/repos/{owner}/{repo}` para stars, forks, license, last push
3. Ver commits recientes para medir actividad real
4. Responder primero con audio TTS (veredicto rápido, 3-4 oraciones)
5. Luego dar análisis escrito con: qué es, tabla de capacidades, valor para Nelson, limitaciones, veredicto, próximos pasos
6. Ofrecer: "¿lo archivamos en brainstorming o lo integramos a una skill existente?"

**Estructura del análisis escrito:**
- Headline: `N stars | Licencia | Último commit: fecha`
- ¿Qué hace? (2-3 líneas)
- Tabla de capacidades/modelos si aplica
- Lo que vale para el equipo (lista con contexto Nelson concreto)
- Limitación real más importante
- Veredicto claro y acción sugerida

**Evaluaciones realizadas (archivadas como referencias):**
- `openai/whisper` → Transcripción de audio, ya corriendo en el servidor vía `faster-whisper`. Ver `nelson-audio-processing`.
- `millionco/react-doctor` → Linter para React generado por agentes. Integrar a CI/CD y como skill de agentes. Ver `nelson-react-doctor`.

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
6. **Suffix `-eval` para evaluaciones externas** — Diferencia visual entre proyecto propio y evaluación de algo ajeno. Carpeta: `YYYY-MM-DD-{nombre}-eval/`

## Flujo de Trabajo Automático

Cuando Tony inicia un brainstorming:

```
1. Detectar tema/proyecto
2. Crear carpeta: mkdir -p ~/brainstorming/YYYY-MM-DD-{nombre}/
3. Generar documento(s) dentro de esa carpeta (SDD, specs, etc.)
4. Crear README.md usando template (ver templates/brainstorming-README.md)
5. Si es proyecto activo → considerar symlink a ~/proyectos/activos/
```

## Evaluación de Repos Externos (Watchlist)

Cuando Tony trae un repo de GitHub para evaluar como herramienta o integración,
el flujo es:

1. **Investigar en profundidad** — stars, forks, commits, releases, código real (no solo README)
2. **Comparar con alternativas** que el equipo ya usa
3. **Veredicto explícito:** ADOPT / WATCHLIST / DESCARTADO
4. **Archivar en brainstorming** con:
   - Hipótesis de valor en formato Nelson (`CREEMOS QUE... RESULTARÁ EN... CRITERIOS DE ACEPTACIÓN`)
   - Señales de madurez a monitorear (stars threshold, version milestone, issue critico cerrado)
   - Próximos pasos concretos (si fuera a adoptarse, qué se haría primero)
   - Alternativas actuales con tabla comparativa
5. **Si hay proyecto propio relacionado** → crear proyecto paralelo linkado

### Señales de madurez a monitorear (genéricas)

- Supera N estrellas (umbral específico del repo)
- Lanza vX.Y.0 (versión con mejoras concretas necesarias)
- Cierra issues críticos abiertos
- Aparece en listas curadas (awesome-X) o posts de referencia
- Crece community (forks, PRs externos, discusiones)

### Formato de carpeta watchlist

```
~/brainstorming/YYYY-MM-DD-{nombre-repo}-{caso-de-uso}/
├── README.md          ← hipótesis + watchlist + señales + próximos pasos
└── notas/
    └── {repo}-analysis.md  ← stats, código revisado, bugs encontrados
```

**Ejemplo:** `2026-06-10-knowhere-rag-universal/` — Knowhere como backend RAG para AlegentAI

## Pitfalls

- **Docker container ≠ código fuente**: En ForestAI el frontend compilado vive en el container `forestai-poc-frontend-1` (puerto 3010). El tunnel CloudFlare apunta al container, NO al directorio de código. Después de cada `npm run build` hay que hacer: `docker cp ~/proyectos/forestai-3d/frontend/dist/. forestai-poc-frontend-1:/usr/share/nginx/html/`. Sin este paso los cambios no se ven aunque el build sea exitoso.
- **NO guardar specs en `~/` suelto**
- **NO guardar specs en `~/` suelto** (sí, está repetido — es el error que más se cometió; ver `nelson-skill-authoring` para el flujo equivalente cuando lo que se archiva es una skill nueva)
- **Imagen no visible en WhatsApp desde path largo:** Si el `MEDIA:` apunta a un path profundo como `~/brainstorming/.../output/reporte.png` y Nelson no ve la imagen, copiarla a `/tmp/reporte.png` y reenviar desde ahí. Workaround confiable cuando el path incluye carpetas muy anidadas.
- **sync-to-repo.sh necesita actualización manual:** El array `SKILLS=()` en `/home/server/repos/nelson-hermes-skills/sync-to-repo.sh` no se actualiza automáticamente. Cada vez que se crea una skill nueva con `skill_manage action=create`, agregarla al array antes del próximo sync o la skill no se pushea al repo GitHub.
- **`git add -A` en `~/.hermes/skills/` borra skills del filesystem:** El repo de skills tiene archivos que git trackea como `D` (deleted) de sesiones anteriores. Si se corre `git add -A` sin revisar el status primero, esos deleteds se aplican al working tree y los archivos se pierden del disco. **Siempre** hacer `git status -s | grep "^D"` antes de `git add -A` en ese repo, o usar `git add <paths específicos>` para stagear solo lo nuevo/modificado. Si se borran por error: `git checkout <SHA-anterior> -- <skill-dir>/` restaura desde el último commit bueno.
- **Dos copias del repo `nelson-hermes-skills`:** La copia activa (donde trabaja Hermes) es `~/.hermes/skills/` (112+ dirs). La copia vieja en `~/repos/nelson-hermes-skills/` está desactualizada (menos dirs). Siempre pushear desde `~/.hermes/skills/`, no desde la copia de repos. Ambas apuntan al mismo remote `github.com/aliagenttucuman-byte/nelson-hermes-skills.git`.
- **NO mezclar README con SDD** — El README debe caber en una pantalla; el SDD puede ser largo
- **NO olvidar la fecha** — Sin fecha no se sabe qué brainstorming es el más reciente
- **NO usar nombres genéricos** como `proyecto-nuevo`; ser específico: `fleet-optimizer`, `rag-documentos`
- **NO intentar correr apps GUI en el servidor headless** — Obsidian, VS Code, etc. son apps de escritorio. Si Tony pide una herramienta visual, la respuesta correcta es: preparar el vault/config en el servidor y sincronizarlo a su Windows vía Syncthing + Tailscale (ver `references/syncthing-vault-sync.md`)
- **`browser_navigate` falla en este servidor** — Chrome tira "No usable sandbox" (AppArmor userns deshabilitado en Ubuntu 23.10+). Para verificar fuentes externas (HF, GitHub, papers) usar `curl` + `sed 's/<[^>]*>//g'` directamente. Más rápido, más confiable, sin dependencies.

## Comandos Útiles

```bash
# Listar brainstormings recientes
ls -lt ~/brainstorming/ | head -20

# Buscar en todos los brainstormings
grep -r "VAN" ~/brainstorming/ --include="*.md"

# Último brainstorming
cd ~/brainstorming/$(ls -t ~/brainstorming/ | head -1)

# Listar solo evaluaciones externas
ls -lt ~/brainstorming/ | grep -- "-eval"
```

## Coding Challenges

Cuando Nelson pide documentar la resolución de un coding challenge, crear en brainstorming:

```
~/brainstorming/YYYY-MM-DD-coding-challenges-{plataforma}/
├── README.md          ← tabla de challenges + flujo de trabajo
└── nombre-problema.py ← solución con docstring (enunciado + tests inline)
```

Usar `nelson-coding-challenges` skill para el flujo completo de resolución.

## Radar de Tecnologías

Cuando Nelson comparte links de GitHub, herramientas o papers nuevos durante una sesión, el flujo es:

1. Fetchear el README via `curl -sL https://raw.githubusercontent.com/{org}/{repo}/main/README.md` (más confiable que browser en el servidor)
2. Resumir con relevancia concreta para el equipo Nelson — no descripción genérica
3. Anotar en el skill correspondiente (nelson-forestai-demo, nelson-document-processing, etc.) bajo "Tecnologías a evaluar"
4. Crear skill específico si la tecnología tiene suficiente profundidad (ver nelson-opik-eval, nelson-gemini-live)
5. Crear entrada en `~/brainstorming/YYYY-MM-DD-tecnologias-radar/README.md` con tabla de acciones y prioridades

Template de entrada en el README del radar:
```
## N. Nombre — Descripción corta
Repo: URL | Licencia | Stars
Skills: `nombre-skill`
### Qué es (2-3 líneas)
### Por qué importa para el equipo (bullets concretos)
### Acción (verbo + resultado esperado)
```

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
   with zipfile.ZipFile('paquete.zip', 'w', zipfile_DEFLATED) as zf:
       zipdir('directorio-a-empaquetar', zf)
   ```
4. Incluir en el ZIP: script principal, datos de ejemplo, outputs de muestra, requirements.txt, README.md, carpeta docs/ con las guías
5. Entregar el ZIP con `MEDIA:/ruta/al/paquete.zip`

**No incluir** en el ZIP: archivos `.env`, credenciales, datasets >50MB, archivos temporales o `__pycache__`.

## Spikes de Datos Energéticos (Argentina)

Para spikes que consuman datos de la Secretaría de Energía Argentina (datos.gob.ar), ver `references/datos-energia-argentina.md` para endpoints probados, quirks del API, y patrón de pipeline completo (descarga → KPIs → reporte imagen → WhatsApp).

## Evaluación de Repos Externos ("¿qué opinás de esto?")

Cuando Tony manda un link a un repo GitHub para opinar, el flujo es:

1. **Usar `delegate_task` con toolset `web`** para scrapear el repo (browser_navigate no funciona en ai-server headless — Cloudflare sandbox lo bloquea). El subagente hace fetch de README, estructura de carpetas, notebooks clave.
2. **Veredicto en 6 puntos:** stars/forks/licencia/último commit, qué es, estructura, stack, valor para el equipo (alto/medio/bajo por capítulo o módulo), gaps vs nuestro stack.
3. **Archivar en brainstorming:** `~/brainstorming/YYYY-MM-DD-{nombre}-eval/README.md`
4. **Push inmediato** al repo `nelson-brainstorming` (commit + push en la misma sesión).

**Estructura del README de eval (template mental):**

```
# {Nombre} — Evaluación del Repo
Fecha / Estado / Fuente / Trigger
## Veredicto (una línea ejecutiva)
## ¿Qué es? (2-3 oraciones)
## Estructura (tabla capítulos/módulos con valor para el equipo)
## Stack tecnológico
## Lo que más vale para nuestro equipo (bullets concretos)
## Lo que NO tiene (gaps reales)
## Cómo usarlo en el flujo Nelson
## Diferencias con nuestro stack (tabla comparativa)
## Próximos pasos (spikes sugeridos si aplica)
## Referencias (skills relacionadas)
```

## Git — Pitfalls del Repo Skills (nelson-hermes-skills)

El repo `~/.hermes/skills/` es el mismo que `github.com/aliagenttucuman-byte/nelson-hermes-skills`. **`git add -A` en ese repo es peligroso** — borra del filesystem todas las skills que estén staged como `D` (delete) en el índice git, incluyendo skills que existen en disco pero cuyo directorio fue borrado por movimiento previo del sync.

**PITFALL CONFIRMADO (2026-06-06):** `git add -A` + commit eliminó skills del disco porque los deletes estaban staged. Skills borradas: `nelson-lean-ctx`, `nelson-optillm`, `nelson-whatsapp-gateway` y otras. El `git rm` en staging tree **también borra el working tree**.

**Regla:** NUNCA hacer `git add -A` ciego en el repo de skills. Siempre revisar primero:
```bash
git status -s | head -30   # Ver exactamente qué se agrega
# Agregar solo directorios propios:
git add nombre-skill-nueva/ nombre-skill-modificada/
# Si hay D (deletes) indeseados — destagearlos:
git restore --staged path/a/skill-borrada/
```

**Recuperación si se borraron por error:**
```bash
cd /home/server/.hermes/skills
git checkout <SHA-anterior> -- nelson-lean-ctx/ nelson-optillm/ nelson-whatsapp-gateway/
ls -d nelson-lean-ctx nelson-optillm nelson-whatsapp-gateway  # verificar
git add nelson-lean-ctx/ nelson-optillm/ nelson-whatsapp-gateway/
git commit -m "fix(skills): restaurar skills borradas por error en git add -A"
git push origin main
``` 

**Regla: SIEMPRE hacer `git add` selectivo** en `~/.hermes/skills/`:

```bash
# CORRECTO: agregar solo las skills que se modificaron esta sesión
git add nelson-poc-ai-quickstart/ nelson-spec-driven-workflow/ nelson-llm-generation/

# PELIGROSO: puede borrar skills del filesystem
git add -A   # ← NUNCA en ~/.hermes/skills/
```

**Si se borraron skills accidentalmente**, recuperar desde el commit previo:

```bash
cd ~/.hermes/skills
# Ver qué skills estaban en el commit bueno (el anterior al que borró)
git ls-tree <SHA-anterior> --name-only | grep "^nelson-"

# Restaurar las skills borradas desde ese commit
git checkout <SHA-anterior> -- nelson-lean-ctx/ nelson-optillm/ nelson-whatsapp-gateway/

# Hacer commit de restauración
git add nelson-lean-ctx/ nelson-optillm/ nelson-whatsapp-gateway/
git commit -m "fix(skills): restaurar skills borradas por error en sync anterior"
git push origin main
```

**Nota:** `git checkout <SHA> -- <path>` restaura al working tree Y al staging area. El push va al repo remoto pero las skills quedan inmediatamente disponibles para Hermes (el filesystem es la fuente de verdad).

## PITFALL CRÍTICO: git add -A en el repo de skills borra archivos

Cuando se hace `git add -A` en `/home/server/.hermes/skills/` (repo `nelson-hermes-skills`), git agrega también los deletes de archivos que estaban staged. Esto borra del filesystem las skills eliminadas de la DB. El `git rm` aplicado en staging tree **también borra el working tree**.

Consecuencia: skills como `nelson-lean-ctx`, `nelson-optillm`, `nelson-whatsapp-gateway` pueden desaparecer del disco si se hace un `git add -A` + `git commit` + `git push` sin revisar el diff primero.

**Regla:** NUNCA hacer `git add -A` ciego en el repo de skills. Siempre:
```bash
# Ver exactamente qué se va a agregar antes
git status -s | head -30
# Agregar solo lo que es mío
git add nelson-skill-nueva/ nelson-skill-modificada/
# Si hay D (deletes) en el status y NO los quiero commitear:
git restore --staged path/a/skill-borrada/
```

**Recuperación si se borraron por error:**
```bash
cd /home/server/.hermes/skills
# Restaurar desde el commit anterior
git checkout <SHA-anterior> -- nelson-lean-ctx/ nelson-optillm/ nelson-whatsapp-gateway/
# Verificar que volvieron
ls -d nelson-lean-ctx nelson-optillm nelson-whatsapp-gateway
# Commitear la restauración
git add nelson-lean-ctx/ nelson-optillm/ nelson-whatsapp-gateway/
git commit -m "fix(skills): restaurar skills borradas por error en git add -A"
git push origin main
```

## Patrón: Evaluación de repositorios externos

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

## Evaluación Rápida de Repos / Modelos / Productos Externos

> **Trigger:** Nelson manda un link y pregunta "¿qué opinas de esto, JARVIS?" o "¿nos sirve?". El link apunta a: un modelo en HuggingFace, un repo en GitHub, un producto SaaS, un paper, una librería nueva. No es una iniciativa propia — es evaluar algo externo para decidir si se adopta, se archiva, o se descarta.

**Patrón de 5 pasos (validado en 2026-06-06 con LocateAnything-3B y FreeLLMAPI):**

1. **Verificar la fuente directo** — usar `curl` a la API oficial:
   - HuggingFace: `https://huggingface.co/api/models/{org}/{name}` (JSON estructurado con tags, downloads, license, base_model, safetensors params, siblings)
   - GitHub: `https://api.github.com/repos/{owner}/{repo}` (stars, forks, license, last push, topics) + `https://api.github.com/repos/{owner}/{repo}/contents/` para tree raíz
   - Para papers / arxiv: leer abstract y arquitectura, no quedarse en el título
   - **EVITAR `browser_navigate`** — Chrome sandbox falla en este servidor (AppArmor userns deshabilitado, error: "No usable sandbox"). Curl + `sed 's/<[^>]*>//g'` es más confiable y rápido.

2. **Extraer metadata clave** en 1-2 calls de curl:
   - Repo: stars/forks/issues/pushed_at/license/archivos clave (package.json, README.md, docker-compose.yml)
   - Modelo: pipeline_tag, base_model, license, params, tags arxiv, siblings (archivos), spaces asociados
   - Producto: pricing, ToS, multi-tenancy, dependencias críticas

3. **Veredicto ejecutivo** — siempre con esta estructura:
   - **TL;DR** (2-3 líneas con el veredicto principal)
   - **Lo que es** (1 párrafo factual)
   - **Lo bueno** (bullets concretos, no genéricos)
   - **Lo malo** (bullets honestos — no nitpicking)
   - **¿Nos sirve?** (sí/no/condicional, con razón)

4. **Match con proyectos Nelson** — tabla con columnas: Proyecto | Veredicto | Razón. Usar la lista canónica: ForestAI, Expreso Bisonte, nelson-browser-agent, JARVIS/Hermes, AlegentAI, nelson-llm-generation, agentes de equipo (Julián/Mercedes).

5. **Archivar** — si Nelson dice "dejalo como brainstorming":
   - Carpeta: `~/brainstorming/YYYY-MM-DD-{nombre-corto}-eval/`
   - **Suffix obligatorio: `-eval`** (diferencia de brainstormings de proyectos propios)
   - README usando `templates/external-eval-README.md`
   - Estructura: TL;DR + Ficha técnica + Capacidades + Veredicto + Alternativas + Match con proyectos + Próximos pasos

**Tono del veredicto:** directo, honesto, con números. Decir "7.9k stars en 6 semanas" no "popular project". Decir "ToS non-commercial → no sirve para AlegentAI" no "verificar licencia antes de usar".

**Honestidad brutal obligatoria** — Nelson valora el veredicto ejecutivo real, no el marketing del repo. Si el repo tiene un killer feature, decirlo. Si depende de algo frágil, decirlo.

**Cuándo decir "no nos sirve":** si la license bloquea producción comercial, si el proyecto está abandonado (push de +6 meses), si el approach es inherentemente frágil (ToS grises de free tiers), o si ya hay algo mejor en el stack.

**Cuándo decir "pendiente de PoC":** si el approach es interesante pero hay que probarlo. Marcar checkbox de próximos pasos con la pregunta de decisión: ¿bajamos? ¿desplegamos? ¿probamos en imagen de muestra?

**No crear skill nueva** — esto es una variación del flujo de brainstorming existente, no una clase nueva. Solo parchear este skill.

Ver template: `templates/external-eval-README.md`
Ver referencia: `references/external-eval-patterns.md` (endpoints de API, comandos curl exactos, pitfalls de cada fuente)

## Evaluación de Repos Externos (GitHub)

Cuando Nelson trae un repo externo para evaluar si sirve al equipo, el flujo es:

1. **Navegar el repo** con `browser_navigate` + `delegate_task` para análisis paralelo (README, estructura, notebooks, código clave)
2. **Generar evaluación** con estructura:
   - Métricas: stars, forks, licencia, último commit, actividad
   - Descripción: qué es, para qué sirve
   - Estructura por capítulo/módulo con nivel de valor para el equipo
   - Stack tecnológico vs nuestro stack (qué usan ellos vs qué usamos nosotros)
   - Lo que SÍ vale y lo que NO tiene (gaps)
   - Cómo usarlo en el flujo Nelson (reglas de uso)
   - Próximos pasos sugeridos (spikes)
3. **Archivar** en `~/brainstorming/YYYY-MM-DD-nombre-repo-eval/README.md`
4. **Pushear** al repo `nelson-brainstorming`

**Veredicto siempre en primera línea** — Nelson es action-oriented, quiere saber de inmediato si sirve o no.

Formato de veredicto: `ÚTIL COMO REFERENCIA`, `ADOPTAR COMO BASE`, `DESCARTAR`, `SPIKE NECESARIO ANTES DE DECIDIR`.

## Evaluación de Repos Externos de IA (¿Lo adoptamos?)

Cuando Tony comparte un repo GitHub de terceros (startup, open-source, proveedor) con "qué opinás",
el flujo es distinto a un análisis interno — el foco es **decisión de adopción**, no mejora del código.

**Preguntas que guían el análisis:**
1. ¿Qué problema resuelve exactamente?
2. ¿Cuál es el stack real? (¿hay bloat, dependencias rancias?)
3. ¿Qué tan activo/maduro es? (commits, estrellas, issues abiertos)
4. ¿Hay fit con el equipo Nelson? (¿reemplaza algo que ya tenemos? ¿complementa ForestAI, meta-orquestador, etc.?)
5. ¿Qué es lo más valioso del diseño? (técnicas, patrones robables)
6. ¿Cuáles son los riesgos de adopción? (vendor lock-in, sin mantenimiento, licencia)

**Formato de respuesta (breve, estilo Tony):**
- 2-3 líneas de qué hace
- Aciertos técnicos concretos (lo que hay que robar)
- Riesgos o limitaciones directas
- Veredicto: 🟢 adoptar / 🟡 robar idea / 🔴 no vale la pena

**No extenderse en análisis académico.** Tony quiere el veredicto rápido.
Si quiere más detalle, lo pide.

Repos notables analizados:
- `Ontos-AI/knowhere` (2026-06-10): knowledge graph + RAG + embeddings. Stack Python/FastAPI.
  Verdict: 🟡 robar patrón de síntesis multi-fuente; no adoptar directo (muy básico y sin mantenimiento activo).
  Ver `references/knowhere-analysis.md` para análisis completo.

---

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

## Archivos de Soporte

- `references/forestai-geotiff-sources.md` — Fuentes públicas de GeoTIFF forestales para PoCs de inventario forestal: NeonTreeEvaluation, ReforesTree, OpenAerialMap. Incluye comandos de descarga directa y limitaciones Argentina.
- `references/external-eval-patterns.md` — Patrones de extracción de metadata de fuentes externas: endpoints API exactos (HF, GitHub, arxiv, npm, PyPI), comandos curl one-liner, campos JSON importantes, y pitfalls por fuente. Para aplicar el patrón de Evaluación Rápida.
- `templates/brainstorming-README.md` — Template copiable para README de cada sesión
- `templates/sdd-template.md` — Template para Software Design Documents
- `templates/spike-conclusion-template.md` — Template para documentar verdict de spikes
- `templates/agenda-regreso-template.md` — Template para agenda de regreso de vacaciones/licencia
- `templates/external-eval-README.md` — Template para README de evaluaciones rápidas de repos/modelos/productos externos. Usar cuando Nelson manda un link y pregunta "¿qué opinas?".
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
