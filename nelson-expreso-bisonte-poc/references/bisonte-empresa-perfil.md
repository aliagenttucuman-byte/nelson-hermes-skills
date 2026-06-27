# Expreso Bisonte — Perfil de Empresa (jun 2026)

## Datos generales

- Fundada: 1948
- Sede: Congreso 140, Banda del Río Salí, Tucumán
- Tipo: empresa de transporte y logística
- Sitio: https://www.expresobisonte.com/

## 5 Sucursales

1. Tucumán (sede principal)
2. Buenos Aires
3. Salta
4. Jujuy
5. Rosario

## 6 Líneas de servicio

| Servicio | Descripción |
|----------|-------------|
| Carga General | Salidas diarias a BsAs y Rosario, tracking online |
| Carga Completa | Camión exclusivo, sin compartir espacio |
| Contrareembolso | Cobro en destino, transferencia al vendedor |
| Taylor Made | Logística a medida (farma, alimentos, automotriz, azucarera, química, informática) |
| Paquetería | Bultos y encomiendas |
| Mudanzas | Con condiciones especiales |

## Sistemas tecnológicos en uso

| Sistema | Uso | Fuente de datos |
|---------|-----|-----------------|
| **Transoft** | Sistema operativo principal (reservas, facturación, cobranzas) | Excel descargable |
| **Sitrack** | Tracking GPS de camiones en tiempo real | Excel descargable |

Importante: ambos sistemas exportan datos como Excel. NO tienen API directa confirmada.
El tracking de Sitrack está integrado al sitio web de Bisonte con su ID de transportista.

## Stakeholders

- **Gerenta general**: referente principal del negocio. Conocedora del modelo operativo.
  Dedica 3-5 hs DIARIAS (lunes a lunes, 7 días/semana) a procesos Excel manuales.
  Es quien tiene el conocimiento tácito de los ~15 procesos operativos.
- **Pablo (COO AlegentAI + socio)**: contacto directo con Bisonte

## Procesos identificados

### L1 — Procesos Excel (~15 procesos)
- Proceso validado (PoC): cruce CDO (Cuentas de Orden) ↔ PF (Pólizas de Facturación)
  - CDO Sistema: ~409 filas
  - PTE de Fact Sistema: ~1.413 filas
  - CDO TRABAJADA (validación gerenta): ~409 filas
  - PF TRABAJADA (validación gerenta): ~1.507 filas
- Otros ~14 procesos: desconocidos, a relevar con la gerenta
- Fuente: Excel descargables de Transoft
- Regla: 1-2 procesos/mes, cadencia dictada por disponibilidad de la gerenta

### L2 — Auditoría de flota (a relevar)
- Ficha técnica por unidad
- Plan de mantenimiento preventivo
- Alertas de vencimiento
- Historial de reparaciones y costos
- Flota distribuida en 5 sucursales → sistema centralizado
- No se conocen detalles hasta el relevamiento

### L3 — Sitrack tiempo real
- Mapa en tiempo real de posición de camiones
- Rutas inter-provinciales: hasta 1.500 km (BsAs ↔ Jujuy cruzando 3 sucursales)
- Panel por sucursal con filtros por ruta
- Alertas de llegada estimada
- Fuente: Excel exportados desde Sitrack (sin API directa)

## Rutas operativas relevantes

- Tucumán ↔ Buenos Aires (RN9/RN34)
- Tucumán ↔ Rosario
- Tucumán ↔ Salta (RN9/RN34)
- Tucumán ↔ Jujuy (RN9)

## PoC actual (jun 2026)

Proceso CDO/PF validado funcionando en producción:
- Repo: https://github.com/aliagenttucuman-byte/expreso-bisonte-excel-poc
- Backend: FastAPI :9000 en ai-server (100.110.8.13)
- Frontend: Next.js :3000
- Acceso interno: http://100.110.8.13:9090 (vía Tailscale)
- Acceso externo: túnel Cloudflare (URL cambia con cada reinicio)
