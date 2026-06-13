---
name: nelson-airline-booking-prediction
description: "Prediccion de conversion de reservas para aerolineas con Python. Clasifica si un usuario completara su reserva. Stack: Polars, XGBoost, scikit-learn Pipelines, SMOTE, MLflow, SHAP. Features: canal de venta, ruta, anticipacion, ancillaries."
triggers:
  - prediccion reservas
  - booking conversion
  - abandono de reserva
  - conversion funnel aerolinea
  - clasificacion booking
version: "1.0.0"
---

# nelson-airline-booking-prediction

Skill de predicción de conversión de reservas para aerolíneas. Contexto: LAN Chile.
Basada en el repo British Airways Data Science Simulation, reescrita production-ready.

---

## El problema

- Las aerolíneas tienen una tasa de abandono de reserva del 40-60%.
- Predecir qué usuarios van a completar permite: retargeting inteligente, ofertas personalizadas, optimización del funnel de venta.
- El dataset está desbalanceado: ~85% no completan, ~15% completan → requiere estrategia especial.

---

## Features clave para LAN Chile

| Feature                | Descripción                                              | Tipo       |
|------------------------|----------------------------------------------------------|------------|
| purchase_lead          | Días entre inicio de búsqueda y fecha de vuelo           | Numérico   |
| sales_channel          | Canal de venta: web, app, call center, agencia           | Categórico |
| trip_type              | Tipo de viaje: solo ida, ida y vuelta, multidestino      | Categórico |
| flight_duration        | Horas de vuelo                                           | Numérico   |
| length_of_stay         | Noches en destino si es ida/vuelta                       | Numérico   |
| flight_hour            | Hora de salida del vuelo                                 | Numérico   |
| flight_day             | Día de la semana del vuelo                               | Categórico |
| booking_origin         | País desde donde se realiza la reserva                   | Categórico |
| origin                 | Aeropuerto de origen (código IATA)                       | Categórico |
| destination            | Aeropuerto de destino (código IATA)                      | Categórico |
| wants_extra_baggage    | Ancillary: equipaje extra                                | Binario    |
| wants_preferred_seat   | Ancillary: asiento preferido                             | Binario    |
| wants_in_flight_meals  | Ancillary: comida a bordo                                | Binario    |
| num_passengers         | Cantidad de pasajeros en la reserva                      | Numérico   |

---

## Pipeline ML producción-ready con scikit-learn Pipelines

