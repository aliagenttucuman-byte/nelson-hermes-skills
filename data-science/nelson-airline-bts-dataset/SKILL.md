---
name: nelson-airline-bts-dataset
description: "Descarga y procesamiento del dataset BTS (Bureau of Transportation Statistics) de EEUU. 70M+ vuelos desde 1987. On-time performance, delays, cancelaciones, pasajeros por ruta, tarifas O-D, load factor. Polars para procesamiento masivo."
triggers:
  - BTS dataset
  - datos vuelos EEUU
  - on-time performance
  - flight delay dataset
  - benchmark aviacion publico
version: "1.0.0"
---

# BTS Dataset — Bureau of Transportation Statistics

Dataset público de aviación de EEUU con 70M+ registros de vuelos desde 1987. Cubre on-time performance, delays, cancelaciones, tarifas y load factor. Referencia de benchmark para la industria aérea americana y rutas internacionales hacia LATAM.

---

## Qué contiene el BTS

El BTS publica cuatro tablas principales, cada una con un propósito distinto:

### 1. On-Time Performance (Tabla principal)
Registro de cada vuelo operado por aerolíneas de EEUU. Columnas clave:

- `FlightDate` — Fecha del vuelo (YYYY-MM-DD)
- `Carrier` — Código IATA de la aerolínea (ej: AA, UA, DL)
- `Origin` / `Dest` — Aeropuertos de origen y destino (IATA)
- `DepDelay` / `ArrDelay` — Retraso en salida/llegada en minutos (negativo = adelantado)
- `Cancelled` — 1 si el vuelo fue cancelado
- `CancellationCode` — Causa de cancelación: A=Carrier, B=Weather, C=NAS, D=Security
- `CarrierDelay` — Minutos de delay atribuibles a la aerolínea
- `WeatherDelay` — Minutos de delay por clima
- `NASDelay` — Minutos de delay por el sistema nacional de aviación (ATC, congestión)
- `SecurityDelay` — Minutos de delay por seguridad
- `LateAircraftDelay` — Minutos de delay por avión tardío del vuelo anterior

### 2. T-100 Domestic Segment
Estadísticas agregadas por par O-D, por mes y aerolínea:
- Pasajeros transportados
- Asientos disponibles (capacidad)
- Número de vuelos operados
- Permite calcular load factor (pasajeros/asientos)

### 3. DB1B Coupon (Tarifas O-D)
Muestra del 10% de todos los boletos vendidos en EEUU, por trimestre:
- Precio pagado por el pasajero
- Ruta completa con conexiones
- Clase de cabina (Economy, Business, First)
- Itinerario completo (origen final → destino final)
- Útil para análisis de revenue y elasticidad de precios

### 4. Aviation Support Tables (Lookups)
- Maestro de aeropuertos con coordenadas, ciudad, estado, país (IATA/ICAO)
- Maestro de aerolíneas con nombre, país, código DOT
- Tablas de referencia para joins con On-Time y T-100

---

## Descarga automática con Python

### Opción A — Descarga directa del BTS (datos raw, histórico completo)

