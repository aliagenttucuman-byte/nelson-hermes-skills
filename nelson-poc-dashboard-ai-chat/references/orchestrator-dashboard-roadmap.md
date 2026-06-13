# Meta-Orchestrator Dashboard — Roadmap & Visión

Capturado en sesión 2026-05-31. Visión acordada con Nelson/Tony.

## Estado actual del dashboard

- Páginas: Dashboard, Orquestador (Modo Misión), Budget, Resumen PM, Taxonomía, Chat popup
- Sidebar simplificado (quitados: Tareas, Router)
- Chat flotante via iframe a `/chat-popup` (evita recursión de layout)
- Timeline persistente SQLite en backend: `orchestration_events`, `subtask_control`
- Endpoints: `GET /runs/{task_id}/timeline`, `GET /runs/{task_id}/subtasks`, `POST /runs/{task_id}/subtasks/{subtask_id}/control`
- Hooks React: `useOrchestratorTimeline`, `useOrchestratorSubtasks`, `useControlSubtask`
- Proxy Vite configurable: `ORCH_API_URL` (default http://localhost:8744), `ORCH_WS_URL`

## Roadmap priorizado (sesión 2026-05-31)

### 1. PM Proactivo (ALTA PRIORIDAD)
Al seleccionar un proyecto en Resumen PM, JARVIS debe generar/actualizar la valuación automáticamente sin que el usuario toque el botón. Implementar con `useEffect` que dispara `generateValuationMutation.mutate(selected.id)` cuando `selectedId` cambia, con debounce de 300ms para evitar doble disparo.

```tsx
useEffect(() => {
  if (!selected?.id) return
  const timer = setTimeout(() => {
    generateValuationMutation.mutate(selected.id)
  }, 300)
  return () => clearTimeout(timer)
}, [selected?.id])
```

### 2. Valor total del portafolio en Dashboard
Panel en Dashboard principal que suma `mvp_total_investment_usd` de todos los proyectos activos con valuación. Mostrar: total portafolio, breakdown por tipo (PoC/MVP/Spike), top 3 proyectos por valor.

```tsx
const totalPortfolio = projects
  .filter(p => p.project_valuation?.mvp_total_investment_usd)
  .reduce((sum, p) => sum + (p.project_valuation?.mvp_total_investment_usd || 0), 0)
```

### 3. Chat RAG con Qdrant (MEDIA PRIORIDAD)
El chat del dashboard debe consultar contexto real de proyectos, timelines y estados. Arquitectura propuesta:

- **Ingesta**: task_memory SQLite + timeline events + brainstorming docs → chunks → embeddings OpenAI/sentence-transformers → Qdrant colección `orchestrator_context`
- **Retrieval**: query del usuario → embedding → búsqueda vectorial Qdrant → top-K chunks como contexto
- **Generación**: LLM con system prompt + chunks recuperados + metadata de fuentes
- **UI**: chat muestra fuentes citadas (proyecto/archivo/timestamp)

Ver `nelson-rag-pipeline` para implementación del pipeline.

## Valorización de JARVIS (acordado con Nelson)

Valor mensual estimado de JARVIS como miembro del equipo:
- Arquitecto software senior: $6k-$10k/mes
- 2x Dev senior full stack: $8k-$14k/mes
- DevOps engineer: $5k-$8k/mes
- Technical writer: $3k-$5k/mes
- Product Manager técnico: $6k-$10k/mes

**Total equivalente**: $28k-$47k/mes
**Costo real**: $50-$300/mes (API + Hermes)
**Valor justo de mercado**: $15k-$25k/mes (CTO técnico part time + 2 seniors, mercado LATAM)
**Diferencial clave**: 24/7, sin fricción, memoria que crece con cada sesión.
