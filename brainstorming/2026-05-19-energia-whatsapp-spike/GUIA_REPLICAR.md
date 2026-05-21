# Guía para Replicar: Pipeline Datos Energía Argentina → Reporte PNG

**Proyecto:** Spike Datos Energéticos Argentina  
**Fecha:** 2026-05-19  
**Resultado final:** Imagen PNG dark-mode con KPIs de producción de petróleo y gas, lista para enviar por WhatsApp o cualquier canal.

---

## Qué hace este pipeline

1. Descarga datos oficiales de producción de petróleo y gas por empresa desde datos.gob.ar
2. Los procesa con pandas para calcular KPIs (YPF, market share, variaciones)
3. Genera una imagen PNG dark-mode con header, cards de KPIs, series históricas, top empresas y análisis automático
4. Todo en menos de 10 segundos

---

## Requisitos

**Python 3.9+** y las siguientes librerías:

```bash
pip install pandas matplotlib numpy requests
```

**Estructura de carpetas necesaria:**

```
tu-carpeta/
├── spike_energia.py        ← script principal
├── data/
│   ├── petroleo_por_empresa.csv
│   └── gas_por_empresa.csv
└── output/                 ← se crea automáticamente
```

---

## Paso 1 — Descargar los datos

Ir a [datos.gob.ar](https://datos.gob.ar) y buscar:

- **"producción de petróleo por empresa"** → descargar CSV
- **"producción de gas natural por empresa"** → descargar CSV

Guardar ambos archivos en la carpeta `data/` con estos nombres exactos:
- `data/petroleo_por_empresa.csv`
- `data/gas_por_empresa.csv`

> **Nota:** Los CSV tienen separador `;` y encoding `utf-8-sig` (no es el estándar). El script ya maneja esto.

---

## Paso 2 — Revisar las columnas del CSV

Abrir cualquiera de los CSV y verificar que tenga estas columnas:

| Columna | Descripción |
|---------|-------------|
| `indice_tiempo` | Fecha del período (ej: `2024-03`) |
| `empresa` | Nombre de la empresa |
| `produccion_*` | Producción en m³/día (el nombre exacto varía) |

El script detecta automáticamente el nombre de la columna de producción buscando cualquier columna que contenga la palabra `produccion`.

---

## Paso 3 — Ejecutar el script

```bash
cd tu-carpeta/
python3 spike_energia.py
```

**Salida esperada en consola:**

```
=======================================================
⚡ Spike: Datos Energéticos → Reporte Visual
=======================================================
📊 Cargando datos...
  Petróleo: 12000+ registros | 2009 - 2024
  Gas: 11000+ registros | 2009 - 2024
🔢 Calculando KPIs...
  Último mes: Marzo 2024
  YPF Petróleo: 123,456 m³/día (+2.3% vs mes ant.)
  YPF Gas: 45.6 MM m³/día (-1.1% vs mes ant.)
  Market share petróleo: 49.8%
  Market share gas: 33.4%
🎨 Generando reporte visual...
  ✅ Reporte guardado: output/reporte_energia.png
=======================================================
✅ SPIKE COMPLETADO
📁 Reporte: output/reporte_energia.png
=======================================================
```

---

## Paso 4 — Verificar el resultado

El archivo `output/reporte_energia.png` debe tener este layout:

```
┌────────────────────────────────────────────────────┐
│  ⚡ REPORTE ENERGÉTICO ARGENTINA      📅 Mes YYYY  │  ← Header
└────────────────────────────────────────────────────┘
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│ YPF Petróleo │ │   YPF Gas    │ │  Market Share YPF │  ← KPI Cards
│  123,456     │ │   45.6 MM    │ │     50% / 33%     │
│ m³/día       │ │  m³/día      │ │  petróleo / gas   │
└──────────────┘ └──────────────┘ └──────────────────┘
┌───────────────────────────────┐ ┌────────────────────┐
│  Serie histórica YPF petróleo │ │  Top 5 empresas    │  ← Fila 3
│  (últimos 3 años)             │ │  petróleo          │
└───────────────────────────────┘ └────────────────────┘
┌───────────────────────────────┐ ┌────────────────────┐
│  Serie histórica YPF gas      │ │  Top 5 empresas    │  ← Fila 4
│  (últimos 3 años)             │ │  gas               │
└───────────────────────────────┘ └────────────────────┘
┌────────────────────────────────────────────────────┐
│  🤖 Análisis JARVIS — texto automático con KPIs   │  ← Footer
└────────────────────────────────────────────────────┘
```

---

## Pitfalls conocidos (errores frecuentes)

### ❌ Market share sale 100% o valores absurdos
**Causa:** Se está usando el último mes del CSV, que casi siempre está incompleto (solo 1-2 empresas reportaron).  
**Solución:** El script ya aplica el filtro correcto — usa el último mes con **≥ 20 empresas reportando**. Si el resultado sigue raro, revisar que `fecha_max` no sea el mes actual.

```python
counts = df_pet.groupby('fecha').size()
fecha_max = counts[counts >= 20].index.max()   # ← filtro crítico
```

### ❌ Error al leer el CSV: `UnicodeDecodeError`
**Causa:** El CSV de datos.gob.ar usa encoding `utf-8-sig` (con BOM).  
**Solución:** Ya está manejado con `encoding='utf-8-sig'` en el script. Si falla igual, probar `encoding='latin-1'`.

### ❌ KeyError en columna de producción
**Causa:** El nombre exacto de la columna varía según el año del dataset.  
**Solución:** El script detecta la columna automáticamente:
```python
col_pet = [c for c in df_pet.columns if 'produccion' in c.lower()][0]
```
Si hay error, hacer `print(df_pet.columns.tolist())` para ver los nombres reales.

### ❌ La imagen se genera pero no tiene datos en las series
**Causa:** El formato de la columna `indice_tiempo` cambió (ej: `2024-03-01` vs `2024-03`).  
**Solución:** `pd.to_datetime(df['indice_tiempo'], errors='coerce')` ya maneja ambos formatos. Si fallan, verificar con `df['indice_tiempo'].head()`.

### ❌ matplotlib muestra una ventana o falla en servidor headless
**Causa:** Backend de matplotlib incorrecto.  
**Solución:** Ya está manejado con `matplotlib.use('Agg')` al inicio del script (debe ir **antes** del import de pyplot).

---

## Cómo adaptar a otro dataset

1. **Reemplazar las URLs/archivos** en la función `cargar_datos()`
2. **Ajustar columnas** en el bloque de limpieza (paso 2 del script)
3. **Cambiar los KPIs** en `calcular_kpis()` — la estructura del dict `kpis` es lo que alimenta al reporte
4. **El bloque visual** (`generar_reporte()`) es reutilizable casi sin cambios — solo cambiar títulos y colores

---

## Archivos del proyecto

```
spike_energia.py          ← script completo (único archivo a ejecutar)
data/
  petroleo_por_empresa.csv    ← descargar de datos.gob.ar
  gas_por_empresa.csv         ← descargar de datos.gob.ar
output/
  reporte_energia.png         ← imagen generada (se crea al correr el script)
README.md                     ← contexto del spike
PROCESO_COMPLETO.md           ← descripción técnica del pipeline
GUIA_REPLICAR.md              ← este archivo
```

---

## Dependencias completas

```
pandas>=1.5
matplotlib>=3.6
numpy>=1.23
requests>=2.28      # solo si se agrega descarga automática
```

Instalar todo de una:
```bash
pip install pandas matplotlib numpy requests
```
