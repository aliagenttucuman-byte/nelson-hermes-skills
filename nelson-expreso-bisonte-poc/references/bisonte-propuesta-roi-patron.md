# Expreso Bisonte — Patrón de Propuesta Comercial y ROI (jun 2026)

## Propuesta validada: Sistema Integral v3

Archivo: `/home/server/brainstorming/2026-06-13-bisonte-propuesta-comercial-v3/PROPUESTA-COMERCIAL-BISONTE-v3.md`
PDF final: `/home/server/brainstorming/2026-06-13-bisonte-propuesta-comercial-v3/PROPUESTA-COMERCIAL-BISONTE-v3.pdf`
También en repo: `nelson-brainstorming/2026-06-13-bisonte-propuesta-comercial/`

## 3 Líneas de trabajo confirmadas

| Línea | Descripción | Hs | USD |
|-------|-------------|-----|-----|
| L1 | Automatización procesos Excel (~15 procesos, 5 sucursales) | 1.000 | 30.000 |
| L2 | Auditoría de flota (multi-sucursal centralizado) | 600 | 18.000 |
| L3 | Sitrack tiempo real (mapa de camiones, 5 sedes) | 480 | 14.400 |
| **Total** | | **2.080** | **62.400** |

## Disclaimers obligatorios (siempre incluir)

- **Fuentes de datos**: Transoft y Sitrack solo como Excel descargable — sin integración API directa
- **Alcance L1**: los ~15 procesos se definen en el relevamiento, NO están comprometidos de antemano
- **Plazos**: dependen de disponibilidad de la referente de negocio (gerenta general)
- **L2 y L3**: impacto multi-sucursal a definir en relevamiento inicial

## Modalidades de contratación

**Opción A — Sistema Propietario** (recomendada para 3+ años)
- USD 62.400 total en fases
- 30% anticipo + 70% por entrega por fase
- Bisonte dueño del código al final
- Sin costos recurrentes salvo mantenimiento post-venta

**Opción B — SaaS**
- USD 5.200/mes
- Contrato mínimo 12 meses
- AlegentAI opera toda la infraestructura
- Actualizaciones incluidas

## Fórmula ROI con costo de oportunidad (gerenta general)

**Dato clave**: la gerenta dedica **3-5 hs DIARIAS, lunes a lunes** (7 días/semana) a procesos Excel manuales.

```python
dias_anio = 7 * 52  # 364 días
# Escenario base (3hs/día)
hs_base = 3 * 364   # 1.092 hs/año
# Escenario real (5hs/día)
hs_real = 5 * 364   # 1.820 hs/año

# Costo directo (operativo, USD 15/h)
costo_directo_3y_real = 1.820 * 15 * 3  # USD 81.900

# Costo de oportunidad (gerenta estratégica, USD 50/h)
costo_oportunidad_3y_real = 1.820 * 50 * 3  # USD 273.000

# Costo total de NO automatizar (3 años, escenario real)
# = USD 81.900 directo + USD 273.000 oportunidad
# = USD 354.900

# Con el sistema (Opción A): USD 62.400 única vez
# Ahorro neto 3 años: USD 354.900 - 62.400 = USD 292.500
# Retorno: 469% sobre la inversión
# Break-even: ~mes 6 (cuando el ahorro acumulado cubre la inversión)
```

**Argumento para la gerenta**: cada hora que dedica a Excel es una hora que no dedica a estrategia, clientes o decisiones que solo ella puede tomar.

## Reglas de alcance (NO hacer)

- NO comprometer procesos específicos de L2/L3 sin relevamiento previo
- NO mencionar dashboards si no los pidieron
- NO expandir alcance en propuesta sin validar con Nelson primero
- NO mencionar APIs de Transoft/Sitrack (no las tenemos confirmadas)

## Impacto multi-sucursal en presupuesto

L2 y L3 escalan con la cantidad de sucursales:
- Vista centralizada de flota de 5 sedes → +15% en L2
- Rutas inter-provinciales (hasta 1.500 km) en Sitrack → +20% en L3
- El costo NO se multiplica × 5 pero SÍ agrega complejidad de reporting y sincronización

## Patrón de scraping del sitio del cliente antes de armar propuesta

Antes de enviar propuesta a un cliente con presencia web:
1. `curl -s https://sitio-cliente.com -A "Mozilla/5.0"` → guardar HTML
2. Extraer links del nav principal (menú)
3. Scrapear cada sección de servicios
4. Identificar líneas de negocio que NO conocíamos
5. Actualizar el alcance de la propuesta antes de presentar

**Caso Bisonte**: el sitio reveló 6 líneas de servicio y 5 sucursales que cambiaron completamente el alcance de L2 y L3.

## Formato de propuesta PM Pablo

Usar formato estilo PM de Pablo Ruiz (COO):
- Documento en Markdown → PDF con WeasyPrint
- Header con logo/nombre empresa + "CONFIDENCIAL"
- Secciones: contexto → 3 líneas → modalidades → fases → ROI → disclaimers
- Tabla de inversión con totales claros
- Gráfico de ROI si es posible (o tabla de break-even)
- Pie de página: AlegentAI + contacto
