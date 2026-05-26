# DeepAgents + NVIDIA NIM — Setup validado (2026-05-21)

## Stack validado

- `deepagents==0.6.3`
- `langchain-openai` (ChatOpenAI apuntando a NVIDIA NIM)
- `langchain-ollama` (alternativa local, pero lenta sin GPU)
- Backend: `LocalShellBackend` para tools reales (shell + filesystem)
- LLM: `deepseek-ai/deepseek-v4-flash` vía NVIDIA NIM

## Instalación

```bash
python3 -m pip install deepagents langchain-openai langchain-ollama
```

## Snippet base — DeepAgents + NVIDIA NIM

```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend

load_dotenv(os.path.expanduser("~/secrets/nvidia_nim_keys.env"))

model = ChatOpenAI(
    model="deepseek-ai/deepseek-v4-flash",
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
    temperature=0.6,
    max_tokens=1024,
)

backend = LocalShellBackend(
    root_dir="/tmp/mi_agente",
    virtual_mode=False,  # evitar DeprecationWarning
    timeout=30,
)

agent = create_deep_agent(
    model=model,
    system_prompt="Sos un asistente técnico. Respondé en español.",
    backend=backend,
)

result = agent.invoke({"messages": "Tu tarea acá"})
print(result["messages"][-1].content)
```

## Tools disponibles por defecto (sin configuración extra)

- `write_todos` — gestión de lista de tareas
- `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep` — operaciones de archivo
- `execute` — ejecutar comandos shell (requiere `LocalShellBackend`)
- `task` — llamar subagentes

## Resultados del Spike 001

| Test | Resultado |
|------|-----------|
| Respuesta simple (555) | ✅ OK — 2 mensajes, rápido |
| write_file con prompt imperativo | ⚠️ PARTIAL — necesita prompt más directivo |
| execute (echo hola) | ✅ OK — 4 mensajes (human→ai→tool→ai), output correcto |

## Pitfalls

- **Ollama sin GPU**: ~9-20s por respuesta. Con tool loops (4+ iteraciones) → timeout. Usar NVIDIA NIM para spikes.
- **LocalShellBackend virtual_mode**: pasar `virtual_mode=False` explícitamente para evitar DeprecationWarning de deepagents 0.6.x.
- **write_file no se dispara**: si el prompt no es imperativo ("escribí X con contenido Y"), el modelo puede responder con texto en lugar de llamar la tool. Usar lenguaje imperativo directo: "Usá write_file para crear el archivo test.txt con el contenido: ..."
- **root_dir**: los paths relativos en tools como write_file se resuelven bajo `root_dir`. Si se necesita escribir en `/tmp/algo.txt`, o bien poner `root_dir="/tmp"` o usar path absoluto y `virtual_mode=False`.

## Modelos recomendados para DeepAgents (NVIDIA NIM)

| Modelo | Uso ideal |
|--------|-----------|
| `deepseek-ai/deepseek-v4-flash` | Agente general, rápido, buen tool calling |
| `meta/llama-3.3-70b-instruct` | Tool calling robusto, sin thinking overhead |
| `qwen/qwen3-coder-480b-a35b-instruct` | Agente de coding complejo |
| `nvidia/llama-3.1-nemotron-ultra-253b-v1` | Razonamiento profundo, tareas multi-step |

## Próximos spikes sugeridos

- Spike 002: agente con memoria (checkpointer) — retiene estado entre invocaciones
- Spike 003: multi-agente — orquestador + subagentes especializados (researcher, coder, reviewer)
- Spike 004: integración en flujo I+D+I real — agente que lee specs y genera código
