---
name: nelson-airline-delay-prediction
description: "Prediccion de delays y cancelaciones de vuelos con Python. Stack: Polars, XGBoost, LightGBM, scikit-learn Pipelines, MLflow, SHAP. Datos: BTS on-time performance. Features: ruta, aeropuerto, hora, clima, congestion. AUC-ROC objetivo >0.85."
triggers:
  - prediccion delay
  - flight delay prediction
  - cancelacion vuelos
  - puntualidad aerolinea
  - on-time performance ML
version: "1.0.0"
---

### El problema

- Las aerolíneas pierden USD 8.300M/año por delays en EEUU (FAA 2019)
- LAN Chile: puntualidad es KPI crítico — publicado mensualmente por la JAC
- Predecir delays con 2-6 horas de anticipación permite: reasignar tripulaciones, alertar pasajeros, optimizar gates, reducir efecto cascada
- El problema tiene 2 versiones: regresión (cuántos minutos de delay) y clasificación (delay >15min = sí/no)

### Features clave

| Feature | Tipo | Fuente |
|---------|------|--------|
| DepHour | Numérico entero | BTS on-time data |
| DayOfWeek | Categórico (1-7) | BTS on-time data |
| Month | Categórico (1-12) | BTS on-time data |
| IsWeekend | Binario | Derivado de DayOfWeek |
| IsHoliday | Binario | Calendario federal EEUU / feriados Chile |
| FlightDuration | Numérico float | BTS on-time data |
| Distance | Numérico float | BTS on-time data |
| OriginAirportCongestion | Numérico float | % delays históricos por aeropuerto origen (ventana rodante 30 días) |
| DestAirportCongestion | Numérico float | % delays históricos por aeropuerto destino (ventana rodante 30 días) |
| AirportHubType | Categórico | FAA airport classification (hub/spoke/regional) |
| CarrierHistoricalDelay | Numérico float | Delay promedio histórico del carrier por ruta |
| AircraftAge | Numérico float | Años del avión (desde fecha de fabricación) |
| AircraftType | Categórico | Boeing/Airbus/Embraer/etc. |
| WeatherCondition_Origin | Categórico/Numérico | OpenMeteo API (windspeed, precipitation, visibility) |
| WeatherCondition_Dest | Categórico/Numérico | OpenMeteo API (windspeed, precipitation, visibility) |
| InboundFlightDelay | Numérico float | Delay del vuelo anterior del mismo avión (tail_number) |
| NumCompetitorsOnRoute | Numérico entero | Número de aerolíneas competidoras en la misma ruta |

### Pipeline ML completo production-ready