```python
# ============================================================
# Pipeline ML Producción-Ready — LAN Chile Booking Prediction
# ============================================================

import polars as pl
import pandas as pd
import numpy as np
import pandera as pa
from pandera import Column, DataFrameSchema, Check

import mlflow
import mlflow.sklearn
import shap
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    classification_report, cohen_kappa_score,
    confusion_matrix, precision_recall_curve, f1_score
)

from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
import matplotlib.pyplot as plt
import holidays

# ------------------------------------------------------------
# 1. CARGA DE DATOS CON POLARS
# ------------------------------------------------------------

def load_data(path: str) -> pl.DataFrame:
    """Carga el dataset desde CSV o Parquet con Polars."""
    if path.endswith(".parquet"):
        df = pl.read_parquet(path)
    else:
        df = pl.read_csv(path, try_parse_dates=True)
    return df


# ------------------------------------------------------------
# 2. VALIDACIÓN DE SCHEMA CON PANDERA
# ------------------------------------------------------------

booking_schema = DataFrameSchema({
    "purchase_lead":         Column(int,   Check.greater_than_or_equal_to(0)),
    "sales_channel":         Column(str,   Check.isin(["Web", "App", "CallCenter", "Agency"])),
    "trip_type":             Column(str,   Check.isin(["OW", "RT", "MD"])),
    "flight_duration":       Column(float, Check.greater_than(0)),
    "length_of_stay":        Column(int,   Check.greater_than_or_equal_to(0)),
    "flight_hour":           Column(int,   Check.in_range(0, 23)),
    "flight_day":            Column(str),
    "booking_origin":        Column(str),
    "route":                 Column(str),   # Ej: "SCL-LIM"
    "wants_extra_baggage":   Column(int,   Check.isin([0, 1])),
    "wants_preferred_seat":  Column(int,   Check.isin([0, 1])),
    "wants_in_flight_meals": Column(int,   Check.isin([0, 1])),
    "num_passengers":        Column(int,   Check.greater_than(0)),
    "booking_date":          Column(pa.DateTime),
    "booking_complete":      Column(int,   Check.isin([0, 1])),
})

def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    return booking_schema.validate(df)


# ------------------------------------------------------------
# 3. FEATURE ENGINEERING
# ------------------------------------------------------------

CL_HOLIDAYS = holidays.Chile()

def feature_engineering(df: pl.DataFrame) -> pl.DataFrame:
    """
    - Extrae origin/destination desde campo route ("SCL-LIM" → "SCL", "LIM")
    - Calcula is_weekend, is_holiday, season
    """
    df = df.with_columns([
        pl.col("route").str.split("-").list.get(0).alias("origin"),
        pl.col("route").str.split("-").list.get(1).alias("destination"),
        pl.col("booking_date").dt.weekday().alias("_weekday"),  # 0=Lun, 6=Dom
    ])

    df = df.with_columns([
        (pl.col("_weekday") >= 5).cast(pl.Int8).alias("is_weekend"),
    ])

    # is_holiday se calcula en pandas (holidays lib no tiene soporte nativo Polars)
    pdf = df.to_pandas()
    pdf["is_holiday"] = pdf["booking_date"].apply(
        lambda d: int(d.date() in CL_HOLIDAYS)
    )

    # Season según mes (hemisferio sur)
    def get_season(month: int) -> str:
        if month in [12, 1, 2]:
            return "summer"
        elif month in [3, 4, 5]:
            return "autumn"
        elif month in [6, 7, 8]:
            return "winter"
        else:
            return "spring"

    pdf["season"] = pdf["booking_date"].dt.month.apply(get_season)

    return pl.from_pandas(pdf)


# ------------------------------------------------------------
# 4. SPLIT TEMPORAL — NO random_state
# ------------------------------------------------------------

def temporal_split(df: pd.DataFrame, test_ratio: float = 0.2):
    """
    Split TEMPORAL ordenado por fecha de reserva.
    NUNCA usar train_test_split random con datos de series temporales.
    """
    df_sorted = df.sort_values("booking_date").reset_index(drop=True)
    split_idx = int(len(df_sorted) * (1 - test_ratio))
    train = df_sorted.iloc[:split_idx]
    test  = df_sorted.iloc[split_idx:]
    return train, test


# ------------------------------------------------------------
# 5. DEFINICIÓN DE FEATURES Y PIPELINE
# ------------------------------------------------------------

NUMERIC_FEATURES = [
    "purchase_lead", "flight_duration", "length_of_stay",
    "flight_hour", "num_passengers",
]

CATEGORICAL_FEATURES = [
    "sales_channel", "trip_type", "flight_day",
    "booking_origin", "origin", "destination",
    "season",
]

BINARY_FEATURES = [
    "wants_extra_baggage", "wants_preferred_seat",
    "wants_in_flight_meals", "is_weekend", "is_holiday",
]

TARGET = "booking_complete"

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BINARY_FEATURES


def build_pipeline() -> Pipeline:
    """
    Pipeline sklearn con:
    - StandardScaler para numéricas
    - OrdinalEncoder para categóricas de baja cardinalidad
      (para rutas usar category_encoders.TargetEncoder)
    - XGBoost como clasificador base
    - Calibración de probabilidades
    """
    numeric_transformer = Pipeline([
        ("scaler", StandardScaler()),
    ])

    # OrdinalEncoder con handle_unknown para producción
    categorical_transformer = Pipeline([
        ("encoder", OrdinalEncoder(
            handle_unknown="use_encoded_value",
            unknown_value=-1,
        )),
    ])

    preprocessor = ColumnTransformer([
        ("num",  numeric_transformer,     NUMERIC_FEATURES),
        ("cat",  categorical_transformer, CATEGORICAL_FEATURES),
        ("bin",  "passthrough",           BINARY_FEATURES),
    ])

    xgb = XGBClassifier(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=6,   # aprox ratio negativo/positivo
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )

    calibrated_xgb = CalibratedClassifierCV(xgb, method="isotonic", cv=3)

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier",   calibrated_xgb),
    ])

    return pipeline


# ------------------------------------------------------------
# 6. SMOTE — SOLO EN TRAIN, NUNCA EN TEST
# ------------------------------------------------------------

def apply_smote(X_train: np.ndarray, y_train: np.ndarray):
    """
    SMOTE solo sobre el conjunto de entrenamiento.
    Aplicarlo antes del split es DATA LEAKAGE garantizado.
    """
    smote = SMOTE(sampling_strategy=0.3, random_state=42, k_neighbors=5)
    X_resampled, y_resampled = smote.fit_resample(X_train, y_train)
    print(f"Antes SMOTE: {np.bincount(y_train)}")
    print(f"Después SMOTE: {np.bincount(y_resampled)}")
    return X_resampled, y_resampled


# ------------------------------------------------------------
# 7. THRESHOLD OPTIMIZATION
# ------------------------------------------------------------

def find_optimal_threshold(y_true, y_proba) -> float:
    """
    Optimiza el threshold maximizando F1 para la clase minoritaria (booking=1).
    El default 0.5 es incorrecto con datasets desbalanceados.
    """
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-9)
    best_idx = np.argmax(f1_scores[:-1])
    best_threshold = thresholds[best_idx]
    print(f"Threshold óptimo: {best_threshold:.4f} | F1: {f1_scores[best_idx]:.4f}")
    return best_threshold


# ------------------------------------------------------------
# 8. ENTRENAMIENTO CON MLFLOW TRACKING
# ------------------------------------------------------------

def train_and_evaluate(data_path: str):
    mlflow.set_tracking_uri("./mlruns")
    mlflow.set_experiment("lan-chile-booking-prediction")

    # Carga y validación
    df_pl = load_data(data_path)
    df_pl = feature_engineering(df_pl)
    df    = df_pl.to_pandas()
    df    = validate_schema(df)

    # Split temporal
    train_df, test_df = temporal_split(df, test_ratio=0.2)

    X_train = train_df[ALL_FEATURES]
    y_train = train_df[TARGET].values
    X_test  = test_df[ALL_FEATURES]
    y_test  = test_df[TARGET].values

    pipeline = build_pipeline()

    # Preprocesar SOLO para SMOTE (pipeline sin clasificador)
    preprocessor_only = Pipeline([
        ("preprocessor", pipeline.named_steps["preprocessor"])
    ])
    X_train_proc = preprocessor_only.fit_transform(X_train, y_train)
    X_test_proc  = preprocessor_only.transform(X_test)

    # SMOTE sobre train procesado
    X_train_resampled, y_train_resampled = apply_smote(X_train_proc, y_train)

    with mlflow.start_run(run_name="xgboost-smote-calibrated"):
        # Entrenar clasificador sobre datos balanceados
        clf = pipeline.named_steps["classifier"]
        clf.fit(X_train_resampled, y_train_resampled)

        # Predecir probabilidades
        y_proba = clf.predict_proba(X_test_proc)[:, 1]

        # Threshold óptimo
        best_threshold = find_optimal_threshold(y_test, y_proba)
        y_pred = (y_proba >= best_threshold).astype(int)

        # Métricas
        auc_roc   = roc_auc_score(y_test, y_proba)
        avg_prec  = average_precision_score(y_test, y_proba)
        kappa     = cohen_kappa_score(y_test, y_pred)
        report    = classification_report(y_test, y_pred, output_dict=True)
        f1_class1 = report["1"]["f1-score"]

        print(f"\nAUC-ROC:          {auc_roc:.4f}")
        print(f"Average Precision: {avg_prec:.4f}")
        print(f"Cohen's Kappa:     {kappa:.4f}")
        print(f"F1 (clase 1):      {f1_class1:.4f}")
        print(classification_report(y_test, y_pred))

        # MLflow: log params
        mlflow.log_param("model",          "XGBoost+SMOTE+Calibrated")
        mlflow.log_param("threshold",      round(best_threshold, 4))
        mlflow.log_param("smote_strategy", 0.3)
        mlflow.log_param("test_ratio",     0.2)

        # MLflow: log metrics
        mlflow.log_metric("auc_roc",           auc_roc)
        mlflow.log_metric("avg_precision",     avg_prec)
        mlflow.log_metric("cohen_kappa",       kappa)
        mlflow.log_metric("f1_class1",         f1_class1)
        mlflow.log_metric("recall_class1",     report["1"]["recall"])
        mlflow.log_metric("precision_class1",  report["1"]["precision"])

        # Confusion matrix normalizada
        cm = confusion_matrix(y_test, y_pred, normalize="true")
        fig, ax = plt.subplots()
        im = ax.imshow(cm, cmap="Blues")
        ax.set_title("Confusion Matrix (normalizada)")
        ax.set_xlabel("Predicho"); ax.set_ylabel("Real")
        fig.colorbar(im)
        plt.savefig("confusion_matrix.png")
        mlflow.log_artifact("confusion_matrix.png")

        # Curva Precision-Recall
        prec, rec, _ = precision_recall_curve(y_test, y_proba)
        fig2, ax2 = plt.subplots()
        ax2.plot(rec, prec)
        ax2.set_xlabel("Recall"); ax2.set_ylabel("Precision")
        ax2.set_title(f"PR Curve — AP={avg_prec:.3f}")
        plt.savefig("pr_curve.png")
        mlflow.log_artifact("pr_curve.png")

        # SHAP values para explicabilidad
        explainer  = shap.TreeExplainer(clf.calibrated_classifiers_[0].estimator)
        shap_vals  = explainer.shap_values(X_test_proc[:500])
        shap.summary_plot(shap_vals, X_test_proc[:500], show=False)
        plt.savefig("shap_summary.png", bbox_inches="tight")
        mlflow.log_artifact("shap_summary.png")

        # Export modelo completo
        joblib.dump(
            {"preprocessor": preprocessor_only, "classifier": clf, "threshold": best_threshold},
            "booking_model.joblib"
        )
        mlflow.log_artifact("booking_model.joblib")
        print("\nModelo guardado: booking_model.joblib")

    return clf, preprocessor_only, best_threshold


if __name__ == "__main__":
    train_and_evaluate("data/bookings.csv")
```

