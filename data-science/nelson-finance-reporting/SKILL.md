---
name: nelson-finance-reporting
description: "Reporting financiero automatizado con Python y Polars. KPIs de aerolinea (CASK, RASK, Load Factor, Yield), dashboards Plotly/Dash, reportes PDF automaticos, pipelines desde Excel/SQL."
triggers:
  - reporte financiero
  - KPIs aerolinea
  - dashboard financiero
  - automatizar reportes
  - CASK RASK yield load factor
version: "1.0.0"
---

# nelson-finance-reporting

Skill de reporting financiero automatizado con Python y Polars para el equipo Nelson (contexto: LAN Chile).

---

### KPIs clave de aerolínea

| KPI | Definición | Fórmula |
|-----|-----------|---------|
| CASK | Cost per Available Seat Kilometer | costos_totales / (asientos_disponibles * km_volados) |
| RASK | Revenue per Available Seat Kilometer | ingresos_totales / (asientos_disponibles * km_volados) |
| Load Factor | Porcentaje de ocupación de la aeronave | pasajeros_reales / capacidad_maxima * 100 |
| Yield | Ingreso promedio por pasajero-km | ingresos_pasajeros / (pasajeros * km_volados) |
| EBITDAR | Earnings before interest, taxes, depreciation, amortization, aircraft rent | EBIT + D&A + renta_aeronaves |
| OTP | On-Time Performance — puntualidad operacional | vuelos_a_tiempo / total_vuelos * 100 |
| Revenue per Employee | Productividad por empleado | ingresos_totales / cantidad_empleados |

Cálculo de todos los KPIs con Polars expressions:

```python
import polars as pl

df_kpis = df.with_columns([
    # CASK
    (pl.col("costos_totales") / (pl.col("asientos") * pl.col("km"))).alias("CASK"),

    # RASK
    (pl.col("ingresos_totales") / (pl.col("asientos") * pl.col("km"))).alias("RASK"),

    # Load Factor (puede superar 100% por overbooking — NO filtrar)
    (pl.col("pasajeros_reales") / pl.col("capacidad_maxima") * 100).alias("load_factor"),

    # Yield
    (pl.col("ingresos_pasajeros") / (pl.col("pasajeros") * pl.col("km"))).alias("yield_"),

    # EBITDAR
    (pl.col("ebit") + pl.col("depreciacion") + pl.col("amortizacion") + pl.col("renta_aeronaves")).alias("EBITDAR"),

    # OTP
    (pl.col("vuelos_a_tiempo") / pl.col("total_vuelos") * 100).alias("OTP"),

    # Revenue per Employee
    (pl.col("ingresos_totales") / pl.col("cantidad_empleados")).alias("rev_per_employee"),
])
```

---

### Stack de reporting con Polars

| Librería | Uso |
|---------|-----|
| **Polars** | Cálculo de KPIs y agregaciones rápidas (librería principal) |
| **plotly** | Dashboards interactivos: pie, waterfall, bullet, heatmap, treemap |
| **Dash** | Dashboard web interactivo con filtros por ruta, mes, año |
| **WeasyPrint** | Generación de PDF desde templates HTML/Jinja2 |
| **openpyxl + XlsxWriter** | Excel con formatos condicionales y gráficos embebidos |
| **APScheduler** | Reportes automáticos programados (diario, semanal, mensual) |
| **Polars -> Excel** | `df.write_excel()` nativo desde Polars 0.19+ |

---

### Pipeline de reporte automático

