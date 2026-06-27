---
name: nelson-lan-airline-poc-stack
description: Stack base para PoCs de aerolíneas LAN/LATAM Airlines Group (LATAM, LAN, JJ, XL, 4M, LP, UC) sobre floci-gcp + Terraform. Extiende nelson-poc-gcp-terraform-template con datasets BTS/OpenFlights pre-cargados en GCS, KPIs CASK/RASK/Load Factor en Firestore, códigos IATA del grupo, contexto de operaciones aéreas, y modelos ML (delay prediction, satisfaction, clustering) pre-conectados. Carga esta skill cuando Nelson dice explícitamente "PoC para LAN" o "LAN/LATAM" o "aerolínea".
when_to_use: Nelson dice "PoC LAN", "PoC LATAM", "aerolínea", "Copilot governance LAN"; bootstrap PoC vertical aerolíneas; demo para LATAM Airlines Group con KPIs operativos; dashboard con métricas CASK/RASK/Load Factor.
---

# nelson-lan-airline-poc-stack

Stack vertical para PoCs de **LATAM Airlines Group** sobre el template base GCP. Cuando Nelson dice "es para LAN", cargás esta skill + `nelson-poc-gcp-terraform-template` y arrancás con datos reales del rubro aéreo en 30 minutos.

## Contexto LAN/LATAM (lo que tenés que saber)

**Cliente:** LATAM Airlines Group — el holding de aerolíneas más grande de LATAM. Sede Chile, opera 6 aerolíneas con códigos IATA distintos.

**Nelson en LAN:** Data Scientist Senior via contractor Intermedia LLC desde 29/06/2026. Tema: governance de M365 Copilot. Pago $28/hr, 8h/día L-V 9-18 ARG. Cobra USDc via ARQ → Lead Bank Kansas City.

**Stack técnico que esperan:** Polars (no pandas), XGBoost, LightGBM, Prophet, SHAP, FastAPI, dashboards con KPIs operativos.

**KPIs operativos clave:**

| KPI | Sigla | Fórmula | Para qué |
|---|---|---|---|
| Cost per Available Seat Kilometer | **CASK** | costos / ASK | Eficiencia de costos |
| Revenue per Available Seat Kilometer | **RASK** | ingresos / ASK | Eficiencia de ingresos |
| Load Factor | **LF** | RPK / ASK × 100 | % ocupación |
| Available Seat Kilometer | **ASK** | asientos × km volados | Capacidad ofrecida |
| Revenue Passenger Kilometer | **RPK** | pax × km volados | Demanda satisfecha |
| Yield | — | revenue / RPK | Precio promedio por km |

**Códigos IATA del grupo LATAM:**

| Aerolínea | IATA | ICAO | Hub principal |
|---|---|---|---|
| LATAM Chile (ex-LAN) | **LA** | LAN | SCL (Santiago) |
| LATAM Brasil (ex-TAM) | **JJ** | TAM | GRU (São Paulo) |
| LATAM Perú | **LP** | LPE | LIM (Lima) |
| LATAM Ecuador | **XL** | LNE | UIO (Quito) |
| LATAM Colombia | **4M** | DSM | BOG (Bogotá) |
| LATAM Cargo Chile | **UC** | LCO | SCL |

**Constraint contractual:** Cláusula 7 de exclusividad de Intermedia LLC choca con AlegentAI. Pendiente carve-out con Cassola. Tener en cuenta al proponer trabajos paralelos.

## Cuándo cargar esta skill

- Nelson dice: "es una PoC para LAN" / "demo para LATAM" / "aerolínea"
- Necesitás KPIs CASK/RASK/Load Factor pre-cargados
- Vas a usar datasets BTS, OpenFlights, o NetFlora aéreo
- Bootstrap del repo con flavor airline (no farmacia genérica)