```python
import polars as pl
import numpy as np
import lightgbm as lgb
import xgboost as xgb
import mlflow
import shap
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from category_encoders import TargetEncoder
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# ─────────────────────────────────────────────
# 1. CARGA CON POLARS (lazy scan para archivos grandes)
# ─────────────────────────────────────────────
# BTS On-Time Performance data: https://www.transtats.bts.gov/
# Descarga: REPORTING_CARRIER, FL_DATE, ORIGIN, DEST, DEP_TIME, DEP_DELAY,
#           ARR_DELAY, CANCELLED, TAIL_NUM, DISTANCE, AIR_TIME

def load_bts_data(path_glob: str) -> pl.DataFrame:
    """Carga lazy de múltiples CSVs anuales de BTS."""
    df = (
        pl.scan_csv(path_glob, infer_schema_length=10000)
        .select([
            "FL_DATE", "REPORTING_CARRIER", "TAIL_NUM",
            "ORIGIN", "DEST", "DEP_TIME", "DEP_DELAY",
            "ARR_DELAY", "CANCELLED", "DISTANCE", "AIR_TIME"
        ])
        .with_columns([
            pl.col("FL_DATE").str.to_date("%Y-%m-%d"),
            pl.col("DEP_TIME").cast(pl.Float32),
            pl.col("DEP_DELAY").cast(pl.Float32),
            pl.col("ARR_DELAY").cast(pl.Float32),
            pl.col("CANCELLED").cast(pl.Int8),
        ])
        .filter(pl.col("CANCELLED") == 0)  # excluir cancelados del modelo de delay
        .collect()
    )
    return df

# ─────────────────────────────────────────────
# 2. FEATURE ENGINEERING
# ─────────────────────────────────────────────
def build_features(df: pl.DataFrame) -> pl.DataFrame:
    df = df.with_columns([
        # Features temporales
        pl.col("FL_DATE").dt.weekday().alias("DayOfWeek"),
        pl.col("FL_DATE").dt.month().alias("Month"),
        pl.col("FL_DATE").dt.weekday().is_in([5, 6]).alias("IsWeekend"),
        (pl.col("DEP_TIME") // 100).cast(pl.Int32).alias("DepHour"),

        # Target: clasificación binaria (delay >15 min)
        (pl.col("DEP_DELAY") > 15).cast(pl.Int8).alias("IsDelayed"),

        # Target: regresión (minutos de delay, solo positivos)
        pl.col("DEP_DELAY").clip(lower_bound=0).alias("DelayMinutes"),
    ])

    # ─── Congestión histórica por aeropuerto (ventana rodante 30 días) ───
    # Requiere ordenar por fecha antes del join
    airport_congestion = (
        df.sort("FL_DATE")
        .group_by_dynamic("FL_DATE", every="1d", period="30d", by="ORIGIN")
        .agg([
            (pl.col("DEP_DELAY") > 15).mean().alias("OriginAirportCongestion")
        ])
    )
    df = df.join(airport_congestion, on=["FL_DATE", "ORIGIN"], how="left")

    # ─── Rolling average de delay por ruta ───
    route_delay = (
        df.sort("FL_DATE")
        .group_by_dynamic("FL_DATE", every="1d", period="14d", by=["ORIGIN", "DEST"])
        .agg([
            pl.col("DEP_DELAY").mean().alias("CarrierHistoricalDelay")
        ])
    )
    df = df.join(route_delay, on=["FL_DATE", "ORIGIN", "DEST"], how="left")

    return df

# ─────────────────────────────────────────────
# 3. EFECTO CASCADA: InboundFlightDelay por tail_number
# (ver sección dedicada abajo)
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# 4. COLUMN TRANSFORMER
# ─────────────────────────────────────────────
NUMERIC_FEATURES = [
    "DepHour", "DayOfWeek", "Month", "IsWeekend",
    "Distance", "AIR_TIME", "OriginAirportCongestion",
    "CarrierHistoricalDelay", "InboundFlightDelay",
    "windspeed_10m_origin", "precipitation_origin",
    "windspeed_10m_dest", "precipitation_dest",
]
CATEGORICAL_FEATURES = ["REPORTING_CARRIER", "ORIGIN", "DEST", "AircraftType"]

preprocessor = ColumnTransformer([
    ("num", StandardScaler(), NUMERIC_FEATURES),
    ("cat", TargetEncoder(), CATEGORICAL_FEATURES),
])

# ─────────────────────────────────────────────
# 5. SPLIT TEMPORAL ESTRICTO
# ─────────────────────────────────────────────
def temporal_split(df: pl.DataFrame, test_year: int):
    """Train en años anteriores, test en el año más reciente."""
    train = df.filter(pl.col("FL_DATE").dt.year() < test_year).to_pandas()
    test  = df.filter(pl.col("FL_DATE").dt.year() == test_year).to_pandas()
    return train, test

# ─────────────────────────────────────────────
# 6. MODELO 1: LightGBM clasificación (delay >15 min)
# ─────────────────────────────────────────────
def train_lgbm_classifier(X_train, y_train, X_test, y_test):
    with mlflow.start_run(run_name="lgbm_delay_classification"):
        params = {
            "objective": "binary",
            "metric": "auc",
            "n_estimators": 1000,
            "learning_rate": 0.05,
            "num_leaves": 63,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_samples": 50,
            "n_jobs": -1,
            "verbose": -1,
        }
        mlflow.log_params(params)

        model = lgb.LGBMClassifier(**params)
        pipe = Pipeline([("prep", preprocessor), ("model", model)])
        pipe.fit(X_train, y_train,
                 model__eval_set=[(X_test, y_test)],
                 model__callbacks=[lgb.early_stopping(50, verbose=False)])

        # Calibración de probabilidades (isotonic para datasets grandes)
        calibrated = CalibratedClassifierCV(pipe, method="isotonic", cv="prefit")
        calibrated.fit(X_test, y_test)

        from sklearn.metrics import roc_auc_score, f1_score
        preds = calibrated.predict(X_test)
        proba = calibrated.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, proba)
        f1  = f1_score(y_test, preds)
        mlflow.log_metrics({"AUC_ROC": auc, "F1": f1})
        mlflow.sklearn.log_model(calibrated, "lgbm_delay_classifier")
        print(f"LightGBM Classification → AUC-ROC: {auc:.4f} | F1: {f1:.4f}")
        return calibrated

# ─────────────────────────────────────────────
# 7. MODELO 2: XGBoost regresión (minutos de delay)
# ─────────────────────────────────────────────
def train_xgb_regressor(X_train, y_train, X_test, y_test):
    with mlflow.start_run(run_name="xgb_delay_regression"):
        params = {
            "objective": "reg:squarederror",
            "n_estimators": 1000,
            "learning_rate": 0.05,
            "max_depth": 6,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "tree_method": "hist",  # más rápido en CPU
            "n_jobs": -1,
        }
        mlflow.log_params(params)

        model = xgb.XGBRegressor(**params)
        pipe = Pipeline([("prep", preprocessor), ("model", model)])
        pipe.fit(X_train, y_train,
                 model__eval_set=[(X_test, y_test)],
                 model__early_stopping_rounds=50,
                 model__verbose=False)

        from sklearn.metrics import mean_squared_error
        preds = pipe.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        mape = np.mean(np.abs((y_test - preds) / (y_test + 1e-6))) * 100
        mlflow.log_metrics({"RMSE": rmse, "MAPE": mape})
        mlflow.sklearn.log_model(pipe, "xgb_delay_regressor")
        print(f"XGBoost Regression → RMSE: {rmse:.2f} min | MAPE: {mape:.2f}%")
        return pipe

# ─────────────────────────────────────────────
# 8. SHAP: explicación de predicciones
# ─────────────────────────────────────────────
def explain_predictions(model, X_sample, feature_names):
    explainer = shap.TreeExplainer(model.named_steps["model"])
    X_transformed = model.named_steps["prep"].transform(X_sample)
    shap_values = explainer.shap_values(X_transformed)
    shap.summary_plot(shap_values, X_transformed, feature_names=feature_names)
    return shap_values

# ─────────────────────────────────────────────
# 9. FASTAPI: endpoint /predict-delay
# ─────────────────────────────────────────────
app = FastAPI(title="Airline Delay Prediction API")

class FlightInput(BaseModel):
    carrier: str
    origin: str
    dest: str
    dep_hour: int
    day_of_week: int
    month: int
    distance: float
    air_time: float
    inbound_flight_delay: float = 0.0
    windspeed_origin: float = 0.0
    precipitation_origin: float = 0.0
    windspeed_dest: float = 0.0
    precipitation_dest: float = 0.0

@app.post("/predict-delay")
def predict_delay(flight: FlightInput):
    import pandas as pd
    # Cargar modelos desde MLflow (en producción usar mlflow.pyfunc.load_model)
    data = pd.DataFrame([flight.dict()])
    delay_prob   = lgbm_model.predict_proba(data)[:, 1][0]
    delay_minutes = max(0, xgb_model.predict(data)[0])
    return {
        "delay_probability": round(float(delay_prob), 4),
        "expected_delay_minutes": round(float(delay_minutes), 1),
        "risk_level": "HIGH" if delay_prob > 0.6 else "MEDIUM" if delay_prob > 0.35 else "LOW"
    }

# uvicorn main:app --host 0.0.0.0 --port 8000
```

