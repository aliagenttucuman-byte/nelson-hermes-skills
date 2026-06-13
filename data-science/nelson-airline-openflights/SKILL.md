---
name: nelson-airline-openflights
description: "Descarga y análisis de la red de rutas aéreas globales con OpenFlights. 67.663 rutas, 10.531 aeropuertos, 5.888 aerolíneas. Grafos con NetworkX. Cobertura de red LAN/LATAM, conectividad hub-and-spoke, centralidad de aeropuertos."
triggers:
  - OpenFlights
  - red de rutas aereas
  - grafo de rutas
  - hub and spoke
  - conectividad red aerolinea
  - cobertura LAN LATAM
version: "1.0.0"
---

# OpenFlights — Red Global de Rutas Aéreas

Dataset gratuito y estático de la red de rutas aéreas mundial. Ideal para análisis de grafos, cobertura de red, hub-and-spoke y features geoespaciales para modelos de demanda. Datos estáticos (no real-time), pero completos y fáciles de usar.

---

## Datasets de OpenFlights

Cuatro archivos CSV sin headers nativos. Descargar desde GitHub y definir columnas manualmente al cargar.

### 1. airports.dat — 10.531 aeropuertos
```
AirportID  — ID interno de OpenFlights (entero)
Name       — Nombre completo del aeropuerto
City       — Ciudad
Country    — País
IATA       — Código IATA de 3 letras (ej: SCL, MIA, JFK) — puede ser \N si no tiene
ICAO       — Código ICAO de 4 letras (ej: SCEL, KMIA) — siempre disponible
Lat        — Latitud decimal
Lon        — Longitud decimal
Altitude   — Altitud en pies
Timezone   — Offset UTC (número)
DST        — Regla de horario de verano (E/A/S/O/Z/N/U)
TzDatabase — Zona horaria IANA (ej: America/Santiago)
Type       — Tipo (airport, station, port, unknown)
Source     — Fuente del dato
```

### 2. airlines.dat — 5.888 aerolíneas
```
AirlineID  — ID interno de OpenFlights
Name       — Nombre de la aerolínea
Alias      — Alias o nombre alternativo
IATA       — Código IATA de 2 letras (ej: LA, AA, UA)
ICAO       — Código ICAO de 3 letras (ej: LAN, AAL, UAL)
Callsign   — Callsign de radio (ej: LANAIR, AMERICAN)
Country    — País de registro
Active     — "Y" si está activa, "N" si cesó operaciones
```

### 3. routes.dat — 67.663 rutas
```
Airline          — Código IATA de 2 letras de la aerolínea
AirlineID        — ID interno de OpenFlights (-1 si desconocido)
SourceAirport    — Código IATA aeropuerto origen
SourceAirportID  — ID interno aeropuerto origen
DestAirport      — Código IATA aeropuerto destino
DestAirportID    — ID interno aeropuerto destino
Codeshare        — "Y" si es vuelo en codeshare, vacío si no
Stops            — Número de escalas (0 = vuelo directo)
Equipment        — Modelos de avión usados (ej: "738 320")
```

### 4. planes.dat — Modelos de aviones
```
Name   — Nombre completo del modelo (ej: Boeing 737-800)
IATA   — Código IATA del avión (ej: 738)
ICAO   — Código ICAO del avión (ej: B738)
```

---

## Descarga directa

