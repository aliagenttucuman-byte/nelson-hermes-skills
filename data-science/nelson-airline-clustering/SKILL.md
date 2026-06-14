---
name: nelson-airline-clustering
description: "Clustering de pasajeros y rutas para aerolineas con Flash-KMeans (GPU) + fallback sklearn CPU. Segmentacion de millones de pasajeros en minutos. Casos de uso: segmentacion LAN PASS, clustering de rutas por KPI, anomaly detection en booking, agrupacion de series de demanda. Stack: Polars, PyTorch, flash-kmeans, scikit-learn."
triggers:
  - clustering pasajeros
  - segmentacion aerolinea
  - kmeans aerolinea
  - flash kmeans
  - clustering rutas
  - segmentacion LAN PASS
version: "1.0.0"
---

# nelson-airline-clustering

## Por qué Flash-KMeans y no sklearn

sklearn KMeans materializa la matriz N×K de distancias completa en RAM — con millones de pasajeros explota.
Flash-KMeans usa kernels Triton IO-aware que nunca materializan esa matriz: O(N×D + K×D) en memoria, mismo resultado exacto.

| | sklearn | flash-kmeans |
|---|---|---|
| Hardware | CPU only | GPU NVIDIA (Triton) |
| Memoria | O(N×K×D) | O(N×D + K×D) |
| Velocidad | baseline | 3-10x más rápido |
| Batching | no | nativo (B, N, D) |
| Distancias | Euclidean | Euclidean, Cosine, Dot |
| Datos > VRAM | OOM | streaming automático |
| Multi-GPU | no | sí, auto |

**Origen:** Paper arXiv:2603.09229 "Flash-KMeans: Fast and Memory-Efficient Exact K-Means" (Berkeley/MIT, 2026). MIT License.

## Instalación

```bash
pip install flash-kmeans torch polars scikit-learn
```

Verificar GPU disponible:
```python
import torch
print(torch.cuda.is_available())   # True = GPU disponible
print(torch.cuda.get_device_name()) # ej: NVIDIA A100
```

## Helper: GPU con fallback automático a sklearn

```python
import torch
import numpy as np
import polars as pl
from typing import Optional

def kmeans_auto(
    df: pl.DataFrame,
    features: list[str],
    k: int,
    niter: int = 25,
    metric: str = "euclidean",
    seed: int = 42
) -> pl.Series:
    """
    K-Means con fallback automático GPU -> CPU.
    Retorna Polars Series con cluster labels.
    """
    X = df.select(features).to_numpy().astype(np.float32)

    if torch.cuda.is_available():
        from flash_kmeans import FlashKMeans
        tensor = torch.from_numpy(X).cuda()
        km = FlashKMeans(d=X.shape[1], k=k, niter=niter, seed=seed)
        labels = km.fit_predict(tensor).cpu().numpy()
        print(f"Flash-KMeans GPU: {k} clusters, {len(X):,} puntos")
    else:
        from sklearn.cluster import KMeans
        km = KMeans(n_clusters=k, n_init=10, random_state=seed)
        labels = km.fit_predict(X)
        print(f"sklearn KMeans CPU: {k} clusters, {len(X):,} puntos (sin GPU)")

    return pl.Series("cluster", labels)
```

## Casos de uso LAN Chile

### 1. Segmentación de pasajeros LAN PASS

Segmentar millones de clientes por comportamiento para pricing personalizado y loyalty dinámico.

```python
import polars as pl
from nelson_airline_clustering import kmeans_auto  # helper de arriba

# Features de pasajero
df_pasajeros = pl.read_parquet("pasajeros_lan.parquet")

features = [
    "vuelos_ultimo_anio",
    "distancia_promedio_km",
    "pct_clase_business",
    "anticipacion_compra_dias",
    "lifetime_value_usd",
    "pct_rutas_internacionales",
    "uso_app",                    # 0/1
    "tiene_lan_pass",             # 0/1
    "millas_acumuladas",
]

# Normalizar antes de clustering
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
df_norm = pl.from_numpy(
    scaler.fit_transform(df_pasajeros.select(features).to_numpy()),
    schema=features
)

# Clustering: 6 segmentos típicos en aerolíneas
labels = kmeans_auto(df_norm, features, k=6, niter=50)
df_pasajeros = df_pasajeros.with_columns(labels)

# Perfil de cada segmento
perfil = df_pasajeros.group_by("cluster").agg([
    pl.len().alias("cantidad"),
    pl.col("lifetime_value_usd").mean().alias("ltv_promedio"),
    pl.col("vuelos_ultimo_anio").mean().alias("frecuencia_media"),
    pl.col("pct_clase_business").mean().alias("pct_business"),
    pl.col("millas_acumuladas").mean().alias("millas_media"),
]).sort("ltv_promedio", descending=True)

print(perfil)
```

