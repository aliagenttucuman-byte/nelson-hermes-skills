---
name: nelson-rust-scraping-tokio
description: "Scraping y crawling de alta concurrencia con Rust + Tokio + reqwest + scraper. Para Sitrack (logística), data ingestion LATAM (BTS, OAG), monitoreo de precios competidores, ETL de fuentes públicas. 100x más concurrente que Python con menos RAM. Integra con Python via HTTP o CSV/parquet."
version: 1.0.0
author: Nelson Acosta
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [rust, scraping, tokio, ETL, data-ingestion, nelson]
    related_skills: [nelson-sitrack-scraper, nelson-browser-agent, nelson-airline-bts-dataset, nelson-rust-axum-microservices]
---

# Scraping y crawling con Rust+Tokio para el equipo Nelson

## Cuándo SÍ usar Rust+Tokio para scraping

USAR Rust cuando:
- **Necesitás miles de requests concurrentes** sin saturar RAM (10k+ páginas)
- **Long-running scrapers**: corren 24/7 (Sitrack polling cada 5 min, monitor de precios)
- **Parsing pesado**: HTML masivo, regex complejas, extracción de tablas grandes
- **Anti-bot bypass robusto**: headers, cookies, retries con backoff, proxies rotativos
- **Integración con pipeline LATAM**: BTS dataset descarga + parsing de cientos de archivos
- **El scraper se vuelve infra crítica** (no es script one-off)

NO USAR cuando:
- Es scraping one-shot, una vez al mes (Python+requests basta)
- Necesitás browser real (JS rendering) → usar Playwright Python o `nelson-browser-agent`
- Es exploración / PoC (Python+BeautifulSoup itera más rápido)
- Volumen < 100 páginas (overhead no compensa)

**Regla práctica:** Rust scraping vale la pena cuando hay > 1000 páginas/hora **y** corre todos los días.

## Por qué te interesa para LAN/LATAM y Sitrack

**Caso Sitrack actual**: el scraper Python tiene problemas de timeout y consumo de RAM cuando hay muchos vehículos. Rust+Tokio puede manejar 10k requests concurrentes con < 100 MB RAM, retries automáticos con backoff exponencial, y persistencia robusta.

**Caso LAN/LATAM ingestion**:
- BTS (USA): cientos de archivos CSV mensuales históricos (6+ años)
- OAG (Official Airline Guide): schedules globales actualizados diarios
- FlightAware/FlightRadar24: tracking en vivo (si licencia lo permite)
- Datos meteorológicos: NOAA, AEMET, METAR per aeropuerto

Un scraper Rust corriendo 24/7 en ai-server puede mantener LATAM con datos frescos sin saturar.

**Caso monitoreo competidores ForestAI**: trackear precios de servicios forestales en sitios web, alertar cambios.

## Stack base

| Componente | Versión | Para qué |
|---|---|---|
| Rust | 1.75+ | Compilador |
| Tokio | 1.36+ | Async runtime |
| reqwest | 0.11+ | HTTP client async |
| scraper | 0.18+ | Parser HTML estilo jQuery/CSS selectors |
| select | 0.6+ | Alternativa scraper (más maduro) |
| serde / serde_json | 1.0+ | JSON ser/deser |
| csv | 1.3+ | CSV streaming |
| polars | 0.36+ | DataFrames si querés transformar antes de guardar |
| anyhow / thiserror | 1.0+ | Error handling |
| tracing | 0.1+ | Logging estructurado |
| sqlx / rusqlite | 0.7+ / 0.30+ | Persistencia |
| governor | 0.6+ | Rate limiting client-side |
| backoff | 0.4+ | Retries con exp backoff |

## Setup inicial

```bash
cargo new --bin sitrack-scraper
cd sitrack-scraper
cargo add tokio --features=full
cargo add reqwest --features=json,gzip,brotli,cookies,rustls-tls --no-default-features
cargo add scraper
cargo add serde --features=derive
cargo add serde_json
cargo add anyhow
cargo add tracing tracing-subscriber --features=tracing-subscriber/env-filter
cargo add governor  # rate limiting
cargo add backoff --features=tokio
cargo add csv
```

## Template: Scraper Sitrack robusto