```python
import requests
import os
import time
from pathlib import Path
from tqdm import tqdm

# Configuración
OUTPUT_DIR = Path("/tmp/bts_data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# El BTS usa un formulario POST para descargar datos
# URL base del sistema de descarga
BTS_BASE_URL = "https://www.transtats.bts.gov/DownLoad_Table.asp"

# Parámetros para On-Time Performance (tabla ID: ONTIME_REPORTING)
# El BTS requiere seleccionar campos específicos — usar los más relevantes
BTS_PARAMS = {
    "Table_ID": "236",       # On-Time Reporting
    "Has_Group": "3",
    "Is_Zipped": "0",
    "Prezip_File": "T_ONTIME_REPORTING",
}

def download_bts_month(year: int, month: int, output_dir: Path, retries: int = 3) -> Path:
    """
    Descarga datos de On-Time Performance del BTS para un año/mes específico.
    Retorna el path del CSV descargado.
    """
    output_path = output_dir / f"ontime_{year}_{month:02d}.csv"
    if output_path.exists():
        print(f"  Ya existe: {output_path.name}")
        return output_path

    params = {
        **BTS_PARAMS,
        "UserTableName": f"On_Time_Reporting_{year}_{month}",
        "RawDataTable": "T_ONTIME_REPORTING",
        "sqlstr": (
            f"SELECT FlightDate,Reporting_Airline,Origin,Dest,"
            f"DepDelay,ArrDelay,Cancelled,CancellationCode,"
            f"CarrierDelay,WeatherDelay,NASDelay,SecurityDelay,LateAircraftDelay "
            f"FROM T_ONTIME_REPORTING "
            f"WHERE Year={year} AND Month={month}"
        ),
        "varlist": "FlightDate,Reporting_Airline,Origin,Dest,DepDelay,ArrDelay,Cancelled,CancellationCode,CarrierDelay,WeatherDelay,NASDelay,SecurityDelay,LateAircraftDelay",
        "grouplist": "",
        "suml": "",
        "sumRegion": "",
        "filter1": "title=",
        "filter2": "title=",
        "geo": "All",
        "time": f"{year}:{month}",
        "timename": "Month",
        "GEOGRAPHY": "All",
        "XYEAR": str(year),
        "FREQUENCY": str(month),
        "VarDesc": "FlightDate",
        "VarType": "Num",
        "VarDesc": "Reporting_Airline",
        "VarType": "Char",
    }

    for attempt in range(retries):
        try:
            print(f"  Descargando {year}-{month:02d} (intento {attempt+1}/{retries})...")
            response = requests.post(
                BTS_BASE_URL,
                data=params,
                timeout=120,
                headers={"User-Agent": "Mozilla/5.0 (research/data-download)"}
            )
            response.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(response.content)

            print(f"  Guardado: {output_path.name} ({output_path.stat().st_size / 1e6:.1f} MB)")
            return output_path

        except Exception as e:
            print(f"  Error intento {attempt+1}: {e}")
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
            else:
                raise

def download_bts_range(start_year: int, end_year: int, output_dir: Path):
    """Descarga todos los meses en un rango de años."""
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            download_bts_month(year, month, output_dir)
            time.sleep(2)  # Rate limiting

# Ejemplo: descargar 2022-2023
# download_bts_range(2022, 2023, OUTPUT_DIR)
```

### Opción B — Dataset Kaggle pre-procesado (recomendado para empezar)

5.7M vuelos de 2015-2019, ya limpios y listos para usar. Mucho más rápido que el BTS raw.

```python
import subprocess
import polars as pl
from pathlib import Path

KAGGLE_DATASET = "yuanyuwendymu/airline-delay-and-cancellation-data-2009-2018"
OUTPUT_DIR = Path("/tmp/bts_kaggle")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_kaggle_bts():
    """
    Requiere configurar credenciales de Kaggle:
    1. Crear cuenta en kaggle.com
    2. Ir a Settings > API > Create New Token
    3. Guardar kaggle.json en ~/.kaggle/kaggle.json
    4. chmod 600 ~/.kaggle/kaggle.json
    """
    subprocess.run([
        "kaggle", "datasets", "download",
        "-d", KAGGLE_DATASET,
        "-p", str(OUTPUT_DIR),
        "--unzip"
    ], check=True)
    print(f"Dataset descargado en {OUTPUT_DIR}")

# Cargar un año específico del dataset Kaggle
def load_kaggle_year(year: int) -> pl.DataFrame:
    csv_path = OUTPUT_DIR / f"{year}.csv"
    return pl.read_csv(csv_path, null_values=["", "NA", "NaN"])

# download_kaggle_bts()
# df_2018 = load_kaggle_year(2018)
```

---

## Schema Polars completo