```python
import polars as pl
import plotly.graph_objects as go
import plotly.express as px
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from apscheduler.schedulers.blocking import BlockingScheduler
import requests
from datetime import date

# ── 1. Carga desde Excel (sin pandas) ──────────────────────────────────────
df = pl.read_excel("reporte.xlsx", sheet_name="Datos")

# Asegurar tipos correctos
df = df.with_columns([
    pl.col("fecha").cast(pl.Date),
    pl.col("ingresos_totales").cast(pl.Decimal(scale=2)),
    pl.col("costos_totales").cast(pl.Decimal(scale=2)),
])

# ── 2. Cálculo de KPIs con Polars expressions ──────────────────────────────
df_kpis = df.with_columns([
    (pl.col("costos_totales") / (pl.col("asientos") * pl.col("km"))).alias("CASK"),
    (pl.col("ingresos_totales") / (pl.col("asientos") * pl.col("km"))).alias("RASK"),
    (pl.col("pasajeros_reales") / pl.col("capacidad_maxima") * 100).alias("load_factor"),
    (pl.col("ingresos_pasajeros") / (pl.col("pasajeros") * pl.col("km"))).alias("yield_"),
    (pl.col("vuelos_a_tiempo") / pl.col("total_vuelos") * 100).alias("OTP"),
])

# ── 3. Comparativo YoY y MoM ───────────────────────────────────────────────
# Year over Year: shift 1 año hacia adelante y hacer join
df_prev_year = df_kpis.with_columns(
    pl.col("fecha").dt.offset_by("1y").alias("fecha")
)
df_yoy = df_kpis.join(
    df_prev_year.select(["ruta", "fecha", "RASK", "CASK", "load_factor"]),
    on=["ruta", "fecha"],
    how="left",
    suffix="_prev_year"
).with_columns([
    ((pl.col("RASK") - pl.col("RASK_prev_year")) / pl.col("RASK_prev_year") * 100).alias("RASK_yoy_pct"),
    ((pl.col("load_factor") - pl.col("load_factor_prev_year"))).alias("LF_yoy_pp"),
])

# Month over Month
df_prev_month = df_kpis.with_columns(
    pl.col("fecha").dt.offset_by("1mo").alias("fecha")
)
df_mom = df_kpis.join(
    df_prev_month.select(["ruta", "fecha", "RASK", "load_factor"]),
    on=["ruta", "fecha"],
    how="left",
    suffix="_prev_month"
)

# ── 4. Gráficos Plotly ─────────────────────────────────────────────────────
# Waterfall P&L
agg = df_kpis.select([
    pl.col("ingresos_totales").sum().alias("ingresos"),
    pl.col("costos_totales").sum().alias("costos"),
]).row(0, named=True)

ebitda = agg["ingresos"] - agg["costos"]

fig_waterfall = go.Figure(go.Waterfall(
    name="P&L",
    orientation="v",
    measure=["absolute", "relative", "total"],
    x=["Ingresos", "Costos", "EBITDA"],
    y=[agg["ingresos"], -agg["costos"], ebitda],
    connector={"line": {"color": "rgb(63, 63, 63)"}},
    increasing={"marker": {"color": "#2ecc71"}},
    decreasing={"marker": {"color": "#e74c3c"}},
    totals={"marker": {"color": "#3498db"}},
))
fig_waterfall.update_layout(title="P&L Waterfall — LAN Chile")

# Heatmap de rutas (revenue por ruta)
pivot = df_kpis.group_by(["ruta", "mes"]).agg(
    pl.col("ingresos_totales").sum()
).pivot(values="ingresos_totales", index="ruta", on="mes")

fig_heatmap = px.imshow(
    pivot.to_pandas().set_index("ruta"),
    title="Revenue por Ruta y Mes",
    color_continuous_scale="Blues",
    labels=dict(color="Ingresos"),
)

# Bullet chart KPI real vs objetivo
fig_bullet = go.Figure(go.Indicator(
    mode="number+gauge+delta",
    value=df_kpis["load_factor"].mean(),
    delta={"reference": 80.0, "valueformat": ".1f"},
    title={"text": "Load Factor (%) vs Objetivo 80%"},
    gauge={
        "axis": {"range": [0, 110]},
        "threshold": {"line": {"color": "red", "width": 4}, "value": 80},
        "bar": {"color": "#3498db"},
    },
))

# ── 5. Template Jinja2 → PDF con WeasyPrint ────────────────────────────────
env = Environment(loader=FileSystemLoader("templates/"))
template = env.get_template("reporte_mensual.html")

html_content = template.render(
    fecha=date.today().strftime("%B %Y"),
    kpis=df_kpis.to_dicts(),
    yoy=df_yoy.to_dicts(),
    waterfall_img=fig_waterfall.to_image(format="png"),
    heatmap_img=fig_heatmap.to_image(format="png"),
)

HTML(string=html_content).write_pdf("reporte_mensual.pdf")
print("PDF generado: reporte_mensual.pdf")

# ── 6. Envío por WhatsApp (gateway Nelson :3001) o guardado local ──────────
def enviar_whatsapp(pdf_path: str, numero: str):
    """Enviar reporte via gateway WhatsApp Nelson en puerto 3001."""
    with open(pdf_path, "rb") as f:
        response = requests.post(
            "http://localhost:3001/send-file",
            files={"file": (pdf_path, f, "application/pdf")},
            data={"to": numero, "caption": f"Reporte Financiero {date.today():%B %Y}"},
        )
    return response.json()

# enviar_whatsapp("reporte_mensual.pdf", "56912345678")

# ── Scheduler automático (mensual, día 1 a las 08:00) ─────────────────────
def job_reporte_mensual():
    # Re-ejecutar pipeline completo
    pass  # reemplazar con la función principal

scheduler = BlockingScheduler()
scheduler.add_job(job_reporte_mensual, "cron", day=1, hour=8, minute=0)
# scheduler.start()
```

