# Spike 1: Datos Públicos API → Reporte Visual

**Fecha:** 2026-05-19
**Caso:** Secretaría de Energía Argentina → PNG dark-mode
**Archivo principal:** `spike_energia.py`

---

## ¿Qué hace este spike?

Descarga datos oficiales de producción de petróleo y gas por empresa
desde la API pública del gobierno argentino, los procesa con pandas,
y genera una imagen PNG dark-mode con KPIs, gráficos y análisis
lista para enviar por WhatsApp.

---

## Paso a Paso

### PASO 1 — Descargar los datos

**Fuente:** https://datos.gob.ar (Secretaría de Energía)

URLs de los datasets:
```
Petróleo:
https://datos.gob.ar/api/3/action/datastore_search?resource_id=...
(o descarga directa CSV desde el portal)

Gas:
https://datos.gob.ar/api/3/action/datastore_search?resource_id=...
```

**Archivos resultantes:**
```
data/petroleo_por_empresa.csv
data/gas_por_empresa.csv
```

**Pitfall:** El CSV usa separador `;` y encoding `utf-8-sig`, NO el estándar.
```python
df = pd.read_csv('petroleo_por_empresa.csv', encoding='utf-8-sig')
# separador se detecta automático por pandas en este caso
```

---

### PASO 2 — Limpiar y parsear

```python
df.columns = df.columns.str.strip()           # quitar espacios en nombres
df['fecha'] = pd.to_datetime(df['indice_tiempo'], errors='coerce')
col_prod = [c for c in df.columns if 'produccion' in c.lower()][0]
df[col_prod] = pd.to_numeric(df[col_prod], errors='coerce').fillna(0)
```

**Columnas clave:**
- `indice_tiempo` → fecha del período
- `empresa` → nombre de la empresa
- `produccion_*` → producción en m³/día

---

### PASO 3 — Detectar el último mes válido

**Pitfall crítico:** El último mes del CSV casi siempre está incompleto
(solo 1-2 empresas reportaron). Usar el último mes con ≥ 20 empresas.

```python
counts = df.groupby('fecha').size()
fecha_max = counts[counts >= 20].index.max()
```

---

### PASO 4 — Calcular KPIs

```python
# Filtrar últimos 12 meses
df_12m = df[df['fecha'] >= fecha_max - pd.DateOffset(months=11)]

# Serie histórica YPF
ypf = df_12m[df_12m['empresa'].str.contains('YPF', case=False)]
serie_ypf = ypf.groupby('fecha')[col_prod].sum()

# Serie total mercado
total = df_12m.groupby('fecha')[col_prod].sum()

# Market share — sobre el MISMO mes (no acumulado)
mes_actual = df[df['fecha'] == fecha_max]
share_ypf = mes_actual[mes_actual['empresa'].str.contains('YPF')][col_prod].sum()
share_total = mes_actual[col_prod].sum()
pct = share_ypf / share_total * 100   # → ~50% petróleo, ~33% gas
```

---

### PASO 5 — Generar el reporte visual

**Librería:** matplotlib con GridSpec (layout de grilla flexible)

```python
fig = plt.figure(figsize=(12, 14), facecolor='#0A0E1A')
gs = GridSpec(5, 3, figure=fig, hspace=0.50, wspace=0.35)
```

**Layout:**
```
[  HEADER — título + fecha + fuente          ]
[ KPI petróleo ][ KPI gas ][ KPI share YPF  ]
[ Serie hist. petróleo    ][ Top empresas   ]
[ Serie hist. gas         ][ Barras market  ]
[  Análisis LLM / JARVIS                    ]
```

**Archivo de salida:**
```
output/reporte_energia.png
```

---

### PASO 6 — Ejecutar

```bash
cd ~/brainstorming/2026-05-19-energia-whatsapp-spike/
python3 spike_energia.py
# → genera output/reporte_energia.png en ~5 segundos
```

---

## Para replicar con otro caso

1. Reemplazar las URLs de descarga por las del nuevo dataset
2. Ajustar los nombres de columnas en el paso de limpieza
3. Cambiar la lógica de KPIs según lo que quieras mostrar
4. El bloque de generación visual (paso 5) es reutilizable casi sin cambios

**Dependencias:**
```bash
pip install pandas matplotlib requests numpy
```