```rust
use anyhow::{Context, Result};
use governor::{Quota, RateLimiter};
use reqwest::{Client, header};
use scraper::{Html, Selector};
use serde::{Deserialize, Serialize};
use std::{num::NonZeroU32, sync::Arc, time::Duration};
use tokio::sync::Semaphore;
use tracing::{info, warn, error, instrument};
use futures::{stream, StreamExt};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct VehicleEvent {
    pub vehicle_id: String,
    pub timestamp: String,
    pub lat: f64,
    pub lon: f64,
    pub speed_kmh: f64,
    pub status: String,
}

pub struct SitrackScraper {
    client: Client,
    rate_limiter: Arc<RateLimiter<governor::state::NotKeyed, governor::state::InMemoryState, governor::clock::DefaultClock>>,
    semaphore: Arc<Semaphore>,
}

impl SitrackScraper {
    pub fn new(token: &str, max_concurrent: usize, rps: u32) -> Result<Self> {
        let mut headers = header::HeaderMap::new();
        headers.insert(header::AUTHORIZATION, header::HeaderValue::from_str(&format!("Bearer {}", token))?);
        headers.insert(header::USER_AGENT, header::HeaderValue::from_static("nelson-sitrack-scraper/1.0"));

        let client = Client::builder()
            .default_headers(headers)
            .timeout(Duration::from_secs(30))
            .connect_timeout(Duration::from_secs(10))
            .pool_max_idle_per_host(50)
            .gzip(true)
            .brotli(true)
            .cookie_store(true)
            .build()?;

        let quota = Quota::per_second(NonZeroU32::new(rps).unwrap());
        let rate_limiter = Arc::new(RateLimiter::direct(quota));

        Ok(Self {
            client,
            rate_limiter,
            semaphore: Arc::new(Semaphore::new(max_concurrent)),
        })
    }

    #[instrument(skip(self))]
    pub async fn fetch_vehicle(&self, vehicle_id: &str) -> Result<VehicleEvent> {
        let _permit = self.semaphore.acquire().await?;
        self.rate_limiter.until_ready().await;

        let url = format!("https://api.sitrack.com/v1/vehicles/{}/last", vehicle_id);

        // Retry con exp backoff
        let op = || async {
            let resp = self.client.get(&url).send().await
                .map_err(|e| backoff::Error::transient(anyhow::anyhow!(e)))?;

            if resp.status().is_server_error() {
                return Err(backoff::Error::transient(anyhow::anyhow!("5xx: {}", resp.status())));
            }
            if !resp.status().is_success() {
                return Err(backoff::Error::permanent(anyhow::anyhow!("status: {}", resp.status())));
            }

            let event: VehicleEvent = resp.json().await
                .map_err(|e| backoff::Error::permanent(anyhow::anyhow!(e)))?;
            Ok(event)
        };

        let backoff = backoff::ExponentialBackoffBuilder::new()
            .with_max_elapsed_time(Some(Duration::from_secs(60)))
            .build();

        backoff::future::retry(backoff, op).await
            .context(format!("Falló fetch de vehicle_id={}", vehicle_id))
    }

    pub async fn fetch_all(&self, vehicle_ids: Vec<String>) -> Vec<Result<VehicleEvent>> {
        stream::iter(vehicle_ids.into_iter().map(|id| {
            let scraper = self;
            async move { scraper.fetch_vehicle(&id).await }
        }))
        .buffer_unordered(50)  // 50 requests concurrentes
        .collect()
        .await
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter("info,sitrack_scraper=debug")
        .json()
        .init();

    let token = std::env::var("SITRACK_TOKEN")?;
    let scraper = SitrackScraper::new(&token, 50, 100)?;

    // Cargar lista de vehicles desde CSV
    let vehicle_ids: Vec<String> = (1..=5000).map(|i| format!("VEH-{:05}", i)).collect();
    info!("Scrapeando {} vehículos...", vehicle_ids.len());

    let t0 = std::time::Instant::now();
    let results = scraper.fetch_all(vehicle_ids).await;

    let ok_count = results.iter().filter(|r| r.is_ok()).count();
    let err_count = results.iter().filter(|r| r.is_err()).count();

    info!("Completado en {:.1}s: {} OK, {} errores", t0.elapsed().as_secs_f64(), ok_count, err_count);

    // Persistir a CSV
    let mut wtr = csv::Writer::from_path("vehicles.csv")?;
    for ev in results.into_iter().filter_map(|r| r.ok()) {
        wtr.serialize(&ev)?;
    }
    wtr.flush()?;
    info!("Guardado a vehicles.csv");
    Ok(())
}
```

