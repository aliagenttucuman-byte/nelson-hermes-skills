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

- Data leakage: nunca fit el scaler/encoder con datos de test
- Overfitting en Optuna: limitar n_trials o usar nested CV
- Desbalance de clases: usar scale_pos_weight en XGBoost o SMOTE
- Features categoricas con alta cardinalidad: usar target encoding, no one-hot
- Polars vs Pandas: Polars es lazy, necesitas `.collect()` para ver resultados
- MLflow tracking URI: configurar bien para no perder experimentos
