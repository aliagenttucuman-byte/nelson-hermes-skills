# [Nombre del Proyecto] — Project Charter v1.0
**Fecha:** [Mes Año] | **Metodología:** PMI / ISO 21502 / PRINCE2 / Agile
**Estado:** Borrador para revisión y firma de socios

---

## 1. Contexto y Oportunidad de Negocio

[2-3 párrafos: problema del mercado, por qué ahora, diferencial competitivo]

### Diferencial competitivo

| Competidor | Propuesta | Precio referencial | Nuestro diferencial |
|-----------|-----------|:-----------------:|-------------------|
| [Competidor 1] | ... | USD ... | ... |
| **[Nombre]** | **...** | **TBD** | **...** |

---

## 2. Mandato del Proyecto

**Nombre del proyecto:** [Nombre]
**CEO:** Nelson Acosta — Tecnología, I+D+I
**COO:** [Socio] — [Dominio]
**Equipo técnico:** Julián (Backend / IA), Mercedes (Frontend / UX), [+ roles]

### Hipótesis de valor
> CREEMOS QUE [hipótesis]
> RESULTARÁ EN [output concreto y medible]
> CRITERIOS DE ACEPTACIÓN:
> - [criterio 1]
> - [criterio 2]
> - [criterio 3]

---

## 3. Alcance del MVP

### Entregables incluidos

| # | Módulo | Descripción | Responsable |
|---|--------|-------------|------------|
| 1 | **[Módulo 1]** | ... | ... |
| 2 | **[Módulo 2]** | ... | ... |

### Fuera de alcance — MVP
- [item 1]
- [item 2]

---

## 4. Equipo y Roles — RACI

### Estructura del equipo

| Persona | Rol en la empresa | Rol en [Proyecto] | Dedicación MVP |
|---------|------------------|----------------|:---:|
| Nelson | CEO | Tech Lead + PM técnico | 60% |
| [Socio] | COO | Domain Expert + Red comercial | 40% |
| Julián | Dev Backend | Backend + IA | 80% |
| Mercedes | Dev Frontend | Frontend + UX | 80% |
| [5to] | [Rol] | [Especialidad] | 100% |

### Matriz RACI por dominio

| Dominio | Nelson | [Socio] | Julián | Mercedes | [5to] |
|---------|:---:|:---:|:---:|:---:|:---:|
| Decisiones estratégicas | **R/A** | **R/A** | I | I | I |
| Arquitectura | **R/A** | C | C | C | C |
| Backend / APIs | C | I | **R/A** | C | I |
| Frontend | C | C | C | **R/A** | I |
| [Dominio específico] | C | **R/A** | I | I | C |
| Acuerdos comerciales | **R/A** | **R/A** | I | I | I |

---

## 5. Cronograma — [N] Meses

| Mes | Foco | Hitos clave |
|-----|------|------------|
| Mes 1 | Fundación + Spike técnico | ... |
| Mes 2 | MVP Backend | ... |
| Mes 3 | MVP Frontend + Integración | ... |
| Mes 4 | Validación + Demo cliente | ... |

### Hitos de gobierno (PMI)

| Hito | Descripción | Mes | Owner | Evidencia mínima |
|------|-------------|:---:|-------|-----------------|
| **H0 — Mandato** | Charter firmado | 1 | Nelson + [Socio] | Este documento firmado |
| **H1 — Inicio aprobado** | Entorno técnico listo, datos de prueba disponibles | 1 | [Owner] | ... |
| **H2 — Spike validado** | Técnica central validada con datos reales | 1-2 | Nelson | Métricas documentadas |
| **H3 — Backend MVP** | APIs funcionales | 2-3 | Julián | Tests passing |
| **H4 — Frontend MVP** | UI completa integrada | 3 | Mercedes | Demo en staging |
| **H5 — Demo interna** | [Socio] valida UX y precisión del dominio | 3-4 | Nelson + [Socio] | Feedback documentado |
| **H6 — Versión 1.0** | Producto presentable a primer cliente | 4 | Nelson + [Socio] | Reunión con cliente |

---

## 6. Presupuesto Referencial — MVP [N] Meses

| Categoría | Costo/mes | [N] meses | Notas |
|-----------|:---------:|:-------:|-------|
| Servidor / GPU (ai-server propio) | USD 0 | USD 0 | Infraestructura existente |
| LLM API | ~USD 80 | ~USD [N*80] | Según volumen |
| Almacenamiento | ~USD 20 | ~USD [N*20] | |
| Herramientas | ~USD 30 | ~USD [N*30] | |
| **Total operativo** | **~USD 130** | **~USD [total]** | |

**Inversión inicial:** ~USD [X]
**Costo total MVP estimado:** ~USD [total] (el grueso es sweat equity del equipo)

---

## 7. Riesgos

| # | Riesgo | Prob | Impacto | Respuesta |
|---|--------|:----:|:-------:|-----------|
| R1 | [Riesgo técnico principal] | Media | Crítico | ... |
| R2 | [Riesgo de datos/insumos] | Media | Alto | ... |
| R3 | [Riesgo de equipo] | Media | Alto | ... |
| R4 | [Riesgo comercial] | Baja | Alto | ... |
| R5 | Scope creep | Alta | Medio | Control formal de cambios desde H0; backlog priorizado conjuntamente |

---

## 8. Estructura Societaria

| Parte | Aporte | Participación |
|-------|--------|:---:|
| **[Socio] (COO)** | Dominio, red de clientes, validación campo | **55%** |
| **Nelson + Equipo I+D+I (CEO)** | Tecnología completa, desarrollo, IA, infraestructura | **45%** |

- **Fase MVP:** sweat equity, sin aportes monetarios
- **Formalización:** al primer cliente pago → SAS
- **Decisiones estratégicas:** consenso de ambas partes
- **Punto de revisión:** cierre de H5

### Proyección financiera (post-MVP)

| Escenario | Clientes/año | Precio/año | Ingreso bruto anual |
|-----------|:-----------:|:----------:|:------------------:|
| Conservador | 5 | USD [X] | USD [5X] |
| Base | 15 | USD [X] | USD [15X] |
| Optimista | 40 | USD [X] | USD [40X] |

---

## 9. KPIs de Éxito

| KPI | Meta MVP | Meta Producto |
|-----|:-------:|:------------:|
| [KPI técnico 1] | [valor] | [valor] |
| [KPI técnico 2] | [valor] | [valor] |
| NPS cliente piloto | ≥7 | ≥8 |

---

## 10. Próximos Pasos Inmediatos

| # | Acción | Responsable | Plazo |
|---|--------|------------|-------|
| 1 | Revisar y firmar este charter | Nelson + [Socio] | Semana 1 |
| 2 | [Acción de insumos / datos] | [Socio] | Semana 1 |
| 3 | Spike técnico | Nelson | Semana 1-2 |
| 4 | Reunión de alineación post-spike | Nelson + [Socio] | Semana 2 |

---

*Metodología: PMI / ISO 21502 / PRINCE2 / Agile-Scrum — v1.0*

---
**Firmas:**

Nelson Acosta — CEO __________________ Fecha: ___________

[Socio] — COO _______________________ Fecha: ___________
