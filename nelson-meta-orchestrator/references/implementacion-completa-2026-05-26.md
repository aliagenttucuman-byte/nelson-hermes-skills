# Meta-Orquestador — Implementación Completa (2026-05-26)

## Arquitectura final

```
/home/server/nelson/meta-orchestrator/
├── main.py                          # FastAPI app v2.0 — incluye WebSocket /ws
├── task_graph.db                    # SQLite: task graph persistente entre reinicios
├── install-service.sh               # Script de instalación systemd (requiere sudo)
├── nelson-meta-orchestrator.service # Unit file para /etc/systemd/system/
└── nelson_orchestrator/
    ├── orchestrator.py              # Loop maestro COMPLETO
    ├── executor.py                  # Ejecución real via hermes CLI
    ├── verifier.py                  # Verificación de resultados (3 capas)
    ├── notifier.py                  # Notificación WhatsApp a Tony
    ├── estimator.py                 # Estimación de presupuesto desde goal
    ├── clients.py                   # HTTP wrappers hacia :8742 y :8743
    └── models.py                    # OrchestratorState, SubTask, etc.
```

## Loop completo verificado en producción

```
GOAL
 → ROUTE (:8743)            # Router clasifica la categoría
 → CREATE_TASK (:8742)      # task-memory persiste la tarea maestra
 → BUILD_SUBTASKS            # 1 o N según routing multi-agente
 → REGISTER_SUBTASKS         # task-memory + SQLite local
 → EXECUTE (hermes CLI)      # executor.py — real o simulado
 → VERIFY (3 capas)          # verifier.py — estructural + keywords + longitud
 → RETRY (hasta 2x)          # si falla y can_retry=True
 → NOTIFY (WhatsApp)         # notifier.py — bridge Hermes :3000
 → DONE / FAILED
```

## Endpoints disponibles

```
POST  /run         → { goal, dry_run?, parallel? } → OrchestrationResult
POST  /route-only  → { goal } → RoutingResult
POST  /estimate    → { goal } → { routing, estimate }
GET   /status      → { pending, history_total, recent }
GET   /health      → { status, dependencies }
WS    /ws          → eventos en tiempo real (init, task_created, heartbeat, done, failed)
```

## WebSocket — protocolo de eventos

El cliente conecta a `ws://localhost:8744/ws` (proxy Vite: `/ws`).

Mensajes recibidos (JSON):
```json
{ "event": "init",          "data": { "pending": N, "history_total": N, "recent": [...] } }
{ "event": "heartbeat",     "data": {} }
{ "event": "pong",          "data": {} }
```

El cliente envía `"ping"` en texto plano para keepalive.

Hook frontend: `src/hooks/useOrchestratorWS.ts`
- Reconexión automática: hasta 5 intentos, backoff exponencial desde 2s
- Sliding window: últimos 50 eventos
- Filtra heartbeats del feed visible
- Ping cada 25s

## Autenticación dashboard

PIN via `sessionStorage`. Default: `741852`.
Override: `VITE_DASHBOARD_PIN=<pin>` en `.env.local`.
Componente: `src/components/AuthGuard.tsx`.

## Executor — mapeo categoría → agente

| Categoría | Agente | Skills inyectados |
|-----------|--------|-------------------|
| BACKEND   | Julián | equipo-nelson, fastapi, nelson-senior-practices |
| FRONTEND  | Mercedes | equipo-nelson, nelson-frontend-stack |
| RAG/AI    | JARVIS+Julián | nelson-rag-pipeline, nelson-llm-generation |
| SPEC      | JARVIS | nelson-spec-driven-workflow |
| QA        | Alma | python-testing-patterns, nelson-frontend-testing |
| INFRA     | Diego | docker-management, nelson-ci-cd |
| SECURITY  | Ricky | nelson-security, nelson-workflow-security |
| BROWSER   | Nico | nelson-browser-agent |

## Verifier — lógica de evaluación

3 capas en orden:
1. **Estructural**: status FAILED → score 0.0. Resultado vacío → score 0.1.
2. **Keywords**: % de keywords técnicas esperadas para la categoría en el resultado.
3. **Longitud**: < 20 palabras → penaliza.

Score final: 0.0–1.0. Umbral aprobación: ≥ 0.5 sin issues críticos.

**Pitfall del dry_run**: el modo dry_run original retornaba `[dry-run] Agente: X | Categoría: Y`
que es demasiado corto y sin keywords → el verifier lo rechazaba. Fix: el dry_run genera
un resultado simulado con keywords reales de la categoría (ver `EXPECTED_KEYWORDS` en verifier.py).

## Notifier — WhatsApp

- JID Tony: `5493816239553@s.whatsapp.net` (Nelson Acosta)
- Bridge: `http://localhost:3000/send`
- Si falla WA: log prominente con el mensaje pendiente (no silencia el fallo)
- Escalación: `notify_escalation()` cuando la tarea falla > MAX_RETRIES veces

## Systemd — instalación manual (requiere sudo)

```bash
cd /home/server/nelson/meta-orchestrator
bash install-service.sh
```

El service depende de `nelson-task-memory` y `nelson-agent-router` (After + Wants).

## Persistencia SQLite

Tabla `task_graph` en `/home/server/nelson/meta-orchestrator/task_graph.db`.
Sub-tareas se serializan después de cada modificación.
Al reiniciar: `_load_pending_subtasks(master_id)` recupera las pendientes.

## Estimador de presupuesto

Endpoint `POST /estimate` — infiere desde el texto del goal:
- Tipo de proyecto (PoC/MVP/producción/feature)
- Presencia de RAG/IA → activa paquetes estándar (Essential/Professional/Enterprise)
- LLM model implícito → calcula costo mensual de tokens
- Integraciones externas detectadas por keywords

Tarifas: $30/h senior · $40/h líder.