## Benchmark esperado vs Python

| Volumen | requests+BS4 (Python) | aiohttp+lxml (Python async) | **reqwest+scraper (Rust)** |
|---|---|---|---|
| 1k pages | 95 s | 18 s | **3.2 s** |
| 10k pages | 16 min | 3.5 min | **28 s** |
| 100k pages | 2.7 h | 35 min | **4.8 min** |
| RAM 10k pages | 850 MB | 320 MB | **65 MB** |

## Caso 2: Parser HTML con `scraper`

```rust
use scraper::{Html, Selector};

fn extract_flight_data(html: &str) -> Vec<FlightRow> {
    let document = Html::parse_document(html);
    let row_sel = Selector::parse("table.flights tr.flight-row").unwrap();
    let col_sel = Selector::parse("td").unwrap();

    document.select(&row_sel).filter_map(|row| {
        let cols: Vec<_> = row.select(&col_sel).map(|c| c.text().collect::<String>()).collect();
        if cols.len() < 5 { return None; }
        Some(FlightRow {
            flight_number: cols[0].trim().to_string(),
            origin: cols[1].trim().to_string(),
            destination: cols[2].trim().to_string(),
            scheduled: cols[3].trim().to_string(),
            actual: cols[4].trim().to_string(),
        })
    }).collect()
}
```

## Caso 3: Download masivo BTS para LAN/LATAM

```rust
async fn download_bts_year(client: &Client, year: u32) -> Result<()> {
    let months: Vec<u32> = (1..=12).collect();
    stream::iter(months)
        .map(|m| async move {
            let url = format!("https://transtats.bts.gov/data/{}_{:02}.csv", year, m);
            let resp = client.get(&url).send().await?;
            let bytes = resp.bytes().await?;
            tokio::fs::write(format!("data/bts_{}_{:02}.csv", year, m), &bytes).await?;
            info!("Descargado {}-{:02}", year, m);
            Ok::<_, anyhow::Error>(())
        })
        .buffer_unordered(4)  // 4 descargas paralelas
        .collect::<Vec<_>>()
        .await;
    Ok(())
}
```

Para 6 años × 12 meses = 72 archivos: **~3 min** (vs Python wget: 25 min).

## Caso 4: Integración con Python (pipeline LATAM)

Rust scrapea y guarda parquet → Python consume:

```rust
// scraper.rs
use polars::prelude::*;

let df = df!(
    "vehicle_id" => &ids,
    "lat" => &lats,
    "lon" => &lons,
    "speed_kmh" => &speeds,
)?;
let mut file = std::fs::File::create("sitrack_latest.parquet")?;
ParquetWriter::new(&mut file).finish(&mut df.clone())?;
```

```python
# data_pipeline.py
import polars as pl
df = pl.read_parquet("sitrack_latest.parquet")
# análisis ML con XGBoost, etc.
```

**Single binary scraper** corriendo en cron, alimenta el pipeline Python.

## Despliegue: systemd unit en ai-server

```ini
# /etc/systemd/system/sitrack-scraper.service
[Unit]
Description=Nelson Sitrack scraper (Rust)
After=network.target

[Service]
Type=simple
User=server
WorkingDirectory=/home/server/proyectos/sitrack-scraper
EnvironmentFile=/home/server/proyectos/sitrack-scraper/.env
ExecStart=/home/server/proyectos/sitrack-scraper/target/release/sitrack-scraper
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sitrack-scraper
journalctl -u sitrack-scraper -f
```

## Pitfalls reales

### 1. `tokio::main` con threads default
Para scraping I/O-bound, multi-thread runtime es overkill (causa context switches). Para scrapers chicos, usar `current_thread`:
```rust
#[tokio::main(flavor = "current_thread")]
```

### 2. Sin rate limiting → ban inmediato
**Nunca scrapear sin rate limiter.** `governor` con quota razonable (10-100 RPS según target). Sitios serios bannean por IP en minutos.

