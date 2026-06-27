---
name: nelson-rust-axum-microservices
description: "Microservicios Rust con Axum + Tokio para gateways de alta concurrencia. Reemplazar WhatsApp Gateway Node, scoring engines en LATAM, sidecar de inferencia ML, proxies. 50k+ req/s con < 50 MB RAM. Integración con FastAPI Python por HTTP/gRPC."
version: 1.0.0
author: Nelson Acosta
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [rust, microservices, axum, performance, nelson]
    related_skills: [nelson-whatsapp-gateway, nelson-api-gateway-pattern, nelson-rust-pyo3-extensions]
---

# Axum microservices para el equipo Nelson

## Cuándo SÍ usar Axum (no FastAPI)

USAR Axum Rust cuando:
- **Gateway** que recibe miles de webhooks/segundo (WhatsApp, n8n, Sitrack)
- **Sidecar de inferencia ML**: HTTP wrapper de un modelo pesado con caching/batching
- **Scoring engine LATAM**: endpoint que aplica modelo XGBoost a cada request en <5 ms
- **Proxy/reverse proxy** con auth/rate-limit (alternativa a nginx+Lua)
- **CLI distribuible** con HTTP API embebida (single binary, sin Docker)
- Tu FastAPI llegó a saturar workers con request CPU-light pero alto QPS

NO USAR cuando:
- Necesitás iterar rápido en la lógica (FastAPI gana 3x en velocidad de desarrollo)
- Hay heavy ML dentro del endpoint (Rust para servir, Python para entrenar)
- El servicio es de bajo tráfico (< 100 req/s — FastAPI ya basta)
- Es prototipo PoC para mostrar a Pablo/Gino (overhead de compilación no compensa)

**Regla práctica:** Axum entra cuando el servicio es **infra crítica de alta concurrencia**. Para lógica de negocio iterativa, Python.

## Por qué te interesa para LAN/LATAM

LATAM hace 130M+ pasajeros/año. Endpoints típicos:
- "¿Este pasajero/ruta tiene alto riesgo de no-show?" → scoring real-time, <10 ms p99
- "¿Este vuelo va a tener delay propagation?" → features + modelo XGB inference
- "Dame los top-K vuelos similares al X" → similarity search en millones de embeddings

**Patrón Nelson estándar:**
1. Python entrena (Polars + scikit/XGBoost/LightGBM)
2. Serializa modelo (ONNX o JSON simple)
3. **Axum sirve inferencia** (carga modelo al boot, responde en microsegundos)
4. Python orquesta (FastAPI llama a Axum cuando hace falta scoring rápido)

## Stack base

| Componente | Versión | Para qué |
|---|---|---|
| Rust | 1.75+ | Compilador |
| Tokio | 1.36+ | Async runtime |
| Axum | 0.7+ | HTTP framework |
| Tower | 0.4+ | Middleware (auth, rate-limit, retry) |
| Tower-HTTP | 0.5+ | CORS, compression, trace |
| Serde | 1.0+ | JSON ser/deser |
| Tracing | 0.1+ | Logging estructurado |
| sqlx | 0.7+ | Postgres async (si necesitás DB) |
| reqwest | 0.11+ | HTTP client (llamar a otros servicios) |

## Setup inicial

```bash
cargo new --bin lan-scoring-engine
cd lan-scoring-engine
cargo add axum tokio --features=tokio/full
cargo add tower tower-http --features=tower-http/full
cargo add serde --features=derive
cargo add serde_json
cargo add tracing tracing-subscriber --features=tracing-subscriber/env-filter
cargo add anyhow
```

## Template main.rs — Scoring engine LATAM