```python
import requests
import polars as pl
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data"
OUTPUT_DIR = Path("/tmp/openflights")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "airports": "airports.dat",
    "airlines": "airlines.dat",
    "routes":   "routes.dat",
    "planes":   "planes.dat",
}

def download_openflights():
    """Descarga todos los archivos de OpenFlights."""
    for name, filename in FILES.items():
        url = f"{BASE_URL}/{filename}"
        path = OUTPUT_DIR / filename
        if path.exists():
            print(f"  Ya existe: {filename}")
            continue
        print(f"  Descargando {filename}...")
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        path.write_bytes(r.content)
        print(f"  Guardado: {path} ({path.stat().st_size / 1e3:.0f} KB)")


# Columnas por archivo (sin headers en los .dat)
AIRPORTS_COLS = [
    "AirportID", "Name", "City", "Country",
    "IATA", "ICAO", "Lat", "Lon",
    "Altitude", "Timezone", "DST", "TzDatabase", "Type", "Source"
]

AIRLINES_COLS = [
    "AirlineID", "Name", "Alias", "IATA",
    "ICAO", "Callsign", "Country", "Active"
]

ROUTES_COLS = [
    "Airline", "AirlineID",
    "SourceAirport", "SourceAirportID",
    "DestAirport", "DestAirportID",
    "Codeshare", "Stops", "Equipment"
]

PLANES_COLS = ["Name", "IATA", "ICAO"]


def load_airports() -> pl.DataFrame:
    """Carga airports.dat con columnas correctas y limpieza de nulos."""
    return (
        pl.read_csv(
            OUTPUT_DIR / "airports.dat",
            has_header=False,
            new_columns=AIRPORTS_COLS,
            null_values=["\\N", ""],
            quote_char='"',
            schema_overrides={
                "AirportID": pl.Int32,
                "Lat": pl.Float64,
                "Lon": pl.Float64,
                "Altitude": pl.Float64,
                "Timezone": pl.Float64,
            }
        )
    )


def load_airlines() -> pl.DataFrame:
    """Carga airlines.dat. Filtra aerolíneas con AirlineID=-1."""
    return (
        pl.read_csv(
            OUTPUT_DIR / "airlines.dat",
            has_header=False,
            new_columns=AIRLINES_COLS,
            null_values=["\\N", ""],
            quote_char='"',
            schema_overrides={"AirlineID": pl.Int32}
        )
        .filter(pl.col("AirlineID") != -1)
    )


def load_routes() -> pl.DataFrame:
    """
    Carga routes.dat. Reemplaza \\N (nulos de OpenFlights) por null.
    Filtra rutas con AirlineID desconocido (-1).
    """
    return (
        pl.read_csv(
            OUTPUT_DIR / "routes.dat",
            has_header=False,
            new_columns=ROUTES_COLS,
            null_values=["\\N", ""],
            quote_char='"',
            schema_overrides={
                "AirlineID": pl.Int32,
                "SourceAirportID": pl.Int32,
                "DestAirportID": pl.Int32,
                "Stops": pl.Int32,
            }
        )
        .filter(pl.col("AirlineID") != -1)
        .filter(pl.col("SourceAirport").is_not_null())
        .filter(pl.col("DestAirport").is_not_null())
    )


# Uso
# download_openflights()
# airports = load_airports()
# airlines = load_airlines()
# routes   = load_routes()
```

---

## Análisis de red con NetworkX