---

### Gráficos financieros esenciales

**Waterfall chart — P&L**
Visualiza ingresos, costos y EBITDA como cascada. Usar `plotly.graph_objects.Waterfall` con `measure=["absolute", "relative", "total"]`.

**Heatmap de rutas**
Revenue por ruta (filas) y mes (columnas). Identifica rutas más rentables y estacionalidad.
```python
fig = px.imshow(pivot_df, color_continuous_scale="Blues", title="Revenue por Ruta")
```

**Bullet chart — KPI real vs objetivo vs año anterior**
```python
go.Indicator(mode="number+gauge+delta", value=kpi_actual,
             delta={"reference": kpi_objetivo},
             gauge={"threshold": {"value": kpi_prev_year}})
```

**Treemap — composición de costos**
```python
fig = px.treemap(df_costos, path=["categoria", "subcategoria"],
                 values="monto", title="Estructura de Costos")
```

**Line chart YoY — comparativo 3 años**
```python
fig = px.line(df_long, x="mes", y="RASK", color="año",
              title="RASK Comparativo 3 Años")
```

---

### Polars para finanzas — patterns útiles

```python
import polars as pl

# Lectura Excel (nativo, sin pandas)
df = pl.read_excel("datos.xlsx")

# Aggregación por ruta y mes
kpis = df.group_by(["ruta", "mes"]).agg([
    pl.col("ingresos").sum(),
    pl.col("costos").sum(),
    pl.col("pasajeros").sum(),
    (pl.col("pasajeros").sum() / pl.col("capacidad").sum() * 100).alias("load_factor")
])

# Comparativo YoY
df_yoy = df.join(
    df.with_columns(pl.col("fecha").dt.offset_by("1y").alias("fecha")),
    on=["ruta", "fecha"], how="left", suffix="_prev_year"
)

# Normalizar monedas CLP/USD (tipo de cambio en columna tc_usd)
df = df.with_columns(
    pl.when(pl.col("moneda") == "CLP")
      .then(pl.col("monto") / pl.col("tc_usd"))
      .otherwise(pl.col("monto"))
      .alias("monto_usd")
)

# Filtro por rango de fechas
df_q = df.filter(
    pl.col("fecha").is_between(pl.date(2024, 1, 1), pl.date(2024, 12, 31))
)

# Rolling average 3 meses
df = df.sort("fecha").with_columns(
    pl.col("RASK").rolling_mean(window_size=3).alias("RASK_3m_avg")
)

# Export a Excel
df.write_excel("reporte_output.xlsx")

# Export a Parquet (eficiente para grandes volúmenes)
df.write_parquet("datos_historicos.parquet")

# Leer desde SQL (via connectorx o adbc)
import connectorx as cx
df = pl.from_arrow(cx.read_sql("SELECT * FROM vuelos", "postgresql://..."))
```

---

### Pitfalls

- Polars read_excel requiere: `pip install 'polars[excel]'` o `pip install xlsx2csv fastexcel`
- WeasyPrint en Linux puede necesitar: `apt install libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0`
- Tipos de datos: usar `pl.Decimal` para monedas — evita errores de precisión float en KPIs financieros
- Load Factor > 100% es válido (overbooking en LAN Chile) — NO filtrar ni hacer clip
- Datos LAN Chile: mezcla CLP/USD — siempre incluir columna `moneda` y normalizar antes de calcular KPIs
- Polars `df.write_excel()` disponible desde v0.19 — verificar versión con `pl.__version__`
- `dt.offset_by("1y")` para YoY respeta años bisiestos; no usar `timedelta(days=365)`
- `group_by` en Polars no garantiza orden — usar `.sort()` después si el orden importa
- Para grandes datasets históricos (LAN tiene años de datos): usar Parquet + lazy frames (`pl.scan_parquet`)

---

### Instalación

```bash
pip install 'polars[excel]' plotly dash weasyprint jinja2 apscheduler sqlalchemy openpyxl xlsxwriter connectorx
```

Dependencias del sistema (Linux/Ubuntu):
```bash
apt install libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0 libffi-dev
```
