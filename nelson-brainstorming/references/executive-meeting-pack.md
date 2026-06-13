# Executive Meeting Pack (stakeholders: Pablo/socios)

Use este patrón cuando Nelson pida “sumar documentación para reunión de hoy” sobre un brainstorming en curso.

## Objetivo
Generar un paquete mínimo, accionable y orientado a decisión en la **misma carpeta del proyecto**.

## Archivos recomendados

1. `estrategia-evangelizacion-automatizacion-operativa-v1.md`
   - diagnóstico ejecutivo
   - propuesta por carriles/fases
   - riesgos + mitigaciones
   - plan corto (1-2 semanas)

2. `briefing-reunion-<stakeholder>-hoy.md`
   - opening de 30 segundos
   - 5 mensajes clave
   - decisiones que se deben aprobar hoy
   - KPIs para seguimiento

3. `agenda-y-preguntas-reunion-<stakeholder>.md`
   - agenda por bloques de tiempo
   - preguntas críticas (owners, reglas, fuentes, excepciones)
   - cierre con acuerdos esperados

4. `minuta-decisiones-reunion-<stakeholder>-template.md`
   - tabla de decisiones
   - responsables + fecha compromiso
   - riesgos y mitigación
   - backlog inmediato + próximo checkpoint

## Pasos operativos

1. Crear/actualizar los 3-4 documentos en la carpeta del brainstorming actual.
2. Actualizar `README.md` del proyecto con los nuevos entregables.
3. Verificar que **todas las rutas internas** apunten a `~/brainstorming/...` (evitar paths legados de otros repos/proyectos).
4. Mantener versión corta para reunión (one-pager/briefing) además del análisis largo.

## Pitfalls

- Dejar rutas viejas (`/home/server/proyectos/...`) en resúmenes ejecutivos.
- Escribir solo documento largo sin guion de reunión ni minuta.
- No dejar explícito “qué se aprueba hoy” y “qué no se decide hoy”.
