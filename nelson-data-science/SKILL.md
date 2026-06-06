---
name: nelson-data-science
title: Data Science - ML, XGBoost, Feature Engineering, Optimizacion
description: Data Science para el equipo Nelson. Carga de datos, feature engineering, entrenamiento con XGBoost/LightGBM/scikit-learn, optimizacion de hiperparametros con Optuna, tracking de experimentos, evaluacion de modelos, serializacion.
skill: nelson-data-science
author: equipo-nelson
version: 1.0.0
keywords: [data-science, ml, xgboost, lightgbm, optuna, feature-engineering, pandas, scikit-learn, hyperparameter-tuning]
dependencies: [nelson-observability]
---

# Data Science - Equipo Nelson

> Machine Learning clasico y feature engineering. La base antes de llegar a LLMs.

## Stack

| Tarea | Libreria | Notas |
|-------|----------|-------|
| Data loading | Polars | Mas rapido que pandas para grandes datasets |
| Data loading (legacy) | Pandas | Cuando la API lo requiere |
| Feature engineering | scikit-learn | Pipelines, transformers, preprocessing |
| Gradient boosting | XGBoost | Predicciones tabulares, clasificacion, regression |
| Gradient boosting (alt) | LightGBM | Mas rapido en datasets grandes |
| Hiperparametros | Optuna | Optimizacion bayesiana |
| Metricas | scikit-learn | Accuracy, precision, recall, AUC, RMSE |
| Tracking | MLflow | Experimentos, modelos, artifacts |
| Serializacion | joblib | Guardar modelos entrenados |
| Validacion | scikit-learn | Cross-validation, train/test split |
## Data Pipelines con Polars (Excel / CSV / Joins)

### Patrón operativo: pipeline de 4 sheets (cobranza + facturación) con visualización

Cuando el usuario trae un Excel operativo con 4 hojas (`pendientes_cobro_contado`, `pendientes_cobro_trabajada`, `pendientes_facturar`, `pendientes_facturar_trabajada`), usar este patrón:

1. Leer las 4 hojas y normalizar `envio_id` como string.
2. Merge de cobranza (`contado` + `trabajada`) y aplicar exclusión `incluir_cc=false`.
3. Excluir del circuito de cobranza toda fila cuyo `envio_id` esté en `pendientes_facturar`.
4. Calcular `saldo_pendiente = importe_total - monto_cobrado` y estado (`cobrado`/`parcial`/`pendiente`).
5. Aplicar regla T+1 para `transferencia` (`fecha_impacto = fecha_cobro + 1 día`).
6. Auto-asignar referente faltante (round-robin) para no dejar casos huérfanos.
7. Generar output Excel con sheets `pipeline_cobranza`, `pipeline_facturacion`, `dashboard` (KPIs).
8. Exponer resumen para UI (KPIs + stages + preview tabular + download URL).

Ver referencia: `references/excel-4sheet-cobranzas-pipeline.md`

### Patrón: Cruzar múltiples Excels con joins + reglas LLM

Escenario típico del equipo: recibir varios archivos Excel/CSV que deben cruzarse por columnas clave, aplicar reglas de negocio, y generar un Excel resultante.

```python
# app/services/excel_processor.py
import polars as pl
from pathlib import Path

def merge_dataframes(
    left: pl.DataFrame, right: pl.DataFrame,
    left_key: str, right_key: str, join_type: str = "inner",
) -> pl.DataFrame:
    """Join seguro con normalización de tipos."""
    if left_key not in left.columns:
        raise ValueError(f"Columna '{left_key}' no existe. Columnas: {left.columns}")
    if right_key not in right.columns:
        raise ValueError(f"Columna '{right_key}' no existe. Columnas: {right.columns}")
    left = left.with_columns(pl.col(left_key).cast(pl.Utf8))
    right = right.with_columns(pl.col(right_key).cast(pl.Utf8))
    return left.join(right, left_on=left_key, right_on=right_key, how=join_type)


def apply_llm_dataframe_rules(
    df: pl.DataFrame, prompt: str, client, model: str
) -> pl.DataFrame:
    """Envía una muestra del DataFrame a un LLM y ejecuta el código Polars generado.
    
    Seguridad: el código se ejecuta en un namespace aislado sin __builtins__
    permitidos. Solo Polars y el DataFrame `df` están disponibles.
    """
    schema_desc = "\n".join([f"  - {c}: {df[c].dtype}" for c in df.columns])
    sample = df.head(5).to_dicts()
    sample_str = "\n".join([f"  {row}" for row in sample])
    
    full_prompt = f"""Sos un experto en análisis de datos con Polars (Python).

REGLAS DE SEGURIDAD:
- NO uses eval(), exec(), open(), os, sys, subprocess.
- SOLO operaciones de Polars: filtros, joins, groupby, select, with_columns.
- El resultado debe ser un DataFrame de Polars.
- No escribas explicaciones. Solo código.

ESTRUCTURA DEL DATAFRAME:
{schema_desc}

MUESTRA DE DATOS:
{sample_str}

DESCRIPCIÓN DEL USUARIO:
{prompt}

GENERÁ SOLO EL CÓDIGO (una expresión que devuelva el DataFrame transformado):"""
    
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": full_prompt}],
        temperature=0.1, max_tokens=2048,
    )
    code = resp.choices[0].message.content.strip()
    # Limpiar markdown
    for prefix in ["```python", "```"]:
        if code.startswith(prefix):
            code = code[len(prefix):]
    if code.endswith("```"):
        code = code[:-3]
    code = code.strip()
    
    local_ns = {"pl": pl, "df": df}
    exec(code, {"__builtins__": {}}, local_ns)
    result = local_ns.get("df", df)
    for key, val in local_ns.items():
        if isinstance(val, pl.DataFrame) and key != "df":
            result = val
            break
    return result