### 3. `reqwest::blocking` dentro de async = catástrofe
Sólo usar `reqwest::Client` async. Si necesitás sync, usar `reqwest::blocking::Client` en context sync (no async).

### 4. `buffer_unordered` con número alto
50-100 está bien. > 500 satura sockets locales (ephemeral port exhaustion). Linux default ~28k puertos disponibles. Ajustar con `sysctl net.ipv4.ip_local_port_range`.

### 5. Sin retries → datos perdidos
Servers tienen flaps. Sin `backoff`, perdés 3-10% de páginas en runs largos. Backoff exponencial obligatorio.

### 6. Cookies sin persistir
Si el site requiere login, usá `cookie_store(true)` en client builder. Si necesitás persistir entre runs, serializar el cookie jar a disco.

### 7. User-Agent default es sospechoso
`reqwest/0.11.x` levanta WAFs. Setear UA realista:
```rust
.user_agent("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
```

### 8. JavaScript-rendered sites
`reqwest` no ejecuta JS. Si el site usa React/Vue para renderizar contenido, **no funciona**. Alternativas:
- Buscar endpoint API que use el frontend (devtools → network)
- `chromiumoxide` (Rust binding a Chrome DevTools Protocol)
- Caer a Playwright Python (`nelson-browser-agent`)

### 9. HTML parsing roba CPU si no streaming
Para HTML > 1 MB, parsear todo en RAM es caro. `scraper::Html::parse_document` carga todo. Para responses gigantes, usar `select` con streaming o filtrar antes con regex.

### 10. Sin observabilidad → debugging horrible
`tracing` con `instrument` en cada función async. Logs JSON a journalctl. Sin esto, errores en runs de 8 horas son imposibles de diagnosticar.

### 11. Compilar con `RUSTFLAGS="-C target-cpu=native"`
Para scrapers corriendo en server fijo, native CPU optimizations dan 10-20% más throughput:
```bash
RUSTFLAGS="-C target-cpu=native" cargo build --release
```

### 12. Robots.txt y términos de servicio
Antes de scrapear cualquier site, leer `/robots.txt` y los ToS. Para sitios comerciales, contactar API oficial. **Para Sitrack usar la API oficial autenticada, no scraping del portal web.**

## Workflow Nelson estándar

1. **¿Hay API oficial?** Siempre primero. Si sí → usar API + reqwest.
2. **¿Volumen justifica Rust?** < 1k pages/run, quedate en Python.
3. **PoC en Python primero** (1 día) para validar selectores y flujo
4. **Portar a Rust** con rate limiting + retries + tracing
5. **Deploy como systemd unit** en ai-server (o Cloud Run para escala)
6. **Persistir a parquet/CSV** → pipeline Python consume
7. **Alertas**: si error rate > 10% en 1 hora, mandar mensaje a JARVIS

## Casos concretos equipo Nelson

| Proyecto | Aplicación | Justificación |
|---|---|---|
| Sitrack scraper | Polling de miles de vehículos | RAM baja + concurrencia + retries |
| LAN/LATAM BTS | Download 6 años × 12 meses CSV | 8x más rápido que wget |
| LAN/LATAM OAG | Refresh diario schedules globales | Long-running 24/7 |
| ForestAI competidores | Monitor precios servicios forestales | Cron diario robusto |
| Farmacia | Scraping precios competencia | Si escala a 1000s productos |
| n8n alternativa | Webhook receiver de alta concurrencia | 10k+ webhooks/s |

## Documentación de referencia

- Tokio: https://tokio.rs/tokio/tutorial
- reqwest: https://docs.rs/reqwest/
- scraper (HTML parser): https://docs.rs/scraper/
- governor (rate limiting): https://docs.rs/governor/
- backoff: https://docs.rs/backoff/

## Checklist antes de proponer scraper Rust

- [ ] ¿No hay API oficial disponible?
- [ ] ¿Volumen > 1k pages/run Y > 1 run/día?
- [ ] ¿Hay PoC Python que validó selectores y flujo?
- [ ] ¿Necesita rate limiting + retries + observabilidad?
- [ ] ¿Va a correr long-running (systemd unit) o batch grande?

Si las 5 son sí → adelante con Rust. Si alguna es no → Python alcanza.
