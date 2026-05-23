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

- **Market share >100% en spikes de datos energéticos:** El último mes del CSV suele estar incompleto (solo 1-3 empresas reportando). Siempre filtrar el mes de referencia por `count >= 20` empresas antes de calcular market share o totales. Calcular el share sobre el **mismo mes filtrado**, nunca sobre el acumulado anual.
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

## Archivos de Soporte

- `references/forestai-geotiff-sources.md` — Fuentes públicas de GeoTIFF forestales para PoCs de inventario forestal: NeonTreeEvaluation, ReforesTree, OpenAerialMap. Incluye comandos de descarga directa y limitaciones Argentina.
- `templates/brainstorming-README.md` — Template copiable para README de cada sesión
- `templates/sdd-template.md` — Template para Software Design Documents
- `templates/spike-conclusion-template.md` — Template para documentar verdict de spikes
- `templates/agenda-regreso-template.md` — Template para agenda de regreso de vacaciones/licencia
- `references/fleet-optimizer-example.md` — Ejemplo concreto de SDD completo con VAN/TIR y OpenAPI
- `references/cookie-extraction-epiphany.md` — Técnica para extraer cookies de GNOME Web/Epiphany y convertir a formato Playwright
- `references/syncthing-vault-sync.md` — Cómo sincronizar un vault Obsidian entre servidor Linux y Windows vía Tailscale + Syncthing
- `references/datos-energia-argentina.md` — Endpoints CSV de Secretaría de Energía, quirks SSL, filtro mes incompleto, KPIs benchmark Abril 2026
- `templates/reporte-energia-argentina.py` — Script completo: descarga → KPIs → reporte PNG dark mode (petróleo y gas por empresa)
- `nelson-ai-vision/references/drowning-detection-market.md` — Análisis de mercado completo para sistema de detección de ahogamiento en piletas

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
