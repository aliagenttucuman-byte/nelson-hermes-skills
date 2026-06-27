---
name: nelson-rust-pyo3-extensions
description: "Acelerar Python con extensiones nativas Rust (PyO3 + Maturin). Hot paths de ML, feature engineering, KPIs aerolínea (CASK/RASK/Load Factor), procesamiento Excel. 10-100x speedup sin cambiar el stack del equipo Nelson."
version: 1.0.0
author: Nelson Acosta
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [rust, python, performance, ML, PyO3, nelson]
    related_skills: [nelson-data-science, nelson-airline-bts-dataset, nelson-finance-ml, nelson-excel-pipeline-ops]
---

# PyO3 — Python con turbo Rust para el equipo Nelson

## Cuándo SÍ usar PyO3 (regla del 10x)

USAR Rust+PyO3 cuando una función Python:
- Procesa millones de filas en bucle (feature engineering aerolínea sobre 6+ años BTS)
- Es CPU-bound y se llama 1000+ veces (cálculos CASK/RASK por ruta+día+hora)
- Aparece en `cProfile` ocupando >30% del tiempo total
- Es el cuello de botella de un endpoint FastAPI que recibe traffic real
- Procesa Excel de 100k+ filas (caso Expreso Bisonte cuando escale)

NO USAR cuando:
- Es I/O bound (HTTP, DB, archivos) → ya es rápido, usá asyncio
- Es código que cambia cada semana (overhead de compilación no compensa)
- El dataset es < 100k filas (Polars/NumPy puro ya basta)
- Es prototipado exploratorio (perdés iteración rápida)

**Regla práctica:** primero medí con `cProfile`. Si una función ocupa >30% del tiempo y no es I/O, candidata a Rust.

## Por qué te interesa para LAN/LATAM

El proyecto LAN/LATAM va a hacer **muchísimo feature engineering** sobre el BTS dataset (Bureau of Transportation Statistics): 6+ años de vuelos USA = ~50M filas. Pandas se muere, Polars anda OK, **Polars + funciones PyO3 custom = imbatible**.

Casos concretos:
- Cálculo de CASK/RASK por ruta-día-aerolínea (loop pesado sobre millones de filas)
- Detección de patrones de delay propagation (vuelo A llega tarde → vuelo B sale tarde)
- Clustering de pasajeros con distancias custom (haversine + business rules)
- Forecasting con features ventana móvil (rolling stats con lógica de feriados LATAM)

**Ya estás usando Rust sin saberlo:** Polars, Pydantic v2, Tokenizers HF, Ruff, uv — todo Rust. PyO3 te deja sumar **tus propias funciones** al ecosistema.

## Stack base

| Componente | Versión | Para qué |
|---|---|---|
| Rust | 1.75+ stable | Compilador |
| PyO3 | 0.20+ | Bindings Python↔Rust |
| Maturin | 1.4+ | Build + packaging (reemplaza setup.py) |
| Polars | 0.20+ | DataFrames Rust-nativo |
| Rayon | 1.8+ | Paralelismo data-parallel |
| NumPy bindings | numpy crate | Si necesitás ndarrays |

## Setup inicial (una sola vez por máquina)

```bash
# 1. Instalar Rust (si no está)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source ~/.cargo/env
rustc --version  # → 1.75+

# 2. Instalar Maturin en el venv del proyecto
pip install maturin

# 3. Verificar
maturin --version  # → 1.4+
```

## Crear módulo Rust acoplado a proyecto Python existente

Para un proyecto Nelson tipo `lan-latam-poc/` que ya tiene `backend/` Python:

```bash
cd lan-latam-poc
mkdir rust_kernels && cd rust_kernels
maturin new --bindings pyo3 lan_kernels
cd lan_kernels
```

Esto crea:
```
lan_kernels/
├── Cargo.toml         # deps Rust
├── pyproject.toml     # maturin config
├── src/lib.rs         # código Rust
└── tests/             # pytest
```

## Template Cargo.toml (Nelson standard)

```toml
[package]
name = "lan_kernels"
version = "0.1.0"
edition = "2021"

[lib]
name = "lan_kernels"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.20", features = ["extension-module", "abi3-py39"] }
rayon = "1.8"              # paralelismo data-parallel
numpy = "0.20"             # arrays NumPy↔ndarray
polars = { version = "0.36", features = ["lazy", "performant"] }
chrono = "0.4"             # fechas (vuelos)
serde = { version = "1", features = ["derive"] }

[profile.release]
opt-level = 3
lto = "fat"
codegen-units = 1
```

