---
name: nelson-rust-wasm-frontend
description: "Rust compilado a WebAssembly para frontend (React/Vite de Mercedes) y edge compute (Cloudflare Workers). Procesamiento Excel client-side sin backend, parsers complejos en browser, lógica ML compartida Python-WASM. Casos LATAM, Expreso Bisonte y PoCs ForestAI."
version: 1.0.0
author: Nelson Acosta
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [rust, wasm, frontend, edge, cloudflare-workers, nelson]
    related_skills: [nelson-frontend-stack, nelson-rust-pyo3-extensions, nelson-cloudflare-tunnel-deploy]
---

# Rust → WASM para frontend y edge (equipo Nelson)

## Cuándo SÍ usar WASM

USAR Rust+WASM cuando:
- **Procesamiento Excel/CSV client-side**: 50k+ filas en browser sin enviar al backend (privacidad + costo)
- **Parsers complejos en frontend**: validaciones de schema, regex masivas, AST
- **Lógica matemática compartida**: la misma función en backend Python (PyO3) y frontend (WASM) — single source of truth
- **Cloudflare Workers**: edge compute global, gratis hasta 100k req/día, latencia < 50 ms en LATAM
- **Compresión/encriptación browser-side**: para evitar tráfico innecesario
- **Visualizaciones pesadas**: clustering en vivo de miles de puntos sin lag

NO USAR cuando:
- Operaciones pequeñas (< 100ms en JS puro)
- Lógica de UI (eventos, DOM) → React/JS gana
- Necesitás acceso DOM directo (no es la fortaleza de WASM)
- El equipo frontend (Mercedes) no tiene contexto Rust mínimo

**Regla práctica:** WASM en browser solo si la operación es CPU pesada Y se ejecuta en el cliente.

## Por qué te interesa para LAN/LATAM y Expreso Bisonte

**Caso Expreso Bisonte real**: hoy el frontend manda el Excel al backend, el backend lo procesa, devuelve resultado. Si el Excel tiene 100k filas, el tráfico es de MB y el backend gasta CPU. **Con WASM**: Mercedes carga el Excel, el parser Rust→WASM procesa todo en el browser de Pablo, solo manda al backend el resumen. Privacidad + velocidad + menos costo Cloud Run.

**Caso LAN/LATAM**: dashboard que recibe stream de vuelos en tiempo real (10k flights). Filtros, clustering, métricas CASK on-the-fly. Sin WASM: cada filtro va al backend. Con WASM: filtros instantáneos en el browser, latencia 0 ms.

**Cloudflare Workers**: edge para PoCs comerciales (gratis hasta 100k req/día). Auth de demos, redirects, A/B testing por país.

## Stack base

| Componente | Versión | Para qué |
|---|---|---|
| Rust | 1.75+ | Compilador |
| wasm-pack | 0.12+ | Build orchestrator (Rust→WASM→npm) |
| wasm-bindgen | 0.2+ | Bindings JS↔Rust |
| serde-wasm-bindgen | 0.6+ | JSON entre JS y Rust |
| js-sys + web-sys | 0.3+ | Acceso a APIs browser |
| worker | 0.0.18+ | Cloudflare Workers SDK |

## Setup (una sola vez)

```bash
# 1. Target WASM
rustup target add wasm32-unknown-unknown

# 2. wasm-pack
curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh

# 3. (Para Cloudflare Workers)
npm install -g wrangler

# Verificar
wasm-pack --version  # → 0.12+
wrangler --version   # → 3.x+
```

## Caso 1: Parser Excel client-side para Expreso Bisonte

```bash
cd expreso-bisonte-frontend
mkdir wasm-modules && cd wasm-modules
wasm-pack new excel-parser
cd excel-parser
```

### Cargo.toml

```toml
[package]
name = "excel-parser"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
wasm-bindgen = "0.2"
serde = { version = "1", features = ["derive"] }
serde-wasm-bindgen = "0.6"
calamine = "0.24"  # parser xlsx/xls/ods
js-sys = "0.3"
console_error_panic_hook = "0.1"  # debug

[profile.release]
opt-level = "z"  # tamaño chico
lto = true
```

### src/lib.rs

