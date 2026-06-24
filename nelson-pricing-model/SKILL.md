---
name: nelson-pricing-model
description: "Fase de estimación de costos del flujo SDD Nelson. Genera ESTIMACION.md con costos reales de desarrollo, infra, LLM y suscripción mensual. Se ejecuta después de PLANEAR y antes de ANALIZAR."
version: 1.0.0
author: Equipo Nelson (Tony + JARVIS)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [pricing, estimation, sdd, workflow, nelson, business-model, poc, mvp]
    related_skills: [nelson-spec-driven-workflow, nelson-project-constitution, writing-plans, nelson-spec-analyzer]
---

# Nelson Pricing Model

Fase de estimación de costos del flujo **Nelson Spec-Driven Development**.

Genera el archivo `ESTIMACION.md` para un proyecto nuevo. Este documento define los costos reales antes de escribir código, permitiendo a Pablo (negocios) cotizar al cliente con números concretos.

**Regla de oro:** Sin ESTIMACION.md aprobada, no se implementa. Tony decide si los números son viables antes de gastar horas de desarrollo.

## Posición en el flujo SDD

```
FASE 1: CONSTITUCIÓN      → nelson-project-constitution
FASE 2: SPECIFICAR        → spec-driven-development
FASE 3: CLARIFICAR        → spec-driven-development (sub-fase)
FASE 4: PLANEAR           → writing-plans
FASE 5: ESTIMAR     ★   → nelson-pricing-model  ← AQUÍ
FASE 6: ANALIZAR          → nelson-spec-analyzer
FASE 7: TAREAS            → subagent-driven-development
FASE 8: CHECKLIST         → requesting-code-review
FASE 9: IMPLEMENTAR       → agentes en paralelo
```

## Modelo de Negocio: 3 Componentes

| Componente | Cuándo se cobra | Base de cálculo |
|------------|-----------------|-----------------|
| **Desarrollo** | One-time, al entregar | $30/hora × personas × horas |
| **Software** | Incluido en desarrollo | Sin costo adicional (no se cobra licencia) |
| **Suscripción mensual** | Recurrente, mes a mes | Infra + soporte + mantenimiento + mejoras menores |

## ¿Cuándo usar?

- Después de tener el PLAN.md (Fase 4) y antes de ANALIZAR (Fase 6)
- Siempre que Tony/Pablo necesiten cotizar al cliente
- Siempre que haya un cambio de scope (se re-estima)

## ¿Quién la genera?

**JARVIS** genera el documento. **Tony valida**. **Pablo lo usa para negociar con el cliente**.

## Datos de entrada requeridos

JARVIS necesita saber (viene del PLAN.md + preguntas a Tony):

| # | Dato | Fuente | Ejemplo |
|---|------|--------|---------|
| 1 | Tipo de proyecto | Tony | PoC / MVP / Feature |
| 2 | Personas del equipo | Plan técnico | 3 (PoC) / 5 (MVP) |
| 3 | Duración estimada | Plan técnico | 2-4 semanas |
| 4 | Usuarios finales esperados | Tony / cliente | 50 / 200 / 1.000 |
| 5 | Consultas por día estimadas | Tony / cliente | 100 / 500 / 2.000 |
| 6 | Tamaño y cantidad de documentos | Tony / cliente | 10 PDFs de 10 MB |
| 7 | Modelo LLM requerido | Plan técnico | gpt-5.4-nano / Claude Haiku / GPT-4o |
| 8 | Cloud preferido | Cliente | Azure / AWS / GCP |
| 9 | Integraciones externas | Plan técnico | SAP, Salesforce, API de terceros |
| 10 | Compliance / seguridad extra | Plan técnico | GDPR, ISO 27001, on-prem |

## Template ESTIMACION.md