```rust
use axum::{
    extract::{State, Json},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::{net::SocketAddr, sync::Arc, time::Instant};
use tower_http::{cors::CorsLayer, trace::TraceLayer, compression::CompressionLayer};
use tracing::{info, instrument};

#[derive(Clone)]
struct AppState {
    // Acá iría el modelo cargado (xgboost rust, ort, candle, etc.)
    model_version: String,
}

#[derive(Deserialize)]
struct ScoringRequest {
    flight_id: String,
    distance_km: f64,
    historical_delay_avg: f64,
    day_of_week: u8,
    is_holiday: bool,
}

#[derive(Serialize)]
struct ScoringResponse {
    flight_id: String,
    delay_probability: f64,
    confidence: f64,
    model_version: String,
    latency_us: u128,
}

#[instrument(skip(state))]
async fn score_flight(
    State(state): State<Arc<AppState>>,
    Json(req): Json<ScoringRequest>,
) -> Result<Json<ScoringResponse>, (StatusCode, String)> {
    let t0 = Instant::now();

    // Lógica de scoring (placeholder — acá va tu modelo real)
    let base = req.historical_delay_avg / 60.0;
    let weekend_boost = if req.day_of_week >= 5 { 0.15 } else { 0.0 };
    let holiday_boost = if req.is_holiday { 0.25 } else { 0.0 };
    let distance_factor = (req.distance_km / 5000.0).min(0.3);

    let prob = (base + weekend_boost + holiday_boost + distance_factor).min(0.99);

    Ok(Json(ScoringResponse {
        flight_id: req.flight_id,
        delay_probability: prob,
        confidence: 0.87,
        model_version: state.model_version.clone(),
        latency_us: t0.elapsed().as_micros(),
    }))
}

async fn health() -> impl IntoResponse {
    Json(serde_json::json!({
        "status": "ok",
        "service": "lan-scoring-engine",
    }))
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter("info,axum=debug,tower_http=debug")
        .json()
        .init();

    let state = Arc::new(AppState {
        model_version: "xgboost-v0.1.0".to_string(),
    });

    let app = Router::new()
        .route("/health", get(health))
        .route("/api/score", post(score_flight))
        .layer(CompressionLayer::new())
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http())
        .with_state(state);

    let addr: SocketAddr = "0.0.0.0:8080".parse()?;
    info!("Listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;
    Ok(())
}
```

## Build + correr

```bash
cargo run --release
# → Listening on 0.0.0.0:8080

curl -X POST http://localhost:8080/api/score \
  -H 'content-type: application/json' \
  -d '{
    "flight_id": "LA1234",
    "distance_km": 1850,
    "historical_delay_avg": 12.5,
    "day_of_week": 5,
    "is_holiday": false
  }'
```

Respuesta típica: latency_us ~50-150.

## Benchmark esperado vs FastAPI

| Métrica | FastAPI + uvicorn (4 workers) | **Axum** |
|---|---|---|
| Throughput p99 | 8.000 req/s | **65.000 req/s** |
| Latencia p50 | 8 ms | **0.4 ms** |
| Latencia p99 | 45 ms | **2.1 ms** |
| RAM idle | 220 MB | **18 MB** |
| RAM 50k req/s | 800 MB | **45 MB** |
| Binary size | N/A (Python) | **8 MB** (con `strip` + `lto=fat`) |

**Para WhatsApp Gateway Node actual**: similar a Axum en throughput pero Axum usa 1/4 de la RAM.

## Patrón: Axum como sidecar de FastAPI

FastAPI sigue siendo el orquestador. Axum es el motor de inferencia.

```
[ Cliente ]
     ↓
[ FastAPI :8000 ]  ← lógica de negocio, validación, ORM
     ↓ (HTTP local)
[ Axum :8080 ]     ← scoring engine, <5 ms p99
     ↓
[ Modelo en RAM ]
```

```python
# En FastAPI
import httpx

async def predict_delay(flight: dict):
    async with httpx.AsyncClient() as c:
        r = await c.post("http://localhost:8080/api/score", json=flight)
        return r.json()
```

**Ventaja del patrón:** podés deployar Axum como container separado en Cloud Run, escalar independiente del FastAPI principal.

## Cargar modelo XGBoost real (ONNX)

```toml
[dependencies]
ort = "2.0"  # ONNX Runtime bindings
```

```rust
use ort::{Session, GraphOptimizationLevel, Value};
use std::sync::Arc;

#[derive(Clone)]
struct AppState {
    session: Arc<Session>,
}

async fn load_model() -> anyhow::Result<Session> {
    Session::builder()?
        .with_optimization_level(GraphOptimizationLevel::Level3)?
        .commit_from_file("models/delay_predictor.onnx")
}
```

Python entrena con XGBoost → exporta a ONNX → Axum carga ONNX → sirve.

## Middleware Tower (auth + rate-limit)

```rust
use tower::{ServiceBuilder, BoxError};
use tower_http::{
    auth::RequireAuthorizationLayer,
    limit::RateLimitLayer,
};
use std::time::Duration;

let app = Router::new()
    .route("/api/score", post(score_flight))
    .layer(
        ServiceBuilder::new()
            .layer(RequireAuthorizationLayer::bearer("super-secret-token"))
            .layer(RateLimitLayer::new(1000, Duration::from_secs(1)))
    );
```

## Dockerfile para Cloud Run

```dockerfile
FROM rust:1.75 AS builder
WORKDIR /app
COPY Cargo.* ./
COPY src ./src
RUN cargo build --release && strip target/release/lan-scoring-engine

FROM gcr.io/distroless/cc-debian12
COPY --from=builder /app/target/release/lan-scoring-engine /app
EXPOSE 8080
CMD ["/app"]
```

