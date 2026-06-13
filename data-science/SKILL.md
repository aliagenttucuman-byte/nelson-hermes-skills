---
name: nelson-finance-ml
description: "Machine Learning aplicado a finanzas con Python. Forecasting de demanda/revenue, clasificacion de riesgo, deteccion de anomalias, optimizacion de precios. Stack: Polars, scikit-learn, XGBoost, LightGBM, Prophet, statsmodels, SHAP."
triggers:
  - finanzas ML
  - machine learning finanzas
  - forecasting financiero
  - revenue forecast
  - prediccion financiera
  - modelos financieros LAN
version: "1.0.0"
---

# nelson-finance-ml — ML aplicado a Finanzas (LAN Chile / Aerolíneas)

Stack y guías para el equipo Nelson. Librería principal de dataframes: **Polars** (no pandas). pandas solo como fallback/interop cuando una librería externa lo exige.

---

## Stack de librerías

| Librería | Uso principal | Instalación |
|---|---|---|
| **Polars** | Dataframes rápidos — reemplaza pandas para toda manipulación y feature engineering | `pip install polars` |
| **scikit-learn** | Clasificación, regresión, pipelines, métricas, validación temporal (TimeSeriesSplit) | `pip install scikit-learn` |
| **XGBoost** | Gradient boosting para forecasting y clasificación de riesgo | `pip install xgboost` |
| **LightGBM** | Alternativa a XGBoost, más rápido en datasets grandes categóricos | `pip install lightgbm` |
| **Prophet** (Meta) | Series temporales con estacionalidad múltiple — requiere pandas como interop | `pip install prophet` |
| **statsmodels** | ARIMA, SARIMA, regresión econométrica, tests estadísticos | `pip install statsmodels` |
| **Optuna** | Hyperparameter tuning automático (reemplaza GridSearch) | `pip install optuna` |
| **SHAP** | Explicabilidad de modelos — feature importance a nivel de predicción individual | `pip install shap` |

---

## Por qué Polars en finanzas

- **10-100x más rápido que pandas** en operaciones de agregación (group by revenue por ruta, rolling KPIs)
- **Lazy evaluation**: `pl.scan_csv()` procesa datasets que no caben en RAM — solo materializa lo necesario
- **Expresiones tipo SQL**: ideal para cálculos de KPIs financieros encadenados sin loops Python
- **Interop limpio con scikit-learn**: `.to_numpy()` para pasar features al modelo, `.to_pandas()` solo cuando la librería lo exige (Prophet, statsmodels)
- **Inmutabilidad**: evita bugs silenciosos por modificación in-place — cada transformación retorna un DataFrame nuevo

Lectura de datos:

```python
import polars as pl

# Eager — archivo cabe en RAM
df = pl.read_csv("rutas.csv")
df = pl.read_excel("revenue_2024.xlsx")

# Lazy — archivos > 500 MB, solo materializa con .collect()
df = pl.scan_csv("historico_vuelos.csv").collect()

# Lazy con filtro antes de cargar todo
df = (
    pl.scan_csv("historico_vuelos.csv")
    .filter(pl.col("ruta") == "SCL-LIM")
    .select(["fecha", "pax", "revenue_usd"])
    .collect()
)
```

---

## Casos de uso aerolínea LAN Chile

- **Forecasting de demanda de pasajeros por ruta** — series temporales con estacionalidad semanal y anual (ej: SCL-MIA, SCL-LIM, SCL-MAD)
- **Predicción de revenue por ruta y temporada** — regresión con variables de precio, ocupación, eventos, tipo de cambio CLP/USD
- **Clasificación de riesgo de churn de clientes frecuentes (LAN PASS)** — clientes en riesgo de bajar de categoría o dejar de volar
- **Detección de anomalías en costos operativos** — combustible, catering, ground handling fuera de rango esperado
- **Optimización dinámica de precios (yield management)** — modelos de demanda price-sensitive por anticipación de compra
- **Forecasting de consumo de combustible** — mayor costo variable de la aerolínea, alta sensibilidad al precio WTI/Brent
- **Predicción de cancelaciones y overbooking óptimo** — balance entre seat revenue y costo de compensación

---

## Pipeline estándar con Polars + XGBoost

Ejemplo completo: forecasting de revenue mensual por ruta.