### Efecto cascada (rotativo)

El efecto cascada ocurre cuando un avión llega tarde a su destino y no tiene tiempo suficiente de turnaround, arrastrando el delay al siguiente vuelo. Este es el predictor más poderoso según múltiples papers de aviación (ATC, Boeing Fleet Statistics).

Ejemplo real: avión CC-BGP llega a SCL con 45 min de delay → sale tarde a GRU → llega tarde a GRU → siguiente vuelo GRU-SCL sale tarde también.

```python
def compute_inbound_delay(df: pl.DataFrame) -> pl.DataFrame:
    """
    Calcula InboundFlightDelay: delay del vuelo anterior del mismo avión.
    Requiere ordenar por TAIL_NUM + FL_DATE + DEP_TIME.
    """
    df = df.sort(["TAIL_NUM", "FL_DATE", "DEP_TIME"])

    # Para cada vuelo, tomar el ARR_DELAY del vuelo inmediatamente anterior
    # del mismo avión (tail_number = matrícula)
    df = df.with_columns([
        pl.col("ARR_DELAY")
          .shift(1)
          .over("TAIL_NUM")
          .alias("InboundFlightDelay"),

        pl.col("DEST")
          .shift(1)
          .over("TAIL_NUM")
          .alias("PrevDest"),  # para validar que coincide con ORIGIN
    ])

    # Validación: el destino anterior debe ser el mismo que el origen actual
    # Si no coincide, el avión rotó de base → InboundFlightDelay = 0
    df = df.with_columns([
        pl.when(pl.col("PrevDest") != pl.col("ORIGIN"))
          .then(0.0)
          .otherwise(pl.col("InboundFlightDelay"))
          .alias("InboundFlightDelay")
    ])

    # Llenar NaN del primer vuelo del día de cada avión con 0
    df = df.with_columns([
        pl.col("InboundFlightDelay").fill_null(0.0)
    ])

    return df

# Importancia típica de InboundFlightDelay en SHAP:
# - En clasificación: mayor SHAP value que cualquier otro feature
# - En regresión: explica ~35% de la varianza del delay
# - ADVERTENCIA: en producción requiere datos en tiempo real del sistema OPS
```