```python
import polars as pl
from pathlib import Path

# Schema explícito para evitar inferencia incorrecta de tipos
BTS_SCHEMA = {
    "FlightDate":          pl.Utf8,    # Se castea a Date después
    "Reporting_Airline":   pl.Utf8,    # Código IATA aerolínea
    "Origin":              pl.Utf8,    # Aeropuerto origen (IATA)
    "Dest":                pl.Utf8,    # Aeropuerto destino (IATA)
    "DepDelay":            pl.Float32, # Float para aceptar NaN
    "ArrDelay":            pl.Float32,
    "Cancelled":           pl.Float32, # 0.0 o 1.0
    "CancellationCode":    pl.Utf8,    # "A", "B", "C", "D" o null
    "CarrierDelay":        pl.Float32,
    "WeatherDelay":        pl.Float32,
    "NASDelay":            pl.Float32,
    "SecurityDelay":       pl.Float32,
    "LateAircraftDelay":   pl.Float32,
}

def load_bts_csv(path: str | Path) -> pl.DataFrame:
    """
    Carga un CSV del BTS con tipos correctos.
    Maneja NaN en columnas de delay (missing by design en vuelos cancelados).
    """
    df = pl.read_csv(
        path,
        schema_overrides=BTS_SCHEMA,
        null_values=["", "NA", "N/A"],
        try_parse_dates=False,  # Parsear manualmente para control total
    )

    df = df.with_columns([
        # Castear fecha correctamente
        pl.col("FlightDate").str.strptime(pl.Date, "%Y-%m-%d").alias("FlightDate"),

        # Extraer componentes de fecha útiles
        pl.col("FlightDate").str.strptime(pl.Date, "%Y-%m-%d").dt.year().alias("Year"),
        pl.col("FlightDate").str.strptime(pl.Date, "%Y-%m-%d").dt.month().alias("Month"),
        pl.col("FlightDate").str.strptime(pl.Date, "%Y-%m-%d").dt.weekday().alias("DayOfWeek"),

        # Convertir delays de minutos a horas (útil para reportes)
        (pl.col("ArrDelay") / 60.0).alias("ArrDelayHours"),
        (pl.col("DepDelay") / 60.0).alias("DepDelayHours"),

        # Booleano de cancelación (más claro que 0.0/1.0)
        (pl.col("Cancelled") == 1.0).alias("IsCancelled"),

        # Los delays de vuelos cancelados son NaN por diseño — NO imputar con 0
        # Mantenerlos como null para no distorsionar estadísticas
    ])

    return df


def load_bts_lazy(glob_pattern: str) -> pl.LazyFrame:
    """
    Carga múltiples CSVs del BTS de forma lazy (sin cargar en memoria).
    Ideal para procesar años completos (1-3 GB por año).

    Ejemplo:
        lf = load_bts_lazy("/tmp/bts_data/ontime_2022_*.csv")
        resultado = lf.filter(pl.col("Origin") == "JFK").collect()
    """
    return pl.scan_csv(
        glob_pattern,
        schema_overrides=BTS_SCHEMA,
        null_values=["", "NA", "N/A"],
    )
```

---

## Feature engineering específico BTS