Segmentos típicos que emergen:
- Cluster 0: Viajero frecuente business, alto LTV — prioridad retención
- Cluster 1: Turista estacional, sensible al precio — target promos
- Cluster 2: Viajero ocasional doméstico — crecer frecuencia
- Cluster 3: Corporativo internacional, anticipa poco — pricing dinámico
- Cluster 4: Nuevo cliente, bajo LTV — onboarding LAN PASS
- Cluster 5: En riesgo de churn, bajó frecuencia — retargeting

### 2. Clustering de rutas por KPI

Agrupar rutas similares para identificar patrones operativos y oportunidades de red.

```python
# Features por ruta
df_rutas = pl.read_csv("kpis_rutas_lan.csv")

features_ruta = [
    "load_factor",           # % ocupación
    "yield_usd_per_pkm",     # revenue por pasajero-km
    "on_time_rate",          # % puntualidad
    "demanda_mensual_pax",
    "distancia_km",
    "competidores_en_ruta",
    "estacionalidad_coef",   # varianza de demanda por mes
    "cask",                  # costo por asiento-km
    "rask",                  # revenue por asiento-km
]

labels = kmeans_auto(df_rutas, features_ruta, k=5, niter=30)
df_rutas = df_rutas.with_columns(labels)

# Interpretar clusters
print(df_rutas.group_by("cluster").agg([
    pl.col("ruta").count().alias("n_rutas"),
    pl.col("load_factor").mean(),
    pl.col("yield_usd_per_pkm").mean(),
    pl.col("on_time_rate").mean(),
]).sort("yield_usd_per_pkm", descending=True))
```

Clusters esperados:
- Alta demanda + alto yield: rutas estrella (SCL-MIA, SCL-MAD)
- Alta demanda + bajo yield: rutas commodity con competencia
- Baja demanda + alto yield: nichos protegidos
- Baja demanda + bajo yield: candidatas a revisar frecuencia
- Estacionales: alto verano, bajo invierno — ajustar capacidad

### 3. Anomaly detection en patrones de booking

Detectar comportamientos anómalos (fraude, error sistemático, oportunidad de precio).

```python
# Embeddings de booking: cada transacción como vector
features_booking = [
    "purchase_lead_dias",
    "precio_pagado_usd",
    "distancia_ruta_km",
    "hora_compra",
    "dia_semana_compra",
    "anticipacion_normalizada",  # precio / precio_promedio_ruta
]

# Clustering con k alto para detectar outliers
labels = kmeans_auto(df_bookings, features_booking, k=50, niter=20)

# Puntos en clusters pequeños = anomalías
cluster_sizes = df_bookings.with_columns(labels).group_by("cluster").len()
small_clusters = cluster_sizes.filter(pl.col("len") < 10)
anomalias = df_bookings.filter(
    pl.col("cluster").is_in(small_clusters["cluster"])
)
print(f"Anomalías detectadas: {len(anomalias):,}")
```

### 4. Clustering de series de demanda por ruta (Batch mode)

Flash-KMeans soporta batching nativo (B, N, D) — ideal para agrupar múltiples series temporales en un solo llamado.

```python
import torch
from flash_kmeans import batch_kmeans_Euclid

# df_demanda: shape (n_rutas, 52, n_features) — 52 semanas por ruta
# Agrupar rutas con patrones de demanda similares

X_batch = torch.from_numpy(
    df_demanda_np.astype(np.float32)  # (n_rutas, 52, features)
).cuda()

# k clusters de patrones temporales
cluster_ids, centroids, n_iters = batch_kmeans_Euclid(
    X_batch,
    n_clusters=8,
    tol=1e-4,
    max_iter=100
)

# cluster_ids: (n_rutas,) — a qué patrón de demanda pertenece cada ruta
print(f"Rutas por patrón: {torch.bincount(cluster_ids)}")
```

