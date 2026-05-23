# Pricing Modelo PoC → Producción — Desarrollo + Suscripción

> Fecha: 2026-05-15
> Autor: JARVIS (para Nelson Acosta / Equipo I+D+I)
> Audiencia: Pablo (negocios) + equipo comercial
> Estado: Borrador — pendiente validación de Nelson antes de compartir

---

## 1. Resumen Ejecutivo

Este documento define el modelo de negocio completo para Pruebas de Concepto (PoC) y proyectos productivos (MVP).

**Filosofía:**
- El **software** se entrega sin costo excesivo (no es el producto, es el medio)
- El **desarrollo** se cobra por hora trabajada ($30/hora)
- El **soporte + mantenimiento + infra** se cobra como suscripción mensual recurrente

---

## 2. Modelo de Negocio: 3 Componentes

| Componente | Cuándo se cobra | Base de cálculo |
|------------|-----------------|-----------------|
| **Desarrollo** | Una vez, al finalizar | $30/hora × personas × horas |
| **Software** | Incluido en desarrollo | Sin costo adicional (no se cobra como producto) |
| **Suscripción mensual** | Recurrente, mes a mes | Infra + soporte + mantenimiento + mejoras menores |

---

## 3. Fase 1: Prueba de Concepto (PoC)

**Objetivo:** Validar que la solución funciona con los documentos reales del cliente.

| Rubro | Detalle | Costo estimado |
|-------|---------|----------------|
| Equipo | 3 personas | — |
| Duración | 2-4 semanas (est. 80-160 horas por persona) | — |
| Rate | $30/hora de desarrollo | — |
| **Costo desarrollo PoC** | 3 personas × 120 horas × $30 | **~$10.800** |
| Infraestructura | Servidor local del equipo (ya existe) | **$0** |
| LLM | gpt-5.4-nano (muy barato) o Ollama local | **~$0-6** |
| **TOTAL PoC** | — | **~$10.800** (one-time) |

> Nota: El PoC corre en nuestro servidor. El cliente prueba sin costo de infra. Solo paga las horas de desarrollo.

---

## 4. Fase 2: MVP / Producción

**Objetivo:** Sistema en producción con infra cloud dedicada.

### 4a. Desarrollo MVP

| Rubro | Detalle | Costo estimado |
|-------|---------|----------------|
| Equipo | 5 personas | — |
| Duración | 4-8 semanas (est. 160-320 horas por persona) | — |
| Rate | $30/hora de desarrollo | — |
| **Costo desarrollo MVP** | 5 personas × 240 horas × $30 | **~$36.000** |

### 4b. Suscripción Mensual Recurrente

| Concepto | Escenario S | Escenario M | Escenario L |
|----------|-------------|-------------|-------------|
| Usuarios | ~10 | ~100 | ~500 |
| Consultas/día | ~50 | ~500 | ~2.000 |
| Infra cloud | ~$150 | ~$200 | ~$350 |
| LLM (nano/mini) | ~$6 | ~$50 | ~$300 |
| Soporte + mantenimiento | ~$500 | ~$800 | ~$1.500 |
| **Suscripción mensual** | **~$656** | **~$1.050** | **~$2.150** |

> Redondeo comercial: **$700 / $1.000 / $2.000 mensuales**

---

## 5. Comparativa: Qué le cobramos al cliente

| Concepto | Cobro | Frecuencia |
|----------|-------|------------|
| Horas de desarrollo (PoC o MVP) | $30/hora | One-time (al entregar) |
| Software en sí | $0 | — |
| Infraestructura cloud | Costo real + 20% | Mensual |
| Soporte y mantenimiento | Fee fijo | Mensual |
| Mejoras / nuevas features | $30/hora | Ad-hoc, por estimación |

---

## 6. Ejemplo Completo: Cliente que hace PoC + MVP

| Etapa | Qué paga | Monto |
|-------|----------|-------|
| PoC (3 pers. × 4 semanas) | Desarrollo | ~$10.800 |
| MVP (5 pers. × 6 semanas) | Desarrollo | ~$36.000 |
| Producción mes 1 | Suscripción (escenario M) | ~$1.050 |
| Producción mes 2 en adelante | Suscripción mensual | ~$1.050/mes |
| Mejoras puntuales | Horas adicionales × $30 | Variable |

**Inversión total primeros 3 meses:** ~$48.900 + $2.100 suscripción
**A partir de mes 4:** Solo suscripción mensual (~$1.050)

---

## 7. Volumetría para Cotizar

Datos que Pablo debe pedir en la primera reunión:

| # | Pregunta | Para qué sirve |
|---|----------|----------------|
| 1 | ¿Cuántos usuarios finales tendría? | Define escenario S/M/L |
| 2 | ¿Cuántas consultas por día estiman? | Define consumo de tokens |
| 3 | ¿Qué tipo de documentos? ¿Cuántos? ¿Tamaño? | Define storage + complejidad de parsing |
| 4 | ¿Necesita integración con sistemas existentes? | Define horas de desarrollo extra |
| 5 | ¿Tiene preferencia de cloud (Azure/AWS/GCP)? | Define costo de infra |
| 6 | ¿Qué tan crítico es el tiempo de respuesta? | Define si necesita modelo premium |

---

## 8. Comparativa Cloud (solo para infra de producción)

| Criterio | Azure | AWS | GCP |
|----------|-------|-----|-----|
| Precio compute | Medio | Medio-alto | Más barato |
| Integración Microsoft | ✅ Excelente | ⚠️ Media | ❌ Mala |
| Créditos startup | $5.000-150.000 | $5.000-100.000 | $2.000-200.000 |
| Latencia Argentina | Buena | Buena | Regular |
| Recomendación | Si el cliente usa M365 | General purpose | Si busca minimizar costo |

---

## 9. Notas para Pablo

> *"Hacemos el PoC en nuestro servidor sin costo de infra. El cliente paga solo las horas de desarrollo ($30/hora). Si avanza a producción, le entregamos el software sin costo de licencia y le armamos una suscripción mensual que cubre infra + soporte. El cliente paga por el valor que recibe (desarrollo + soporte), no por el software en sí."

**Ventajas para vender:**
1. **PoC accesible:** Paga solo horas de trabajo, no licencias.
2. **Software incluido:** No hay costo de licencia sorpresa.
3. **Suscripción predecible:** Sabe cuánto paga mes a mes.
4. **Escalable:** Crece con el cliente sin renegociar todo.
5. **Sin vendor lock-in:** El código es suyo, la infra es configurable.

---

## 10. Pendientes / Next Steps

- [ ] Nelson valida rate de $30/hora y estructura de equipos (3 PoC, 5 MVP)
- [ ] Definir si el rate varía según seniority (ej: líder $40, dev $30)
- [ ] Armar formulario de 6 preguntas para relevamiento con cliente
- [ ] Crear 1-slide resumen para Pablo (PPT o Canva)
- [ ] Definir SLA de soporte por tier de suscripción

---

**No compartir con Pablo hasta aprobación de Nelson.**
