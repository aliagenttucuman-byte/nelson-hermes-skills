---
name: nelson-optillm
description: "Integracion de OptiLLM como proxy de inferencia optimizado para el equipo Nelson. Infraestructura lista, reservada para modelos grandes (13B+)."
category: software-development
version: "1.0.0"
author: "Equipo Nelson (I+D+I)"
tags: [optillm, inference-optimization, proxy, ollama, mcts, moa, llm]
---

# OptiLLM — Proxy de Inferencia Optimizado

## 1. ¿Qué es?

OptiLLM es un proxy OpenAI API que intercepta requests y aplica técnicas de optimización de inferencia (MCTS, MOA, Best-of-N, etc.) antes de enviar al modelo. Es transparente para el cliente: solo cambia el nombre del modelo (`moa-gpt-4o`, `mcts-llama3.1:8b`).

## 2. Estado en el equipo Nelson

| Aspecto | Estado |
|---------|--------|
| **OpenCode Zen API** | ✅ Conectado — `gpt-5.4-nano` default en producción |
| Infraestructura local | ✅ Ollama + OptiLLM + 3 RAGs corriendo |
| Integración RAGs | ⏳ Pendiente — requiere cambiar `base_url` y `model` en cada backend |
| Benchmarks | ✅ Completados (mayo 2026) |
| Skill + Templates | ✅ Actualizados (OpenCode Zen + OptiLLM) |

**Arquitectura actual:**
- **Producción:** OpenCode Zen API → `gpt-5.4-nano` (más barato, mejor calidad)
- **Fallback:** Ollama local → `llama3.2:3b` (sin internet, sin costo)
- **Experimental:** OptiLLM proxy → reservado para modelos grandes (13B+)

**Veredicto actual (mayo 2026):** Con `llama3.2:3b` local, las técnicas complejas (MOA, MCTS) no aportan. OpenCode Zen con `gpt-5.4-nano` es más barato y mejor que cualquier modelo local en nuestra GPU.

## 3. Instalación y Deploy

```bash
# 1. Clonar e instalar en entorno virtual
python3 -m venv /home/server/optillm-venv
source /home/server/optillm-venv/bin/activate
pip install git+https://github.com/algorithmicsuperintelligence/optillm.git
pip install math-verify  # dependencia faltante

# 2. Levantar como proxy apuntando a Ollama
OPENAI_API_KEY=sk-dummy optillm \
  --base_url http://localhost:11434/v1 \
  --host 0.0.0.0 \
  --port 18000 \
  --log info
```

## 4. Tabla de Técnicas

| Técnica | Slug | Cuándo usar | Overhead |
|---------|------|-------------|----------|
| **Passthrough** | `none` | Queries simples, RAGs actuales | 0% |
| **MOA** | `moa` | Síntesis de múltiples perspectivas, creatividad | ~4x tokens |
| **MCTS** | `mcts` | Razonamiento multi-paso complejo | ~4x tokens |
| **Best of N** | `bon` | Generar N respuestas, elegir la mejor | ~2-3x tokens |
| **CoT Reflection** | `cot_reflection` | Chain-of-Thought + auto-corrección | ~2x tokens |
| **PlanSearch** | `plansearch` | Problemas de programación/análisis | ~3x tokens |
| **Rereading** | `re2` | Relectura del prompt para mejor comprensión | ~1.5x tokens |
| **CePO** | `cepo` | Planificación de tareas grandes | ~3x tokens |
| **Z3 Solver** | `z3` | Problemas formales/matemáticos exactos | Variable |

## 5. Cómo usar (código)

```python
from openai import OpenAI

# Apuntar a OptiLLM en lugar de Ollama directo
client = OpenAI(base_url="http://localhost:18000/v1", api_key="sk-dummy")

# Directo (passthrough)
resp = client.chat.completions.create(
    model="llama3.2:3b",
    messages=[{"role": "user", "content": "Hola"}]
)

# Con técnica MOA
resp = client.chat.completions.create(
    model="moa-llama3.2:3b",
    messages=[{"role": "user", "content": "Resume este texto..."}]
)

# Alternativa: via extra_body
resp = client.chat.completions.create(
    model="llama3.2:3b",
    messages=[{"role": "user", "content": "..."}],
    extra_body={"optillm_approach": "mcts"}
)
```

## 6. Combinaciones

```python
# Secuencial: CoT -> MOA
model="cot_reflection&moa-llama3.2:3b"

# Paralelo: ejecutar 3 técnicas, devolver lista
model="bon|moa|mcts-llama3.2:3b"
```

## 7. Benchmarks realizados (mayo 2026)

