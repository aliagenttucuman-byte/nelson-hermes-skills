# Deploy de OptiLLM como proxy a Ollama — Sesión 2026-05-15

## Contexto

Ollama corre local en `localhost:11434` con modelos locales (`llama3.2:3b`,
`nomic-embed-text`, etc.). Queremos interponer OptiLLM entre el cliente y
Ollama para aplicar técnicas de optimización de inferencia (MOA, MCTS, etc.)
sin cambiar el código del cliente.

## Arquitectura

```
[Cliente] --OpenAI API--> [OptiLLM :18000] --OpenAI compatible--> [Ollama :11434/v1] --> [llama3.2:3b GPU]
```

## Instalación paso a paso

### 1. Clonar repo (shallow) e instalar en venv

```bash
cd /home/server
python3 -m venv optillm-venv
source optillm-venv/bin/activate

git clone --depth 1 https://github.com/algorithmicsuperintelligence/optillm.git /tmp/optillm
pip install /tmp/optillm

# Fix: dependencia faltante no declarada en pyproject.toml
pip install math-verify
```

### 2. Verificar instalación

```bash
python3 -c "import optillm; print(optillm.__version__)"
# Esperado: 0.3.15
```

### 3. Levantar OptiLLM apuntando a Ollama

```bash
source /home/server/optillm-venv/bin/activate
OPENAI_API_KEY=sk-dummy \
  optillm \
  --base_url http://localhost:11434/v1 \
  --host 0.0.0.0 \
  --port 18000 \
  --log info
```

> `OPENAI_API_KEY=sk-dummy` es necesario porque OptiLLM detecta la variable
> para decidir qué provider instanciar. El valor real no importa porque el
> proxy reenvía a Ollama.

### 4. Verificar que está escuchando

```bash
ss -tlnp | grep :18000
# Debe mostar: LISTEN ... 0.0.0.0:18000 ... users:(("optillm",...))
```

### 5. Probar requests

```bash
# Listar modelos (delega a Ollama)
curl -s http://localhost:18000/v1/models | python3 -c \
  "import sys,json; [print(' -',m['id']) for m in json.load(sys.stdin).get('data',[])]"

# Chat directo (sin técnica = passthrough transparente)
curl -s http://localhost:18000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:3b",
    "messages": [{"role": "user", "content": "Decime en una sola palabra: ¿de qué color es el cielo?"}],
    "max_tokens": 20,
    "temperature": 0
  }' | python3 -c "import sys,json; print('Respuesta:', json.load(sys.stdin)['choices'][0]['message']['content'])"

# Chat con técnica MOA activada
curl -s http://localhost:18000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "moa-llama3.2:3b",
    "messages": [{"role": "user", "content": "Decime en una sola palabra: ¿de qué color es el cielo?"}],
    "max_tokens": 20,
    "temperature": 0
  }' | python3 -c "import sys,json; print('Respuesta MOA:', json.load(sys.stdin)['choices'][0]['message']['content'])"
```

## Resultados de esta sesión

- **Proxy transparente** (`llama3.2:3b`) → "Azul."
- **Con técnica MOA** (`moa-llama3.2:3b`) → "Azul."

OptiLLM detectó el prefijo `moa-`, aplicó Mixture of Agents (generó 3
completions y un agente síntesis), y devolvió la respuesta consolidada.
Todo transparente para el cliente.

## Problemas encontrados y fixes

| Problema | Causa | Fix |
|----------|-------|-----|
| `ModuleNotFoundError: No module named 'math_verify'` | Dependencia faltante en `pyproject.toml` | `pip install math-verify` |
| Puerto 8000 ocupado | Otro servicio ya escuchaba en :8000 | Usar `--port 18000` |
| Puerto 8001 ocupado | Intento anterior de OptiLLM quedó zombie | `pkill -f optillm` y reintentar |
| `torch.cuda` warning | Driver NVIDIA 535 vs PyTorch compilado con CUDA 12.1 | Ignorable; inferencia corre en GPU via Ollama |

## Estado del servicio (2026-05-15)

- OptiLLM corriendo en `http://localhost:18000/v1`
- Backend: Ollama en `http://localhost:11434/v1`
- Modelos disponibles via OptiLLM: todos los de Ollama (`llama3.2:3b`, `llama3.1:8b`, `gemma3:4b`, etc.)
- Técnicas activas: MOA (probada), listas para probar: MCTS, PlanSearch, BON, etc.
