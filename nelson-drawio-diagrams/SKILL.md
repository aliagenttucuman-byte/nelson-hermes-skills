---
name: nelson-drawio-diagrams
description: Genera diagramas draw.io profesionales para el equipo Nelson — arquitecturas de agentes IA, pipelines RAG, infra FastAPI+React, ERDs, flowcharts, UML. Wrapper sobre drawio-skill con configuración headless lista para ai-server Linux. Usa logos reales de Claude, OpenAI, Groq, Qdrant, LangChain (321 marcas AI/LLM). Auto-extrae grafos de imports de proyectos Python reales.
version: 1.0.0
author: JARVIS
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [drawio, diagram, architecture, ai-agents, fastapi, rag, visualization, nelson]
    category: creative
    related_skills: [drawio-skill, excalidraw, architecture-diagram, nelson-ai-agents, nelson-rag-pipeline]
---

# nelson-drawio-diagrams

> **Trigger:** Nelson pide un diagrama de arquitectura, flujo, infra, pipeline RAG, estructura de agentes, ERD, UML — o hay un sistema con 3+ componentes que se explica mejor visualmente.

## Setup en ai-server (ya instalado)

| Componente | Estado | Path |
|---|---|---|
| draw.io CLI v30.0.4 | ✅ instalado | `/usr/bin/drawio` |
| Graphviz (autolayout) | ✅ instalado | `/usr/bin/dot` |
| xvfb (headless) | ✅ instalado | `/usr/bin/xvfb-run` |
| drawio-skill repo | ✅ clonado | `/home/server/drawio-skill/` |
| skill en hermes | ✅ | `~/.hermes/skills/creative/drawio-skill/` |

## Comando base (SIEMPRE usar xvfb-run en ai-server)

```bash
xvfb-run -a drawio --export --format png --output /tmp/diagrama.png /tmp/diagrama.drawio
```

Para SVG (vectorial, mejor para docs):
```bash
xvfb-run -a drawio --export --format svg --output /tmp/diagrama.svg /tmp/diagrama.drawio
```

Para PDF:
```bash
xvfb-run -a drawio --export --format pdf --output /tmp/diagrama.pdf /tmp/diagrama.drawio
```

Con XML embebido (editable al abrir en draw.io):
```bash
xvfb-run -a drawio --export --format png --embed-diagram --output /tmp/diagrama.drawio.png /tmp/diagrama.drawio
python3 /home/server/drawio-skill/skills/drawio-skill/scripts/repair_png.py /tmp/diagrama.drawio.png
```

## Workflow completo (seguir siempre este orden)

1. **Cargar drawio-skill original** con `skill_view(name='drawio-skill')` para las instrucciones detalladas de generación de XML
2. **Generar el XML** `.drawio` siguiendo las instrucciones de drawio-skill
3. **Exportar** con `xvfb-run -a drawio --export ...`
4. **Self-check visual** con `vision_analyze` — corregir solapamientos, labels cortados, edges mal conectados
5. **Enviar** PNG por WhatsApp (MEDIA:) o SVG/PDF por Telegram

## Scripts útiles del repo

```bash
SCRIPTS=/home/server/drawio-skill/skills/drawio-skill/scripts

# Logos AI/LLM (Claude, OpenAI, Groq, Qdrant, LangChain, etc.)
python3 $SCRIPTS/aiicons.py "claude"
python3 $SCRIPTS/aiicons.py "openai groq qdrant"

# Buscar shapes oficiales (10k+ shapes AWS/GCP/K8s/Cisco...)
python3 $SCRIPTS/shapesearch.py "kubernetes pod"
python3 $SCRIPTS/shapesearch.py "aws lambda"

# Extraer grafo de imports de un proyecto Python real
python3 $SCRIPTS/pyimports.py /home/server/proyectos/forestai-poc/app --group -o /tmp/graph.json
python3 $SCRIPTS/autolayout.py /tmp/graph.json -o /tmp/structure.drawio
xvfb-run -a drawio --export --format png --output /tmp/structure.png /tmp/structure.drawio

# Jerarquía de clases Python
python3 $SCRIPTS/pyclasses.py /home/server/proyectos/farmacia-poc --group -o /tmp/classes.json

# Validar XML antes de exportar
python3 $SCRIPTS/validate.py /tmp/diagrama.drawio
```

## Casos de uso frecuentes para el equipo Nelson

### Mapa mental de propuesta comercial
```
"Mapa mental de la propuesta Bisonte con 5 ramas:
3 líneas de trabajo / costo de no automatizar / ROI / modalidades / disclaimers"
```
Usar: layout radial, nodo central grande, ramas con colores semánticos (rojo=líneas, naranja=costo, verde=ROI, azul=SaaS, gris=disclaimers), edges curvos (curved=1).

**Patrón para mapas mentales:**
- Nodo central: x=700, y=500, ancho=200, alto=60, fillColor=#0d3b66, fontStyle=1, fontSize=14
- Ramas principales: distribuir radialmente, 5 direcciones (N, NE, SE, SO, NO)
- Sub-nodos: fillColor según color de la rama, fontSize=10-11
- Edges: curved=1, strokeColor igual al fillColor de la rama
- NO usar autolayout para mapas mentales — posicionar manualmente para control visual