```python
import networkx as nx
import polars as pl
import community as community_louvain  # python-louvain

def build_route_graph(
    routes: pl.DataFrame,
    airline_filter: str | list[str] | None = None
) -> nx.DiGraph:
    """
    Construye grafo dirigido de rutas aéreas.

    Args:
        routes: DataFrame de load_routes()
        airline_filter: Código IATA o lista de códigos. None = todas las aerolíneas.

    Returns:
        nx.DiGraph donde nodos=aeropuertos IATA, aristas=rutas.
        Peso de cada arista = número de rutas entre ese par (si hay múltiples aerolíneas).
    """
    df = routes
    if airline_filter is not None:
        if isinstance(airline_filter, str):
            airline_filter = [airline_filter]
        df = routes.filter(pl.col("Airline").is_in(airline_filter))

    G = nx.DiGraph()

    for row in df.iter_rows(named=True):
        src = row["SourceAirport"]
        dst = row["DestAirport"]
        airline = row["Airline"]

        if G.has_edge(src, dst):
            G[src][dst]["weight"] += 1
            G[src][dst]["airlines"].add(airline)
        else:
            G.add_edge(src, dst, weight=1, airlines={airline})

    return G


def network_metrics(G: nx.DiGraph, airports: pl.DataFrame) -> pl.DataFrame:
    """
    Calcula métricas de centralidad para todos los nodos del grafo.

    Retorna DataFrame con:
    - degree_centrality: fracción de nodos conectados (qué tan conectado está)
    - betweenness_centrality: qué tan frecuente es el nodo en caminos más cortos
    - pagerank: importancia ponderada recursiva (como Google PageRank)
    - in_degree / out_degree: rutas que llegan / salen
    """
    print("Calculando degree centrality...")
    degree_cent = nx.degree_centrality(G)

    print("Calculando betweenness centrality (puede tardar)...")
    betweenness = nx.betweenness_centrality(G, normalized=True)

    print("Calculando PageRank...")
    pagerank = nx.pagerank(G, alpha=0.85, max_iter=200)

    in_deg  = dict(G.in_degree())
    out_deg = dict(G.out_degree())

    metrics_df = pl.DataFrame({
        "IATA":                 list(degree_cent.keys()),
        "degree_centrality":    list(degree_cent.values()),
        "betweenness_centrality": [betweenness.get(n, 0) for n in degree_cent],
        "pagerank":             [pagerank.get(n, 0) for n in degree_cent],
        "in_degree":            [in_deg.get(n, 0) for n in degree_cent],
        "out_degree":           [out_deg.get(n, 0) for n in degree_cent],
    })

    # Join con datos del aeropuerto para contexto
    return metrics_df.join(
        airports.select(["IATA", "Name", "City", "Country", "Lat", "Lon"]),
        on="IATA",
        how="left"
    ).sort("pagerank", descending=True)


def shortest_path_between(G: nx.DiGraph, origin: str, dest: str) -> list[str]:
    """
    Ruta más corta (menor número de escalas) entre dos aeropuertos.

    Ejemplo:
        path = shortest_path_between(G, "SCL", "NRT")
        # ['SCL', 'MIA', 'LAX', 'NRT']  → 2 escalas
    """
    try:
        return nx.shortest_path(G, source=origin, target=dest)
    except nx.NetworkXNoPath:
        return []  # Sin conexión posible


def network_diameter(G: nx.DiGraph) -> int:
    """
    Máxima distancia entre cualquier par de aeropuertos conectados.
    ATENCIÓN: muy lento en grafos grandes. Solo usar con subgrafos filtrados.
    """
    # Solo calcular sobre la componente fuertemente conectada más grande
    largest_scc = max(nx.strongly_connected_components(G), key=len)
    subgraph = G.subgraph(largest_scc)
    return nx.diameter(subgraph)


def detect_hub_communities(G: nx.DiGraph) -> dict[str, int]:
    """
    Detecta comunidades (hubs regionales) con algoritmo de Louvain.
    Requiere: pip install python-louvain

    Retorna dict {aeropuerto_IATA: comunidad_id}
    """
    # Louvain trabaja con grafo no dirigido
    G_undirected = G.to_undirected()
    partition = community_louvain.best_partition(G_undirected)
    return partition  # {nodo: comunidad_id}
```

---

## Red LAN/LATAM específica