```python
import polars as pl

def add_bts_features(df: pl.DataFrame) -> pl.DataFrame:
    """
    Agrega features de negocio al dataset BTS.
    Espera el schema cargado con load_bts_csv().
    """

    return df.with_columns([

        # --- DELAY CATEGORY ---
        # Clasifica el retraso en 4 categorías de industria
        pl.when(pl.col("ArrDelay") < 0)
            .then(pl.lit("On-Time"))
        .when(pl.col("ArrDelay").is_between(0, 15))
            .then(pl.lit("Minor"))
        .when(pl.col("ArrDelay").is_between(15, 45))
            .then(pl.lit("Moderate"))
        .when(pl.col("ArrDelay") > 45)
            .then(pl.lit("Major"))
        .otherwise(pl.lit(None))  # Vuelos cancelados → null
        .alias("delay_category"),

        # --- CAUSA PRINCIPAL DEL DELAY ---
        # Identifica cuál de las 5 causas es la dominante
        pl.when(
            (pl.col("CarrierDelay") >= pl.col("WeatherDelay")) &
            (pl.col("CarrierDelay") >= pl.col("NASDelay")) &
            (pl.col("CarrierDelay") >= pl.col("SecurityDelay")) &
            (pl.col("CarrierDelay") >= pl.col("LateAircraftDelay"))
        ).then(pl.lit("Carrier"))
        .when(
            (pl.col("WeatherDelay") >= pl.col("NASDelay")) &
            (pl.col("WeatherDelay") >= pl.col("SecurityDelay")) &
            (pl.col("WeatherDelay") >= pl.col("LateAircraftDelay"))
        ).then(pl.lit("Weather"))
        .when(
            (pl.col("NASDelay") >= pl.col("SecurityDelay")) &
            (pl.col("NASDelay") >= pl.col("LateAircraftDelay"))
        ).then(pl.lit("NAS"))
        .when(pl.col("SecurityDelay") >= pl.col("LateAircraftDelay"))
            .then(pl.lit("Security"))
        .otherwise(pl.lit("LateAircraft"))
        .alias("delay_cause_primary"),

        # --- IS CANCELLED ---
        (pl.col("Cancelled") == 1.0).alias("is_cancelled"),

        # --- RUTA NORMALIZADA (siempre alphabetical) ---
        # Evita duplicados: "SCL-MIA" y "MIA-SCL" son la misma ruta
        pl.when(pl.col("Origin") < pl.col("Dest"))
            .then(pl.col("Origin") + pl.lit("-") + pl.col("Dest"))
            .otherwise(pl.col("Dest") + pl.lit("-") + pl.col("Origin"))
        .alias("route"),

        # --- SEASON (hemisferio norte, referencia BTS/EEUU) ---
        pl.when(pl.col("Month").is_in([12, 1, 2]))
            .then(pl.lit("Winter"))
        .when(pl.col("Month").is_in([3, 4, 5]))
            .then(pl.lit("Spring"))
        .when(pl.col("Month").is_in([6, 7, 8]))
            .then(pl.lit("Summer"))
        .otherwise(pl.lit("Fall"))
        .alias("season"),

    ]).with_columns([

        # --- IS PEAK HOUR ---
        # Requiere columna DepTime (hora de salida programada, formato HHMM)
        # Si no está disponible, agregar al schema de carga
        pl.when(pl.col("DepTime").is_not_null())
            .then(
                (
                    pl.col("DepTime").is_between(700, 900) |
                    pl.col("DepTime").is_between(1700, 2000)
                )
            )
        .otherwise(pl.lit(None))
        .alias("is_peak_hour"),

    ])


def add_airport_congestion(df: pl.DataFrame) -> pl.DataFrame:
    """
    Agrega ranking de congestión por aeropuerto basado en % de delays.
    Calcula sobre el DataFrame completo (requiere todos los vuelos).
    """
    # Calcular % de delays por aeropuerto de origen
    congestion = (
        df
        .filter(pl.col("is_cancelled").not_())
        .group_by("Origin")
        .agg([
            pl.len().alias("total_flights"),
            (pl.col("ArrDelay") > 15).sum().alias("delayed_flights"),
        ])
        .with_columns([
            (pl.col("delayed_flights") / pl.col("total_flights") * 100)
            .alias("delay_pct")
        ])
        .with_columns([
            pl.col("delay_pct")
            .rank(method="ordinal", descending=True)
            .alias("congestion_rank")
        ])
        .select(["Origin", "delay_pct", "congestion_rank"])
    )

    return df.join(congestion, on="Origin", how="left")
```

---

## Análisis de benchmark