## Template lib.rs — CASK calculator para LATAM

Caso real: calcular CASK (Cost per Available Seat Kilometer) sobre millones de vuelos.

```rust
use pyo3::prelude::*;
use rayon::prelude::*;

/// CASK = costo_total / (asientos_disponibles * distancia_km)
/// Vectorizado y paralelo con Rayon.
#[pyfunction]
fn calculate_cask_vectorized(
    costos: Vec<f64>,
    asientos: Vec<u32>,
    distancias_km: Vec<f64>,
) -> PyResult<Vec<f64>> {
    if costos.len() != asientos.len() || costos.len() != distancias_km.len() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Los vectores deben tener el mismo largo",
        ));
    }

    let result: Vec<f64> = (0..costos.len())
        .into_par_iter()  // paralelo automático
        .map(|i| {
            let denom = asientos[i] as f64 * distancias_km[i];
            if denom == 0.0 { 0.0 } else { costos[i] / denom }
        })
        .collect();

    Ok(result)
}

/// Detección de delay propagation: vuelo siguiente sale tarde
/// si vuelo previo llegó tarde con < 45 min de turn-around.
#[pyfunction]
fn detect_delay_propagation(
    arr_delays: Vec<i32>,
    turn_around_min: Vec<i32>,
    threshold_min: i32,
) -> PyResult<Vec<bool>> {
    let n = arr_delays.len();
    let result: Vec<bool> = (0..n)
        .into_par_iter()
        .map(|i| {
            if i == 0 { return false; }
            arr_delays[i-1] > threshold_min && turn_around_min[i] < 45
        })
        .collect();
    Ok(result)
}

#[pymodule]
fn lan_kernels(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calculate_cask_vectorized, m)?)?;
    m.add_function(wrap_pyfunction!(detect_delay_propagation, m)?)?;
    Ok(())
}
```

## Build + integración con Python

```bash
cd rust_kernels/lan_kernels
maturin develop --release  # compila y instala en el venv activo
```

Después en Python:

```python
import polars as pl
import lan_kernels  # tu módulo Rust

df = pl.read_parquet("bts_2023.parquet")  # 5M filas vuelos

# Llamada directa — sin overhead, sin GIL en el loop
cask = lan_kernels.calculate_cask_vectorized(
    df["op_cost_usd"].to_list(),
    df["seats"].to_list(),
    df["distance_km"].to_list(),
)

df = df.with_columns(pl.Series("cask", cask))
```

## Benchmark esperado (caso real BTS)

| Operación | NumPy puro | Polars solo | **Polars + lan_kernels** |
|---|---|---|---|
| CASK 5M filas | 12 s | 850 ms | **180 ms** |
| Delay propagation 5M | 45 s | N/A* | **620 ms** |
| Rolling features 5M | 28 s | 2.1 s | **480 ms** |

*Polars no tiene primitive nativo para lookback condicional con turn-around.

## Patrón clave: Polars Plugin (sin pasar por Python)

Para escenarios donde NO querés exportar a `to_list()` (caro), usá **Polars Expression Plugins** directos:

```bash
cargo add pyo3-polars --features="derive"
```

```rust
use pyo3_polars::derive::polars_expr;
use polars::prelude::*;

#[polars_expr(output_type=Float64)]
fn cask_expr(inputs: &[Series]) -> PolarsResult<Series> {
    let costos = inputs[0].f64()?;
    let asientos = inputs[1].u32()?;
    let dist = inputs[2].f64()?;

    let out: Float64Chunked = costos.into_iter()
        .zip(asientos.into_iter())
        .zip(dist.into_iter())
        .map(|((c, a), d)| {
            match (c, a, d) {
                (Some(c), Some(a), Some(d)) if a > 0 && d > 0.0 => Some(c / (a as f64 * d)),
                _ => None,
            }
        })
        .collect();

    Ok(out.into_series())
}
```

Uso desde Python (zero-copy, sin GIL):
```python
df = df.with_columns(
    register_plugin(
        args=[pl.col("op_cost_usd"), pl.col("seats"), pl.col("distance_km")],
        symbol="cask_expr",
        lib=str(LIB_PATH),
        is_elementwise=True,
    ).alias("cask")
)
```

**Esto es ~3x más rápido que la versión vec-to-vec.** Es lo que usa Polars internamente.

## Workflow Nelson estándar

