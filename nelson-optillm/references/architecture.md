# OptiLLM — Arquitectura y Análisis del Repo

## Estructura de carpetas (snapshot 2026-05-15)

```
optillm/
├── optillm.py                 # Entry point: servidor Flask + routing de inference
├── optillm/
│   ├── inference.py           # Motor de inferencia local (transformers)
│   ├── plugins/               # Plugin system extensible
│   │   ├── mcp_plugin.py
│   │   ├── memory_plugin.py
│   │   ├── privacy_plugin.py
│   │   ├── executecode_plugin.py
│   │   ├── json_plugin.py
│   │   ├── spl/
│   │   ├── deepthink/
│   │   └── longcepo/
│   ├── cot_reflection.py      # Chain-of-Thought con auto-reflexión
│   ├── plansearch.py          # Búsqueda de planes estructurados
│   ├── mcts.py                # Monte Carlo Tree Search
│   ├── moa.py                 # Mixture of Agents
│   ├── bon.py                 # Best of N sampling
│   ├── self_consistency.py    # Votación entre múltiples razonamientos
│   ├── rstar.py               # R* Algorithm
│   ├── leap.py                # Leap reasoning
│   ├── reread.py              # Re-read prompting
│   ├── pvg.py                 # Prover-Verifier Game
│   ├── z3_solver.py           # Integración Z3 SMT solver
│   ├── rto.py                 # Round Trip Optimization
│   ├── cot_decoding.py        # CoT sin prompting explícito
│   ├── entropy_decoding.py    # Muestreo adaptativo por entropía
│   ├── thinkdeeper.py         # Escalar profundidad de razonamiento
│   └── autothink/             # Clasificación de complejidad + steering
├── scripts/                   # Evaluación y benchmarks
│   ├── eval_math500_benchmark.py
│   ├── eval_aime_benchmark.py
│   ├── eval_arena_hard_auto_rtc.py
│   ├── eval_frames_benchmark.py
│   ├── gen_optillmbench.py
│   └── eval_optillmbench.py
├── test.py                    # Suite de tests por approach
├── docker-compose.yml         # Docker compose para deploy
├── Dockerfile                 # Variantes: latest, latest-proxy, latest-offline
├── pyproject.toml             # Config de paquete + entry point `optillm`
├── requirements.txt           # Dependencias
└── CLAUDE.md                  # Guía para Claude Code (detalle de dev)
```

## Componentes Core

### 1. `optillm.py` — Servidor Flask + Router

- Expone `/v1/chat/completions` compatible OpenAI.
- Parsea el `model` string para detectar prefijos de approach (`moa-`, `mcts-`, etc.).
- Si no hay prefijo, lee `extra_body["optillm_approach"]` o busca tags `<optillm_approach>` en el prompt.
- Deriva la llamada al módulo de técnica correspondiente.
- Soporta multi-provider: detecta API keys (OpenAI, Cerebras, Azure) y fallback a LiteLLM.

### 2. `optillm/inference.py` — Motor Local

- Carga modelos HuggingFace con `transformers`.
- Soporta LoRA adapters concatenados: `model+lora1+lora2`.
- Habilitado cuando `OPTILLM_API_KEY=optillm`.
- Usa GPU si disponible; fallback a CPU.

### 3. Técnicas de Optimización (carpeta `optillm/`)

Cada técnica es un módulo Python independiente con interfaz estándar:
- Recibe el prompt/mensajes.
- Puede hacer múltiples llamadas al LLM (backend externo o local).
- Retorna la respuesta optimizada.

**Pipeline (`&`)**: la salida del primer módulo se pasa como entrada al segundo.
**Paralelo (`|`)**: se ejecutan todos y se retorna una lista de respuestas.

### 4. Plugin System (`optillm/plugins/`)

- Cada plugin implementa una interfaz estandarizada para modificar requests,
  procesar responses, o añadir herramientas.
