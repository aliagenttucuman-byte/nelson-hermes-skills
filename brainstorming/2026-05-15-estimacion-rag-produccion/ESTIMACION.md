# ESTIMACIÓN — RAG MinIO (Docs RPA) a Producción Cloud

> Fecha: 2026-05-15
> Autor: JARVIS (para Nelson Acosta)
> Aprobado por: [Tony] — [PENDIENTE]
> Cliente: [POR DEFINIR — PoC / interno / cliente externo]
> Tipo: MVP Producción (llevar PoC existente a cloud)

---

## 1. Resumen Ejecutivo

| Concepto | Monto |
|----------|-------|
| Desarrollo one-time | **$21.600 a $30.000** (según paquete) |
| Suscripción mensual | **$1.000 a $1.500/mes** (según paquete + LLM) |
| Inversión primeros 3 meses | **$24.600 a $34.500** |
| Break-even estimado | Mes 4-6 |

---

## 2. Paquetes de Producción — Estándar Equipo Nelson

> **Regla:** Todo RAG que salga de PoC a producción se cotiza con uno de estos 3 paquetes. No negociamos funcionalidad individual, solo el paquete.

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
| **Total** | | **480h × $30/h + 40h × $40/h = $16.000** |

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

## 3. Comparativa de Paquetes

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

---

## 4. Infraestructura Cloud — Costo Mensual

### Escenario elegido: **M** (100 usuarios, 500 consultas/día)

| Ítem | Proveedor | Costo/mes |
|------|-----------|-----------|
| VM 8 vCPU, 32 GB RAM | Azure (B8ms) | $180 |
| Storage SSD 200 GB | Azure Managed Disk | $25 |
| Network / transferencia | Azure | $30 |
| Backup / snapshots | Azure | $20 |
| Container Registry | Azure ACR | $15 |
| **Subtotal infra** | — | **$270** |

### Comparativa de providers

| Provider | Costo estimado/mes | Recomendación |
|----------|-------------------|---------------|
| **Azure** | **$270** | ✅ Si el cliente usa M365 / entorno Microsoft |
| AWS | $290 | General purpose, más servicios |
| GCP | $240 | Más barato en compute, bueno para startups |

> **Nota:** Con créditos de startup (Azure $5K-150K, AWS $5K-100K, GCP $2K-200K), los primeros 6-18 meses pueden salir **$0** en infra.

---

## 5. LLM — Costo Mensual

| Modelo | Tokens/mes | Essential | Professional | Enterprise |
|--------|-----------|-----------|--------------|------------|
| gpt-5.4-nano | ~15M | $6 | $6 | $6 |
| Claude Haiku | ~15M | — | $300 | $300 |
| Claude Sonnet | ~15M | — | — | $800-1.500 |

> **Recomendación:** Arrancar con gpt-5.4-nano. Escalar según necesidad del cliente.

---

## 6. Suscripción Mensual por Paquete

| Paquete | Infra+20% | LLM (nano) | Soporte | Mejoras | **Total/mes** |
|---------|-----------|------------|---------|---------|---------------|
| Essential | $325 | $6 | $500 | $200 | **$1.000** |
| Professional | $325 | $6 | $600 | $300 | **$1.200** |
| Enterprise | $325 | $6 | $800 | $400 | **$1.500** |

> Si el cliente elige Claude Haiku, sumar $300/mes. Sonnet: sumar $800-1.500/mes.

---

## 7. Plan de Pagos Sugerido

| Hito | Entregable | % | Essential | Professional | Enterprise |
|------|-----------|---|-----------|--------------|------------|
| 1 | Kickoff + spec aprobada | 30% | $6.480 | $7.920 | $9.000 |
| 2 | Staging funcional en cloud | 40% | $8.640 | $10.560 | $12.000 |
| 3 | Deploy producción + entrega | 30% | $6.480 | $7.920 | $9.000 |
| Recurrente | Suscripción mensual | — | $1.000 | $1.200 | $1.500 |

---

## 8. Notas para Pablo

> "Tenemos el RAG funcionando como PoC. Ofrecemos 3 paquetes según lo que necesite el cliente. Essential para arrancar rápido, Professional para corporativos que necesitan control y analytics, Enterprise para grandes organizaciones. El software es suyo, sin licencias. Paga desarrollo una vez y suscripción mensual predecible."

**Ventajas para vender:**
1. **PoC ya hecho:** El cliente puede verlo funcionar hoy.
2. **3 opciones claras:** No negociamos funcionalidad individual.
3. **Sin vendor lock-in:** Código open source, el cliente puede migrar cuando quiera.
4. **Suscripción predecible:** Sabe cuánto paga mes a mes.
5. **Escalable:** Empieza con Essential y sube cuando crece.
6. **Créditos cloud:** Los primeros meses pueden salir $0 en infra.

---

## 9. Supuestos y Riesgos

| Supuesto | Valor asumido | Impacto si cambia |
|----------|---------------|-------------------|
| Usuarios finales | 100 | Si son 500+, pasar a infra L (+$100/mes) |
| Consultas/día | 500 | Si son 2.000+, re-estimar VM más grande |
| Documentos indexados | ~50 PDFs, ~500 MB | Si son 1.000+ docs o 10GB+, agregar storage |
| Cloud provider | Azure | Cambiar si cliente usa AWS/GCP (±$30/mes) |
| Frontend actual | Streamlit básico | Si necesita React desde cero: +$1.200 (40h) |
| Integraciones externas | Ninguna | SAP, Salesforce, API terceros = +$3.000-8.000 |
| Compliance | Básico | GDPR, ISO 27001, on-prem = +$5.000-15.000 |

---

## 10. Aprobación

| Rol | Nombre | Fecha | Estado |
|-----|--------|-------|--------|
| Técnico | Tony Acosta | — | [PENDIENTE] |
| Comercial | Pablo | — | [PENDIENTE] |
| Cliente | [POR DEFINIR] | — | [PENDIENTE] |

---

**NO compartir con el cliente hasta aprobación de Tony y Pablo.**