**Siempre cargar también:** `nelson-poc-gcp-terraform-template` (cimiento) + las skills de datos según el caso:
- Delays/cancelaciones → `nelson-airline-delay-prediction`
- Reservas → `nelson-airline-booking-prediction`
- Satisfaction → `nelson-airline-passenger-satisfaction`
- Network analysis → `nelson-airline-openflights`
- Sentiment de reseñas → `nelson-airline-sentiment`
- Clustering → `nelson-airline-clustering`
- Dataset histórico → `nelson-airline-bts-dataset`

## Bootstrap PoC LAN (basado en farmacia-poc-gcp)

### 1) Crear repo

```bash
cd /home/server/proyectos
PROYECTO=lan-{vertical}-poc   # ej: lan-loadfactor-poc, lan-delays-poc, lan-copilot-gov-poc
```

Seguir el bootstrap de `nelson-poc-gcp-terraform-template` y reemplazar `farmacia-poc` → `$PROYECTO`.

### 2) Adaptar `backend/main.py` con KPIs aéreos

Reemplazar el endpoint `/api/kpis` por:

```python
@app.get("/api/kpis")
async def get_kpis():
    """KPIs operativos diarios del grupo LATAM."""
    return {
        "fecha": date.today().isoformat(),
        "load_factor_grupo": 84.3,           # %
        "cask_usd_cents": 6.82,              # USD cents per ASK
        "rask_usd_cents": 7.94,              # USD cents per ASK
        "yield_usd": 0.0942,                 # USD per RPK
        "ask_millones": 1247.5,              # millones ASK del día
        "rpk_millones": 1051.6,              # millones RPK
        "vuelos_operados": 1342,
        "puntualidad_a15_pct": 87.2,         # % vuelos <15 min retraso
        "cancelaciones": 12,
        "pax_transportados": 168400,
        "ingresos_dia_usd_mm": 9.91,         # millones USD
        "top_ruta_yield": "SCL-GRU",
        "alertas_operacionales": 3,
        "hora_actualizacion": datetime.now().strftime("%H:%M"),
    }

@app.get("/api/flota")
async def get_flota():
    """Composición de flota por aerolínea del grupo."""
    return {
        "LA": {"a320": 87, "a321": 35, "b787": 22, "total": 144},
        "JJ": {"a319": 18, "a320": 89, "a321": 26, "b777": 10, "b787": 14, "total": 157},
        "LP": {"a319": 11, "a320": 23, "total": 34},
        "XL": {"a319": 5, "a320": 3, "total": 8},
        "4M": {"a320": 14, "total": 14},
        "UC": {"b767f": 12, "b777f": 4, "total": 16},
    }

@app.get("/api/rutas/{iata_aerolinea}")
async def get_rutas(iata_aerolinea: str):
    """Top rutas operadas por la aerolínea del grupo."""
    # Devolver desde Firestore o mock
    ...
```

### 3) System prompt del chat

```python
SYSTEM_PROMPT = """Sos un asistente operativo de LATAM Airlines Group. Conocés:
- Las 6 aerolíneas del grupo (LA Chile, JJ Brasil, LP Perú, XL Ecuador, 4M Colombia, UC Cargo)
- KPIs operativos: CASK, RASK, Load Factor, Yield, ASK, RPK
- Hubs: SCL (Santiago), GRU (São Paulo), LIM (Lima), UIO (Quito), BOG (Bogotá)
- Flota: A319, A320, A321, B767F, B777, B777F, B787
- Datos del día actual via función get_kpis(), get_flota(), get_rutas()

Respondé en español rioplatense, conciso, números con separador de miles."""
```

### 4) Cargar datasets en GCS (opcional, para PoCs con datos reales)

Si la PoC necesita datos reales:

```bash
# Ver skill nelson-airline-bts-dataset para descarga BTS
# Ver skill nelson-airline-openflights para red de rutas

# Subir al bucket en floci:
gsutil -o "Credentials:gs_json_host=localhost" -o "Credentials:gs_json_port=4588" \
       cp data/bts_*.parquet gs://$PROYECTO-data/datasets/bts/
```

O via Python desde el backend:

```python
from gcp_adapters import get_storage_client
client = get_storage_client()
bucket = client.bucket(f"{PROYECTO}-data")
blob = bucket.blob("datasets/bts/flights_2025.parquet")
blob.upload_from_filename("data/bts_2025.parquet")
```