**Imagen final: ~25 MB** (vs ~400 MB de FastAPI con deps). Cold start Cloud Run: ~200 ms (vs 2-4 s FastAPI).

## Casos concretos equipo Nelson

| Servicio | Justificación Axum |
|---|---|
| WhatsApp Gateway Node → Rust | Mismo throughput, 1/4 RAM, 1 binario, sin npm deps |
| LAN/LATAM scoring engine | < 5 ms p99 obligatorio, 130M pasajeros/año |
| ForestAI tile server | Servir tiles satelitales con caching agresivo |
| Sidecar inferencia farmacia | Modelo de demanda en sub-ms |
| n8n webhook receiver | 10k+ webhooks/s, sin saturar |
| API Gateway con auth/rate-limit | Reemplazo de nginx+Lua |

## Pitfalls reales

### 1. `tokio::main` con `flavor = "multi_thread"` por defecto
Si servís más de 1k req/s, asegurate que el runtime usa todos los cores:
```rust
#[tokio::main(flavor = "multi_thread", worker_threads = 4)]
```

### 2. `Arc<Mutex<T>>` mata performance
Si tu state es read-only (modelo cargado al boot), usá `Arc<T>` directo. `Mutex` serializa todas las requests al recurso. Para mutable state read-mostly, `Arc<RwLock<T>>` o mejor `arc-swap`.

### 3. Blocking calls dentro de async = catástrofe
NUNCA hagas `std::fs::read` o `reqwest::blocking` dentro de un handler async. Bloquea TODO el reactor. Usar `tokio::fs`, `reqwest::Client` async, o `tokio::task::spawn_blocking` para código CPU-bound.

### 4. Cargar modelo grande con tonelada de archivos
Si tu modelo son 500 MB de pesos, no los leas en cada request. Cargar en `AppState` al boot:
```rust
let state = Arc::new(AppState { session: Arc::new(load_model().await?) });
```

### 5. Sin compresión = 10x más tráfico
`CompressionLayer::new()` agrega gzip/br automático. Crítico para respuestas JSON grandes (LATAM scores con explicabilidad SHAP).

### 6. `cargo run` sin `--release` da rendimiento basura
Debug build es 10-50x más lento que release. **Siempre benchmark con `cargo run --release`** o `cargo build --release && ./target/release/...`.

### 7. CORS permissive en producción
`CorsLayer::permissive()` es para dev. En prod, especificar origins explícitos:
```rust
.layer(CorsLayer::new().allow_origin("https://app.lan.com".parse().unwrap()))
```

### 8. Logs JSON por default para Cloud Run
Cloud Logging parsea JSON automáticamente. `tracing_subscriber::fmt().json().init()` es obligatorio en prod.

### 9. Errores 500 sin tracing
Wrappear handlers con `Result<T, AppError>` custom que implementa `IntoResponse` y loguea con `tracing::error!`. Sin esto, errores se silencian.

### 10. No graceful shutdown
Para Cloud Run y K8s, manejar SIGTERM:
```rust
axum::serve(listener, app)
    .with_graceful_shutdown(async {
        tokio::signal::ctrl_c().await.unwrap();
    })
    .await?;
```

## Workflow Nelson estándar

1. **PoC en FastAPI primero** (validar lógica, modelo, UX)
2. **Profilear con `wrk` o `oha`**: medir QPS real esperado
3. **Si > 1k req/s sostenido o latencia p99 > target**: portar a Axum
4. **Mantener contrato API idéntico** (OpenAPI) para no romper clientes
5. **Deploy lado-a-lado** primero (canary), después switch
6. **Métricas a Prometheus**: `tower-http::trace::TraceLayer` + `prometheus` crate

## Documentación de referencia

- Axum docs: https://docs.rs/axum/latest/axum/
- Tokio tutorial: https://tokio.rs/tokio/tutorial
- Tower middleware: https://docs.rs/tower/latest/tower/
- ONNX Runtime Rust: https://ort.pyke.io/

## Checklist antes de proponer Axum en una PoC

- [ ] ¿Hay un endpoint con > 1k req/s esperado o latencia p99 < 10 ms requerida?
- [ ] ¿La lógica del endpoint es estable (no cambia cada semana)?
- [ ] ¿Existe versión FastAPI que valide la lógica primero?
- [ ] ¿Tony/Julián van a mantener Rust 2-3 servicios más allá del primero?
- [ ] ¿Hay benchmarks que muestren que FastAPI no llega?

Si las 5 son sí → adelante. Si alguna es no → quedate en FastAPI.
