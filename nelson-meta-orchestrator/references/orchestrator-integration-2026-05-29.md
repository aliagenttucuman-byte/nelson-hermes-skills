# Integración y actualización del Orchestrator (2026-05-29)

## Contexto
Usuario pidió localizar la app `orchestrator` y actualizarla para vincular funcionalidades nuevas dentro del sistema existente.

## Descubrimiento operativo
- Backend real: `/home/server/nelson/meta-orchestrator`
- Dashboard real: `/home/server/nelson/orchestrator-dashboard`
- Servicio en producción: `127.0.0.1:8744` (systemd `nelson-meta-orchestrator.service`)
- Dependencias chequeadas OK:
  - task-memory `:8742`
  - agent-router `:8743`

## Cambio aplicado en código
Archivo editado: `nelson_orchestrator/executor.py`

### 1) Enriquecimiento de skills por categoría
Se extendió `CATEGORY_SKILLS` para incluir skills nuevas del backlog en BACKEND, RAG/AI, INFRA y EXTERNAL.

### 2) Inyección contextual por keyword
Se agregó `KEYWORD_SKILLS` para mapear términos del goal (ej: `firestore`, `pubsub`, `gcs`, `vllm`, `whatsapp`, `telegram`, `arduino`, `mqtt`, `nginx`, `orchestrator`) a skills específicas.

### 3) Prompt con skills combinadas
`_build_prompt()` ahora combina:
- skills base por categoría
- skills extras inferidas por keywords
- deduplicación preservando orden

## Verificación realizada
- `python3 -m py_compile .../executor.py` OK
- prueba de `_build_prompt()` confirmó skills nuevas inyectadas en prompts de sub-tareas

## Runbook sugerido para próximas sesiones
1. Confirmar rutas reales + puerto activo.
2. Probar `/health` en orchestrator + dependencias.
3. Al agregar skill nueva de dominio, reflejarla en `CATEGORY_SKILLS` y/o `KEYWORD_SKILLS`.
4. Validar compilación y muestra de prompt antes de reinicio.
5. Reiniciar servicio systemd y volver a verificar `/health`.

## Nota de diseño
Este aprendizaje se solapa parcialmente con `nelson-multi-agent-orchestrator` (orquestación por agentes) pero este archivo es específico de la app operativa `meta-orchestrator` y su wiring de skills en runtime.
