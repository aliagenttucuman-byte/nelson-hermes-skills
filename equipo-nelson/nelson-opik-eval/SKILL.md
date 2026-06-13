---
name: nelson-opik-eval
description: Plataforma open-source de evaluación de LLMs (Opik by Comet). Tracing, LLM-as-a-Judge, experimentos y datasets. Self-hosted con Docker. Aplicar en ForestAI VLM y agentes del equipo Nelson.
category: equipo-nelson
---

# Opik — Evaluación de LLMs para el equipo Nelson

https://github.com/comet-ml/opik | Apache 2.0 | 5.1k stars

## Qué es

Plataforma open-source de evaluación y observabilidad para aplicaciones LLM. Cubre:
- Tracing de llamadas a LLMs (prompts, respuestas, tokens, latencia, costo)
- Evaluación automática con LLM-as-a-Judge
- Gestión de datasets y experimentos
- Dashboard visual para comparar versiones

## Instalación self-hosted

```bash
pip install opik
opik server install   # levanta con Docker Compose
```

Acceso: http://localhost:5173

Para el servidor ai-server (evitar conflictos de puertos):
```bash
# Verificar puertos libres antes
ss -tlnp | grep -E ':(5173|8000|3000)'
# Si hay conflicto, editar docker-compose en ~/.opik/
```

## Uso básico — instrumentar un pipeline

```python
import opik

opik.configure(use_local=True)  # apunta al server local

@opik.track
def clasificar_especie(imagen_b64: str, bbox: dict) -> dict:
    # tu llamada a claude-haiku acá
    response = anthropic_client.messages.create(...)
    return {"especie": ..., "salud": ..., "confianza": ...}
```

Cada llamada queda trackeada automáticamente en el dashboard.

## Caso de uso ForestAI — VLM de clasificación de especies

### 1. Instrumentar el VLM en tree_detection.py

```python
import opik

@opik.track(name="vlm_clasificar_especie")
def _vlm_classify_tree(client, image_b64: str, tree: dict) -> dict:
    # código existente de clasificación claude-haiku
    ...
```

### 2. Armar dataset de evaluación

```python
import opik

client = opik.Opik()
dataset = client.get_or_create_dataset("forestai-especies-tucuman")

# Agregar ejemplos etiquetados manualmente
dataset.insert([
    {"input": {"imagen": "...", "bbox": {...}}, "expected_output": "Eucalipto"},
    {"input": {"imagen": "...", "bbox": {...}}, "expected_output": "Jacarandá"},
    # ...
])
```

### 3. Correr experimento de evaluación

```python
from opik.evaluation import evaluate
from opik.evaluation.metrics import Hallucination, Equals

evaluate(
    dataset=dataset,
    task=lambda x: clasificar_especie(x["imagen"], x["bbox"]),
    scoring_metrics=[
        Equals(name="especie_correcta"),
        Hallucination(name="no_alucina"),
    ],
    experiment_name="haiku-vs-sonnet-forestai"
)
```

### 4. Comparar modelos/prompts

Correr el mismo experimento con claude-haiku-4-5 vs claude-sonnet — ver cuál clasifica mejor en el dashboard.

## Métricas útiles para ForestAI

| Métrica | Qué mide |
|---------|----------|
| `Equals` | Especie predicha == ground truth |
| `Hallucination` | El modelo inventa especies que no existen |
| Custom `ConfidenceCalibration` | Confianza reportada vs accuracy real |
| `Latency` | Tiempo de clasificación por árbol |
| `TokenCost` | Costo por imagen procesada |

## Aplicaciones en el equipo Nelson

- **ForestAI VLM**: evaluar calidad de clasificación de especies
- **Meta-orquestador**: tracing de decisiones de routing
- **RAG pipeline**: evaluar relevancia de respuestas
- **WhatsApp bot**: monitorear calidad de respuestas de JARVIS
- **Cualquier agente**: visibilidad de costos y latencia en producción

## Integración con stack Nelson

- Compatible con Anthropic (claude-haiku, claude-sonnet) ✅
- Compatible con OpenAI, Groq, OpenRouter ✅
- Compatible con LangChain, LlamaIndex ✅
- Self-hosted — datos no salen del servidor ✅
- Apache 2.0 — sin restricciones comerciales ✅

## Pitfalls conocidos

- El server de Opik usa puerto 5173 (frontend) y 8000 (backend) — verificar conflictos con otros servicios
- `opik server install` requiere Docker y Docker Compose instalados
- Para producción: montar volumen persistente para no perder traces en restart

## Próximo paso

Integrar en ForestAI antes de la propuesta formal a ReforestLatam — poder mostrar métricas de calidad del clasificador de especies como argumento de venta.