```

Ver referencia completa: `references/excel-polars-llm-pattern.md`

Caso operativo sin IA (reglas determinísticas CDO/PF): `references/excel-cdo-pf-static-pipeline.md`

## Pipeline estático CDO/PF (sin IA)

Cuando la operación requiere reproducir exactamente el flujo manual de hojas trabajadas (ej. `CDO Trabajada` y `PF Trabajada`), usar lógica fija en Python y **no** LLM.

Patrón recomendado:
1. Tomar solo hojas base del sistema (`CDO Sistema`, `PTE de Fact Sistema`).
2. Normalizar llaves (`envio_id`/`guia`) y columnas numéricas (`cobro`, `saldo`, `importe`).
3. Excluir ítems fuera de CC (según columna de inclusión/exclusión si existe).
4. Bloquear cobro para ítems presentes en pendientes de facturación.
5. Calcular `saldo_pendiente` y estado (`cobrado`/`parcial`) con reglas determinísticas.
6. Aplicar impacto T+1 para transferencias.
7. Asignar referente automáticamente cuando falta (round-robin configurable).
8. Exportar salida final con hojas exactas de negocio: `CDO Trabajada` y `PF Trabajada` (+ `KPIs` opcional).

Pitfall crítico:
- No usar `CDO Trabajada`/`PF Trabajada` como input del pipeline de producción; usarlas sólo como referencia de validación. El pipeline debe correr con las hojas sistema y producir trabajadas como output.

Ver referencia: `references/excel-cdo-pf-static-pipeline.md`.

## Visualizacion | matplotlib, seaborn, plotly | Ver skill `nelson-data-viz` |

## Carga de Datos

### Con Polars (recomendado)

```python
# app/services/data_loader.py
import polars as pl
from pathlib import Path
from app.core.logging import get_logger

logger = get_logger(__name__)

class DataLoader:
    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir

    def load_csv(self, filename: str) -> pl.DataFrame:
        """Cargar CSV con tipos inferidos."""
        path = self.data_dir / filename
        logger.info("loading_csv", path=str(path))
        return pl.read_csv(path, infer_schema_length=10000)

    def load_parquet(self, filename: str) -> pl.DataFrame:
        """Cargar Parquet (mas rapido y comprimido)."""
        path = self.data_dir / filename
        logger.info("loading_parquet", path=str(path))
        return pl.read_parquet(path)

    def load_from_db(self, query: str, db_url: str) -> pl.DataFrame:
        """Cargar desde PostgreSQL."""
        import connectorx
        logger.info("loading_from_db", query=query[:50])
        return pl.read_database_uri(query, db_url)
```

### Streaming para datasets gigantes

```python
def stream_csv_chunks(filename: str, chunk_size: int = 100_000):
    """Procesar CSV en chunks para no cargar todo en memoria."""
    return pl.read_csv_batched(filename, batch_size=chunk_size)
```

## Feature Engineering

```python
# app/services/features.py
import polars as pl
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

class FeatureEngineer:
    def __init__(self):
        self.numeric_features = []
        self.categorical_features = []
        self.pipeline = None

    def build_pipeline(self, numeric: list[str], categorical: list[str]):
        """Construir pipeline de preprocessing."""
        self.numeric_features = numeric
        self.categorical_features = categorical

        self.pipeline = ColumnTransformer([
            ("num", StandardScaler(), numeric),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
        ])
        return self.pipeline

    def add_temporal_features(self, df: pl.DataFrame, date_col: str) -> pl.DataFrame:
        """Agregar features temporales."""
        return df.with_columns([
            pl.col(date_col).dt.year().alias("year"),
            pl.col(date_col).dt.month().alias("month"),
            pl.col(date_col).dt.day().alias("day"),
            pl.col(date_col).dt.weekday().alias("weekday"),
            pl.col(date_col).dt.hour().alias("hour"),
        ])

    def add_lag_features(self, df: pl.DataFrame, col: str, lags: list[int]) -> pl.DataFrame:
        """Agregar features de lag (series temporales)."""
        for lag in lags:
            df = df.with_columns(
                pl.col(col).shift(lag).alias(f"{col}_lag_{lag}")
            )
        return df

    def add_rolling_stats(self, df: pl.DataFrame, col: str, window: int) -> pl.DataFrame:
        """Estadisticas rolling window."""
        return df.with_columns([
            pl.col(col).rolling_mean(window).alias(f"{col}_rolling_mean_{window}"),
            pl.col(col).rolling_std(window).alias(f"{col}_rolling_std_{window}"),
        ])
