# Template — Integrar OptiLLM en un proyecto FastAPI + React

## Objetivo

Reemplazar llamadas directas a OpenAI por llamadas al proxy OptiLLM local,
habilitando técnicas de optimización de inferencia sin cambiar el frontend.

## Pre-requisitos

- Proyecto existente con backend FastAPI y frontend React.
- Docker o Python 3.10+ en el servidor.
- API key de OpenAI (o provider alternativo) configurada.

---

## Paso 1 — Deploy de OptiLLM

### Opción A: Docker Compose (recomendado)

Crear `docker-compose.optillm.yml` en la raíz del proyecto:

```yaml
services:
  optillm:
    image: ghcr.io/algorithmicsuperintelligence/optillm:latest
    container_name: optillm-proxy
    ports:
      - "8080:8080"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      # Descomentar para usar LiteLLM como fallback:
      # - LITELLM_API_KEY=${LITELLM_API_KEY}
    restart: unless-stopped
```

Levantar:

```bash
docker compose -f docker-compose.optillm.yml up -d
```

Verificar:

```bash
curl http://localhost:8080/v1/models
```

### Opción B: venv local (para desarrollo)

```bash
cd /opt/optillm  # o la ruta que prefieran
python3 -m venv .venv
source .venv/bin/activate
pip install optillm
python -m optillm.optillm --port 8080
```

---

## Paso 2 — Configurar FastAPI para apuntar a OptiLLM

### 2.1 Actualizar settings / config

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Reemplazar URL directa de OpenAI por OptiLLM proxy
    OPENAI_BASE_URL: str = "http://localhost:8080/v1"
    OPENAI_API_KEY: str = "sk-dummy"  # OptiLLM ignora esto si usa provider externo
    OPENAI_MODEL: str = "gpt-4o-mini"  # Modelo base (sin prefijo de approach)
    
    # OptiLLM approach por defecto (puede sobreescribirse por request)
    OPTILLM_APPROACH: str | None = None  # ej: "moa", "mcts", "cot_reflection"

settings = Settings()
```

### 2.2 Crear cliente OpenAI con base_url custom

```python
# app/services/llm_client.py
import os
from openai import AsyncOpenAI
from app.core.config import settings

_llm_client: AsyncOpenAI | None = None

def get_llm_client() -> AsyncOpenAI:
    global _llm_client
    if _llm_client is None:
        _llm_client = AsyncOpenAI(
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENAI_API_KEY,
        )
    return _llm_client
```

### 2.3 Servicio de generación con approach configurable

```python
# app/services/generation.py
from openai import AsyncOpenAI
from app.services.llm_client import get_llm_client
from app.core.config import settings

async def generate_text(
    messages: list[dict],
    approach: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
) -> str:
    """
    Genera texto via OptiLLM proxy.
    
    Args:
        messages: Lista de mensajes OpenAI format.
        approach: Técnica OptiLLM (moa, mcts, bon, etc.).
                Si None, usa OPTILLM_APPROACH de config.
        model: Modelo base. Si approach se provee, se prefija automáticamente.
    """
    client = get_llm_client()
    
    # Resolver approach
    selected_approach = approach or settings.OPTILLM_APPROACH
    
    # Construir nombre de modelo (con prefijo si aplica)
    base_model = model or settings.OPENAI_MODEL
    if selected_approach:
        model_name = f"{selected_approach}-{base_model}"
    else:
        model_name = base_model
    
    response = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
    )
    
    return response.choices[0].message.content
```

### 2.4 Endpoint FastAPI de ejemplo

```python
# app/api/v1/chat.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.generation import generate_text

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    approach: str | None = None  # ej: "moa", "mcts", "cot_reflection"

class ChatResponse(BaseModel):
    response: str
    approach_used: str | None

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    messages = [{"role": "user", "content": req.message}]
    
    text = await generate_text(
        messages=messages,
        approach=req.approach,
    )
    
    return ChatResponse(
        response=text,
        approach_used=req.approach,
    )