---

## Métricas correctas para dataset desbalanceado

NO usar accuracy como métrica principal.
Con 85% de clase negativa, un modelo que predice siempre 0 obtiene 85% de accuracy — y es inútil.

Métricas correctas:

- AUC-ROC: área bajo curva ROC, mide discriminación general.
- Average Precision (PR curve): más informativa que ROC cuando el dataset está muy desbalanceado.
- F1-score por clase: especialmente F1 de clase 1 (completó reserva).
- Cohen's Kappa: mide acuerdo corregido por azar, excelente para desbalance.
- Confusion matrix normalizada: muestra recall real por clase.
- Curva Precision-Recall: siempre incluirla para datasets desbalanceados. ROC sola miente.

```python
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    ConfusionMatrixDisplay,
    PrecisionRecallDisplay,
)

# Ejemplo de reporte completo
print(classification_report(y_test, y_pred, target_names=["No completó", "Completó"]))

# PR curve
PrecisionRecallDisplay.from_predictions(y_test, y_proba).plot()

# Confusion matrix normalizada
ConfusionMatrixDisplay(
    confusion_matrix(y_test, y_pred, normalize="true"),
    display_labels=["No completó", "Completó"]
).plot(cmap="Blues")
```

---

## Serving del modelo

```python
# ============================================================
# FastAPI — Serving del modelo de booking prediction
# ============================================================
# Ejecutar: uvicorn serving:app --host 0.0.0.0 --port 8000

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import joblib
import numpy as np
import shap
import pandas as pd

app = FastAPI(title="LAN Chile Booking Prediction API", version="1.0.0")

# Cargar modelo al startup
model_artifacts = joblib.load("booking_model.joblib")
preprocessor    = model_artifacts["preprocessor"]
classifier      = model_artifacts["classifier"]
threshold       = model_artifacts["threshold"]
explainer       = shap.TreeExplainer(classifier.calibrated_classifiers_[0].estimator)

FEATURE_NAMES = [
    "purchase_lead", "flight_duration", "length_of_stay", "flight_hour",
    "num_passengers", "sales_channel", "trip_type", "flight_day",
    "booking_origin", "origin", "destination", "season",
    "wants_extra_baggage", "wants_preferred_seat", "wants_in_flight_meals",
    "is_weekend", "is_holiday",
]


class BookingFeatures(BaseModel):
    purchase_lead:          int   = Field(..., ge=0,  description="Días entre búsqueda y vuelo")
    flight_duration:        float = Field(..., gt=0,  description="Duración del vuelo en horas")
    length_of_stay:         int   = Field(..., ge=0,  description="Noches en destino")
    flight_hour:            int   = Field(..., ge=0, le=23)
    num_passengers:         int   = Field(..., ge=1)
    sales_channel:          str   = Field(..., description="Web | App | CallCenter | Agency")
    trip_type:              str   = Field(..., description="OW | RT | MD")
    flight_day:             str   = Field(..., description="Mon | Tue | Wed | Thu | Fri | Sat | Sun")
    booking_origin:         str   = Field(..., description="Código ISO país")
    origin:                 str   = Field(..., description="IATA origen, ej: SCL")
    destination:            str   = Field(..., description="IATA destino, ej: LIM")
    season:                 str   = Field(..., description="summer | autumn | winter | spring")
    wants_extra_baggage:    int   = Field(..., ge=0, le=1)
    wants_preferred_seat:   int   = Field(..., ge=0, le=1)
    wants_in_flight_meals:  int   = Field(..., ge=0, le=1)
    is_weekend:             int   = Field(..., ge=0, le=1)
    is_holiday:             int   = Field(..., ge=0, le=1)


class PredictionResponse(BaseModel):
    booking_complete: int
    probability:      float
    explanation:      dict


@app.post("/predict", response_model=PredictionResponse)
def predict(features: BookingFeatures):
    try:
        row = pd.DataFrame([features.dict()])[FEATURE_NAMES]

        X_proc = preprocessor.transform(row)
        proba  = classifier.predict_proba(X_proc)[0, 1]
        pred   = int(proba >= threshold)

        # SHAP top features
        shap_vals   = explainer.shap_values(X_proc)[0]
        top_idx     = np.argsort(np.abs(shap_vals))[::-1][:5]
        top_features = {
            FEATURE_NAMES[i]: round(float(shap_vals[i]), 4)
            for i in top_idx
        }

        return PredictionResponse(
            booking_complete=pred,
            probability=round(float(proba), 4),
            explanation={"top_features": top_features},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok", "threshold": threshold}
```

