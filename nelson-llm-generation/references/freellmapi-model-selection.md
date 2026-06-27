# FreeLLMAPI — Selección de modelo para PoCs

Workflow reusable cuando arrancás una PoC del equipo Nelson que va a llamar al proxy FreeLLMAPI (`http://localhost:3101/v1` en ai-server). No hardcodear un modelo a ciegas: el catálogo cambia, y modelos "obvios" como `meta-llama/llama-4-maverick:free` no están registrados.

## Cuándo aplicar

- Estás creando una PoC nueva con cliente OpenAI apuntando a FreeLLMAPI.
- Una PoC existente devuelve `"Model 'X' is not in the catalog"` (error 400).
- Querés elegir el modelo free de mejor relación calidad/velocidad para el caso de uso.
- Vas a presentar la PoC a un cliente (Gino, Pablo, prospecto) y necesitás un modelo estable.

## Paso 1 — Listar el catálogo real

```bash
curl -s -H "Authorization: Bearer freellmapi-0b0b33d6a9c82a2b15ec6e2006867256e26e7b244e71a57d" \
  http://localhost:3101/v1/models \
  | python3 -c "import json,sys; d=json.load(sys.stdin); [print(m['id']) for m in d.get('data',[]) if 'free' in m['id'].lower() or m['id'].endswith(':free')]"
```

Hoy hay ~101 modelos en total, ~40 free. La lista cambia: siempre re-ejecutar antes de hardcodear.

## Paso 2 — Benchmark de 5 candidatos free

Probá 4-5 modelos contra UNA pregunta representativa del dominio de la PoC. **No usar "hola"** — usá una pregunta real del caso de uso (farmacia, contratos, logística, etc.) para medir si el modelo entiende el contexto.

```python
import json, time
from hermes_tools import terminal

# Editá esta lista según el caso de uso
candidates = [
    "openai/gpt-oss-120b:free",        # OpenAI open-source — calidad alta
    "z-ai/glm-4.5-air:free",            # más rápido típicamente
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-coder:free",            # mejor para código/datos
    "deepseek-ai/deepseek-v4-flash",    # ruteado vía OpenRouter Stealth
]

# Prompt representativo del dominio (ejemplo farmacia)
prompt = "Sos un asistente de farmacia. Tengo 7 productos bajo stock minimo. Dame 3 acciones concretas en 2 lineas."

for m in candidates:
    payload = json.dumps({
        "model": m,
        "messages": [{"role":"user","content":prompt}],
        "max_tokens": 150,
        "temperature": 0.3
    })
    cmd = f"""curl -s -m 25 -H 'Authorization: Bearer freellmapi-0b0b33d6a9c82a2b15ec6e2006867256e26e7b244e71a57d' -H 'Content-Type: application/json' -X POST http://localhost:3101/v1/chat/completions -d {repr(payload)}"""
    t0 = time.time()
    r = terminal(cmd, timeout=30)
    dt = time.time() - t0
    try:
        d = json.loads(r.get("output",""))
        content = d.get("choices",[{}])[0].get("message",{}).get("content","")[:200]
        prov = d.get("provider","?")
        print(f"[{dt:.1f}s] {m} (prov={prov})\n  → {content}\n")
    except Exception as e:
        print(f"[{dt:.1f}s] {m} FAIL: {r.get('output','')[:150]}\n")
```

## Paso 3 — Elegir según el criterio del caso

| Criterio | Modelo recomendado |
|---|---|
| Calidad alta + tono ejecutivo (cliente, demos formales) | `openai/gpt-oss-120b:free` |
| Velocidad extrema (chat tiempo real, UX snappy) | `z-ai/glm-4.5-air:free` (~2.3s) |
| Razonamiento estructurado en español | `meta-llama/llama-3.3-70b-instruct:free` |
| Código / queries SQL / dataframes | `qwen/qwen3-coder:free` |
| Auto-routing sin elegir | `auto` (el router decide) |

## Resultados verificados (2026-06-25, prompt farmacia, max_tokens=150)

| Modelo | Latencia | Provider real | Calidad respuesta |
|---|---|---|---|
| `z-ai/glm-4.5-air:free` | 2.3s | OpenInference | Estructurada, concisa |
| `openai/gpt-oss-120b:free` | 3.7s | (stealth) | Estructurada, completa ⭐ |
| `meta-llama/llama-3.3-70b-instruct:free` | 5.5s | OpenInference | Estructurada, detallada |
| `deepseek-ai/deepseek-v4-flash` | 5.5s | OpenInference | Estructurada, con emojis |
| `qwen/qwen3-coder:free` | 5.9s | Stealth | Estructurada |

## Pitfalls específicos del benchmarking

- **`provider` en la respuesta NO es el ID del modelo real ruteado.** Puede decir `Stealth`, `OpenInference`, `openrouter/owl-alpha`. El router de FreeLLMAPI re-rutea internamente. Esto es esperable, no es un bug.
- **Latencias varían entre runs.** El primer request a un modelo "frío" puede tardar 2x. Correr el benchmark 2 veces y promediar si la decisión es ajustada.
- **No confundir `gpt-oss-120b:free` (free, modelo open de OpenAI) con `gpt-4o-mini`** (pago, custom provider). El `:free` viene de OpenRouter, no de OpenAI directo.
- **No bencharkear con `max_tokens: 20`** — los reasoning models (Nemotron, o-series, Qwen-Thinking) consumen tokens en chain-of-thought y truncan la respuesta. Mínimo 100, ideal 150-300.
- **El catálogo en `/v1/models` lista 100+ modelos pero NO todos están en el routing chain (`fallback_config`).** Si un modelo aparece en `/v1/models` pero da 400 al llamarlo, probablemente no está en `fallback_config`. Ver pitfall principal en SKILL.md.

## Aplicación en PoC

Cambiar la constante en el código:

```python
# Antes (en main.py de la PoC)
AI_MODEL = "meta-llama/llama-4-maverick:free"   # ❌ no en el catálogo

# Después
AI_MODEL = "openai/gpt-oss-120b:free"   # ✅ verificado funcional 2026-06-25
```

Si el modelo elegido falla en producción, cambiar a `"auto"` como fallback (el router elige por intelligence rank con `max_tokens: 1000+` para evitar truncation en reasoning models).