- Plugins relevantes para nuestro ecosistema:
  - **MCP**: conecta servidores MCP (nuestro interés futuro en MCP).
  - **Memory**: chunking + retrieval para contexto ilimitado.
  - **Privacy**: anonimiza PII antes de enviar al LLM.
  - **ExecuteCode**: intérprete de código sandboxed.
  - **JSON**: salidas estructuradas via `outlines` library.

## Cómo se implementa cada técnica (resumen)

| Técnica | Estrategia core | Complejidad computacional |
|---------|----------------|---------------------------|
| MCTS | Expande árbol de razonamiento, simula rollouts, selecciona mejor camino | Alto (múltiples llamadas) |
| MOA | Genera N respuestas con agentes diversos, agrega/refina | Medio-Alto |
| BON | Genera N candidatos, scoring de calidad, elige mejor | Medio |
| CoT Reflection | Genera CoT, luego reflexiona y critica, luego refina | Medio |
| PlanSearch | Descompone problema en sub-objetivos, busca planes | Medio |
| Self-Consistency | Genera múltiples CoT, vota por mayoría | Medio |
| CePO | Divide problema en fases, optimiza cada una | Medio |
| PVG | Genera prueba + verificación, itera hasta verificar | Alto |
| Z3 Solver | Traduce a SMT, resuelve con Z3, traduce respuesta | Bajo (si es factible) |
| Entropy Decoding | Muestrea basado en incertidumbre del modelo | Bajo |
| CoT Decoding | Decodifica con bias hacia tokens de razonamiento | Bajo |
| ThinkDeeper | Escala tokens de razonamiento según complejidad | Bajo |

## Dependencias críticas

- `flask` — servidor HTTP.
- `openai` — cliente para llamadas a providers externos.
- `transformers`, `torch` — inferencia local.
- `litellm` — routing multi-proveedor.
- `outlines` — structured outputs (plugin json).
- `z3-solver` — verificación formal (plugin z3).
- `mcp` — Model Context Protocol (plugin mcp).

## Variantes Docker

| Tag | Qué incluye | Cuándo usar |
|-----|-------------|-------------|
| `latest` | Todo completo | Desarrollo / producción general |
| `latest-proxy` | Solo proxy, sin inferencia local | Si solo se usa como proxy a OpenAI/Cerebras |
| `latest-offline` | Incluye modelos embebidos | Aire gapped / sin internet |

## Multi-provider auto-detection

OptiLLM detecta automáticamente el provider según variables de entorno:
1. `OPENAI_API_KEY` → OpenAI
2. `CEREBRAS_API_KEY` → Cerebras
3. `AZURE_OPENAI_API_KEY` → Azure
4. Fallback → LiteLLM (soporta 100+ providers)

## Configuración de plugins

### MCP (`~/.optillm/mcp_config.json`)

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/server"]
    }
  }
}
```

### Memory

Activa automáticamente si el contexto supera el límite de tokens del modelo.
Chunking configurable + retrieval vectorial implícito.

## Testing del repo

```bash
# Completo
python test.py

# Selección
python test.py --approaches moa mcts bon --model gpt-4o-mini

# Con endpoint custom
python test.py --base-url http://localhost:8080/v1
```

## Integración con nuestro ecosistema Hermes

Hermes tiene un sistema de model providers extensible (ver AGENTS.md). OptiLLM
puede integrarse como:

1. **Model Provider alternativo**: en lugar de apuntar directo a OpenAI,
   el gateway de Hermes apunta a `http://localhost:8080/v1`.
2. **Skill de optimización**: cuando un agente necesita razonamiento profundo,
   la skill `nelson-optillm` configura el approach y redirige la petición.
3. **Plugin de gateway**: interceptar requests salientes y enriquecerlas
   con técnicas de OptiLLM sin que el agente lo sepa.

## Notas de sesión (2026-05-15)

- Repo clonado desde `algorithmicsuperintelligence/optillm`.
- Analizado con `skill_view` del CLAUDE.md interno.
- No se ejecutó aún en nuestro servidor; el siguiente paso es deploy local
  para validación.
- Tony quiere que esto se convierta en skill oficial del equipo + template
  de integración FastAPI/React.