Ejemplo de request:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "purchase_lead": 45,
    "flight_duration": 3.5,
    "length_of_stay": 7,
    "flight_hour": 10,
    "num_passengers": 2,
    "sales_channel": "Web",
    "trip_type": "RT",
    "flight_day": "Fri",
    "booking_origin": "CL",
    "origin": "SCL",
    "destination": "LIM",
    "season": "summer",
    "wants_extra_baggage": 1,
    "wants_preferred_seat": 0,
    "wants_in_flight_meals": 0,
    "is_weekend": 0,
    "is_holiday": 0
  }'
```

Respuesta esperada:

```json
{
  "booking_complete": 1,
  "probability": 0.73,
  "explanation": {
    "top_features": {
      "purchase_lead": 0.2841,
      "wants_extra_baggage": 0.1203,
      "flight_duration": 0.0987,
      "length_of_stay": 0.0812,
      "sales_channel": -0.0631
    }
  }
}
```

---

## Comparativa de modelos (lecciones del repo BA)

| Modelo                          | AUC-ROC | Recall clase 1 | Nota                     |
|---------------------------------|---------|----------------|--------------------------|
| RF vanilla                      | 0.55    | 11%            | Baseline malo            |
| RF + SMOTE                      | 0.61    | 31%            | Mejora con balance       |
| XGBoost + SMOTE                 | 0.64    | 42%            | Mejor sin tuning         |
| XGBoost + SMOTE + GridSearch    | 0.76    | 37%            | Mejor global             |
| LightGBM + SMOTE + Optuna       | ~0.82   | ~50%           | Objetivo producción      |

Nota: GridSearch mejora AUC-ROC pero puede bajar el recall de clase 1. Siempre evaluar el tradeoff según el objetivo de negocio. Para retargeting, priorizar recall. Para ofertas personalizadas, priorizar precision.

---

## Pitfalls críticos

- NUNCA aplicar SMOTE antes del split — data leakage garantizado. SMOTE crea muestras sintéticas interpolando vecinos en train; si ya vio datos de test, las métricas están infladas y el modelo no generaliza.

- NUNCA usar train_test_split random con datos de reservas — temporal split obligatorio. Los patrones de booking cambian con el tiempo (temporadas, precios, eventos). Un split random filtra información del futuro al pasado.

- OrdinalEncoder en rutas con alta cardinalidad (miles de pares OD) — usar TargetEncoder o embeddings. OrdinalEncoder asigna orden arbitrario; para LAN Chile con cientos de pares origen-destino, usar `category_encoders.TargetEncoder` o embeddings de entidades.

- Threshold de 0.5 es incorrecto con desbalance — optimizar con precision_recall_curve. Con 85/15 de split, el modelo tiende a predecir 0 casi siempre. El threshold óptimo suele estar entre 0.25 y 0.40.

- purchase_lead=0 puede indicar error de datos o reserva same-day — validar. Filtrar o imputar antes de entrenar. Un valor de 0 podría ser una reserva legítima del mismo día o un error de captura del PNR.

- Datos de LAN Chile vienen de Amadeus/Sabre en formato PNR — parsing previo necesario. Los sistemas de reserva exportan datos en formato PNR criptado. Necesitas un parser ETL antes de llegar a este pipeline.

- MLflow necesita servidor o carpeta local: `mlflow.set_tracking_uri("./mlruns")`. Sin esto, MLflow guarda en memoria y se pierden los runs al reiniciar.

---

## Feature importance real (del repo BA)

Los 4 features más predictivos en British Airways (validados con SHAP):

1. purchase_lead — anticipación de compra
2. flight_duration — duración del vuelo
3. length_of_stay — duración de la estadía
4. flight_hour — hora de salida

Implicación para LAN Chile: el comportamiento de compra anticipada es el predictor más fuerte. Usuarios que buscan vuelos con más de 30 días de anticipación tienen mayor intención de compra real. Esto sugiere una estrategia de precios y retargeting diferenciada por ventana temporal:

- purchase_lead > 60 días: alta intención, ofrecer early bird discount
- purchase_lead 15-60 días: zona gris, candidatos a retargeting
- purchase_lead < 15 días: búsqueda impulsiva o comparativa, menor conversión

---

## Instalación

```bash
pip install polars scikit-learn xgboost lightgbm imbalanced-learn mlflow shap pandera joblib fastapi uvicorn optuna
```

Opcional para TargetEncoder de alta cardinalidad:

```bash
pip install category_encoders
```

Verificar versiones compatibles:

```bash
pip install "scikit-learn>=1.3" "xgboost>=2.0" "polars>=0.20" "mlflow>=2.10"
```
