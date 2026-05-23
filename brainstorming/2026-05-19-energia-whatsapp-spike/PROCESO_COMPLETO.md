# Proceso Completo: Pipeline Datos Energía → Reporte PNG → WhatsApp

**Fecha:** 2026-05-19  
**Equipo:** Tony + JARVIS  
**Estado:** ✅ Validado y funcionando  
**Script:** `spike_energia.py`

---

## Qué resuelve este pipeline

Consume datos públicos de la Secretaría de Energía Argentina (datos.gob.ar),
los procesa con pandas, genera un reporte visual dark-mode en PNG y lo envía por WhatsApp.
Todo corre en menos de 10 segundos desde cero.

---

## Paso 1 — Descargar los datos

**Fuente:** https://datos.gob.ar — Secretaría de Energía Argentina

Datasets usados:
- Producción de petróleo por empresa (m³/día)
- Producción de gas natural por empresa (m³/día)

Los CSV se descargan directamente desde el portal y se guardan en `data/`.

**Pitfall:** El CSV usa separador `;` y encoding `utf-8-sig`, NO el estándar.
```python
df = pd.read_csv('petroleo_por_empresa.csv', encoding='utf-8-sig')
```

---

## Paso 2 — Limpiar y parsear

```python
df.columns = df.columns.str.strip()           # quitar espacios en nombres de columna
df['fecha'] = pd.to_datetime(df['indice_tiempo'], errors='coerce')
col_prod = [c for c in df.columns if 'produccion' in c.lower()][0]
df[col_prod] = pd.to_numeric(df[col_prod], errors='coerce').fillna(0)
```

Columnas clave:
- `indice_tiempo` → período del dato
- `empresa` → nombre de la empresa
- `produccion_*` → producción en m³/día

---

## Paso 3 — Detectar el último mes válido

**Pitfall crítico:** El último mes del CSV casi siempre está incompleto
(solo 1-2 empresas reportaron). Hay que usar el último mes con ≥ 20 empresas reportando.
Sin este filtro, el market share sale mal (por ejemplo, 100% en lugar de ~50%).

```python
counts = df.groupby('fecha').size()
fecha_max = counts[counts >= 20].index.max()
```

---

## Paso 4 — Calcular KPIs

```python
# Filtrar últimos 12 meses
df_12m = df[df['fecha'] >= fecha_max - pd.DateOffset(months=11)]

# Serie histórica YPF
ypf = df_12m[df_12m['empresa'].str.contains('YPF', case=False)]
serie_ypf = ypf.groupby('fecha')[col_prod].sum()

# Serie total del mercado
total = df_12m.groupby('fecha')[col_prod].sum()

# Market share — calcular sobre el MISMO mes filtrado, nunca sobre acumulado anual
mes_actual = df[df['fecha'] == fecha_max]
share_ypf   = mes_actual[mes_actual['empresa'].str.contains('YPF')][col_prod].sum()
share_total = mes_actual[col_prod].sum()
pct = share_ypf / share_total * 100   # → ~50% petróleo, ~33% gas
```

---

## Paso 5 — Generar el reporte visual (PNG dark-mode)

**Librería:** matplotlib con GridSpec

```python
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

fig = plt.figure(figsize=(12, 14), facecolor='#0A0E1A')
gs  = GridSpec(5, 3, figure=fig, hspace=0.50, wspace=0.35)
```

Layout del reporte:
```
[  HEADER — título + fecha + fuente                    ]
[ KPI petróleo  ][ KPI gas        ][ KPI share YPF    ]
[ Serie hist. petróleo (12 meses) ][ Top 5 empresas   ]
[ Serie hist. gas (12 meses)      ][ Barras market %  ]
[  Análisis / comentario LLM                           ]
```

Output: `output/reporte_energia.png`

---

## Paso 6 — Enviar por WhatsApp

Desde JARVIS, incluir en la respuesta:
```
MEDIA:/ruta/absoluta/output/reporte_energia.png
```

Si la imagen no llega por path muy profundo, copiarla a /tmp primero:
```bash
cp output/reporte_energia.png /tmp/reporte_energia.png
```
Y enviar desde `/tmp/reporte_energia.png`.

---

## Paso 7 — Ejecutar el pipeline completo

```bash
cd ~/brainstorming/2026-05-19-energia-whatsapp-spike/
python3 spike_energia.py
# → genera output/reporte_energia.png en ~5-10 segundos
```

---

## Dependencias

```bash
pip install pandas matplotlib requests numpy
```

---

## Para reutilizar con otro dataset

1. Reemplazar las URLs de descarga por las del nuevo dataset
2. Ajustar nombres de columnas en el paso de limpieza (paso 2)
3. Cambiar la lógica de KPIs según lo que se quiera mostrar (paso 4)
4. El bloque de visualización (paso 5) es reutilizable casi sin cambios

---

## Archivos del spike

```
spike_energia.py          ← script principal completo
data/
  petroleo_por_empresa.csv
  gas_por_empresa.csv
output/
  reporte_energia.png     ← reporte final generado
PASO_A_PASO.md            ← versión técnica detallada
PROCESO_COMPLETO.md       ← este archivo (visión general)
README.md                 ← contexto del spike
```
