# Post-Mortem: <nombre corto del incidente>

> **Servicio:** <ej: ForestAI backend>
> **Severidad:** <Sev-1 / Sev-2>
> **Fecha del incidente:** <YYYY-MM-DD HH:MM UTC>
> **Duración total:** <X horas Y minutos>
> **Owner del post-mortem:** <nombre>
> **Fecha de este doc:** <YYYY-MM-DD, dentro de las 24h del cierre>

## Resumen ejecutivo (3 líneas)

Una oración: qué pasó.
Una oración: impacto en usuarios.
Una oración: cómo se resolvió.

## Timeline (UTC)

| Hora | Evento | Quién |
|------|--------|-------|
| HH:MM | Primera señal de alarma (alerta externa, primer reporte) | |
| HH:MM | Acknowledged by | |
| HH:MM | Sev declarada | |
| HH:MM | Escalamiento a Diego | |
| HH:MM | Causa raíz identificada | |
| HH:MM | Mitigación aplicada | |
| HH:MM | Servicio verificado funcional | |
| HH:MM | Incidente cerrado en canal | |
| HH:MM | Post-mortem iniciado | |

## Impacto

- **Usuarios afectados:** <cantidad, quiénes>
- **Funcionalidad caída:** <qué no andaba>
- **Downtime medido:** <X min entre HH:MM y HH:MM>
- **Pérdida estimada de datos:** <sí/no, alcance>
- **Clientes externos impactados:** <lista>
- **Ingresos o reputación afectados:** <estimación, aunque sea cualitativa>

## Causa raíz

**No es lo que pasó, es POR QUÉ pasó.** No "la DB se cayó". Sí "el job de limpieza a las 3am no tenía timeout y dejó 2000 locks abiertos, lo que hizo que PostGIS no pudiera escribir".

Si hubo múltiples causas encadenadas, listar la cadena completa: causa 1 → causa 2 → síntoma.

## Por qué no lo detectamos antes

- [ ] No había health check en ese path
- [ ] El monitoreo no cubría este caso
- [ ] Alguien sabía pero no lo reportó
- [ ] El umbral de alerta estaba mal calibrado
- [ ] Otro: <especificar>

## Lo que estuvo bien

Cosas que el equipo hizo bien durante el incidente. Esto es para reforzar lo que funciona:
- <ej: Diego respondió en 7 minutos>
- <ej: Teníamos backup verificado, restauró en 5 min>
- <ej: El playbook de RAG aceleró el diagnóstico>

## Lo que estuvo mal

Cosas concretas que salieron mal, sin eufemismos:
- <ej: Tardamos 40 min en darnos cuenta de que era la DB, no el backend>
- <ej: No había forma de rollback, hubo que patchear en caliente>
- <ej: El cliente se enteró del problema por nosotros en vez de al revés>

## Acciones correctivas (inmediatas, ≤7 días)

| # | Acción | Owner | Fecha límite | Estado |
|---|--------|-------|--------------|--------|
| 1 | <ej: Agregar health check en /api/health que verifique DB> | Diego | YYYY-MM-DD | Pendiente |
| 2 | <ej: Documentar procedimiento de rollback en runbook> | Ricky | YYYY-MM-DD | Pendiente |
| 3 | | | | |

## Acciones preventivas (sistémicas, ≤30 días)

Estas son las que evitan que el incidente se repita. Son las que más cuestan y las que más sirven.

| # | Acción | Owner | Fecha límite | Estado |
|---|--------|-------|--------------|--------|
| 1 | <ej: Mover job de limpieza a horario de baja concurrencia con timeout> | Diego | YYYY-MM-DD | Pendiente |
| 2 | <ej: Implementar circuit breaker en llamadas a Ollama> | Julián | YYYY-MM-DD | Pendiente |
| 3 | | | | |

## Lecciones aprendidas (1-3 bullets)

- <ej: Nuestros runbooks de ForestAI no contemplan fallos de DB, solo de app>
- <ej: Necesitamos un canal de comunicación con clientes para Sev-1>
- <ej: El on-call rotativo no estaba claro, Tony terminó siendo first responder por default>

## Links útiles

- Hilo del incidente en WhatsApp: <link>
- Logs relevantes: <path o link>
- Commits del fix: <SHAs>
- Docs actualizados: <links>