```

## Entrenamiento con XGBoost

```python
# app/services/trainer.py
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, roc_auc_score, mean_squared_error
import joblib
from pathlib import Path
from app.core.logging import get_logger

logger = get_logger(__name__)

class XGBoostTrainer:
    def __init__(self, task: str = "classification"):
        self.task = task
        self.model = None
        self.metrics = {}

    def train(
        self,
        X,
        y,
        test_size: float = 0.2,
        params: dict | None = None,
    ):
        """Entrenar modelo XGBoost."""
        logger.info("training_start", task=self.task, samples=len(X))

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y if self.task == "classification" else None
        )

        default_params = {
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
        }

        if self.task == "classification":
            default_params["objective"] = "binary:logistic"
            default_params["eval_metric"] = "logloss"
            self.model = xgb.XGBClassifier(**{**default_params, **(params or {})})
        else:
            default_params["objective"] = "reg:squarederror"
            self.model = xgb.XGBRegressor(**{**default_params, **(params or {})})

        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            early_stopping_rounds=10,
            verbose=False,
        )

        # Metricas
        y_pred = self.model.predict(X_test)
        if self.task == "classification":
            self.metrics["accuracy"] = accuracy_score(y_test, y_pred)
            self.metrics["auc"] = roc_auc_score(y_test, self.model.predict_proba(X_test)[:, 1])
        else:
            self.metrics["rmse"] = mean_squared_error(y_test, y_pred, squared=False)

        logger.info("training_complete", metrics=self.metrics)
        return self.metrics

    def cross_validate(self, X, y, cv: int = 5) -> dict:
        """Cross-validation."""
        scoring = "roc_auc" if self.task == "classification" else "neg_root_mean_squared_error"
        scores = cross_val_score(self.model, X, y, cv=cv, scoring=scoring)
        return {
            "mean": float(scores.mean()),
            "std": float(scores.std()),
            "scores": scores.tolist(),
        }

    def save(self, path: Path):
        """Guardar modelo."""
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
        logger.info("model_saved", path=str(path))

    def load(self, path: Path):
        """Cargar modelo."""
        self.model = joblib.load(path)
        logger.info("model_loaded", path=str(path))

    def feature_importance(self) -> dict:
        """Importancia de features."""
        if self.model is None:
            raise ValueError("Model not trained")
        importance = self.model.feature_importances_
        names = self.model.feature_names_in_ if hasattr(self.model, "feature_names_in_") else []
        return dict(sorted(zip(names, importance), key=lambda x: x[1], reverse=True))
```

## Optimizacion con Optuna

```python
# app/services/optimizer.py
import optuna
from sklearn.model_selection import cross_val_score
from app.core.logging import get_logger

logger = get_logger(__name__)

class HyperparameterOptimizer:
    def __init__(self, model_class, X, y, task: str = "classification"):
        self.model_class = model_class
        self.X = X
        self.y = y
        self.task = task
        self.study = None

    def objective(self, trial: optuna.Trial) -> float:
        """Funcion objetivo para Optuna."""
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 500),
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "gamma": trial.suggest_float("gamma", 0, 5),
            "reg_alpha": trial.suggest_float("reg_alpha", 0, 1),
            "reg_lambda": trial.suggest_float("reg_lambda", 0, 1),
        }

        model = self.model_class(**params)
        scoring = "roc_auc" if self.task == "classification" else "neg_root_mean_squared_error"
        scores = cross_val_score(model, self.X, self.y, cv=3, scoring=scoring, n_jobs=-1)
        return scores.mean()

    def optimize(self, n_trials: int = 50, timeout: int = 300) -> dict:
        """Optimizar hiperparametros."""
        logger.info("optimization_start", n_trials=n_trials)
        self.study = optuna.create_study(direction="maximize")
        self.study.optimize(self.objective, n_trials=n_trials, timeout=timeout, show_progress_bar=True)

        logger.info(
            "optimization_complete",
            best_score=self.study.best_value,
            best_params=self.study.best_params,
        )
        return {
            "best_score": self.study.best_value,
            "best_params": self.study.best_params,
            "n_trials": len(self.study.trials),
        }