```markdown
# ESTIMACIÓN — [Nombre del Proyecto]

> Fecha: YYYY-MM-DD
> Autor: JARVIS (para Nelson Acosta)
> Aprobado por: [Tony] — [SI/NO]
> Cliente: [Nombre o "Interno"]
> Tipo: [PoC / MVP / Feature]

---

## 1. Resumen Ejecutivo

| Concepto | Monto |
|----------|-------|
| Desarrollo (one-time) | $XX.XXX |
| Suscripción mensual (recurrente) | $X.XXX/mes |
| Inversión primeros 3 meses | $XX.XXX |
| Break-even estimado | Mes X |

---

## 2. Desarrollo — Costo One-Time

### 2a. Equipo y duración

| Rol | Personas | Horas/persona | Rate | Subtotal |
|-----|----------|---------------|------|----------|
| Arquitecto / Líder | 1 | 120 h | $30/h | $3.600 |
| Backend Dev | 2 | 240 h | $30/h | $14.400 |
| Frontend Dev | 1 | 240 h | $30/h | $7.200 |
| DevOps / QA | 1 | 120 h | $30/h | $3.600 |
| **Total desarrollo** | **5** | — | — | **$28.800** |

> Nota: Rate base $30/hora. Puede ajustarse según seniority (líder $40, dev $30).

### 2b. Software

| Ítem | Costo |
|-------|-------|
| Licencia de software propio | **$0** (incluido en desarrollo) |
| Librerías open source | **$0** |
| **Total software** | **$0** |

---

## 3. Infraestructura Cloud — Costo Mensual

### Escenario elegido: [S / M / L]

| Ítem | Proveedor | Costo/mes |
|------|-----------|-----------|
| VM (4-8 vCPU, 16-32 GB) | [Azure/AWS/GCP] | $XXX |
| Storage SSD (100 GB) | [Azure/AWS/GCP] | $XX |
| Network / transferencia | [Azure/AWS/GCP] | $XX |
| Backup / snapshots | [Azure/AWS/GCP] | $XX |
| **Subtotal infra** | — | **$XXX** |

### Comparativa de providers

| Provider | Costo estimado/mes | Recomendación |
|----------|-------------------|---------------|
| Azure | $XXX | ✅ Si el cliente usa M365 |
| AWS | $XXX | General purpose |
| GCP | $XXX | Más barato en compute |

---

## 4. LLM — Costo Mensual

| Modelo | Tokens/mes estimados | Costo/mes |
|--------|---------------------|-----------|
| [gpt-5.4-nano / Claude Haiku / GPT-4o] | XXM tokens | $XXX |

> Supuesto: [X] consultas/día × [Y] días × [Z] tokens/consulta = XXM tokens/mes

---

## 5. Suscripción Mensual Total

| Concepto | Costo/mes | Nota |
|----------|-----------|------|
| Infraestructura cloud | $XXX | Costo real + 20% |
| LLM (tokens) | $XXX | Según volumen real |
| Soporte + mantenimiento | $XXX | SLA, bugfixes |
| Mejoras menores incluidas | $XXX | Hasta X horas/mes |
| **Total suscripción** | **$X.XXX** | Facturación recurrente |

---

## 6. Comparativa: PoC vs MVP vs Producción

| Fase | Desarrollo | Suscripción | Total primeros 3 meses |
|------|------------|-------------|------------------------|
| PoC (2-4 sem) | $10.800 | $0 (infra local) | $10.800 |
| MVP (4-8 sem) | $36.000 | $1.000/mes | $39.000 |
| Producción | $0 (ya hecho) | $2.000/mes | $6.000 |

---

## 7. Plan de pagos sugerido

| Hitgo | Entregable | Monto | Fecha estimada |
|-------|-----------|-------|----------------|
| 1 (30%) | Kickoff + especificación aprobada | $X.XXX | Semana 1 |
| 2 (40%) | Demo funcional (staging) | $X.XXX | Semana [N] |
| 3 (30%) | Deploy a producción + entrega | $X.XXX | Semana [N+M] |
| Recurrente | Suscripción mensual | $X.XXX | Mes 1 en adelante |

---

## 8. Notas para Pablo

> "Hacemos el PoC en nuestro servidor sin costo de infra. El cliente paga solo las horas de desarrollo ($30/hora). Si avanza a producción, le entregamos el software sin costo de licencia y le armamos una suscripción mensual que cubre infra + soporte."

**Ventajas para vender:**
1. PoC accesible: paga solo horas, no licencias.
2. Software incluido: no hay costo de licencia sorpresa.
3. Suscripción predecible: sabe cuánto paga mes a mes.
4. Escalable: crece con el cliente sin renegociar todo.
5. Sin vendor lock-in: el código es suyo.

---

## 9. Supuestos y Riesgos

| Supuesto | Impacto si cambia |
|----------|-------------------|
| [X] usuarios / [Y] consultas/día | Re-estimar infra y LLM |
| Rate $30/hora | Ajustar si el equipo cambia |
| Cloud provider [Z] | Cambiar si el cliente lo requiere |
| Modelo LLM [W] | Re-estimar costo de tokens |
| Integraciones externas | Agregar horas de desarrollo |

---

## 10. Aprobación

| Rol | Nombre | Fecha | Estado |
|-----|--------|-------|--------|
| Técnico | Tony Acosta | — | [Pendiente] |
| Comercial | Pablo | — | [Pendiente] |
| Cliente | [Nombre] | — | [Pendiente] |

---

**NO compartir con el cliente hasta aprobación de Tony y Pablo.**
```

## Tarifas Base del Equipo

