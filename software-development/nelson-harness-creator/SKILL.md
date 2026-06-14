---
name: nelson-harness-creator
description: "Harness Engineering para proyectos Python del equipo Nelson. Genera AGENTS.md, feature_list.json, progress.md e init.sh para que agentes IA (Claude Code, Codex) trabajen de forma confiable en repos reales. Stack: Python 3.12, Polars, FastAPI, pytest, ruff, mypy, MLflow. Basado en walkinglabs/learn-harness-engineering (8.4K stars)."
triggers:
  - harness engineering
  - agents.md
  - feature list
  - agente coding confiable
  - session continuity
  - harness proyecto
  - claude code setup
  - codex setup
version: "1.0.0"
---

# nelson-harness-creator

## Por qué importa

El modelo más poderoso igualmente falla si no construís el ambiente correcto.

Anthropic — mismo modelo (Claude Opus 4.5), mismo prompt:
- SIN harness: USD 9, 20 min → resultado no funciona
- CON harness: USD 200, 6 horas → producto completamente funcional

Un equipo agregó AGENTS.md a un proyecto FastAPI+PostgreSQL+Redis (~15.000 líneas).
El mismo modelo pasó de 1/5 runs exitosos (20%) a 4-5/5 (80-100%).
Sin cambiar el modelo.

## Los 5 subsistemas del harness

```
┌─────────────────────────────────────────────────────┐
│                   HARNESS COMPLETO                  │
├──────────────┬──────────────┬──────────────────────┤
│ INSTRUCTIONS │    STATE     │    VERIFICATION      │
│  AGENTS.md   │feature_list  │     init.sh          │
│  100 líneas  │+progress.md  │  tests+lint+build    │
├──────────────┴──────────────┴──────────────────────┤
│        SCOPE          │        LIFECYCLE           │
│  1 feature a la vez   │  session-handoff.md        │
│  definition of done   │  init → work → cleanup     │
└───────────────────────┴────────────────────────────┘
```

## Setup en un nuevo proyecto (5 pasos)

```bash
# 1. Ir al repo del proyecto
cd ~/repos/mi-proyecto-lan

# 2. Crear los 5 archivos del harness
# (copiar templates de abajo y personalizar)

# 3. Validar el harness
node ~/.hermes/scripts/validate-harness.mjs

# 4. Hacer el primer run del agente
# El agente lee AGENTS.md primero, luego feature_list.json
# NUNCA empieza a codificar sin leer el harness

# 5. Al finalizar la sesión
# El agente corre cleanup: git status, tests, actualiza progress.md
```

---

## Template 1: AGENTS.md

Máximo 100 líneas. Es un mapa/router, NO una enciclopedia.

```markdown
# AGENTS.md — [Nombre del Proyecto]

## Stack
- Python 3.12
- Polars (NUNCA pandas — si ves import pandas, es un error)
- FastAPI + uvicorn
- pytest + pytest-cov
- ruff (linter + formatter)
- mypy (type checking)
- MLflow (tracking de modelos — SIEMPRE registrar con mlflow.log_model())
- Docker (producción)

## Comandos de verificación
Antes de declarar cualquier tarea como "lista", correr:
```bash
bash init.sh
```
Si falla → NO está listo.

## Estructura del proyecto
```
src/
  api/          # FastAPI routers
  models/       # Modelos ML (XGBoost, LightGBM)
  data/         # Pipelines Polars
  utils/        # Helpers compartidos
tests/
  unit/
  integration/
feature_list.json   # Estado actual del proyecto
progress.md         # Log de sesiones
```

## Convenciones críticas
- Polars: usar lazy API (scan_csv, scan_parquet) para archivos > 100MB
- FastAPI: cada endpoint tiene su schema Pydantic
- MLflow: cada experimento tiene run_name descriptivo
- Tests: cobertura mínima 80% en src/models/
- Commits: conventional commits (feat:, fix:, docs:)

## Estado actual
Ver feature_list.json para el estado de cada feature.
Ver progress.md para el log de la última sesión.

## Lo que NO hacer
- No instalar dependencias sin agregarlas a pyproject.toml
- No usar pandas (usar Polars)
- No hardcodear paths (usar variables de entorno)
- No declarar "listo" sin pasar init.sh
```

---

## Template 2: feature_list.json

