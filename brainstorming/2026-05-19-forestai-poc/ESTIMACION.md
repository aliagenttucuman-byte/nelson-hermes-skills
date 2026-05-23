# ESTIMACIÓN — ForestAI · PoC → Producción

> Fecha: 2026-05-20
> Autor: JARVIS (para Nelson Acosta)
> Aprobado por: Tony — PENDIENTE
> Cliente: A definir (forestales, gobierno, agro)
> Tipo: PoC → MVP → SaaS

---

## 1. Resumen Ejecutivo

| Concepto | Monto |
|----------|-------|
| Desarrollo PoC → Producción (one-time) | $28.000 |
| Suscripción mensual por cliente (recurrente) | $800 – $2.000/mes |
| Inversión primeros 3 meses | $28.000 + $2.400–$6.000 |
| Margen en desarrollo | ~37% |
| Margen en suscripción | ~68–80% |
| Break-even estimado | Mes 8–10 con 1 cliente Business |

---

## 2. Contexto: PoC ya completada

La PoC está funcionando en el servidor. Incluye:
- Upload y procesamiento de GeoTIFF con OBIA/watershed
- Detección de árboles, especie, biomasa, edad (tablas INTA)
- Frontend React con MapLibre — grilla + mapa + panel de detalle
- Integración WFS bosques nativos (MAyDS) y Sentinel-2 NDVI (CDSE)
- 5 análisis argentinos en DB con resultados reales

**Lo que falta para producción:**
1. Auth multi-usuario y multi-tenant
2. Hardening (tests, seguridad, manejo de errores)
3. CI/CD y deploy en cloud del cliente
4. Export de reportes en PDF
5. Dashboard analytics + observabilidad
6. Mejora de detección con DeepForest (modelo pre-entrenado RGB)
7. API REST pública para integraciones
8. Documentación operativa y runbooks

---

## 3. Desarrollo · Costo One-Time

### 3a. Equipo y duración

| Rol | Persona | Horas | Rate | Subtotal |
|-----|---------|-------|------|----------|
| Líder Técnico / Arquitecto | Tony | 140 h | $40/h | $5.600 |
| Backend Dev | Julián | 260 h | $30/h | $7.800 |
| Frontend Dev | Mercedes | 220 h | $30/h | $6.600 |
| DevOps / QA | Julián + Tony | 100 h | $30/h | $3.000 |
| Documentación | Todos | 50 h | $30/h | $1.500 |
| Gestión y PM | Tony | 40 h | $40/h | $1.600 |
| **TOTAL** | — | **810 h** | — | **$26.100** |

> **Precio al cliente: $28.000** (redondeo + buffer 7%)
> **Duración estimada: 6–7 semanas** (3 personas working in parallel)

### 3b. Tareas incluidas

| Módulo | Horas |
|--------|-------|
| Auth multi-usuario (JWT, roles admin/user, multi-tenant) | 80 h |
| Gestión de análisis desde UI (subir, borrar, re-indexar) | 40 h |
| Export PDF de reportes por análisis | 50 h |
| Hardening backend (tests 80%, manejo errores, logging) | 120 h |
| Seguridad (JWT hardening, CORS, secrets, sanitización) | 60 h |
| CI/CD + Docker optimizado + deploy cloud | 80 h |
| Observabilidad (health checks, métricas, alertas) | 40 h |
| Integración DeepForest (modelo pre-entrenado RGB) | 60 h |
| Dashboard analytics (consultas, uso por usuario) | 50 h |
| API REST pública documentada | 50 h |
| Migración datos PoC → cloud + validación | 30 h |
| Documentación + runbooks | 50 h |
| PM y coordinación | 50 h |
| **Total** | **810 h** |

### 3c. Software

| Ítem | Costo |
|------|-------|
| Código propio ForestAI (PoC base + producción) | **$0** (incluido en desarrollo) |
| DeepForest (modelo open source) | **$0** |
| Librerías open source (rasterio, OpenCV, MapLibre, etc.) | **$0** |
| **Total software** | **$0** |

---

## 4. Infraestructura Cloud · Costo Mensual

### Configuración Base (Starter)

| Ítem | Proveedor | Costo/mes |
|------|-----------|-----------|
| VM 4 vCPU / 16 GB RAM (backend + celery) | Azure/GCP/AWS | $120 |
| PostgreSQL + PostGIS managed 100 GB | Azure/GCP/AWS | $50 |
| Redis managed (Celery broker) | Azure/GCP/AWS | $15 |
| Storage S3-compatible para GeoTIFFs (500 GB) | Azure Blob / S3 | $25 |
| Network / egress | — | $20 |
| Backups automáticos | — | $10 |
| **Subtotal infra Starter** | — | **$240/mes** |

### Para Business (más usuarios, más análisis)

| Ítem | Costo/mes |
|------|-----------|
| VM 8 vCPU / 32 GB RAM | $200 |
| Storage 2 TB | $50 |
| Resto igual | $100 |
| **Subtotal infra Business** | **$350/mes** |

### Sentinel-2 / CDSE

| Volumen | Costo/mes |
|---------|-----------|
| < 1.000 consultas/mes | **$0** (free tier CDSE) |
| 1.000–10.000 consultas/mes | ~$50–100 |

---

## 5. Suscripción Mensual por Cliente

| Plan | Usuarios | Análisis/mes | Dev incluido | Precio/mes | Costo real | Margen |
|------|----------|--------------|-------------|------------|------------|--------|
| **Starter** | Hasta 5 | Hasta 100 | ✅ | **$800** | $240 | 70% |
| **Business** | Hasta 20 | Hasta 500 | ✅ | **$1.200** | $350 | 71% |
| **Enterprise** | Ilimitado | Ilimitado | ✅ + SLA 4h | **$2.000** | $500 | 75% |