```python
import polars as pl

def benchmark_ontime_rate(df: pl.DataFrame) -> pl.DataFrame:
    """
    On-Time Rate por aerolínea (vuelos con ArrDelay <= 15 minutos).
    Estándar de la industria DOT: on-time = llegada con <=15 min de retraso.
    """
    return (
        df
        .filter(pl.col("is_cancelled").not_())
        .group_by("Reporting_Airline")
        .agg([
            pl.len().alias("total_flights"),
            (pl.col("ArrDelay") <= 15).sum().alias("ontime_flights"),
            pl.col("ArrDelay").mean().alias("avg_arr_delay_min"),
            pl.col("ArrDelay").median().alias("median_arr_delay_min"),
        ])
        .with_columns([
            (pl.col("ontime_flights") / pl.col("total_flights") * 100)
            .round(2)
            .alias("ontime_rate_pct")
        ])
        .sort("ontime_rate_pct", descending=True)
    )


def benchmark_delay_by_cause(df: pl.DataFrame) -> pl.DataFrame:
    """Average delay en minutos por causa, por aerolínea."""
    return (
        df
        .filter(pl.col("ArrDelay") > 0)  # Solo vuelos con delay real
        .filter(pl.col("is_cancelled").not_())
        .group_by("Reporting_Airline")
        .agg([
            pl.col("CarrierDelay").mean().alias("avg_carrier_delay"),
            pl.col("WeatherDelay").mean().alias("avg_weather_delay"),
            pl.col("NASDelay").mean().alias("avg_nas_delay"),
            pl.col("SecurityDelay").mean().alias("avg_security_delay"),
            pl.col("LateAircraftDelay").mean().alias("avg_late_aircraft_delay"),
        ])
        .sort("avg_carrier_delay", descending=True)
    )


def benchmark_cancellation_rate(df: pl.DataFrame) -> pl.DataFrame:
    """Cancellation rate por aerolínea, mes y año."""
    return (
        df
        .group_by(["Reporting_Airline", "Year", "Month"])
        .agg([
            pl.len().alias("total_flights"),
            pl.col("is_cancelled").sum().alias("cancelled_flights"),
        ])
        .with_columns([
            (pl.col("cancelled_flights") / pl.col("total_flights") * 100)
            .round(2)
            .alias("cancellation_rate_pct")
        ])
        .sort(["Year", "Month", "cancellation_rate_pct"], descending=[False, False, True])
    )


def benchmark_load_factor(t100_path: str) -> pl.DataFrame:
    """
    Load factor desde T-100 Domestic Segment.
    Descarga desde: https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FHK
    """
    t100 = pl.read_csv(t100_path, null_values=["", "NA"])

    return (
        t100
        .group_by(["Carrier", "Year", "Month"])
        .agg([
            pl.col("PASSENGERS").sum().alias("total_passengers"),
            pl.col("SEATS").sum().alias("total_seats"),
            pl.col("DEPARTURES_PERFORMED").sum().alias("total_flights"),
        ])
        .with_columns([
            (pl.col("total_passengers") / pl.col("total_seats") * 100)
            .round(2)
            .alias("load_factor_pct")
        ])
        .sort("load_factor_pct", descending=True)
    )


def top_routes_by_volume(t100_path: str, top_n: int = 20) -> pl.DataFrame:
    """Top rutas por volumen de pasajeros desde T-100."""
    t100 = pl.read_csv(t100_path, null_values=["", "NA"])

    return (
        t100
        .group_by(["Origin", "Dest"])
        .agg(pl.col("PASSENGERS").sum().alias("total_passengers"))
        .sort("total_passengers", descending=True)
        .head(top_n)
    )


def benchmark_lan_vs_competitors(df: pl.DataFrame) -> pl.DataFrame:
    """
    Compara LAN (código LA) vs competidores en rutas EEUU-LATAM.
    LAN aparece en BTS en rutas internacionales con escala en EEUU.

    Códigos LATAM Group:
    - LA  = LAN Airlines (Chile)
    - XL  = LATAM Airlines Ecuador
    - 4M  = LATAM Argentina
    - JJ  = LATAM Brasil
    """
    LATAM_CODES = ["LA", "XL", "4M", "JJ"]
    COMPETITORS = ["AA", "UA", "CO", "AV", "CM", "AR"]  # American, United, Copa, Avianca, Aerolineas

    # Aeropuertos de LATAM como punto de comparación
    LATAM_AIRPORTS = ["GRU", "SCL", "BOG", "LIM", "EZE", "GIG", "MVD", "ASU"]

    # Filtrar rutas relevantes: vuelos desde/hacia aeropuertos de LATAM
    df_latam_routes = df.filter(
        pl.col("Dest").is_in(LATAM_AIRPORTS) |
        pl.col("Origin").is_in(LATAM_AIRPORTS)
    )

    # Incluir LATAM group + competidores
    airlines_of_interest = LATAM_CODES + COMPETITORS
    df_filtered = df_latam_routes.filter(
        pl.col("Reporting_Airline").is_in(airlines_of_interest)
    )

    return benchmark_ontime_rate(df_filtered)
```

---

## Adaptación para LAN Chile

El BTS tiene cobertura principalmente de aerolíneas estadounidenses, pero incluye aerolíneas extranjeras en rutas internacionales con origen o destino en aeropuertos americanos.