### Integración con clima

```python
# OpenMeteo: API gratuita sin key, datos históricos y forecast
# Endpoint: https://api.open-meteo.com/v1/forecast
# Features útiles: windspeed_10m, precipitation, visibility, cloudcover, weathercode
# Código para batch request de condiciones climáticas por aeropuerto y fecha
import requests
import time
from typing import Dict, List

# Coordenadas de aeropuertos clave LATAM
AIRPORT_COORDS = {
    "SCL": (-33.393, -70.786),   # Santiago
    "EZE": (-34.822, -58.535),   # Buenos Aires Ezeiza
    "GRU": (-23.431, -46.469),   # São Paulo Guarulhos
    "LIM": (-12.022, -77.114),   # Lima Jorge Chávez
    "BOG": (4.702,  -74.147),    # Bogotá El Dorado
    "PMC": (-38.926, -72.985),   # Temuco (clima andino)
    "PUQ": (-53.002, -70.855),   # Punta Arenas (Patagonia)
    "ATL": (33.640, -84.428),    # Atlanta (referencia BTS)
    "ORD": (41.978, -87.905),    # Chicago O'Hare (referencia BTS)
}

def get_weather_for_flight(lat: float, lon: float, date: str) -> Dict:
    """
    Obtiene condiciones climáticas horarias para un aeropuerto y fecha.
    date: formato YYYY-MM-DD
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&hourly=windspeed_10m,precipitation,visibility,cloudcover,weathercode"
        f"&start_date={date}&end_date={date}"
        f"&timezone=auto"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "hours": data["hourly"]["time"],
        "windspeed": data["hourly"]["windspeed_10m"],
        "precipitation": data["hourly"]["precipitation"],
        "visibility": data["hourly"]["visibility"],
        "cloudcover": data["hourly"]["cloudcover"],
        "weathercode": data["hourly"]["weathercode"],
    }

def get_weather_for_flights_batch(
    flights: pl.DataFrame,
    airport_coords: Dict[str, tuple]
) -> pl.DataFrame:
    """
    Enriquece un DataFrame de vuelos con datos climáticos.
    Respeta el rate limit de OpenMeteo: máx 10,000 req/día.
    """
    weather_cache = {}
    results = []

    for row in flights.iter_rows(named=True):
        origin = row["ORIGIN"]
        dep_date = str(row["FL_DATE"])
        cache_key = f"{origin}_{dep_date}"

        if cache_key not in weather_cache:
            if origin in airport_coords:
                lat, lon = airport_coords[origin]
                try:
                    weather_cache[cache_key] = get_weather_for_flight(lat, lon, dep_date)
                    time.sleep(0.1)  # 10 req/seg máx para no saturar la API
                except Exception as e:
                    print(f"Weather API error for {origin} {dep_date}: {e}")
                    weather_cache[cache_key] = None

        dep_hour = int(row["DEP_TIME"] // 100) if row["DEP_TIME"] else 12
        weather = weather_cache.get(cache_key)
        if weather and dep_hour < len(weather["windspeed"]):
            results.append({
                "windspeed_10m_origin": weather["windspeed"][dep_hour],
                "precipitation_origin": weather["precipitation"][dep_hour],
                "visibility_origin": weather["visibility"][dep_hour],
            })
        else:
            results.append({
                "windspeed_10m_origin": 0.0,
                "precipitation_origin": 0.0,
                "visibility_origin": 10000.0,  # buena visibilidad por defecto
            })

    weather_df = pl.DataFrame(results)
    return pl.concat([flights, weather_df], how="horizontal")

# WMO Weather Codes relevantes para aviación:
# 0: Despejado | 51-67: Lluvia | 71-77: Nieve | 80-99: Tormentas
# Crear feature binario: IsAdverseWeather = weathercode >= 51
```