```python
import polars as pl
import numpy as np
import xgboost as xgb
import shap
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
import openpyxl

# ── 1. CARGA CON POLARS ────────────────────────────────────────────────────────

# Desde Excel
df = pl.read_excel("revenue_rutas.xlsx")

# Desde CSV grande (lazy)
# df = pl.scan_csv("historico.csv").collect()

print(df.head())
print(df.schema)

# ── 2. FEATURE ENGINEERING CON POLARS ─────────────────────────────────────────

# Asegurar tipo fecha
df = df.with_columns(
    pl.col("fecha").str.to_date("%Y-%m-%d")
)

# Ordenar por ruta y fecha (crítico antes de lags)
df = df.sort(["ruta", "fecha"])

# Features de fecha
df = df.with_columns([
    pl.col("fecha").dt.month().alias("mes"),
    pl.col("fecha").dt.quarter().alias("trimestre"),
    pl.col("fecha").dt.weekday().alias("dia_semana"),
    pl.col("fecha").dt.year().alias("anio"),
])

# Lags y rolling por ruta (window over partition)
df = df.with_columns([
    pl.col("revenue_usd")
      .shift(1)
      .over("ruta")
      .alias("revenue_lag1"),

    pl.col("revenue_usd")
      .shift(3)
      .over("ruta")
      .alias("revenue_lag3"),

    pl.col("revenue_usd")
      .shift(12)
      .over("ruta")
      .alias("revenue_lag12"),

    pl.col("revenue_usd")
      .rolling_mean(window_size=3)
      .over("ruta")
      .alias("revenue_rolling_3m"),

    pl.col("pax")
      .rolling_mean(window_size=6)
      .over("ruta")
      .alias("pax_rolling_6m"),
])

# Normalizar moneda: convertir CLP a USD si corresponde
# (asumir col tipo_moneda y col tipo_cambio_clp_usd)
df = df.with_columns(
    pl.when(pl.col("tipo_moneda") == "CLP")
      .then(pl.col("revenue_raw") / pl.col("tipo_cambio_clp_usd"))
      .otherwise(pl.col("revenue_raw"))
      .alias("revenue_usd")
)

# Eliminar filas con nulls generados por lags
df = df.drop_nulls()

# ── 3. SPLIT TEMPORAL CORRECTO — NUNCA ALEATORIO ──────────────────────────────

# Corte por fecha: 80% train, 20% test preservando orden temporal
fechas = df.select("fecha").to_series().sort()
corte = fechas[int(len(fechas) * 0.8)]

df_train = df.filter(pl.col("fecha") < corte)
df_test  = df.filter(pl.col("fecha") >= corte)

print(f"Train: {df_train.shape} | Test: {df_test.shape}")
print(f"Corte en: {corte}")

# ── 4. CONVERSIÓN A NUMPY PARA EL MODELO ──────────────────────────────────────

FEATURES = [
    "mes", "trimestre", "dia_semana", "anio",
    "revenue_lag1", "revenue_lag3", "revenue_lag12",
    "revenue_rolling_3m", "pax_rolling_6m",
    "precio_promedio_usd", "load_factor",
]
TARGET = "revenue_usd"

X_train = df_train.select(FEATURES).to_numpy()
y_train = df_train.select(TARGET).to_numpy().ravel()

X_test = df_test.select(FEATURES).to_numpy()
y_test = df_test.select(TARGET).to_numpy().ravel()

# ── 5. ESCALAR FEATURES (DESPUÉS DEL SPLIT) ───────────────────────────────────

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)   # fit SOLO en train
X_test_sc  = scaler.transform(X_test)        # transform en test

# ── 6. XGBOOST CON EARLY STOPPING ─────────────────────────────────────────────

model = xgb.XGBRegressor(
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    early_stopping_rounds=50,
    eval_metric="rmse",
)

model.fit(
    X_train_sc, y_train,
    eval_set=[(X_test_sc, y_test)],
    verbose=100,
)

# ── 7. EVALUACIÓN ─────────────────────────────────────────────────────────────

y_pred = model.predict(X_test_sc)

mae  = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

# MAPE — solo si no hay ceros (en finanzas puede haberlos)
mask = y_test != 0
mape = np.mean(np.abs((y_test[mask] - y_pred[mask]) / y_test[mask])) * 100

# SMAPE — robusto ante valores cercanos a 0
smape = np.mean(
    2 * np.abs(y_pred - y_test) / (np.abs(y_pred) + np.abs(y_test) + 1e-8)
) * 100

print(f"MAE:   {mae:,.0f} USD")
print(f"RMSE:  {rmse:,.0f} USD")
print(f"MAPE:  {mape:.2f}%")
print(f"SMAPE: {smape:.2f}%")

# ── 8. SHAP — EXPLICABILIDAD ───────────────────────────────────────────────────

explainer   = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test_sc)

shap.summary_plot(shap_values, X_test_sc, feature_names=FEATURES, show=False)

# Feature importance global
importancia = pl.DataFrame({
    "feature": FEATURES,
    "shap_mean_abs": np.abs(shap_values).mean(axis=0).tolist(),
}).sort("shap_mean_abs", descending=True)

print(importancia)

# ── 9. EXPORT A EXCEL ─────────────────────────────────────────────────────────

# Agregar predicciones al DataFrame de test
resultado = df_test.with_columns(
    pl.Series("revenue_pred_usd", y_pred)
)

# Polars no escribe Excel directamente — convertir a pandas para openpyxl
resultado.to_pandas().to_excel("resultado_forecast.xlsx", index=False)
importancia.to_pandas().to_excel("shap_importancia.xlsx", index=False)

print("Archivos exportados: resultado_forecast.xlsx, shap_importancia.xlsx")
```