```python
import polars as pl
import networkx as nx

# Todos los códigos IATA del grupo LATAM
LATAM_GROUP_CODES = ["LA", "XL", "4M", "JJ", "LP", "UC"]
# LA  = LAN Airlines (Chile)
# XL  = LATAM Airlines Ecuador
# 4M  = LATAM Argentina
# JJ  = LATAM Brasil (ex-TAM)
# LP  = LAN Perú
# UC  = LAN Ecuador (histórico)

# Competidores directos en LATAM
LATAM_COMPETITORS = {
    "AR": "Aerolíneas Argentinas",
    "CM": "Copa Airlines (Panamá)",
    "AV": "Avianca (Colombia)",
    "G3": "Gol (Brasil)",
    "AD": "Azul (Brasil)",
}

# Hub principal del grupo
HUB_SCL = "SCL"  # Arturo Merino Benítez, Santiago de Chile

# Rutas de largo radio (long-haul)
LONG_HAUL_ROUTES = [
    ("SCL", "MIA"),  # Santiago - Miami
    ("SCL", "MAD"),  # Santiago - Madrid (IB codeshare)
    ("SCL", "GRU"),  # Santiago - São Paulo
    ("SCL", "JFK"),  # Santiago - Nueva York
    ("SCL", "LAX"),  # Santiago - Los Angeles
    ("SCL", "CDG"),  # Santiago - París
    ("GRU", "MIA"),  # São Paulo - Miami (LATAM Brasil)
]

# Aeropuertos domésticos Chile
CHILE_DOMESTIC_AIRPORTS = [
    "SCL",  # Santiago
    "PMC",  # Puerto Montt
    "CCP",  # Concepción
    "ZCO",  # Temuco
    "IQQ",  # Iquique
    "ANF",  # Antofagasta
    "ARI",  # Arica
    "LSC",  # La Serena
    "ZAL",  # Valdivia
    "PMC",  # Puerto Montt
    "PUQ",  # Punta Arenas
    "MHC",  # Mocopulli (Chiloé)
]


def analyze_latam_network(routes: pl.DataFrame, airports: pl.DataFrame) -> dict:
    """
    Análisis completo de la red del grupo LATAM vs competidores.
    """
    # 1. Red completa del grupo LATAM
    G_latam = build_route_graph(routes, airline_filter=LATAM_GROUP_CODES)

    # 2. Red de cada competidor
    competitor_graphs = {
        code: build_route_graph(routes, airline_filter=code)
        for code in LATAM_COMPETITORS
    }

    # 3. Métricas de SCL como hub
    scl_metrics = {
        "out_degree":  G_latam.out_degree(HUB_SCL) if HUB_SCL in G_latam else 0,
        "in_degree":   G_latam.in_degree(HUB_SCL) if HUB_SCL in G_latam else 0,
        "pagerank":    nx.pagerank(G_latam).get(HUB_SCL, 0),
        "betweenness": nx.betweenness_centrality(G_latam).get(HUB_SCL, 0),
    }

    # 4. Rutas domésticas Chile (LATAM)
    chile_routes = (
        routes
        .filter(pl.col("Airline").is_in(LATAM_GROUP_CODES))
        .filter(
            pl.col("SourceAirport").is_in(CHILE_DOMESTIC_AIRPORTS) &
            pl.col("DestAirport").is_in(CHILE_DOMESTIC_AIRPORTS)
        )
    )

    # 5. Índice de conectividad: rutas directas vs con escala en SCL
    direct_routes = (
        routes
        .filter(pl.col("Airline").is_in(LATAM_GROUP_CODES))
        .filter(pl.col("SourceAirport") != HUB_SCL)
        .filter(pl.col("DestAirport") != HUB_SCL)
        .height
    )
    hub_routes = (
        routes
        .filter(pl.col("Airline").is_in(LATAM_GROUP_CODES))
        .filter(
            (pl.col("SourceAirport") == HUB_SCL) |
            (pl.col("DestAirport") == HUB_SCL)
        )
        .height
    )
    total_routes = direct_routes + hub_routes
    hub_dependency = hub_routes / total_routes if total_routes > 0 else 0

    # 6. Coverage comparison
    coverage = {
        "LATAM Group": routes.filter(pl.col("Airline").is_in(LATAM_GROUP_CODES)).height,
    }
    coverage.update({
        code: routes.filter(pl.col("Airline") == code).height
        for code in LATAM_COMPETITORS
    })

    return {
        "scl_hub_metrics":     scl_metrics,
        "chile_domestic_routes": chile_routes,
        "hub_dependency_ratio": hub_dependency,
        "route_coverage":      coverage,
        "latam_graph":         G_latam,
    }
```