```

---

## Paso 3 — Frontend React (sin cambios de lógica)

El frontend sigue llamando al endpoint de FastAPI. La única diferencia es
que el backend ahora soporta un parámetro `approach` opcional.

### 3.1 Hook de chat con approach seleccionable

```typescript
// src/hooks/useChat.ts
import { useState } from 'react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (text: string, approach?: string) => {
    setLoading(true);
    
    const res = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, approach }),
    });
    
    const data = await res.json();
    
    setMessages(prev => [
      ...prev,
      { role: 'user', content: text },
      { role: 'assistant', content: data.response },
    ]);
    
    setLoading(false);
  };

  return { messages, sendMessage, loading };
}
```

### 3.2 UI con selector de approach

```tsx
// src/components/Chat.tsx
import { useChat } from '../hooks/useChat';

const APPROACHES = [
  { value: '', label: 'Default (sin optimización)' },
  { value: 'moa', label: 'Mixture of Agents' },
  { value: 'mcts', label: 'Monte Carlo Tree Search' },
  { value: 'cot_reflection', label: 'CoT Reflection' },
  { value: 'bon', label: 'Best of N' },
  { value: 'plansearch', label: 'PlanSearch' },
];

export function Chat() {
  const { messages, sendMessage, loading } = useChat();
  const [input, setInput] = useState('');
  const [approach, setApproach] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage(input, approach || undefined);
    setInput('');
  };

  return (
    <div>
      <div>
        {messages.map((m, i) => (
          <div key={i} className={m.role}>
            {m.content}
          </div>
        ))}
      </div>
      
      <form onSubmit={handleSubmit}>
        <select
          value={approach}
          onChange={e => setApproach(e.target.value)}
        >
          {APPROACHES.map(a => (
            <option key={a.value} value={a.value}>{a.label}</option>
          ))}
        </select>
        
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Escribí tu mensaje..."
        />
        
        <button type="submit" disabled={loading}>
          {loading ? 'Pensando...' : 'Enviar'}
        </button>
      </form>
    </div>
  );
}
```

---

## Paso 4 — Validación

### 4.1 Test de conectividad

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-dummy" \
  -d '{
    "model": "moa-gpt-4o-mini",
    "messages": [{"role": "user", "content": "2+2=?"}]
  }'
```

### 4.2 Test desde FastAPI

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explicá el teorema de Pitágoras", "approach": "moa"}'
```

### 4.3 Benchmark rápido (comparar approachs)

```bash
python3 << 'EOF'
import asyncio
from app.services.generation import generate_text

async def benchmark():
    prompt = "Resolvé: Juan tiene 3 manzanas, le da 1 a María, ¼cuántas le quedan?"
    messages = [{"role": "user", "content": prompt}]
    
    for approach in [None, "moa", "mcts", "cot_reflection"]:
        print(f"\n=== Approach: {approach or 'default'} ===")
        try:
            resp = await generate_text(messages, approach=approach)
            print(resp[:200])
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(benchmark())
EOF
```

---

## Paso 5 — Producción

### Docker Compose completo (app + optillm)

```yaml
services:
  app:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_BASE_URL=http://optillm:8080/v1
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPTILLM_APPROACH=${OPTILLM_APPROACH:-moa}
    depends_on:
      - optillm

  optillm:
    image: ghcr.io/algorithmicsuperintelligence/optillm:latest
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "8080:8080"

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
```

---

## Checklist de integración

- [ ] OptiLLM corriendo en `localhost:8080` (o contenedor).
- [ ] `OPENAI_BASE_URL` apuntando al proxy.
- [ ] Endpoint `/api/v1/chat` acepta parámetro `approach`.
- [ ] Frontend muestra selector de approach.
- [ ] Test de benchmark ejecutado y comparado.
- [ ] Logs de OptiLLM revisados para confirmar que aplica la técnica.
- [ ] Variables de entorno documentadas en `.env.example`.

---

## Notas del equipo

- **Latencia**: MOA y MCTS generan múltiples llamadas → más lento. Usar
  para tareas de razonamiento complejo, no para chat casual.
- **Costo**: cada llamada a OptiLLM que use técnicas multi-llamada consume
  más tokens. Monitorear con W&B o similar.
- **Fallback**: si OptiLLM cae, el backend puede fallback a OpenAI directo
  cambiando `base_url` en runtime.
- **Modelos locales**: con nuestra GTX 1650 4GB, no usar inferencia local
  OptiLLM. Solo como proxy a OpenAI/Cerebras.