```

## Tracking de Experimentos (MLflow)

```python
# app/services/experiments.py
import mlflow
from app.core.config import get_settings

settings = get_settings()

class ExperimentTracker:
    def __init__(self, experiment_name: str = "nelson-default"):
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI or "http://localhost:5000")
        mlflow.set_experiment(experiment_name)
        self.run = None

    def __enter__(self):
        self.run = mlflow.start_run()
        return self

    def __exit__(self, *args):
        mlflow.end_run()

    def log_params(self, params: dict):
        for key, value in params.items():
            mlflow.log_param(key, value)

    def log_metrics(self, metrics: dict, step: int | None = None):
        for key, value in metrics.items():
            mlflow.log_metric(key, value, step=step)

    def log_model(self, model, artifact_path: str = "model"):
        mlflow.sklearn.log_model(model, artifact_path)

    def log_artifact(self, local_path: str):
        mlflow.log_artifact(local_path)

# Uso
# with ExperimentTracker("flight-delay") as exp:
#     exp.log_params({"model": "xgboost", "n_estimators": 100})
#     exp.log_metrics({"auc": 0.85, "accuracy": 0.82})
#     exp.log_model(trained_model)
```

## Pipeline Completo

```python
# app/services/ml_pipeline.py
from app.services.data_loader import DataLoader
from app.services.features import FeatureEngineer
from app.services.trainer import XGBoostTrainer
from app.services.optimizer import HyperparameterOptimizer
from app.services.experiments import ExperimentTracker
import xgboost as xgb

class MLPipeline:
    def __init__(self):
        self.loader = DataLoader()
        self.engineer = FeatureEngineer()
        self.trainer = XGBoostTrainer()

    def run(self, data_path: str, target_col: str, optimize: bool = False):
        # 1. Cargar datos
        df = self.loader.load_csv(data_path)

        # 2. Feature engineering
        df = self.engineer.add_temporal_features(df, "fecha")
        df = df.drop_nulls()

        X = df.drop(target_col).to_pandas()
        y = df[target_col].to_pandas()

        # 3. Optimizar (opcional)
        if optimize:
            optimizer = HyperparameterOptimizer(xgb.XGBClassifier, X, y)
            result = optimizer.optimize(n_trials=30)
            self.trainer.train(X, y, params=result["best_params"])
        else:
            self.trainer.train(X, y)

        # 4. Guardar
        self.trainer.save("models/xgboost_model.joblib")

        return {
            "metrics": self.trainer.metrics,
            "feature_importance": self.trainer.feature_importance(),
        }
```

## Dependencias

```toml
# pyproject.toml [project.dependencies]
"polars>=1.15",
"fastexcel>=0.7",   # requerido por pl.read_excel
"xlsxwriter>=3.2",  # requerido por df.write_excel
"pandas>=2.2",
"xgboost>=2.1",
"lightgbm>=4.5",
"scikit-learn>=1.5",
"optuna>=4.1",
"mlflow>=2.19",
"joblib>=1.4",
"connectorx>=0.4",
```

## Checklist

- [ ] Datos cargados con tipos correctos
- [ ] Missing values tratados (imputacion o drop)
- [ ] Features temporales creadas si aplica
- [ ] Train/test split con stratify si es clasificacion
- [ ] Pipeline de preprocessing en produccion (mismo que en training)
- [ ] Modelo evaluado con metricas apropiadas (no solo accuracy)
- [ ] Cross-validation para estimar performance real
- [ ] Hiperparametros optimizados con Optuna
- [ ] Feature importance analizada
- [ ] Modelo versionado con MLflow
- [ ] Modelo serializado con joblib (no pickle crudo)
- [ ] Tests del pipeline completos

## Pitfalls

- FastAPI + pandas preview: `to_dict()` puede incluir `NaN/NaT/Timestamp` y romper JSON con `ValueError: Out of range float values are not JSON compliant`. Antes de responder, convertir explícitamente: `NaN/NaT -> None` y fechas a `isoformat()`.
- Polars Excel I/O usa dependencias opcionales: si falla `pl.read_excel` con `required package 'fastexcel' not found`, instalar `fastexcel`; si falla `df.write_excel` por `xlsxwriter`, instalar `xlsxwriter` y agregar ambas al proyecto para no romper en runtime.
- Data leakage: nunca fit el scaler/encoder con datos de test
- Overfitting en Optuna: limitar n_trials o usar nested CV
- Desbalance de clases: usar scale_pos_weight en XGBoost o SMOTE
- Features categoricas con alta cardinalidad: usar target encoding, no one-hot
- Polars vs Pandas: Polars es lazy, necesitas `.collect()` para ver resultados
- MLflow tracking URI: configurar bien para no perder experimentos