---

## Casos de uso para ML

```python
import polars as pl
import networkx as nx
from math import radians, cos, sin, asin, sqrt

def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Distancia geodésica en km entre dos puntos (Fórmula de Haversine)."""
    R = 6371  # Radio de la Tierra en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))


def build_route_features(
    routes: pl.DataFrame,
    airports: pl.DataFrame,
    G: nx.DiGraph,
) -> pl.DataFrame:
    """
    Construye features de red para modelos de demanda y ML.

    Genera un DataFrame con una fila por ruta (par O-D) y features:
    - degree_centrality_src / dst: conectividad del aeropuerto
    - betweenness_src / dst: importancia como nodo puente
    - pagerank_src / dst: importancia relativa del hub
    - geodesic_distance_km: distancia real en km
    - n_airlines_on_route: número de aerolíneas compitiendo en el par O-D
    - has_direct_flight: si existe vuelo directo (Stops == 0)
    - n_alternatives: caminos alternativos de 1 escala entre O-D
    """
    degree_cent  = nx.degree_centrality(G)
    betweenness  = nx.betweenness_centrality(G, normalized=True)
    pagerank     = nx.pagerank(G)

    # Enriquecer con coordenadas
    airports_coords = airports.select(["IATA", "Lat", "Lon"]).to_pandas().set_index("IATA")

    # Competencia por ruta
    competition = (
        routes
        .group_by(["SourceAirport", "DestAirport"])
        .agg(pl.n_unique("Airline").alias("n_airlines_on_route"))
    )

    # Rutas directas
    direct_flights = (
        routes
        .filter(pl.col("Stops") == 0)
        .with_columns(pl.lit(True).alias("has_direct_flight"))
        .select(["SourceAirport", "DestAirport", "has_direct_flight"])
        .unique()
    )

    # Base: todas las rutas únicas O-D
    od_pairs = routes.select(["SourceAirport", "DestAirport"]).unique()

    return (
        od_pairs
        .join(competition, on=["SourceAirport", "DestAirport"], how="left")
        .join(direct_flights, on=["SourceAirport", "DestAirport"], how="left")
        .with_columns([
            pl.col("has_direct_flight").fill_null(False),
            # Features de centralidad del aeropuerto origen
            pl.col("SourceAirport").map_elements(
                lambda x: degree_cent.get(x, 0), return_dtype=pl.Float64
            ).alias("degree_centrality_src"),
            pl.col("SourceAirport").map_elements(
                lambda x: pagerank.get(x, 0), return_dtype=pl.Float64
            ).alias("pagerank_src"),
            pl.col("SourceAirport").map_elements(
                lambda x: betweenness.get(x, 0), return_dtype=pl.Float64
            ).alias("betweenness_src"),
            # Features de centralidad del aeropuerto destino
            pl.col("DestAirport").map_elements(
                lambda x: degree_cent.get(x, 0), return_dtype=pl.Float64
            ).alias("degree_centrality_dst"),
            pl.col("DestAirport").map_elements(
                lambda x: pagerank.get(x, 0), return_dtype=pl.Float64
            ).alias("pagerank_dst"),
        ])
    )


def find_underserved_routes(
    routes: pl.DataFrame,
    airports: pl.DataFrame,
    min_distance_km: float = 500,
    max_airlines: int = 1,
) -> pl.DataFrame:
    """
    Detecta rutas sub-explotadas: pares O-D con pocos competidores
    pero potencial por distancia (mercados sin competencia real).

    Útil para identificar oportunidades de expansión de red.
    """
    airports_with_coords = airports.filter(
        pl.col("IATA").is_not_null() & pl.col("Lat").is_not_null()
    )

    competition = (
        routes
        .group_by(["SourceAirport", "DestAirport"])
        .agg(pl.n_unique("Airline").alias("n_airlines"))
        .filter(pl.col("n_airlines") <= max_airlines)
    )

    # TODO: Agregar filtro de distancia geodésica y población para completar el análisis
    return competition.sort("n_airlines")


def impact_analysis_route_removal(
    G: nx.DiGraph,
    route_to_remove: tuple[str, str],
) -> dict:
    """
    Simula la eliminación de una ruta y analiza el impacto en conectividad.
    ¿Cuántos pares O-D pierden su camino más corto?

    Args:
        G: Grafo dirigido de rutas
        route_to_remove: (SourceAirport, DestAirport) de la ruta a eliminar

    Returns:
        Dict con pares O-D afectados y alternativas disponibles
    """
    G_modified = G.copy()
    src, dst = route_to_remove

    if G_modified.has_edge(src, dst):
        G_modified.remove_edge(src, dst)

    affected_pairs = []
    for node_s in G.nodes():
        for node_d in G.nodes():
            if node_s == node_d:
                continue
            had_path = nx.has_path(G, node_s, node_d)
            still_has_path = nx.has_path(G_modified, node_s, node_d)
            if had_path and not still_has_path:
                affected_pairs.append({"origin": node_s, "dest": node_d})

    return {
        "route_removed": f"{src}-{dst}",
        "pairs_disconnected": len(affected_pairs),
        "affected_pairs": affected_pairs,
    }
```

