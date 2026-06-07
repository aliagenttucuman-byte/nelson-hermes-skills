# ADR-XXX: Estrategia de Multi-Tenancy para <nombre del proyecto>

> **Estado:** Propuesta | Aceptada | Deprecada | Superseded
> **Fecha:** YYYY-MM-DD
> **Decidido por:** Nelson + equipo
> **Servicio:** <ej: RAG chat-con-documentos, ForestAI backend, Excel Merger>

## Contexto

Cuál es la situación que fuerza esta decisión.

- ¿Cuántos tenants hay hoy? ¿Cuántos se esperan en 12-24 meses?
- ¿Qué tan sensibles son los datos de cada tenant? (financiero, salud, PII, público)
- ¿Hay regulación específica? (HIPAA, GDPR, ley de datos personales Argentina, etc.)
- ¿Los tenants comparten producto/UI o son customizaciones pesadas?
- ¿Cuál es la presión de costo? (¿se puede pagar N× DB o hay que maximizar densidad?)
- ¿Hay requisitos de SLA diferenciado por tenant?

Ejemplo: "Expreso Bisonte factura mensualmente en Excel y nos pidió un sistema automatizado. Hoy tenemos 1 cliente pero Pablo está negociando con 2 clientes más en el mismo vertical. Datos financieros sensibles, 5-15 tenants esperados en 24 meses."

## Opciones consideradas

### Opción A: DB separada

Resumen de pros/contras aplicados a este caso concreto.

### Opción B: Schema separado

Resumen de pros/contras aplicados a este caso concreto.

### Opción C: Row-level + RLS

Resumen de pros/contras aplicados a este caso concreto.

## Decisión

Qué estrategia se eligió y por qué. Una sola opción ganadora.

Ejemplo: "Opción C (row-level + RLS). Razón: 5-15 tenants esperados, mismo producto, datos sensibles pero no regulados por norma específica, equipo chico, costo importa. Aceptamos el riesgo de RLS mal configurado a cambio de velocidad de desarrollo y on/offboarding instantáneo."

## Consecuencias

Qué se vuelve más fácil y qué se vuelve más difícil con esta decisión.

- **Positivo:** onboarding de tenant nuevo = 0 infra nueva.
- **Positivo:** una sola migración, un solo backup, métricas agregadas.
- **Negativo:** RLS mal configurado = leak. Mitigación: tests de aislamiento en CI.
- **Negativo:** si Expreso Bisonte crece a millones de filas, va a empezar a molestar a los otros tenants. Plan: cuando un tenant supere 1M filas o 100GB, migrar a DB separada (es un script, no una reescritura).

## Plan de implementación

- [ ] Tabla `tenants` + columna `tenant_id` en tablas tenant-scoped
- [ ] RLS habilitada y forzada en cada tabla
- [ ] Middleware que setea `app.current_tenant_id` por request
- [ ] Tests de aislamiento (read/update/delete cross-tenant)
- [ ] Qdrant: índice en `tenant_id` + helper `require_tenant_filter()`
- [ ] Storage: prefijos por tenant
- [ ] Celery: tenant_id como argumento explícito
- [ ] CI: tests de aislamiento bloquean merge
- [ ] Onboarding script (`scripts/onboard_tenant.py`)
- [ ] Offboarding script (`scripts/offboard_tenant.py`)

## Trigger de re-evaluación

Cuándo revisamos esta decisión. Ejemplo: "Cuando lleguemos a 50 tenants, o cuando un tenant individual represente >30% de la carga, o cuando un cliente nos exija aislamiento físico por compliance."

## Discusión / Comentarios

(opcional)