### Métricas objetivo

| Modelo | Métrica | Baseline (RF vanilla) | Objetivo producción |
|--------|---------|-----------------------|---------------------|
| Clasificación delay | AUC-ROC | 0.72 | >0.87 |
| Clasificación delay | F1-score | 0.58 | >0.75 |
| Regresión minutos | RMSE | 28 min | <18 min |
| Regresión minutos | MAPE | 45% | <25% |

Comando de evaluación rápida:
```python
from sklearn.metrics import classification_report, roc_auc_score
print(classification_report(y_test, preds))
print(f"AUC-ROC: {roc_auc_score(y_test, proba):.4f}")
```

### Pitfalls

- InboundFlightDelay es el feature más poderoso pero requiere datos en tiempo real en producción — en entrenamiento usar el valor real, en inferencia usar el dato del sistema OPS
- No incluir ArrDelay en features para predecir DepDelay (leakage obvio: ArrDelay del vuelo actual no existe en el momento de predecir)
- El clima en Patagonia y Andes es muy diferente al clima en EEUU — los modelos entrenados en BTS subestiman el impacto climático en rutas andinas (PUQ, PMC, CJC)
- LightGBM es 3-5x más rápido que XGBoost en datasets grandes de BTS — usar LightGBM como modelo base y XGBoost solo para regresión o ensemble
- Datos de BTS: vuelos cancelados tienen ArrDelay=NaN — crear target separado para cancelación vs delay (problema de clasificación binaria independiente)
- OpenMeteo tiene rate limiting: máximo 10,000 requests/día en tier gratuito — implementar caché por aeropuerto+fecha para no repetir requests
- TargetEncoder puede causar data leakage si no se aplica correctamente en cross-validation — usar fit solo en train fold
- Las aerolíneas de bajo costo (Spirit, Frontier) tienen distribuciones de delay muy distintas a las legacy (AA, UA, DL) — considerar modelos por segmento o feature de tipo de aerolínea

### Instalación

```bash
pip install polars lightgbm xgboost scikit-learn mlflow shap fastapi uvicorn category-encoders requests
```

Versiones recomendadas (Jun 2025):
- polars>=0.20.0
- lightgbm>=4.3.0
- xgboost>=2.0.0
- scikit-learn>=1.4.0
- mlflow>=2.12.0
- shap>=0.45.0
- fastapi>=0.111.0