---

## Geoespacial: mapa de red

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import networkx as nx
import polars as pl

# NOTA: Para rutas Great Circle usar cartopy, NO matplotlib directo
# pip install cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature


def plot_route_network(
    G: nx.DiGraph,
    airports: pl.DataFrame,
    G_highlight: nx.DiGraph | None = None,  # Red a resaltar (ej: solo LAN)
    title: str = "Red de Rutas Aéreas",
    output_path: str = "/tmp/route_network.png",
):
    """
    Visualiza la red de rutas sobre un mapa mundial.

    - Nodos (aeropuertos): color por degree_centrality, tamaño por PageRank
    - Aristas (rutas): gris semitransparente para red global
    - Aristas highlight: rojo para la red específica (ej: LAN/LATAM)
    - Proyección: Robinson (buena para mapas mundiales)
    """
    pagerank     = nx.pagerank(G)
    degree_cent  = nx.degree_centrality(G)

    # Coordenadas de aeropuertos
    coords = (
        airports
        .filter(pl.col("IATA").is_not_null())
        .select(["IATA", "Lat", "Lon"])
        .to_pandas()
        .set_index("IATA")
    )

    fig = plt.figure(figsize=(20, 12))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson())

    # Fondo del mapa
    ax.add_feature(cfeature.LAND, facecolor="#1a1a2e", edgecolor="none")
    ax.add_feature(cfeature.OCEAN, facecolor="#0d0d1a")
    ax.add_feature(cfeature.COASTLINE, linewidth=0.3, edgecolor="#444466")
    ax.add_feature(cfeature.BORDERS, linewidth=0.2, edgecolor="#333355")
    ax.set_global()

    # Dibujar rutas de fondo (toda la red) — gris semitransparente
    for src, dst in G.edges():
        if src in coords.index and dst in coords.index:
            lat1, lon1 = coords.loc[src, ["Lat", "Lon"]]
            lat2, lon2 = coords.loc[dst, ["Lat", "Lon"]]
            ax.plot(
                [lon1, lon2], [lat1, lat2],
                color="white", alpha=0.04, linewidth=0.3,
                transform=ccrs.Geodetic(),  # Great Circle automático
            )

    # Dibujar rutas highlight (ej: LAN/LATAM) — rojo
    if G_highlight is not None:
        for src, dst in G_highlight.edges():
            if src in coords.index and dst in coords.index:
                lat1, lon1 = coords.loc[src, ["Lat", "Lon"]]
                lat2, lon2 = coords.loc[dst, ["Lat", "Lon"]]
                ax.plot(
                    [lon1, lon2], [lat1, lat2],
                    color="#ff4444", alpha=0.7, linewidth=0.8,
                    transform=ccrs.Geodetic(),
                )

    # Dibujar nodos (aeropuertos)
    for iata in G.nodes():
        if iata not in coords.index:
            continue
        lat, lon = coords.loc[iata, ["Lat", "Lon"]]
        pr   = pagerank.get(iata, 0)
        dc   = degree_cent.get(iata, 0)
        size = max(5, pr * 5000)   # Tamaño proporcional a PageRank
        color_intensity = min(1.0, dc * 10)
        color = (color_intensity, 0.5, 1 - color_intensity)

        ax.plot(
            lon, lat,
            "o", markersize=size, color=color,
            transform=ccrs.PlateCarree(), alpha=0.8,
        )

        # Label para aeropuertos muy importantes
        if pr > 0.005:
            ax.text(
                lon + 1, lat + 1, iata,
                fontsize=5, color="white", alpha=0.9,
                transform=ccrs.PlateCarree(),
            )

    # Leyenda
    legend_elements = [
        mpatches.Patch(color="#ff4444", label="Rutas LAN/LATAM"),
        mpatches.Patch(color="white", alpha=0.4, label="Red global"),
    ]
    ax.legend(handles=legend_elements, loc="lower left", fontsize=9,
              facecolor="#1a1a2e", labelcolor="white")

    plt.title(title, fontsize=16, color="white", pad=20)
    fig.patch.set_facecolor("#0d0d1a")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Mapa guardado en: {output_path}")
    plt.show()