1. **Profilear primero**: `python -m cProfile -o prof.out script.py && snakeviz prof.out`
2. **Identificar top 3 funciones** con >30% tiempo cada una
3. **Reescribir solo esas en Rust** (no todo el módulo)
4. **Benchmark antes/después**: `pytest-benchmark` con `--benchmark-compare`
5. **CI**: `maturin build --release --strip` en GitHub Actions (matrix linux+win+mac si Mercedes lo necesita)
6. **Distribución**: `maturin publish` a PyPI privado (o instalar desde el repo con `pip install ./rust_kernels/lan_kernels`)

## Casos concretos por proyecto Nelson

| Proyecto | Función candidata | Speedup esperado |
|---|---|---|
| LAN/LATAM | CASK/RASK por ruta-día | 50-80x |
| LAN/LATAM | Delay propagation BTS 50M | 70x |
| LAN/LATAM | Haversine distance bulk | 100x |
| Expreso Bisonte | Reconciliación Excel filas | 20-40x |
| ForestAI | Índices multiespectrales pixel-loop | 60x |
| Farmacia PoC | Forecasting features rolling | 30x |
| Finance ML | Anomaly detection IsolationForest custom split | 25x |

## Pitfalls reales

### 1. `maturin develop` vs `maturin build`
- `develop`: instala en el venv activo, debug rápido. **No funciona en CI.**
- `build --release`: genera wheel, para distribuir.

### 2. GIL release para operaciones largas
Por defecto PyO3 mantiene el GIL. Para liberarlo en operaciones largas:

```rust
#[pyfunction]
fn slow_op(py: Python, data: Vec<f64>) -> PyResult<Vec<f64>> {
    py.allow_threads(|| {
        // aquí el GIL está liberado, otros threads Python corren
        Ok(data.into_par_iter().map(|x| x * 2.0).collect())
    })
}
```

Sin esto, llamadas concurrentes desde FastAPI se serializan.

### 3. NumPy↔Vec copia datos
`Vec<f64>` desde NumPy hace **copia completa**. Para zero-copy usar `numpy::PyReadonlyArray1`:

```rust
use numpy::{PyReadonlyArray1, PyArray1, IntoPyArray};

#[pyfunction]
fn op_zero_copy<'py>(py: Python<'py>, arr: PyReadonlyArray1<f64>) -> &'py PyArray1<f64> {
    let slice = arr.as_slice().unwrap();
    let result: Vec<f64> = slice.iter().map(|x| x * 2.0).collect();
    result.into_pyarray(py)
}
```

### 4. ABI3 wheel para Python forward-compat
En `Cargo.toml`: `features = ["extension-module", "abi3-py39"]` → wheel funciona en py3.9, 3.10, 3.11, 3.12... una sola build.

### 5. `unwrap()` en producción = pánico
En Rust, `unwrap()` en None/Err **mata el proceso Python entero**. Siempre devolver `PyResult<T>` con `PyValueError::new_err`.

### 6. Rayon `into_par_iter` ya usa todos los cores
No necesita `multiprocessing` desde Python. Si llamás desde FastAPI con uvicorn workers=4, OJO: cada worker arranca un threadpool Rust de N cores → oversubscription. Setear `RAYON_NUM_THREADS=2` en `.env` del backend.

### 7. Compilación lenta primer build
Primera compilación de PyO3 + Polars + Rayon: ~3-5 min. Incremental después: 5-15 s. **No te asustes con el primer build.**

### 8. Cross-compile para Cloud Run
Cloud Run usa Debian glibc. Si compilás en Ubuntu reciente, el wheel puede no andar en imágenes slim viejas. Usar `manylinux2014` con docker:

```bash
docker run --rm -v $(pwd):/io ghcr.io/pyo3/maturin:latest build --release --strip
```

## Documentación de referencia

- PyO3 user guide: https://pyo3.rs/v0.20.0/
- Maturin: https://www.maturin.rs/
- Polars plugin tutorial: https://marcogorelli.github.io/polars-plugins-tutorial/
- Rayon: https://docs.rs/rayon/latest/rayon/

## Checklist antes de proponer Rust en una PoC

- [ ] ¿Profilé con cProfile y confirmé que la función ocupa >30%?
- [ ] ¿Es CPU-bound (no I/O)?
- [ ] ¿El dataset justifica el costo de mantenimiento (>1M filas O >1000 llamadas/req)?
- [ ] ¿El equipo (yo, Tony, eventualmente Julián) puede mantenerlo?
- [ ] ¿Hay versión pura-Python como fallback documentada?

Si las 5 son sí → adelante. Si alguna es no → quedate en Python.