### 5) Frontend con vista airline

Componentes mínimos:

- **KPI cards arriba:** Load Factor / CASK / RASK / Puntualidad
- **Mapa de red:** rutas activas (usar `nelson-airline-openflights` + leaflet/maplibre)
- **Chart:** Load Factor por aerolínea (LA/JJ/LP/XL/4M/UC)
- **Tabla:** top rutas por yield
- **Chat:** asistente operativo (system prompt arriba)

## PoCs LAN típicas que podemos ofrecer

| Vertical | Vertical-id | Skills extras necesarias |
|---|---|---|
| Load Factor monitoring | `lan-loadfactor-poc` | nelson-airline-bts-dataset, nelson-data-viz |
| Delay prediction | `lan-delays-poc` | nelson-airline-delay-prediction |
| Booking conversion | `lan-booking-poc` | nelson-airline-booking-prediction |
| Passenger satisfaction | `lan-csat-poc` | nelson-airline-passenger-satisfaction |
| Network optimization | `lan-network-poc` | nelson-airline-openflights, nelson-airline-clustering |
| Review sentiment | `lan-sentiment-poc` | nelson-airline-sentiment |
| **M365 Copilot governance** | `lan-copilot-gov-poc` | nelson-m365-copilot-governance-gcp |

## Pitfalls específicos de LAN

1. **Husos horarios:** SCL=UTC-3 (verano UTC-4), GRU=UTC-3, LIM=UTC-5. Cuidado al graficar series. Usar `tz="America/Santiago"` por defecto.
2. **Códigos IATA vs ICAO:** El usuario operativo habla en IATA (LA, JJ). Los sistemas internos a veces usan ICAO (LAN, TAM). Mostrar IATA en UI.
3. **ASK/RPK en millones:** Los KPIs operativos se reportan en millones, no en unidades. No confundir escalas.
4. **Polars no pandas:** Stack LATAM es Polars. Si copiás código viejo de pandas, convertir. `pl.read_parquet()` en lugar de `pd.read_parquet()`.
5. **Exclusividad Intermedia:** Cualquier trabajo paralelo (AlegentAI) requiere carve-out por escrito. NO commitear código de AlegentAI en repos LAN.
6. **Datos sensibles:** Pasajeros = PII. Si el dataset tiene nombres reales, anonimizar antes de subir a floci/repo. Mock data por defecto.
7. **Sin nombres de prospectos en commits:** Si la PoC es para presentar a alguien específico de LAN, NO poner el nombre en el repo. "PoC para LAN" basta.

## Quick wins para demos LAN

- **Mapa animado de la red:** usar OpenFlights + Mapbox/MapLibre, anima vuelos en tiempo "real" con Pub/Sub local (floci).
- **Comparador de aerolíneas:** dropdown LA vs JJ vs LP, mismo KPI lado a lado.
- **Predicción de delay con SHAP:** XGBoost + SHAP waterfall plot por vuelo → "explicabilidad" gana puntos.
- **Chat con contexto operativo:** preguntar "¿cuál fue el peor día de puntualidad este mes para JJ?" y que responda con datos reales.

## Para M365 Copilot governance específicamente

Cargar también `nelson-m365-copilot-governance-gcp`. El stack es el mismo (floci + Terraform) pero el dataset y los endpoints cambian: audit logs de Graph API en GCS, dashboards de uso/risk en Firestore.

## Referencias

- Base obligatoria: `nelson-poc-gcp-terraform-template`
- Datasets: `nelson-airline-bts-dataset`, `nelson-airline-openflights`
- Modelos: `nelson-airline-delay-prediction`, `nelson-airline-booking-prediction`, `nelson-airline-passenger-satisfaction`, `nelson-airline-clustering`, `nelson-airline-sentiment`
- Viz: `nelson-data-viz`
- Governance Copilot: `nelson-m365-copilot-governance-gcp`
- Contractor info: USER.md (Intermedia LLC, ARQ, Lead Bank)