> Nota: "Costo real" = solo infra + tokens CDSE. Sin soporte ni mantenimiento.
> Con soporte real incluido (~10h/mes): costo real $550–800, margen real ~40–55%.

### Incluido en todas las suscripciones

- Hosting y operación (infra, backups, monitoreo)
- Soporte técnico (SLA: 24h Starter / 8h Business / 4h Enterprise)
- Actualizaciones de seguridad y bugfixes
- Mejoras menores (hasta 8h/mes Starter, 15h Business, 20h Enterprise)
- Acceso a nuevas versiones del algoritmo de detección

---

## 6. Comparativa PoC vs MVP vs Producción

| Fase | Costo | Duración | Resultado |
|------|-------|----------|-----------|
| **PoC (hecha)** | Tiempo del equipo | 2 semanas | Demo funcional, 1 usuario |
| **MVP (= esta estimación)** | $28.000 | 6-7 semanas | Producción real, multi-tenant |
| **Mantenimiento año 1** | $9.600–24.000 | 12 meses | Operación + mejoras |

---

## 7. Modelo de Ingresos Proyectado

### Escenario conservador: 1 cliente Business en mes 3

| Mes | Ingresos | Costos acumulados | Saldo |
|-----|----------|-------------------|-------|
| 1-2 | $0 | $28.000 (dev) | -$28.000 |
| 3 | $1.200 | $350 (infra) | -$27.150 |
| 4-12 | $1.200/mes | $350/mes | +$7.650 al mes 12 |
| Break-even | — | — | **Mes 8** |

### Escenario realista: 2 clientes Business en mes 4

| Mes | Ingresos | Costos | Saldo |
|-----|----------|--------|-------|
| 1-3 | $0 | $28.000 | -$28.000 |
| 4-12 | $2.400/mes | $700/mes | +$7.400 al mes 12 |
| Break-even | — | — | **Mes 8** |

---

## 8. Modelo Alternativo: Cobro por Hectárea

Si el cliente prefiere no pagar desarrollo:

| Modelo | Precio | Costo para nosotros | Margen |
|--------|--------|---------------------|--------|
| Por análisis (por archivo subido) | $15–30/análisis | $0.50 infra | 97%+ |
| Por hectárea procesada | $0.50–1.50/ha | $0.01/ha | 99%+ |
| Por reporte exportado | $5–10/reporte | $0.10 | 98%+ |

> Este modelo escala mejor para clientes grandes (>10.000 ha).
> Recomendado como add-on sobre la suscripción base.

---

## 9. Plan de Pagos Sugerido (Desarrollo)

| Hito | Entregable | Monto | Fecha |
|------|-----------|-------|-------|
| 1 — 30% | Kickoff + spec técnica aprobada | $8.400 | Semana 1 |
| 2 — 40% | Demo funcional en staging (auth + análisis + export) | $11.200 | Semana 4-5 |
| 3 — 30% | Deploy en cloud del cliente + entrega + capacitación | $8.400 | Semana 6-7 |
| Recurrente | Suscripción mensual | $800–$2.000 | Mes 1 en adelante |

---

## 10. Ventajas Competitivas para Negociar

1. **PoC probada:** El cliente puede ver el sistema funcionando hoy. No es promesa.
2. **Sin licencias sorpresa:** El software es suyo. No paga royalties.
3. **Datos abiertos:** Usamos Sentinel-2 (ESA, gratis) y datos INTA — sin costo de datos satelitales en la mayoría de los casos.
4. **Stack abierto:** Python + FastAPI + React — cualquier dev puede mantenerlo. Sin vendor lock-in.
5. **Suscripción predecible:** Sabe exactamente cuánto paga mes a mes.
6. **Modelo de detección mejorable:** DeepForest + futuro NIR/LiDAR — el producto crece.
7. **Único en Argentina:** No hay competidor local con esta propuesta de valor.

---

## 11. Perfil de Cliente Objetivo

| Segmento | Dolor | Fit |
|----------|-------|-----|
| Empresas forestales (Arauco, MASISA, etc.) | Inventario manual caro y lento | ⭐⭐⭐⭐⭐ |
| Consultoras ambientales | Clientes piden NDVI y biomasa | ⭐⭐⭐⭐ |
| Proyectos de carbono | Deben demostrar stock de carbono anualmente | ⭐⭐⭐⭐⭐ |
| Gobiernos provinciales (Chaco, Misiones) | Ley de Bosques obliga monitoreo | ⭐⭐⭐⭐ |
| YPF Agro / Gasoductos (monitoreo franja vegetal) | Compliance ambiental | ⭐⭐⭐ |
| INTA / universidades | Investigación sin presupuesto | ⭐⭐ |

---

## 12. Supuestos y Riesgos

| Supuesto | Impacto si cambia |
|----------|-------------------|
| Rate $30/h junior, $40/h líder | Ajustar si equipo cambia |
| GeoTIFFs RGB (sin NIR) para v1 | Si cliente pide NIR: +60h dev |
| Cloud provider agnóstico | Sin impacto (Docker) |
| Sentinel-2 free tier suficiente | Si > 1.000 req/mes: +$50-100/mes |
| 1-2 clientes año 1 | Break-even sensible a velocidad de ventas |
| Tiempo estimado 6-7 semanas | Si hay scope creep: re-cotizar |

---

## 13. Aprobación

| Rol | Nombre | Estado |
|-----|--------|--------|
| Técnico | Tony Acosta | PENDIENTE |
| Comercial | Pablo | PENDIENTE |
| Cliente | — | — |

---

*NO compartir con el cliente hasta aprobación de Tony.*
*Generado por JARVIS — 2026-05-20*