# Ejemplo de uso
# G_global = build_route_graph(routes)
# G_latam  = build_route_graph(routes, airline_filter=LATAM_GROUP_CODES)
# plot_route_network(G_global, airports, G_highlight=G_latam, title="Red LATAM vs Global")
```

---

## Pitfalls

- **`\N` como nulos en todos los archivos**: OpenFlights usa `\N` (backslash-N literal) para valores nulos, no el estándar de CSV vacío. Al cargar con Polars, usar `null_values=["\\N", ""]` en `read_csv`. Si se olvida este paso, todas las columnas de IATA sin código aparecerán como strings `"\N"`.

- **AirlineID = -1**: Rutas con `AirlineID = -1` tienen aerolínea desconocida. Siempre filtrar antes de análisis para evitar ruidos en el grafo.

- **Datos estáticos, no real-time**: OpenFlights se actualiza de forma irregular. Muchas aerolíneas que cesaron operaciones (ej: LAN Ecuador) todavía aparecen. El dataset refleja la red aérea aproximada de ~2014-2017 para la mayoría de rutas.

- **Aeropuertos sin código IATA**: Aeropuertos pequeños o militares pueden tener `IATA = \N`. Al hacer joins entre `routes.dat` y `airports.dat`, usar `ICAO` como fallback si `IATA` es nulo.

- **NetworkX lento en grafos grandes**: Para la red global (67.663 rutas), `betweenness_centrality` puede tardar horas. Opciones:
  1. Usar muestreo: `betweenness_centrality(G, k=500)` (aproximación por muestreo)
  2. Usar `graph-tool` (C++, 100x más rápido) o `igraph` para grafos >100K nodos
  3. Filtrar por aerolínea antes de calcular métricas pesadas

- **Rutas Great Circle en mapas**: No usar `matplotlib` directamente para líneas entre coordenadas — quedan rectas en proyección y no representan la ruta real. Usar `cartopy` con `transform=ccrs.Geodetic()` que calcula automáticamente la curva geodésica (Great Circle) correcta.

- **Codeshares duplicados**: Si una ruta tiene `Codeshare = Y`, puede aparecer duplicada bajo distintos códigos de aerolínea. Al contar rutas únicas de una aerolínea, considerar si incluir o excluir codeshares según el análisis.

---

## Instalación

```bash
pip install polars networkx python-louvain geopandas cartopy matplotlib requests
```