| Rol | Rate / hora | Nota |
|-----|-------------|------|
| Líder Técnico / Arquitecto | $40/h | Nelson, Beto |
| Senior Developer | $30/h | Ricky, Nico, Diego, Alma |
| Developer | $25/h | Agentes junior |

> Rate promedio ponderado para estimaciones: **$30/hora**

## Tablas de Referencia Rápida

### Equipo por tipo de proyecto

| Tipo | Personas | Duración | Horas totales | Costo dev |
|------|----------|----------|---------------|-----------|
| PoC | 3 | 2-4 sem | 360-720 h | $10.800-21.600 |
| MVP | 5 | 4-8 sem | 800-1.600 h | $24.000-48.000 |
| Feature mayor | 3 | 1-2 sem | 180-360 h | $5.400-10.800 |
| Feature menor | 1 | 2-3 días | 16-24 h | $480-720 |

### Infra cloud mensual

| Escenario | Usuarios | Consultas/día | Azure | AWS | GCP |
|-----------|----------|---------------|-------|-----|-----|
| S | ~10 | ~50 | $150 | $160 | $130 |
| M | ~100 | ~500 | $200 | $210 | $180 |
| L | ~500 | ~2.000 | $350 | $370 | $320 |

### LLM mensual (60k consultas/mes = 144M tokens)

| Modelo | Costo/mes |
|--------|-----------|
| gpt-5.4-nano | ~$6 |
| Claude Haiku / GPT-4o-mini | ~$300-500 |
| Claude Sonnet / GPT-4o | ~$500-2.000 |

### Suscripción mensual redondeada (comercial)

| Plan | Usuarios | Consultas/día | Precio/mes |
|------|----------|---------------|------------|
| Starter | Hasta 50 | Hasta 300 | $700 |
| Business | Hasta 200 | Hasta 1.000 | $1.000 |
| Enterprise | Hasta 1.000 | Hasta 5.000 | $2.000+ |

---

## Paquetes Estándar para RAG (PoC → Producción)

> **Regla del equipo:** Todo RAG que salga de PoC a producción se cotiza con uno de estos 3 paquetes. No negociamos funcionalidad individual, solo el paquete.
> **Actualizado:** 2026-05-15 por Nelson + JARVIS.

### Paquete ESSENTIAL — $21.600 dev + $1.000/mes

| Funcionalidad | Qué incluye | Esfuerzo |
|--------------|-------------|----------|
| Auth multi-usuario | Login, roles (admin/user/readonly), tenant separation | 40h |
| Gestión de documentos | Subir, borrar, re-indexar PDFs desde la UI | 60h |
| Rate limiting por usuario | Límite de consultas/hora, anti-abuso | 16h |
| Hardening backend | Tests unitarios + integración (80%), manejo de errores, logging | 120h |
| Seguridad base | JWT auth, CORS hardening, sanitización, secrets management | 60h |
| CI/CD + Deploy cloud | GitHub Actions, Docker optimizado, deploy automático, rollback | 80h |
| Observabilidad | Health checks, métricas básicas, logs centralizados | 40h |
| Migración de datos | Exportar Qdrant local → cloud, validación de integridad | 24h |
| Documentación | README, API docs, runbooks de operación | 40h |
| **Total** | | **480h × $30/h + 40h × $40/h = $16.000 + Líder $5.600 = $21.600** |

> **Para quién es:** Cliente que necesita RAG funcional en producción con seguridad base. Sin frills.

---

### Paquete PROFESSIONAL — $26.400 dev + $1.200/mes

> Incluye TODO lo de Essential más:

| Funcionalidad | Qué incluye | Esfuerzo extra |
|--------------|-------------|----------------|
| Historial de conversaciones | Guardar threads, buscar chats anteriores, continuar | 40h |
| Dashboard analytics | Consultas/día, temas más buscados, uso por usuario | 40h |
| Modo "solo docs oficiales" | Filtro por fuente: legal, RRHH, técnico, etc. | 24h |
| API pública REST | Para que otros sistemas del cliente consuman el RAG | 32h |
| Alertas y monitoreo | Notificar si falla el sistema, umbral de errores | 24h |
| Frontend profesional | Mejora del existente (responsive, UX, accesibilidad) | 80h |
| **Total extra** | | **240h × $30/h = $7.200** |

> **Total Professional = Essential $16.000 + Extra $7.200 + Líder 80h $3.200 = $26.400**
> **Para quién es:** Cliente corporativo que necesita visibilidad, control y conectar con otros sistemas.

---

### Paquete ENTERPRISE — $30.000 dev + $1.500/mes

> Incluye TODO lo de Professional más:

