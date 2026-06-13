# Executor Routing Expansion — Categorías IOT/AUTOMATION/DOMAIN/SCRAPING

Fecha: 2026-05-31
Archivo: `/home/server/nelson/meta-orchestrator/nelson_orchestrator/executor.py`

## Contexto

El executor original tenía 12 categorías (BACKEND, FRONTEND, RAG/AI, SPEC, QA, INFRA, DOCS, SECURITY, BROWSER, VISION, AUDIO, EXTERNAL). Se agregaron 4 nuevas para cubrir los dominios reales de ForestAI y Fleet Optimizer.

## Categorías agregadas

```python
CATEGORY_SKILLS: dict[str, list[str]] = {
    # ... (existentes) ...
    "IOT":        ["equipo-nelson", "nelson-iot-arduino-spike", "nelson-external-integrations"],
    "AUTOMATION": ["equipo-nelson", "nelson-automation-n8n", "nelson-background-jobs", "nelson-scheduled-jobs"],
    "DOMAIN":     ["equipo-nelson", "nelson-forestai-roadmap", "nelson-mrv-reports", "nelson-netflora",
                   "nelson-multispectral-indices", "nelson-forest-inventory"],
    "SCRAPING":   ["equipo-nelson", "nelson-browser-agent", "nelson-sitrack-scraper", "nelson-external-integrations"],
}

CATEGORY_AGENT: dict[str, str] = {
    # ... (existentes) ...
    "IOT":        "Julián + JARVIS",
    "AUTOMATION": "JARVIS",
    "DOMAIN":     "JARVIS + Nelson",
    "SCRAPING":   "Nico",
}
```

## Keywords agregadas a KEYWORD_SKILLS

```python
# IOT
"iot":          "nelson-iot-arduino-spike",
"sensor":       "nelson-iot-arduino-spike",
"telemetria":   "nelson-iot-arduino-spike",
"serial":       "nelson-iot-arduino-spike",
# AUTOMATION
"n8n":            "nelson-automation-n8n",
"workflow":       "nelson-automation-n8n",
"automatizacion": "nelson-automation-n8n",
"trigger":        "nelson-automation-n8n",
# DOMAIN - ForestAI
"mrv":                 "nelson-mrv-reports",
"carbono":             "nelson-mrv-reports",
"ndvi":                "nelson-multispectral-indices",
"ndre":                "nelson-multispectral-indices",
"gndvi":               "nelson-multispectral-indices",
"forestal":            "nelson-forestai-roadmap",
"netflora":            "nelson-netflora",
"cobertura de copa":   "nelson-multispectral-indices",
"inventario forestal": "nelson-forest-inventory",
"reforest":            "nelson-forestai-roadmap",
# DOMAIN - Fleet
"sitrack":  "nelson-sitrack-scraper",
"camion":   "nelson-sitrack-scraper",
"flota":    "nelson-sitrack-scraper",
"scraping": "nelson-sitrack-scraper",
```

## Pitfall: escaping en patch

Al hacer el patch con `skill_manage`, un string con backslash-quote dentro del `old_string` puede corromperse. Siempre verificar con `py_compile` después de aplicar un patch en executor.py.

```bash
python3 -m py_compile nelson_orchestrator/executor.py && echo "OK"
```

## Diseño: cuándo agregar una categoría nueva

Agregar categoría cuando:
- Hay 2+ skills del equipo que cubren un dominio cohesivo que no encaja en categorías existentes
- El dominio tiene keywords propias que los LLMs mencionan en goals reales
- Hay un agente natural responsable del dominio

No crear una categoría por skill individual — las categorías son dominios, no skills.
