# Anti-duplicación sobre sistemas existentes (Meta-Orchestrator)

Contexto detectado en sesión: el usuario corrigió explícitamente evitar "hacer las cosas 2 veces" al hablar de META-Agente.

## Síntoma de mala práctica
- Se propone un nuevo "OS", "blueprint" o "orchestrator" paralelo sin auditar capacidades actuales.

## Patrón correcto
1. Reusar base existente (loop, timeline, subtasks, routing, dashboard, memory).
2. Hacer GAP `actual vs objetivo` con evidencia concreta (endpoints, tablas, vistas).
3. Definir roadmap incremental (hardening por capas).
4. Medir progreso por reducción de gaps, no por cantidad de componentes nuevos.

## Plantilla de salida para Tony
- Qué ya está funcionando
- Qué falta exactamente
- Qué módulo se toca primero
- Qué no se va a rehacer

## Criterio de aceptación
Una propuesta queda aprobada sólo si demuestra que extiende el sistema actual y evita duplicación estructural.