**Códigos IATA del grupo LATAM en BTS:**
- `LA` — LAN Airlines (Chile, hub SCL)
- `XL` — LATAM Airlines Ecuador
- `4M` — LATAM Argentina
- `JJ` — LATAM Brasil (ex-TAM)

**Rutas con datos disponibles en BTS:**
- SCL ↔ MIA (Miami), JFK (Nueva York), LAX (Los Angeles), IAD (Washington)
- GRU ↔ MIA, JFK
- BOG ↔ MIA, JFK (Copa, Avianca como referencia)

**Para benchmark de mercado EEUU-LATAM:**
```python
# Filtrar rutas desde/hacia aeropuertos EEUU con destino LATAM
LATAM_AIRPORTS_BTS = ["GRU", "SCL", "BOG", "LIM", "EZE", "GIG", "MVD", "CCS"]

df_benchmark = df.filter(
    (pl.col("Dest").is_in(LATAM_AIRPORTS_BTS)) |
    (pl.col("Origin").is_in(LATAM_AIRPORTS_BTS))
).filter(
    pl.col("Reporting_Airline").is_in(["LA", "JJ", "AA", "UA", "CM", "AV"])
)
```

**Para datos de operaciones domésticas en Chile:**
La JUNTA DE AERONÁUTICA CIVIL (JAC) publica estadísticas mensuales en Excel:
- URL: https://www.jac.gob.cl/estadisticas/
- Formato: Excel mensual (.xlsx), NO hay API disponible
- Requiere descarga manual o scraping web
- Columnas: ruta, aerolínea, pasajeros, vuelos, asientos por mes
- Lag: publicación con ~2 meses de retraso
- Carga: `pl.read_excel(path, engine="openpyxl")`

```python
import polars as pl

def load_jac_excel(path: str) -> pl.DataFrame:
    """Carga estadísticas de la JAC Chile desde Excel mensual."""
    return pl.read_excel(
        path,
        engine="openpyxl",
        # Ajustar sheet_name según el Excel descargado
        sheet_name="Hoja1",
    ).rename({
        # Renombrar columnas según formato JAC (puede variar por año)
        "AEROLINEA": "airline",
        "ORIGEN": "origin",
        "DESTINO": "dest",
        "PASAJEROS": "passengers",
        "VUELOS": "flights",
        "ASIENTOS": "seats",
    })
```

---

## Pitfalls

- **Archivos pesados**: Los CSVs del BTS pesan 1-3 GB por año. Usar siempre `pl.scan_csv()` (lazy evaluation) para filtrar antes de cargar en memoria. Nunca usar `pl.read_csv()` en producción con años completos.

- **NaN en delays por diseño**: Las columnas `CarrierDelay`, `WeatherDelay`, `NASDelay`, `SecurityDelay`, `LateAircraftDelay` son `NaN`/`null` cuando el vuelo fue cancelado. **No imputar con 0** — son missing by design. Si se imputa, las estadísticas de delay quedarán distorsionadas.

- **CancellationCode mapping**:
  - `A` = Carrier (culpa de la aerolínea — mantenimiento, tripulación)
  - `B` = Weather (clima)
  - `C` = NAS (National Airspace System — ATC, congestión aeropuerto)
  - `D` = Security (incidente de seguridad)

- **Lag de datos BTS**: Los datos de On-Time Performance se publican con 2-3 meses de retraso. Si se necesitan datos de noviembre, estarán disponibles en febrero siguiente.

- **Kaggle dataset como punto de partida**: El dataset de Kaggle (2009-2018) ya está limpio, normalizado y listo para usar. Recomendado para prototipado y análisis exploratorio antes de conectarse al BTS raw.

- **JAC Chile**: Solo Excel manual, sin API. Requiere scraping de la web con Selenium/BeautifulSoup para automatizar la descarga mensual. URL: https://www.jac.gob.cl/estadisticas/

- **Columna DepTime**: Formato HHMM como entero (ej: 830 = 08:30, 2045 = 20:45). Convertir para análisis de horarios pico.

---

## Instalación

```bash
pip install polars requests tqdm kaggle openpyxl
```