### 7.1 Razonamiento matemático (trenes cruzados, respuesta exacta: 280 km)

| Variante | Respuesta | Calidad |
|----------|-----------|---------|
| Directo llama3.2:3b | 560 km | ❌ Mal |
| MOA llama3.2:3b | 350 km | ❌ Mal |
| MCTS llama3.2:3b | 2800 km | ❌ Mal |
| Directo llama3.1:8b | 560 km | ❌ Calculó bien, interpretó mal |
| **Re2 llama3.1:8b** | **280 km** ✅ | ✅ **¡Acertó!** |
| MOA llama3.1:8b | 350 km | ❌ Peor que directo |
| MCTS llama3.1:8b | Incompleto | ❌ No terminó |
| CoT Reflection 8B | 140 km | ❌ Overthinking |
| BON 8B | ~290 km | ❌ Concepto erróneo |

### 7.2 RAG real — Manual de RRHH

| Pregunta | Directo | Passthrough | MOA |
|----------|---------|-------------|-----|
| Licencia paternidad (30 días) | ✅ con disclaimer | ✅ perfecto | ✅ pero alucinó dato de maternidad |
| Beneficios económicos (6 ítems) | ✅ con disclaimer | ✅ conciso | ✅ pero 34s, 900 tokens |
| 7 tardanzas (descuento) | ✅ correcto | ❌ dijo "aviso escrito" | ✅ con info irrelevante |

### 7.3 Conclusiones del benchmark

1. **OptiLLM funciona técnicamente perfecto.** Infraestructura lista, proxy estable.
2. **Con modelos 3B-8B, las técnicas complejas no aportan.** Consumen 4-5x recursos sin mejorar calidad.
3. **El problema es el modelo, no OptiLLM.** 8B parámetros no alcanzan para razonamiento confiable.
4. **Para RAGs de documentos (no matemáticas), passthrough es suficiente.** MOA puede mejorar síntesis pero alucina datos.
5. **Re2 (rereading) mostró mejor resultado en 8B** que MOA/MCTS en matemáticas.

## 8. Roadmap de integración

| Fase | Modelo objetivo | Técnica a evaluar | Cuándo |
|------|-----------------|-------------------|--------|
| I+D+I | minimax2.7 / kimi2.6 / qwen3 | MOA, MCTS, Re2 | Cuando estén disponibles local/via API |
| I+D+I | 13B+ local (llama3.1:70b, etc.) | MOA, MCTS | Cuando haya GPU suficiente |
| Producción | Modelo aprobado en I+D+I | La que gane el benchmark | Post aprobación de Tony |

## 9. Templates de integración en FastAPI

### 9a. Backend con OpenCode Zen (default del equipo — producción)

Ver `templates/rag-opencode-backend.py` — Switch entre OpenCode Zen API, Ollama local y OptiLLM. Default: `gpt-5.4-nano` vía OpenCode Zen (más barato, mejor calidad).

```python
# Default del equipo (producción):
export LLM_BACKEND=opencode
export OPENCODE_MODEL=gpt-5.4-nano
export OPENCODE_API_KEY=sk-xxxxxxxx
```

### 9b. Backend con OptiLLM (experimental — modelos grandes)

Ver `templates/rag-optillm-backend.py` — Proxy local de optimización de inferencia. Reservado para modelos 13B+.

```python
# Experimental:
export LLM_BACKEND=optillm
export OPTILLM_TECHNIQUE=moa
export OPTILLM_MODEL=llama3.1:8b
```

## 10. Comandos útiles

### OpenCode Zen (producción)

```bash
# Test rápido con gpt-5.4-nano
curl https://opencode.ai/zen/v1/chat/completions \
  -H "Authorization: Bearer $OPENCODE_API_KEY" \
  -H "HTTP-Referer: https://tu-app.com" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-5.4-nano","messages":[{"role":"user","content":"Hola"}]}'

# Listar modelos disponibles
curl https://opencode.ai/zen/v1/models \
  -H "Authorization: Bearer $OPENCODE_API_KEY"
```

### OptiLLM (experimental local)

```bash
# Ver logs
tail -f /home/server/optillm.log

# Ver modelos disponibles
curl http://localhost:18000/v1/models

# Test rápido MOA
curl http://localhost:18000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"moa-llama3.2:3b","messages":[{"role":"user","content":"Hola"}]}'

# Matar proceso
pkill -f 'optillm --base_url'
```

## 11. Referencias

- `references/benchmark-mayo-2026.md` — Reporte completo del benchmark
- `templates/rag-optillm-backend.py` — Template FastAPI con switch OptiLLM/Ollama
- Repo upstream: https://github.com/algorithmicsuperintelligence/optillm
