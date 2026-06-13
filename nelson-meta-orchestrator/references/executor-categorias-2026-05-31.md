# Executor — Categorías nuevas (2026-05-31)

## 4 categorías agregadas al executor

Archivo: `/home/server/nelson/meta-orchestrator/nelson_orchestrator/executor.py`

```python
# CATEGORY_SKILLS nuevas
"IOT":        ["equipo-nelson", "nelson-iot-arduino-spike", "nelson-external-integrations"],
"AUTOMATION": ["equipo-nelson", "nelson-automation-n8n", "nelson-background-jobs", "nelson-scheduled-jobs"],
"DOMAIN":     ["equipo-nelson", "nelson-forestai-roadmap", "nelson-mrv-reports", "nelson-netflora", "nelson-multispectral-indices", "nelson-forest-inventory"],
"SCRAPING":   ["equipo-nelson", "nelson-browser-agent", "nelson-sitrack-scraper", "nelson-external-integrations"],

# CATEGORY_AGENT nuevos
"IOT":        "Julián + JARVIS",
"AUTOMATION": "JARVIS",
"DOMAIN":     "JARVIS + Nelson",
"SCRAPING":   "Nico",
```

## Keywords nuevos en KEYWORD_SKILLS

```python
# IOT
"iot", "sensor", "telemetria", "serial" → nelson-iot-arduino-spike

# AUTOMATION
"n8n", "workflow", "automatizacion", "trigger" → nelson-automation-n8n

# DOMAIN - ForestAI
"mrv" → nelson-mrv-reports
"carbono" → nelson-mrv-reports
"ndvi", "ndre", "gndvi", "cobertura de copa" → nelson-multispectral-indices
"forestal", "reforest" → nelson-forestai-roadmap
"netflora" → nelson-netflora
"inventario forestal" → nelson-forest-inventory

# DOMAIN - Fleet
"sitrack", "camion", "flota", "scraping" → nelson-sitrack-scraper
```

## Dashboard — nuevas páginas

Archivo: `/home/server/nelson/orchestrator-dashboard/src/pages/ProjectView.tsx`

Rutas nuevas en App.tsx:
- `/forestai` → `<ForestAIPage />`
- `/fleet` → `<FleetPage />`

Sidebar organizado con secciones (dividers):
- Proyectos: ForestAI, Fleet Optimizer
- Gestión: Presupuesto, Resumen PM, Taxonomía

Para servir el build del dashboard:
```bash
cd /home/server/nelson/orchestrator-dashboard
npm run build
npx serve dist -l 5173
cloudflared tunnel --url http://localhost:5173
```
