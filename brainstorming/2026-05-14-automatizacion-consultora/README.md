# Automatización de la Consultora — Plan n8n

**Fecha:** 2026-05-14
**Autor:** Equipo Nelson (Tony/JARVIS)
**Estado:** Planificación — pendiente implementación

---

## Objetivo

Transformar la consultora en una **máquina de automatización** donde los procesos repetitivos corren solos y el equipo humano (Tony + asesores) se enfoca en decisiones estratégicas.

**Principio:** Si una tarea se repite más de 2 veces por semana, debe estar automatizada.

---

## Workflows Prioritarios

### 1. Onboarding de Nuevo Proyecto (Alta Prioridad)

**Trigger:** Tony dice "empezamos proyecto X" o se recibe un email con subject "[NUEVO PROYECTO]"

**Acciones:**
1. Crear carpeta en `~/brainstorming/YYYY-MM-DD-nombre-proyecto/`
2. Generar `README.md` con template estándar
3. Crear repo en GitHub (si aplica)
4. Generar scaffold backend+frontend con `nelson-project-bootstrap`
5. Enviar confirmación a Tony por WhatsApp: "Proyecto X creado. Estructura lista en [path]. Repo: [url]"
6. Si es proyecto de cliente, notificar a Gino (gestión) para seguimiento

**Tiempo ahorrado:** ~30 min por proyecto
**Frecuencia:** 2-4 proyectos por mes

---

### 2. Reporte Semanal Automático (Alta Prioridad)

**Trigger:** Todos los lunes a las 9:00 AM (America/Argentina)

**Acciones:**
1. Revisar commits de la semana en repos del equipo
2. Contar tareas completadas (checklist de skills)
3. Revisar estado de servicios (RAGs, n8n, Ollama)
4. Generar resumen en audio (TTS) o texto breve
5. Enviar a Pablo por WhatsApp: "Reporte semanal: X commits, Y proyectos activos, todos los servicios OK"

**Tiempo ahorrado:** ~45 min por semana
**Frecuencia:** Semanal

---

### 3. Monitoreo de Servicios + Alerta (Media-Alta)

**Trigger:** Cada 5 minutos (ya implementado como cronjob)

**Acciones actuales:**
1. Revisar /health de cada RAG
2. Si está caído: reiniciar contenedor
3. Si sigue caído: enviar alerta a Tony

**Mejoras con n8n:**
- Dashboard visual con estado de todos los servicios
- Historial de uptime/downtime
- Alerta escalonada: 1er fallo → reinicio automático, 2do fallo → alerta Tony, 3er fallo → alerta Pablo
- Métricas: tiempo medio de recuperación (MTTR)

**Tiempo ahorrado:** ~0 (ya automatizado) pero mejora visibilidad

---

### 4. Nuevo Lead/Prospecto (Media)

**Trigger:** Formulario web, email a contacto@consultora.com, o mensaje de LinkedIn

**Acciones:**
1. Extraer datos: nombre, empresa, necesidad, presupuesto estimado
2. Guardar en Airtable/Notion (CRM)
3. Notificar a Luigi (economía/negocios) por WhatsApp
4. Si presupuesto > umbral, notificar también a Pablo
5. Enviar auto-reply al prospecto: "Gracias por contactarnos. Un representante se comunicará en 24hs"

**Tiempo ahorrado:** ~15 min por lead
**Frecuencia:** Variable

---

### 5. Backup Automático de Skills y Memoria (Media)

**Trigger:** Todos los sábados a las 2:00 AM

**Acciones:**
1. Ejecutar `sync-to-repo.sh`
2. Ejecutar `git push`
3. Si push falla, reintentar con `gh auth login` o notificar a Tony
4. Confirmar backup exitoso

**Tiempo ahorrado:** ~10 min por semana
**Frecuencia:** Semanal

---

### 6. Recolección de Tech News (Media-Baja)

**Trigger:** Todos los días a las 9:00 AM y 6:00 PM (America/Argentina)

**Acciones:**
1. Scrapear fuentes de novedades IA (ya implementado como cronjob `ai-news-aggregator`)
2. Generar resumen en audio con TTS
3. Enviar a Tony por WhatsApp

**Estado:** ✅ Ya implementado

---

### 7. Facturación/Recordatorio de Pagos (Baja — delegar a Luigi)

**Trigger:** 5 días antes del vencimiento de cada factura

**Acciones:**
1. Revisar Airtable/Notion de facturación
2. Enviar recordatorio amable al cliente
3. Si vence sin pago, escalar a Luigi y Pablo

**Nota:** Esto es más de Luigi, pero n8n puede automatizar los recordatorios.

---

## Dashboard de n8n

Panel central donde Tony puede ver:
- Estado de todos los servicios (RAGs, Ollama, n8n)
- Proyectos activos y su progreso
- Leads nuevos del mes
- Commits de la semana por equipo
- Alertas pendientes

---

## Roadmap de Implementación

| Fase | Workflows | Esfuerzo | Impacto |
|------|-----------|----------|---------|
| **Fase 1** (esta semana) | Monitoreo + Reporte semanal | 2-3h | Alto |
| **Fase 2** (próxima semana) | Onboarding proyecto + Backup auto | 3-4h | Alto |
| **Fase 3** (próximo mes) | Leads + Facturación + Dashboard | 5-6h | Medio |

---

## Credenciales n8n
- **URL:** http://localhost:5678
- **Email:** aliagenttucuman@gmail.com
- **Password:** Aliagent1234

---

## Notas

- Cada workflow debe tener un **nombre enterprise** (ej: "Project Onboarding Pipeline", no "crear proyecto nuevo")
- Todo workflow debe documentarse con: trigger, acciones, fallback, quien lo aprobó
- Antes de implementar cada workflow, validar con Tony