### Arquitectura de agentes IA
```
"Dibujame la arquitectura del meta-orquestador: 
Nelson → JARVIS → Tool Router → [FastAPI Agent, Frontend Agent, Data Agent] 
→ Honcho Memory + Qdrant Vector DB"
```
Usar: aiicons.py para logos + swimlanes por tier + shapes de base de datos

### Pipeline RAG
```
"Diagrama del pipeline RAG: 
ingest → chunk → embed (OpenAI) → Qdrant → retrieval → Claude Sonnet → respuesta"
```
Usar: aiicons.py para OpenAI/Claude/Qdrant + flechas con etiquetas

### Infra de una PoC (Bisonte, Farmacia, ForestAI)
```
"Diagrama de infra de la PoC Bisonte:
nginx :80 → [FastAPI :9000, Next.js :3000] → PostgreSQL + Redis
Cloudflare Tunnel → nginx"
```
Usar: shapes AWS/network + colores por tier (frontend/backend/data)

### Flota Bisonte
```
"Diagrama del módulo de flota:
React → FastAPI → [PostgreSQL (flota), Redis (alertas)] 
→ Notificaciones WhatsApp via Baileys"
```

### Flujo de proceso Excel (Bisonte)
```
"Flowchart del proceso CDO/PF:
Excel upload → parse sheets → split CDO/PF → compare vs baseline → 
generate trabajada → download Excel resultado"
```
Usar: shapes de flowchart (diamantes para decisiones, rectángulos para procesos)

## Estilos recomendados para el equipo

Usar paleta AlegentAI en diagramas para clientes:
- Primary: `#0d3b66` (azul oscuro — headers, componentes principales)
- Accent: `#e94560` (rojo — alertas, componentes críticos)
- Background: `#f0f4fa` (gris claro — swimlane backgrounds)
- Success: `#2ecc71` (verde — estados OK)
- Warning: `#f39c12` (amarillo — alertas)

Ejemplo de estilo para un nodo principal:
```xml
style="rounded=1;fillColor=#0d3b66;fontColor=#ffffff;strokeColor=none;fontSize=12;fontStyle=1;"
```

## Output path estándar

Guardar en:
```
/home/server/brainstorming/YYYY-MM-DD-[proyecto]-diagramas/
├── arquitectura-[nombre].drawio      ← editable
├── arquitectura-[nombre].drawio.png  ← con XML embebido
└── arquitectura-[nombre].svg         ← vectorial para docs
```

Entregar:
- PNG → WhatsApp (MEDIA:)
- SVG/PDF → Telegram

## Pitfalls

1. **Sin xvfb-run en ai-server = crash**. El server no tiene display. SIEMPRE `xvfb-run -a drawio`.
2. **PNG con IEND truncado** al usar `--embed-diagram`. Fix: correr `repair_png.py` después del export.
3. **Logos AI requieren red** al renderizar (CDN unpkg). En export offline usar `--embed` o SVG.
4. **Primera ejecución tarda ~25-30s** — draw.io inicializa Electron. Es normal, no reintentar. Siguientes ~5s.
5. **NO usar snap** — AppArmor bloquea keyring. Usar el .deb instalado en `/usr/bin/drawio`.
6. **Export timeout en diagramas muy grandes** (>200 nodos) — dividir en sub-diagramas o usar SVG.
7. **Mapas mentales radiales: usar layout manual**, NO autolayout. El autolayout de Graphviz no respeta la distribución radial — calcular coordenadas x/y manualmente con nodo central fijo y ramas distribuidas en ángulos (0°, 72°, 144°, 216°, 288° para 5 ramas).
8. **watch_patterns con "error"** en docker/uvicorn puede dar falsos positivos — `uvicorn.error` es el nombre del logger de uvicorn, no un error real. No alarmar si el output es `INFO - Application startup complete`.
9. **delegate_task para exportes paralelos**: se puede generar el XML de draw.io y el PDF de WeasyPrint en paralelo con dos subagentes — ahorran 60-80s vs secuencial.
7. **watch_patterns con "error"** — no usar "error" como watch pattern en background processes de drawio: el logger de uvicorn/electron se llama "uvicorn.error" y dispara falsos positivos. Usar "startup complete" o "Application startup" como patterns.

## Generación paralela con delegate_task

Cuando hay que generar diagrama + actualizar documento al mismo tiempo, usar delegate_task con dos tareas en paralelo:
- Tarea 1: actualizar el .md y regenerar el PDF
- Tarea 2: generar el drawio XML y exportar el PNG

Esto ahorra ~2 minutos respecto a hacerlo secuencial. Las tareas son independientes si el diagrama no depende del contenido final del PDF.

## Referencia rápida de formatos

| Formato | Cuándo | Comando |
|---|---|---|
| PNG | WhatsApp, docs rápidos | `--format png` |
| SVG | Docs técnicos, escalable | `--format svg` |
| PDF | Propuestas formales | `--format pdf` |
| drawio.png | Editable + imagen | `--format png --embed-diagram` + repair_png.py |

## Verificar instalación

```bash
drawio --version          # debe mostrar 30.0.4
dot -V                    # graphviz
xvfb-run -a drawio --help | head -5   # headless OK
```