```json
{
  "project": "nombre-del-proyecto",
  "version": "1.0.0",
  "last_updated": "2026-06-13",
  "features": [
    {
      "id": "F01",
      "name": "Ingesta de datos desde Excel",
      "description": "Pipeline Polars que lee Excel de Transoft y valida schema",
      "status": "done",
      "definition_of_done": [
        "pl.read_excel() funciona con archivos reales",
        "validación de schema con Pandera",
        "test unitario en tests/unit/test_ingesta.py pasa"
      ],
      "dependencies": [],
      "assigned_to": "agent"
    },
    {
      "id": "F02",
      "name": "Modelo de predicción de delay",
      "description": "LightGBM clasificador con features de ruta, hora, clima",
      "status": "in-progress",
      "definition_of_done": [
        "AUC-ROC > 0.85 en test set",
        "SHAP values calculados",
        "modelo registrado en MLflow",
        "endpoint /predict-delay en FastAPI funciona",
        "tests de integración pasan"
      ],
      "dependencies": ["F01"],
      "assigned_to": "agent"
    },
    {
      "id": "F03",
      "name": "Dashboard de KPIs",
      "description": "Dash interactivo con CASK, RASK, Load Factor por ruta",
      "status": "not-started",
      "definition_of_done": [
        "dashboard levanta en puerto 8050",
        "filtros por ruta y mes funcionan",
        "datos se actualizan al refrescar"
      ],
      "dependencies": ["F01", "F02"],
      "assigned_to": "agent"
    }
  ],
  "blocked": [],
  "notes": "Prioridad: F02 antes del sprint review del viernes"
}
```

Status válidos: `not-started` | `in-progress` | `done` | `blocked`

---

## Template 3: init.sh

El agente corre esto antes de declarar cualquier tarea como lista.

```bash
#!/usr/bin/env bash
set -e  # salir en el primer error

echo "=== VERIFICACIÓN DEL HARNESS ==="
echo ""

# 1. Instalar dependencias
echo "[1/5] Instalando dependencias..."
pip install -e ".[dev]" -q

# 2. Type checking
echo "[2/5] Type checking (mypy)..."
mypy src/ --ignore-missing-imports

# 3. Linting
echo "[3/5] Linting (ruff)..."
ruff check src/ tests/

# 4. Tests
echo "[4/5] Tests (pytest)..."
pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=80

# 5. Verificar feature en progreso
echo "[5/5] Verificando feature_list.json..."
python3 -c "
import json
with open('feature_list.json') as f:
    data = json.load(f)
in_progress = [f for f in data['features'] if f['status'] == 'in-progress']
if in_progress:
    print(f'  Feature en progreso: {in_progress[0][\"name\"]}')
    print(f'  Definition of done:')
    for item in in_progress[0]['definition_of_done']:
        print(f'    - {item}')
"

echo ""
echo "✅ HARNESS OK — listo para continuar"
```

---

## Template 4: progress.md

Log de sesiones para continuidad entre agentes/sesiones.

```markdown
# progress.md — Log de Sesiones

## Sesión actual
- Fecha: 2026-06-13
- Feature: F02 — Modelo de predicción de delay
- Estado al inicio: in-progress
- Objetivo de la sesión: llegar a AUC-ROC > 0.85

## Lo que se hizo
- [ ] Feature engineering: lag features del inbound flight
- [ ] Entrenamiento LightGBM con TimeSeriesSplit
- [ ] SHAP values calculados
- [ ] Registro en MLflow

## Blockers
- Ninguno

## Estado al cerrar
- Resultado: ...
- Siguiente paso: ...
- Tests pasando: sí/no
- init.sh: ✅/❌

---

## Sesiones anteriores

### 2026-06-12
- Feature: F01 — Ingesta de datos
- Completado: sí
- Notas: el archivo Excel de Transoft tiene encoding windows-1252, se agregó encoding='cp1252' al pl.read_excel()
```

---

## Template 5: session-handoff.md

Protocolo de inicio y cierre de sesión del agente.

```markdown
# session-handoff.md

## AL INICIAR UNA SESIÓN
1. Leer AGENTS.md completo
2. Leer feature_list.json — identificar feature "in-progress"
3. Leer progress.md — ver qué se hizo en la sesión anterior
4. Correr init.sh — verificar que el repo está en estado limpio
5. Confirmar el objetivo de la sesión antes de codificar

## AL CERRAR UNA SESIÓN
1. Correr init.sh — todos los checks deben pasar
2. Actualizar feature_list.json — cambiar status si corresponde
3. Actualizar progress.md — documentar lo que se hizo y el siguiente paso
4. git add -A && git commit -m "feat: [descripción]"
5. Verificar que no hay archivos temporales o cambios sin commitear

## REGLAS IRRENUNCIABLES
- NO declarar una feature como "done" si init.sh falla
- NO empezar una feature nueva sin terminar la "in-progress"
- NO instalar dependencias sin actualizar pyproject.toml
- NO usar pandas (siempre Polars)
- SIEMPRE registrar modelos en MLflow
```

