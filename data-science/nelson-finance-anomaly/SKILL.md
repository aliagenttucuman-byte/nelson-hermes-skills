---
name: nelson-finance-anomaly
description: "Deteccion de anomalias y scoring de riesgo financiero con Python. Isolation Forest, Autoencoders, LOF, DBSCAN. Aplicado a costos operativos, fraude, outliers contables y alertas automaticas."
triggers:
  - anomalias financieras
  - deteccion de fraude
  - outliers contables
  - riesgo financiero
  - scoring de riesgo
version: "1.0.0"
---

## Algoritmos de detección de anomalías

| Algoritmo | Tipo | Fortaleza | Caso de uso Nelson |
|---|---|---|---|
| Isolation Forest | No supervisado | Rápido, bueno para alta dimensión | Costos operativos |
| Local Outlier Factor (LOF) | Basado en densidad | Bueno para clusters locales | Comportamiento de clientes |
| DBSCAN | Clustering + outliers | Bueno para datos geoespaciales | Rutas |
| Autoencoder (PyTorch/Keras) | Reconstrucción de errores | Bueno para series temporales | Transacciones |
| Z-Score / IQR | Baseline simple | Rápido, interpretable | Siempre correr primero |
| CUSUM | Detección de cambio | Series de tiempo financieras | Tendencias KPI |

## Casos de uso aerolínea

- Detección de gastos anómalos por ruta/aeropuerto
- Outliers en costos de combustible (comparado con precio mercado)
- Anomalías en patrones de reserva (fraude o error sistemático)
- Alertas automáticas cuando un KPI se desvía más de N sigmas
- Auditoria automática de transacciones contables

## Pipeline estándar

```python
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
import plotly.express as px
import plotly.graph_objects as go

# 1. Carga y limpieza de datos financieros
df = pd.read_csv("transacciones_nelson.csv", parse_dates=["fecha"])
df = df.dropna(subset=["monto", "ruta", "aeropuerto"])
df = df[df["monto"] > 0]  # eliminar montos negativos / nulos

# 2. Normalización - RobustScaler es mejor para datos financieros
features = ["monto", "costo_combustible", "pasajeros", "carga_kg"]
scaler = RobustScaler()  # menos sensible a outliers extremos que StandardScaler
X_scaled = scaler.fit_transform(df[features])

# 3. Isolation Forest con sklearn
model = IsolationForest(
    contamination=0.05,  # 5% de anomalías esperadas - ajustar con domain expert
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)
model.fit(X_scaled)

# 4. Scoring de anomalía
df["anomaly_score"] = model.decision_function(X_scaled)  # más negativo = más anómalo
df["is_anomaly"] = model.predict(X_scaled)  # -1 = anomalía, 1 = normal
df["anomaly_label"] = df["is_anomaly"].map({1: "Normal", -1: "ANOMALÍA"})

anomalias = df[df["is_anomaly"] == -1].sort_values("anomaly_score")
print(f"Anomalías detectadas: {len(anomalias)} ({len(anomalias)/len(df)*100:.1f}%)")

# 5. Visualización con plotly
fig = px.scatter(
    df,
    x="fecha",
    y="monto",
    color="anomaly_label",
    color_discrete_map={"Normal": "steelblue", "ANOMALÍA": "crimson"},
    hover_data=["ruta", "aeropuerto", "anomaly_score"],
    title="Detección de Anomalías - Costos Operativos Nelson",
    labels={"monto": "Monto (USD)", "fecha": "Fecha"}
)
fig.update_traces(marker=dict(size=6, opacity=0.7))
fig.show()

# 6. Export a Excel con contexto
top_anomalias = anomalias.head(50).copy()
top_anomalias["anomaly_rank"] = range(1, len(top_anomalias) + 1)

with pd.ExcelWriter("anomalias_nelson.xlsx", engine="openpyxl") as writer:
    top_anomalias.to_excel(writer, sheet_name="Anomalías Detectadas", index=False)
    df[df["is_anomaly"] == 1].to_excel(writer, sheet_name="Transacciones Normales", index=False)
    
    # Hoja de resumen
    resumen = pd.DataFrame({
        "Métrica": ["Total transacciones", "Anomalías detectadas", "% anomalías", "Monto anómalo total"],
        "Valor": [
            len(df),
            len(anomalias),
            f"{len(anomalias)/len(df)*100:.2f}%",
            f"${anomalias['monto'].sum():,.2f}"
        ]
    })
    resumen.to_excel(writer, sheet_name="Resumen", index=False)

print("Export completado: anomalias_nelson.xlsx")

# 7. Sistema de alertas - notificación WhatsApp via gateway Nelson
THRESHOLD_ANOMALIAS = 50  # umbral configurable

def enviar_alerta_whatsapp(mensaje: str, gateway_url: str = "http://nelson-gateway/send"):
    """Enviar alerta al gateway WhatsApp del equipo Nelson."""
    import requests
    payload = {
        "to": "+56912345678",  # reemplazar con número del equipo
        "message": mensaje
    }
    try:
        resp = requests.post(gateway_url, json=payload, timeout=10)
        resp.raise_for_status()
        print("Alerta enviada correctamente")
    except Exception as e:
        print(f"Error enviando alerta: {e}")

if len(anomalias) > THRESHOLD_ANOMALIAS:
    mensaje = (
        f"ALERTA ANOMALÍAS FINANCIERAS - Nelson\n"
        f"Fecha: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"Anomalías detectadas: {len(anomalias)}\n"
        f"Monto total involucrado: ${anomalias['monto'].sum():,.2f}\n"
        f"Top ruta afectada: {anomalias['ruta'].value_counts().index[0]}\n"
        f"Revisar: anomalias_nelson.xlsx"
    )
    enviar_alerta_whatsapp(mensaje)
```

## Pitfalls

- RobustScaler > StandardScaler en datos financieros (menos sensible a outliers extremos)
- contamination param en Isolation Forest: empezar con 0.05 (5%), ajustar con domain expert
- No confundir outlier con error de datos: siempre validar manualmente los top-10 anomalías detectadas
- Datos financieros de aerolíneas tienen outliers legítimos (COVID, huelgas, desastres) - considerar variables exógenas
- LOF no escala bien con datasets > 100k filas: usar Isolation Forest o PyOD en ese caso
- Autoencoder requiere suficientes datos históricos "normales" para entrenamiento (>10k registros recomendado)

## Instalación

```bash
pip install scikit-learn torch plotly openpyxl pyod
```