```rust
use wasm_bindgen::prelude::*;
use calamine::{Reader, Xlsx, Data};
use std::io::Cursor;
use serde::Serialize;

#[derive(Serialize)]
pub struct InvoiceRow {
    pub row_num: u32,
    pub cliente: String,
    pub monto: f64,
    pub fecha: String,
    pub estado: String,
}

#[derive(Serialize)]
pub struct ParseResult {
    pub total_rows: usize,
    pub valid_rows: usize,
    pub total_amount: f64,
    pub rows: Vec<InvoiceRow>,
    pub errors: Vec<String>,
}

#[wasm_bindgen(start)]
pub fn init() {
    console_error_panic_hook::set_once();
}

#[wasm_bindgen]
pub fn parse_invoices(file_bytes: Vec<u8>) -> Result<JsValue, JsValue> {
    let cursor = Cursor::new(file_bytes);
    let mut workbook: Xlsx<_> = Xlsx::new(cursor)
        .map_err(|e| JsValue::from_str(&format!("Error abriendo Excel: {}", e)))?;

    let sheet_name = workbook.sheet_names()[0].clone();
    let range = workbook.worksheet_range(&sheet_name)
        .map_err(|e| JsValue::from_str(&format!("Error leyendo hoja: {}", e)))?;

    let mut rows = Vec::new();
    let mut errors = Vec::new();
    let mut total = 0.0;

    for (idx, row) in range.rows().enumerate().skip(1) {
        let cliente = row.get(0).map(|c| c.to_string()).unwrap_or_default();
        let monto = row.get(1).and_then(|c| match c {
            Data::Float(f) => Some(*f),
            Data::Int(i) => Some(*i as f64),
            _ => None,
        });

        match monto {
            Some(m) if m > 0.0 => {
                total += m;
                rows.push(InvoiceRow {
                    row_num: (idx + 1) as u32,
                    cliente,
                    monto: m,
                    fecha: row.get(2).map(|c| c.to_string()).unwrap_or_default(),
                    estado: row.get(3).map(|c| c.to_string()).unwrap_or_default(),
                });
            },
            _ => errors.push(format!("Fila {}: monto inválido", idx + 1)),
        }
    }

    let total_rows = range.rows().count() - 1;
    let result = ParseResult {
        total_rows,
        valid_rows: rows.len(),
        total_amount: total,
        rows,
        errors,
    };

    serde_wasm_bindgen::to_value(&result).map_err(|e| JsValue::from_str(&e.to_string()))
}
```

### Build

```bash
wasm-pack build --target web --release
# → genera ./pkg/ con .wasm + .js wrapper + .d.ts
```

### Uso en React (Mercedes)

```typescript
// frontend/src/components/ExcelUploader.tsx
import { useEffect, useState } from 'react';
import init, { parse_invoices } from '../../wasm-modules/excel-parser/pkg/excel_parser';

export function ExcelUploader() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => { init(); }, []);

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    const bytes = new Uint8Array(await file.arrayBuffer());
    try {
      const t0 = performance.now();
      const parsed = parse_invoices(bytes);
      console.log(`Parse time: ${(performance.now() - t0).toFixed(0)} ms`);
      setResult(parsed);
    } catch (err) {
      console.error('Parse error:', err);
    }
    setLoading(false);
  };

  return (
    <div>
      <input type="file" accept=".xlsx" onChange={handleFile} />
      {loading && <p>Procesando...</p>}
      {result && (
        <div>
          <p>Filas válidas: {result.valid_rows} / {result.total_rows}</p>
          <p>Total: ${result.total_amount.toFixed(2)}</p>
          <p>Errores: {result.errors.length}</p>
        </div>
      )}
    </div>
  );
}
```

**Benchmark esperado**: 50k filas Excel → 180 ms en browser. JS puro con SheetJS: 4.2 s. **23x más rápido**, todo client-side.

## Caso 2: Lógica ML compartida Python ↔ WASM

Misma función para cálculo CASK en backend (PyO3) y frontend (WASM):

```rust
// shared/src/lib.rs (sin features wasm o pyo3)
pub fn cask(costo: f64, asientos: u32, distancia_km: f64) -> Option<f64> {
    if asientos == 0 || distancia_km <= 0.0 { return None; }
    Some(costo / (asientos as f64 * distancia_km))
}

// rust_kernels/src/lib.rs (feature=pyo3)
use pyo3::prelude::*;
#[pyfunction]
fn calc_cask(c: f64, a: u32, d: f64) -> Option<f64> {
    shared::cask(c, a, d)
}

// wasm-modules/src/lib.rs (feature=wasm)
use wasm_bindgen::prelude::*;
#[wasm_bindgen]
pub fn cask_wasm(c: f64, a: u32, d: f64) -> Option<f64> {
    shared::cask(c, a, d)
}
```

**Una sola fórmula, mantenida en un solo lugar.** No más drift entre backend y frontend.

## Caso 3: Cloudflare Worker para edge demo

PoC para Gino donde la latencia importa (auth, geofencing, A/B):

```bash
npm create cloudflare@latest my-worker -- --type=hello-world-rust
cd my-worker
```

### src/lib.rs

```rust
use worker::*;

#[event(fetch)]
async fn fetch(req: Request, _env: Env, _ctx: Context) -> Result<Response> {
    let url = req.url()?;
    let country = req.cf().and_then(|cf| cf.country()).unwrap_or("XX".into());

    match url.path() {
        "/api/score" => {
            let body: serde_json::Value = req.json().await?;
            let distance = body["distance_km"].as_f64().unwrap_or(0.0);
            let prob = (distance / 5000.0).min(0.95);
            Response::from_json(&serde_json::json!({
                "delay_probability": prob,
                "country": country,
                "edge": true,
            }))
        },
        "/health" => Response::ok("ok"),
        _ => Response::error("Not found", 404),
    }
}
```

### Deploy

```bash
wrangler login
wrangler deploy
# → https://my-worker.aliagenttucuman.workers.dev
```