---

## Variantes por tipo de proyecto Nelson

### Proyecto LAN Chile (ML + FastAPI)
AGENTS.md agrega:
```
## Convenciones LAN Chile
- KPIs: CASK, RASK, Load Factor, Yield — ver nelson-finance-reporting skill
- Datos desde: BTS CSV (lazy scan), Excel Transoft, Sitrack
- Modelos: registrar con mlflow.set_experiment("lan-chile-[nombre]")
- Moneda: siempre normalizar CLP/USD antes de features
```

init.sh agrega:
```bash
# Verificar que no hay imports de pandas
echo "Verificando imports prohibidos..."
if grep -r "import pandas" src/ --include="*.py"; then
  echo "❌ ERROR: pandas detectado — usar Polars"
  exit 1
fi
```

### Proyecto ForestAI (visión + YOLO)
AGENTS.md agrega:
```
## Convenciones ForestAI
- Modelos YOLO: siempre versionar con mlflow + artefactos en /models/
- Imágenes de entrenamiento: nunca en el repo — usar rutas absolutas desde .env
- GPU: verificar torch.cuda.is_available() antes de entrenar
```

### Proyecto Bisonte (Excel pipeline)
AGENTS.md agrega:
```
## Convenciones Bisonte
- Flujo 1:1: CDO Sistema → CDO Trabajada, PF Sistema → PF Trabajada
- Input: Excel del sistema, Output: Excel procesado en UPLOAD_DIR
- Nombres de columnas: exactamente como los usa la gerente operativa
```

---

## Script de validación (Node.js)

Instalar el harness-creator del repo original:

```bash
# Clonar el skill
cd /home/server
git clone https://github.com/walkinglabs/learn-harness-engineering /tmp/learn-harness
cp -r /tmp/learn-harness/skills/harness-creator ~/.hermes/scripts/harness-creator

# Correr validación en un proyecto
cd ~/repos/mi-proyecto
node ~/.hermes/scripts/harness-creator/validate-harness.mjs
```

Output esperado:
```
HARNESS VALIDATION REPORT
========================
INSTRUCTIONS (AGENTS.md):  ████████░░ 4/5
STATE (feature_list.json): ██████████ 5/5
VERIFICATION (init.sh):    ████████░░ 4/5
SCOPE:                     ██████░░░░ 3/5
LIFECYCLE:                 ████████░░ 4/5

Total: 20/25 — GOOD
```

---

## Quickstart: harness en 10 minutos

```bash
# 1. En el repo del proyecto
cd ~/repos/mi-proyecto

# 2. Crear AGENTS.md desde el template de arriba (personalizar stack)
# 3. Crear feature_list.json con las features actuales del proyecto
# 4. Crear init.sh y darle permisos
chmod +x init.sh

# 5. Correr init.sh una vez para verificar que funciona
bash init.sh

# 6. Crear progress.md y session-handoff.md
# 7. Commitear todo
git add AGENTS.md feature_list.json init.sh progress.md session-handoff.md
git commit -m "feat: harness engineering setup"

# 8. En la próxima sesión con el agente, empezar con:
# "Lee AGENTS.md, feature_list.json y progress.md antes de hacer cualquier cosa"
```

---

## Pitfalls críticos

- AGENTS.md largo = inútil: si supera 100 líneas el agente lo ignora. Cortar sin piedad.
- init.sh que no falla = inútil: si los tests no tienen cobertura mínima configurada, el agente siempre pasa aunque no haga nada.
- feature_list.json con muchos "in-progress" = caos: máximo 1 feature in-progress a la vez.
- progress.md desactualizado = sesión perdida: el agente no tiene telepacia, si no está escrito no lo sabe.
- AGENTS.md sin convenciones prohibidas: siempre incluir "NO usar pandas", "NO hardcodear paths" — el agente necesita saber qué NO hacer tanto como qué hacer.
- Harness sin tests = decoración: sin pytest corriendo en init.sh, el agente puede declarar todo "done" sin que nada funcione.

## Referencias

- Repo original: https://github.com/walkinglabs/learn-harness-engineering
- Paper Anthropic long-running agents: https://www.anthropic.com/research
- OpenAI Harness Engineering (2026): https://openai.com/research
- Curso completo en español: https://walkinglabs.github.io/learn-harness-engineering/es/