## Elegir el número óptimo de clusters (K)

```python
import numpy as np
from sklearn.metrics import silhouette_score

def find_optimal_k(df: pl.DataFrame, features: list[str],
                   k_range: range = range(3, 12)) -> int:
    """Método del codo + silhouette score para elegir K óptimo."""
    X = df.select(features).to_numpy().astype(np.float32)
    inertias, silhouettes = [], []

    for k in k_range:
        if torch.cuda.is_available():
            from flash_kmeans import FlashKMeans
            km = FlashKMeans(d=X.shape[1], k=k, niter=25)
            labels = km.fit_predict(torch.from_numpy(X).cuda()).cpu().numpy()
            # inertia manual
            centroids = np.array([X[labels==i].mean(0) for i in range(k)])
            inertia = sum(((X[labels==i] - centroids[i])**2).sum() for i in range(k))
        else:
            from sklearn.cluster import KMeans
            km = KMeans(n_clusters=k, n_init=5, random_state=42)
            labels = km.fit_predict(X)
            inertia = km.inertia_

        inertias.append(inertia)
        silhouettes.append(silhouette_score(X, labels, sample_size=5000))
        print(f"k={k}: inertia={inertia:.0f}, silhouette={silhouettes[-1]:.3f}")

    # K óptimo = mejor silhouette
    best_k = k_range[np.argmax(silhouettes)]
    print(f"\nK óptimo: {best_k}")
    return best_k
```

## Visualización de clusters

```python
import plotly.express as px
from sklearn.decomposition import PCA

def plot_clusters(df: pl.DataFrame, features: list[str],
                  label_col: str = "cluster",
                  title: str = "Segmentación de Pasajeros"):
    """PCA 2D + scatter plot interactivo con Plotly."""
    X = df.select(features).to_numpy()
    labels = df[label_col].to_numpy()

    # Reducir a 2D para visualización
    pca = PCA(n_components=2, random_state=42)
    X_2d = pca.fit_transform(X)

    df_plot = pl.DataFrame({
        "PC1": X_2d[:, 0],
        "PC2": X_2d[:, 1],
        "cluster": labels.astype(str),
    })

    fig = px.scatter(
        df_plot.to_pandas(),
        x="PC1", y="PC2", color="cluster",
        title=title,
        template="plotly_white",
        opacity=0.6
    )
    fig.write_html(f"/tmp/{title.replace(' ', '_')}.html")
    fig.show()
```

## Pitfalls críticos

- **Compilación JIT Triton**: el primer llamado tarda ~30s compilando el kernel — es normal, los siguientes son instantáneos. No cancelar.
- **Normalizar SIEMPRE antes de K-Means**: features en escalas distintas dominan el clustering. Usar StandardScaler o MinMaxScaler antes de pasar a flash-kmeans.
- **Semilla no determinista en GPU**: los resultados pueden variar levemente entre runs en GPU — fijar `seed` en FlashKMeans y usar `torch.manual_seed()`.
- **Batch mode requiere mismo N en todas las batches**: si las rutas tienen diferente cantidad de semanas, hacer padding a la longitud máxima antes del batch.
- **FP16 vs FP32**: FP16 es 2x más rápido y usa la mitad de VRAM, pero puede tener errores numéricos en centroides con features de magnitud muy diferente — normalizar primero.
- **Sin GPU en ai-server**: el fallback sklearn funciona pero es lento para >500K filas — considerar Modal o RunPod para jobs de clustering grandes.
- **K-Means no es determinista con clusters vacíos**: si K es muy alto relativo a los datos, algunos clusters pueden quedar vacíos — reducir K o filtrar outliers antes.

## Integración con el pipeline completo LAN Chile

```
Polars (ETL) → StandardScaler → flash-kmeans → labels en Polars
     ↓                                              ↓
 KPIs por cluster (group_by) → reporte Excel → WhatsApp gateway :3001
     ↓
 SHAP analysis por cluster (¿qué features definen cada segmento?)
     ↓
 Dashboard Dash (filtros por cluster, comparativo KPIs)
```

## Dependencias

```bash
pip install flash-kmeans torch polars scikit-learn plotly dash openpyxl
```

Para GPU en cloud si ai-server no tiene CUDA:
```bash
# Modal (serverless GPU, pago por uso)
pip install modal
# RunPod: container con imagen pytorch/pytorch:latest
```