| Funcionalidad | Qué incluye | Esfuerzo extra |
|--------------|-------------|----------------|
| Feedback del usuario | 👍/👎 en cada respuesta, flag "respuesta incorrecta" | 20h |
| Exportar conversaciones | Descargar chat como PDF o enviar por email | 24h |
| Multi-idioma | Detectar idioma del usuario, responder en ese idioma | 20h |
| SLA prioritario | Soporte 4h respuesta, 24h resolución | — (incluido en suscripción) |
| Onboarding asistido | 2 sesiones de capacitación + documentación custom | 16h |
| **Total extra** | | **80h × $30/h = $2.400** |

> **Total Enterprise = Professional $26.400 + Extra $2.400 + Líder extra 40h $1.200 = $30.000**
> **Para quién es:** Cliente grande (500+ usuarios), multinacional, o con requisitos de compliance.

---

### Comparativa Rápida: Paquetes RAG

| | Essential | Professional | Enterprise |
|---|-----------|--------------|------------|
| **Desarrollo** | $21.600 | $26.400 | $30.000 |
| **Suscripción/mes** | $1.000 | $1.200 | $1.500 |
| **Duración** | 4 semanas | 5 semanas | 6 semanas |
| **Equipo** | 5 personas | 5 personas | 5 personas |
| Auth multi-usuario | ✅ | ✅ | ✅ |
| Gestión documentos | ✅ | ✅ | ✅ |
| Rate limiting | ✅ | ✅ | ✅ |
| CI/CD + cloud deploy | ✅ | ✅ | ✅ |
| Historial conversaciones | ❌ | ✅ | ✅ |
| Dashboard analytics | ❌ | ✅ | ✅ |
| API REST pública | ❌ | ✅ | ✅ |
| Alertas monitoreo | ❌ | ✅ | ✅ |
| Feedback usuario | ❌ | ❌ | ✅ |
| Exportar chats | ❌ | ❌ | ✅ |
| Multi-idioma | ❌ | ❌ | ✅ |
| SLA 4h | ❌ | ❌ | ✅ |

> **Nota:** Si el cliente necesita algo que no está en ningún paquete → Feature aparte cotizada por hora ($30/h).

## Flujo de Uso

### Paso 1: Tony describe el proyecto

```
Tony: "Necesitamos estimar el proyecto de RAG para YPF. Sería un MVP."
```

> **Si el proyecto es un RAG (PoC → Producción):** JARVIS carga directamente los 3 paquetes estándar del equipo (Essential / Professional / Enterprise) y pregunta a Tony cuál se ajusta mejor, en vez de estimar desde cero.

### Paso 2: JARVIS carga PLAN.md + hace preguntas

JARVIS lee el PLAN.md existente (Fase 4) y completa datos faltantes con preguntas a Tony:
- "¿Cuántos usuarios finales tendría?"
- "¿Hay integración con sistemas de YPF?"
- "¿Prefieren Azure por ser Microsoft shop?"

### Paso 3: JARVIS genera ESTIMACION.md

Completa el template con los datos recopilados.

### Paso 4: Tony revisa y aprueba

Tony lee los números, ajusta si es necesario, y dice "aprobado" o "ajustar X".

### Paso 5: Pablo recibe el documento

Pablo usa los números para negociar con el cliente. No comparte el documento completo, solo los precios finales por hitgo.

### Paso 6: Guardar en el proyecto

```
proyecto/
├── CONSTITUTION.md      ← Fase 1
├── specs/
│   ├── openapi.yaml     ← Fase 2
│   └── user-stories.md  ← Fase 2
├── PLAN.md              ← Fase 4
├── ESTIMACION.md  ★    ← Fase 5 (esta skill)
├── TASKS.md             ← Fase 7
├── backend/
├── frontend/
└── README.md
```

## Variantes

### Proyecto Interno (herramienta propia)
- No se cobra al cliente
- Estimación sirve para decidir si vale la pena el esfuerzo
- Suscripción = costo real de infra (sin margen)

### Proyecto con precio fijo
- Cliente paga un monto cerrado por el desarrollo
- La estimación sirve para saber si el precio fijo cubre costos + margen
- Riesgo: scope creep. Muy importante tener spec claro.

### Proyecto time & materials
- Cliente paga horas reales trabajadas
- Estimación sirve como guía, no como presupuesto cerrado
- Más flexible, pero requiere reporte de horas semanal

## Notas

- La estimación es una **guía**, no una promesa. El scope puede cambiar.
- Si el cliente pide cambios de scope, se re-estima.
- El rate de $30/hora es base. Puede negociarse para clientes grandes o proyectos largos.
- La suscripción mensual se factura por adelantado (primero del mes).
- Si el cliente no paga la suscripción, se suspende el servicio (no se borran datos).
- Los créditos de startup (Azure $5K-150K, AWS $5K-100K, GCP $2K-200K) pueden reducir drásticamente los costos de infra en los primeros meses.