**Costo: $0 hasta 100k requests/día.** Latencia: < 30 ms en LATAM.

## Benchmark esperado

| Operación | JS/TS puro | **Rust→WASM** |
|---|---|---|
| Parse Excel 50k filas | 4.2 s | **180 ms** |
| Filter 100k rows by múltiples cols | 320 ms | **18 ms** |
| Haversine 10k puntos | 85 ms | **3 ms** |
| Cluster K-means 1k puntos | 1.4 s | **40 ms** |
| Regex masivo (50 patterns × 10k strings) | 2.1 s | **70 ms** |

## Pitfalls reales

### 1. Tamaño del .wasm
Sin optimización: 800 KB - 2 MB. Con `opt-level = "z" + lto + wasm-opt`: 80-250 KB. Mercedes va a notar el bundle.

```toml
[profile.release]
opt-level = "z"
lto = true
codegen-units = 1
strip = true
```

Y después:
```bash
wasm-opt -Oz -o pkg/excel_parser_bg_opt.wasm pkg/excel_parser_bg.wasm
```

### 2. Llamadas WASM↔JS tienen overhead
Cada cruce de boundary cuesta ~microsegundos. Para operaciones cortas, hacelas en JS. Para masivas, batch: pasar todo el array de una vez, no fila por fila.

### 3. WASM no tiene threads por defecto
Para paralelismo necesitás SharedArrayBuffer + COOP/COEP headers. Mercedes tiene que configurar Vite:

```ts
// vite.config.ts
export default {
  server: {
    headers: {
      'Cross-Origin-Embedder-Policy': 'require-corp',
      'Cross-Origin-Opener-Policy': 'same-origin',
    },
  },
};
```

### 4. `console.log` desde Rust
```rust
use wasm_bindgen::prelude::*;
#[wasm_bindgen]
extern "C" {
    #[wasm_bindgen(js_namespace = console)]
    fn log(s: &str);
}
log(&format!("Procesando {} filas", n));
```

O directamente `web_sys::console::log_1(&"hola".into())`.

### 5. Panics silenciosos
Sin `console_error_panic_hook`, los `panic!` en Rust dan errores incomprensibles en browser. **Siempre incluirlo en `init()`.**

### 6. Vite + WASM moderno
Vite 5+ soporta `?init` import directo:
```ts
import init from './excel_parser.wasm?init';
const instance = await init();
```

### 7. CORS en Cloudflare Workers
Workers no agregan CORS automáticamente. Headers manuales:
```rust
Response::from_json(&data)?
    .with_headers(Headers::from_iter([
        ("Access-Control-Allow-Origin", "*"),
    ]))
```

### 8. Estado entre requests en Worker
Workers son stateless por request. Para estado persistente: **Workers KV** (key-value, eventual consistency) o **Durable Objects** (strong consistency, $$).

### 9. Limitar tamaño de upload en browser
File API max ~2 GB en Chrome, ~512 MB en Safari iOS. Para Excel > 100 MB, hacer chunking.

### 10. `wasm-bindgen-cli` versión debe matchear
La versión de `wasm-bindgen` en Cargo.toml debe matchear `wasm-bindgen-cli` instalada. Si no: errores crípticos al hacer `wasm-pack build`.

## Workflow Nelson estándar

1. **¿Es operación pesada Y client-side relevante?** Si no → JS/TS y listo
2. **Prototipo en Rust nativo primero** (test con `cargo test`)
3. **Compilar a WASM** y benchmark vs versión JS
4. **Si > 5x speedup**: integrar en frontend
5. **Optimizar tamaño .wasm** con `wasm-opt`
6. **Documentar API JS para Mercedes** (.d.ts auto-generado por wasm-bindgen)

## Casos concretos equipo Nelson

| Proyecto | Aplicación WASM | Beneficio |
|---|---|---|
| Expreso Bisonte | Parser Excel client-side | Privacidad + 23x speedup |
| LAN/LATAM dashboard | Filtros/clustering en browser | UX instantánea |
| ForestAI tiles | Decode multispectral en browser | Sin backend overhead |
| Demo Pablo/Gino | Cloudflare Worker auth | Edge global gratis |
| Farmacia PoC | Validación schema upload | Sin round-trip |
| Sitrack viewer | Parser CSV con miles de filas | Sin saturar backend |

## Documentación de referencia

- wasm-bindgen guide: https://rustwasm.github.io/wasm-bindgen/
- wasm-pack: https://rustwasm.github.io/wasm-pack/
- Cloudflare Workers Rust: https://developers.cloudflare.com/workers/languages/rust/
- calamine (Excel): https://docs.rs/calamine/

## Checklist antes de proponer WASM

- [ ] ¿Es CPU-heavy (> 200 ms en JS puro)?
- [ ] ¿Es client-side (no es lógica que necesita server)?
- [ ] ¿El tamaño .wasm < 500 KB después de optimizar?
- [ ] ¿Mercedes tiene tiempo para integrarlo (1-2 días primer caso)?
- [ ] ¿Hay fallback JS para browsers viejos (< 1% tráfico)?