---

## Pitfalls críticos en finanzas con ML

**NUNCA usar train_test_split aleatorio en series temporales**
El split aleatorio filtra información futura al modelo (data leakage). Siempre cortar por fecha. Usar `TimeSeriesSplit` de sklearn para validación cruzada walk-forward.

```python
from sklearn.model_selection import TimeSeriesSplit
tscv = TimeSeriesSplit(n_splits=5)
for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train_sc)):
    # entrenar en train_idx, validar en val_idx
    pass
```

**Polars es inmutable**
Las transformaciones NO modifican el DataFrame original — siempre retornan uno nuevo. Reasignar: `df = df.with_columns(...)`.

**Polars lazy vs eager**
Para archivos > 500 MB usar `pl.scan_csv()` + `.collect()`. El plan lazy optimiza qué columnas y filas se leen realmente desde disco.

**Prophet requiere pandas**
Prophet solo acepta un pandas DataFrame con columnas exactas `ds` (datetime) y `y` (target). Convertir desde Polars:

```python
from prophet import Prophet

df_prophet = df.select([
    pl.col("fecha").alias("ds"),
    pl.col("revenue_usd").alias("y"),
]).to_pandas()   # <-- único uso legítimo de .to_pandas() aquí

m = Prophet(yearly_seasonality=True, weekly_seasonality=True)
m.fit(df_prophet)
```

**Escalar features DESPUÉS del split, no antes**
Fit del scaler solo sobre datos de train. Aplicar transform al test. Si se escala antes del split, el scaler vio el futuro → leakage.

**MAPE falla con valores cercanos a 0**
Revenue de rutas nuevas o de baja frecuencia puede ser 0 en algunos períodos. Usar SMAPE como métrica principal en esos casos.

**Estacionalidad doble en aerolíneas**
Los datos de LAN Chile tienen estacionalidad semanal (menor demanda lunes/martes) Y anual (verano/invierno, Fiestas Patrias, Semana Santa). Prophet y SARIMA manejan esto nativamente. En XGBoost, incluir explícitamente `mes`, `dia_semana`, `semana_del_anio` como features.

**Mezcla de monedas CLP/USD**
Normalizar a una sola moneda ANTES de cualquier modelo. Revenue internacional en USD, doméstico en CLP. Aplicar tipo de cambio histórico al momento de la transacción, no el actual.

**Polars con columnas categóricas para XGBoost**
XGBoost acepta categorías directamente (enable_categorical=True), pero verificar el tipo en Polars:

```python
df = df.with_columns(pl.col("ruta").cast(pl.Categorical))
# Luego al to_numpy() convertir a códigos numéricos:
X = df.select(FEATURES).to_pandas()  # solo para cat encoding si es necesario
```

---

## Instalación del stack completo

```bash
pip install polars scikit-learn xgboost lightgbm prophet statsmodels optuna shap openpyxl xlrd
```

Versiones recomendadas (estables a 2025):

```bash
pip install polars>=0.20 scikit-learn>=1.4 xgboost>=2.0 lightgbm>=4.3 \
            prophet>=1.1 statsmodels>=0.14 optuna>=3.6 shap>=0.45 \
            openpyxl>=3.1 xlrd>=2.0
```

Para entornos con GPU (XGBoost):

```bash
pip install xgboost[cuda]
```
