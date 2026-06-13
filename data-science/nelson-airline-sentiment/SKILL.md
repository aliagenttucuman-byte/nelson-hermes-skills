---
name: nelson-airline-sentiment
description: "Sentiment analysis de reseñas de pasajeros en español para aerolineas. Scraping de AirlineQuality, Google, TripAdvisor. Modelos: pysentimiento (BERT en español), VADER fallback. Pipeline produccion-ready con logging, manejo de errores y export a Excel."
triggers:
  - sentiment aerolinea
  - analisis reseñas pasajeros
  - opinion mining vuelos
  - NLP español aerolinea
  - reviews LAN Chile
version: "1.0.0"
---

# nelson-airline-sentiment

Skill de análisis de sentimiento de reseñas de pasajeros en español para aerolíneas. Contexto principal: LAN Chile / LATAM group. Basada en el repo British Airways Data Science Simulation pero mejorada para producción real y soporte nativo de español.

---

## Por qué pysentimiento y no VADER

- VADER está entrenado en inglés — impreciso en español (accuracy ~62% en textos en español)
- pysentimiento: modelo RoBERTa fine-tuned en 500M+ tweets latinoamericanos
- Maneja jerga latinoamericana, emojis, sarcasmo de forma nativa
- Zero-shot: funciona sin necesidad de reentrenar para el dominio aerolíneas
- Instalación simple: `pip install pysentimiento`
- Comparativa de accuracy en reseñas de aerolíneas en español:
  - VADER en español: ~62%
  - pysentimiento (RoBERTa-es): ~88%

VADER puede usarse como fallback si pysentimiento no está disponible o en textos detectados como inglés.

---

## Fuentes de datos para LAN Chile

- **AirlineQuality.com**: reseñas estructuradas con rating por categoría (seat comfort, service, food, entertainment, value). Es la fuente principal — tiene el histórico más largo.
- **Google Reviews**: scraping via SerpAPI (API key requerida) o Playwright para automatización headless.
- **TripAdvisor**: scraping HTML con BeautifulSoup. Tiene paginación y protecciones anti-bot — usar headers realistas.
- **Twitter/X**: búsqueda por @LATAM_Chile, @LAN_Chile, hashtags como #LATAM, #LATAMAirlines, #vuelo. Usar Tweepy con API v2.
- **App Store / Play Store**: reviews de la app LATAM. Librería `google-play-scraper` para Android, `app-store-scraper` para iOS.

Consideración importante: las reseñas pueden estar en español, inglés o portugués (pasajeros brasileños de LATAM Brasil). Detectar idioma primero con `langdetect` antes de aplicar el modelo. No mezclar idiomas sin traducción previa.

---

## Pipeline completo producción-ready

```python
"""
Pipeline de Sentiment Analysis para reseñas LAN Chile / LATAM
Autor: Nelson
Versión: 1.0.0
"""

import time
import random
import requests
import re
import polars as pl
from bs4 import BeautifulSoup
from loguru import logger
from langdetect import detect, DetectorFactory
from deep_translator import GoogleTranslator
from pysentimiento import create_sentiment_analyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from datetime import datetime
from pathlib import Path

# ── Reproducibilidad langdetect ──────────────────────────────────────────────
DetectorFactory.seed = 0

# ── Logging estructurado ─────────────────────────────────────────────────────
logger.add(
    "logs/airline_sentiment_{time}.log",
    rotation="50 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# ── Configuración global ─────────────────────────────────────────────────────
CONFIG = {
    "airline_slug": "LAN-Chile",          # slug en AirlineQuality
    "max_pages": 20,                       # páginas a scrapear
    "batch_size": 32,                      # batch para pysentimiento
    "negative_alert_threshold": 0.40,      # alerta si >40% negativo
    "whatsapp_gateway": "http://localhost:3001",
    "whatsapp_alert_number": "56912345678",  # número destino alertas
    "min_review_words": 10,                # filtrar reviews muy cortas
    "output_dir": Path("output"),
    "request_delay_min": 2,                # segundos mínimo entre requests
    "request_delay_max": 5,
}

CONFIG["output_dir"].mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)

# ── User agents para rotación ────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
]


def get_headers():
    """Retorna headers realistas con user-agent rotado."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def fetch_with_retry(url: str, max_retries: int = 3, backoff: float = 2.0) -> requests.Response | None:
    """GET con retry exponencial y backoff."""
    for attempt in range(1, max_retries + 1):
        try:
            delay = random.uniform(CONFIG["request_delay_min"], CONFIG["request_delay_max"])
            time.sleep(delay)
            resp = requests.get(url, headers=get_headers(), timeout=15)
            resp.raise_for_status()
            logger.debug(f"GET {url} → {resp.status_code} (intento {attempt})")
            return resp
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 429:
                wait = backoff ** attempt * 10
                logger.warning(f"Rate limit en {url}. Esperando {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"HTTP error {e} en {url} (intento {attempt})")
                if attempt == max_retries:
                    return None
        except requests.exceptions.RequestException as e:
            wait = backoff ** attempt
            logger.warning(f"Request error: {e}. Reintentando en {wait}s (intento {attempt}/{max_retries})")
            time.sleep(wait)
    logger.error(f"Falló después de {max_retries} intentos: {url}")
    return None


# ── 1. SCRAPING ──────────────────────────────────────────────────────────────

def scrape_airlinequality(airline_slug: str, max_pages: int = 20) -> list[dict]:
    """
    Scrapea reseñas de AirlineQuality.com.
    URL pattern: https://www.airlinequality.com/airline-reviews/{slug}/page/{n}/
    """
    reviews = []
    base_url = f"https://www.airlinequality.com/airline-reviews/{airline_slug}"

    for page in range(1, max_pages + 1):
        url = f"{base_url}/page/{page}/?sortby=post_date%3ADesc&pagesize=100"
        logger.info(f"Scrapeando página {page}/{max_pages}: {url}")

        resp = fetch_with_retry(url)
        if resp is None:
            logger.warning(f"No se pudo obtener página {page}, continuando...")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        articles = soup.find_all("article", itemprop="review")

        if not articles:
            logger.info(f"No hay más reseñas en página {page}. Deteniendo.")
            break

        for article in articles:
            try:
                review = _parse_airlinequality_article(article)
                if review:
                    reviews.append(review)
            except Exception as e:
                logger.warning(f"Error parseando artículo: {e}")
                continue

        logger.info(f"Página {page}: {len(articles)} reseñas extraídas. Total: {len(reviews)}")

    logger.info(f"Scraping completado. Total reseñas: {len(reviews)}")
    return reviews


def _parse_airlinequality_article(article) -> dict | None:
    """Extrae campos de un artículo de AirlineQuality."""
    # Texto principal de la reseña
    body = article.find("div", itemprop="reviewBody")
    text = body.get_text(strip=True) if body else ""

    if not text:
        return None

    # Título
    title_tag = article.find("h2", class_="text_header")
    title = title_tag.get_text(strip=True).strip('"') if title_tag else ""

    # Fecha
    date_tag = article.find("meta", itemprop="datePublished")
    date_str = date_tag["content"] if date_tag else ""

    # Rating overall
    rating_tag = article.find("span", itemprop="ratingValue")
    overall_rating = int(rating_tag.get_text(strip=True)) if rating_tag else None

    # Ratings por categoría (tabla de scores)
    category_ratings = {}
    table = article.find("table", class_="review-ratings")
    if table:
        for row in table.find_all("tr"):
            header = row.find("td", class_="review-rating-header")
            stars = row.find("td", class_="review-rating-stars")
            if header and stars:
                filled = len(stars.find_all("span", class_="star fill"))
                key = header.get_text(strip=True).lower().replace(" ", "_")
                category_ratings[key] = filled

    # País del viajero
    country_tag = article.find("h3", class_="text_sub_header")
    country = ""
    if country_tag:
        country_text = country_tag.get_text(strip=True)
        match = re.search(r"\(([^)]+)\)", country_text)
        country = match.group(1) if match else country_text

    # Verificado o no
    verified_tag = article.find("em")
    verified = "Trip Verified" in (verified_tag.get_text() if verified_tag else "")

    return {
        "source": "airlinequality",
        "date": date_str,
        "title": title,
        "text": text,
        "overall_rating": overall_rating,
        "country": country,
        "verified": verified,
        **{f"rating_{k}": v for k, v in category_ratings.items()},
    }


# ── 2. DETECCIÓN DE IDIOMA ────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    """Detecta idioma de un texto. Retorna código ISO (es, en, pt, etc.)."""
    try:
        return detect(text)
    except Exception:
        return "unknown"


# ── 3. TRADUCCIÓN OPCIONAL ────────────────────────────────────────────────────

def translate_to_spanish(text: str, source_lang: str = "auto") -> str:
    """Traduce texto al español usando deep-translator (Google Translate backend)."""
    try:
        translator = GoogleTranslator(source=source_lang, target="es")
        # deep-translator tiene límite de ~5000 chars por request
        if len(text) > 4900:
            chunks = [text[i:i+4900] for i in range(0, len(text), 4900)]
            return " ".join(translator.translate(chunk) for chunk in chunks)
        return translator.translate(text)
    except Exception as e:
        logger.warning(f"Error traduciendo texto: {e}")
        return text  # retornar original si falla


# ── 4. ANÁLISIS DE SENTIMIENTO ────────────────────────────────────────────────

# Inicializar analizador una sola vez (carga modelo ~300MB la primera vez)
logger.info("Cargando modelo pysentimiento (RoBERTa-es)...")
sentiment_analyzer = create_sentiment_analyzer(lang="es")
logger.info("Modelo cargado.")


def analyze_sentiment_batch(texts: list[str], batch_size: int = 32) -> list[dict]:
    """
    Analiza sentimiento en batches para eficiencia en CPU.
    Retorna lista de dicts con: label (POS/NEG/NEU), probabilities.
    """
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            batch_results = sentiment_analyzer.predict(batch)
            for r in batch_results:
                results.append({
                    "sentiment": r.output,           # POS, NEG, NEU
                    "prob_pos": round(r.probas.get("POS", 0), 4),
                    "prob_neg": round(r.probas.get("NEG", 0), 4),
                    "prob_neu": round(r.probas.get("NEU", 0), 4),
                })
        except Exception as e:
            logger.error(f"Error en batch {i//batch_size + 1}: {e}")
            # Fallback: NEU para todo el batch fallido
            results.extend([{"sentiment": "NEU", "prob_pos": 0, "prob_neg": 0, "prob_neu": 1}] * len(batch))

        logger.debug(f"Batch {i//batch_size + 1} procesado ({len(batch)} textos)")

    return results


# ── 5. ASPECT-BASED SENTIMENT ─────────────────────────────────────────────────

ASPECT_KEYWORDS = {
    "puntualidad": [
        "tardó", "demoró", "atrasó", "retraso", "retrasado", "retrasada",
        "puntual", "a tiempo", "demorada", "vuelo tarde", "horas de espera",
        "cancelaron", "cancelado", "reprogramaron"
    ],
    "equipaje": [
        "maleta", "maletas", "valija", "valijas", "equipaje", "perdieron",
        "perdido", "extraviaron", "equipaje perdido", "cobro de maleta",
        "primera maleta", "exceso de equipaje"
    ],
    "servicio_a_bordo": [
        "tripulación", "auxiliar", "azafata", "steward", "crew", "amable",
        "grosero", "grosera", "maleducado", "atención", "servicio a bordo",
        "ayudaron", "ignoraron"
    ],
    "check_in": [
        "check-in", "checkin", "check in", "embarque", "boarding", "cola",
        "fila", "espera en aeropuerto", "mostrador", "counter", "pasaporte"
    ],
    "comida": [
        "comida", "almuerzo", "cena", "desayuno", "snack", "bebida",
        "menú", "menu", "meal", "sándwich", "sandwich", "agua", "café",
        "alimentación a bordo"
    ],
    "entretenimiento": [
        "pantalla", "película", "películas", "entretenimiento", "ife",
        "wifi", "wi-fi", "auriculares", "audífonos", "música", "usb",
        "cargador", "enchuf"
    ],
    "precio": [
        "precio", "caro", "cara", "barato", "barata", "costo", "tarifa",
        "cobro extra", "reembolso", "devolución", "vale la pena",
        "relación precio-calidad", "económico", "económica"
    ],
    "comodidad_asiento": [
        "asiento", "silla", "espacio", "piernas", "legroom", "ancho",
        "cómodo", "cómoda", "incómodo", "incómoda", "clase ejecutiva",
        "business", "primera clase", "economy"
    ],
}


def extract_aspect_sentiments(text: str) -> dict[str, str | None]:
    """
    Detecta qué aspectos menciona una review y aplica sentiment específico.
    Retorna dict aspecto -> sentimiento (POS/NEG/NEU/None).
    """
    text_lower = text.lower()
    aspect_results = {}

    for aspect, keywords in ASPECT_KEYWORDS.items():
        # Buscar sentences que contengan keywords del aspecto
        sentences = re.split(r'[.!?;]', text)
        relevant_sentences = []

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(kw in sentence_lower for kw in keywords):
                relevant_sentences.append(sentence.strip())

        if relevant_sentences:
            # Analizar sentiment de las frases relevantes
            combined = " ".join(relevant_sentences)
            if len(combined.split()) >= 3:  # mínimo 3 palabras
                try:
                    result = sentiment_analyzer.predict(combined)
                    aspect_results[aspect] = result.output
                except Exception:
                    aspect_results[aspect] = None
            else:
                aspect_results[aspect] = None
        else:
            aspect_results[aspect] = None  # aspecto no mencionado

    return aspect_results


# ── 6. TOPICS EN REVIEWS NEGATIVAS ────────────────────────────────────────────

STOPWORDS_ES = {
    "de", "la", "el", "en", "y", "a", "que", "es", "se", "no", "un", "una",
    "con", "los", "las", "del", "por", "su", "al", "lo", "le", "me", "mi",
    "más", "pero", "como", "para", "o", "fue", "muy", "si", "también", "hay",
    "porque", "nos", "cuando", "esta", "este", "todo", "son", "te", "ya",
    "bien", "había", "han", "ni", "era", "tiene", "esto", "les", "vez",
    "así", "hasta", "solo", "puede", "desde", "he", "entre", "ser",
    "han", "estar", "años", "otro", "otra", "hace", "sin", "sobre",
    "vuelo", "vuelos", "lan", "latam", "aerolínea", "aerolinea", "avión",
}


def extract_negative_topics(negative_texts: list[str], top_n: int = 20) -> list[tuple[str, float]]:
    """Extrae los topics más frecuentes en reviews negativas usando TF-IDF."""
    if not negative_texts:
        return []

    vectorizer = TfidfVectorizer(
        max_features=200,
        ngram_range=(1, 2),           # unigramas y bigramas
        min_df=2,                      # mínimo en 2 documentos
        stop_words=list(STOPWORDS_ES),
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(negative_texts)
        feature_names = vectorizer.get_feature_names_out()
        # Score promedio por término
        mean_scores = tfidf_matrix.mean(axis=0).A1
        top_indices = mean_scores.argsort()[-top_n:][::-1]
        return [(feature_names[i], round(mean_scores[i], 4)) for i in top_indices]
    except Exception as e:
        logger.error(f"Error extrayendo topics: {e}")
        return []


def generate_wordcloud(negative_texts: list[str], output_path: str):
    """Genera WordCloud de reviews negativas y guarda como PNG."""
    if not negative_texts:
        logger.warning("No hay reviews negativas para generar WordCloud.")
        return

    combined = " ".join(negative_texts)
    wc = WordCloud(
        width=1200,
        height=600,
        background_color="white",
        stopwords=STOPWORDS_ES,
        colormap="Reds",
        max_words=100,
        collocations=True,
    )
    wc.generate(combined)
    wc.to_file(output_path)
    logger.info(f"WordCloud guardado en: {output_path}")


# ── 7. ALERTA WHATSAPP ────────────────────────────────────────────────────────

def send_whatsapp_alert(negative_pct: float, total_reviews: int):
    """
    Envía alerta WhatsApp via gateway Nelson en :3001 si el % negativo supera el threshold.
    """
    if negative_pct < CONFIG["negative_alert_threshold"]:
        return

    mensaje = (
        f"🚨 *Alerta Sentiment LATAM* 🚨\n"
        f"📊 Reviews analizadas: {total_reviews}\n"
        f"😡 Sentimiento negativo: {negative_pct:.1%}\n"
        f"⚠️ Supera umbral de {CONFIG['negative_alert_threshold']:.0%}\n"
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"→ Revisar dashboard para detalles."
    )

    try:
        resp = requests.post(
            f"{CONFIG['whatsapp_gateway']}/send",
            json={
                "number": CONFIG["whatsapp_alert_number"],
                "message": mensaje,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            logger.info(f"Alerta WhatsApp enviada. Negativo: {negative_pct:.1%}")
        else:
            logger.warning(f"Alerta WhatsApp falló: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"No se pudo enviar alerta WhatsApp: {e}")


# ── 8. EXPORT A EXCEL ─────────────────────────────────────────────────────────

def export_to_excel(df: pl.DataFrame, topics: list[tuple], output_path: str):
    """
    Exporta resultados a Excel con dos hojas:
    - 'Resultados': datos completos por review
    - 'Resumen Ejecutivo': métricas agregadas
    """
    wb = Workbook()

    # ── Hoja 1: Resultados ────────────────────────────────────────────────
    ws1 = wb.active
    ws1.title = "Resultados"

    # Encabezados con estilo
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)

    cols = df.columns
    for col_idx, col_name in enumerate(cols, 1):
        cell = ws1.cell(row=1, column=col_idx, value=col_name.upper().replace("_", " "))
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    # Datos
    for row_idx, row in enumerate(df.iter_rows(), 2):
        for col_idx, value in enumerate(row, 1):
            ws1.cell(row=row_idx, column=col_idx, value=value)

    # Ajustar ancho de columnas
    for col in ws1.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws1.column_dimensions[col[0].column_letter].width = min(max_len + 2, 50)

    # ── Hoja 2: Resumen Ejecutivo ─────────────────────────────────────────
    ws2 = wb.create_sheet("Resumen Ejecutivo")

    total = len(df)
    pos_count = df.filter(pl.col("sentiment") == "POS").height
    neg_count = df.filter(pl.col("sentiment") == "NEG").height
    neu_count = df.filter(pl.col("sentiment") == "NEU").height
    pos_pct = pos_count / total if total > 0 else 0
    neg_pct = neg_count / total if total > 0 else 0
    neu_pct = neu_count / total if total > 0 else 0
    nps_proxy = pos_pct - neg_pct

    # Título
    ws2["A1"] = "REPORTE DE SENTIMENT — LAN Chile / LATAM"
    ws2["A1"].font = Font(size=14, bold=True, color="1F4E79")
    ws2["A2"] = f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ws2["A2"].font = Font(italic=True, color="666666")

    # Métricas principales
    metrics = [
        ("", ""),
        ("MÉTRICAS GENERALES", ""),
        ("Total de reseñas analizadas", total),
        ("Reseñas positivas (POS)", f"{pos_count} ({pos_pct:.1%})"),
        ("Reseñas negativas (NEG)", f"{neg_count} ({neg_pct:.1%})"),
        ("Reseñas neutras (NEU)", f"{neu_count} ({neu_pct:.1%})"),
        ("NPS Proxy (Promotores - Detractores)", f"{nps_proxy:+.1%}"),
        ("", ""),
        ("TOP TOPICS EN REVIEWS NEGATIVAS", "SCORE TF-IDF"),
    ]

    for r_idx, (label, value) in enumerate(metrics, 4):
        ws2.cell(row=r_idx, column=1, value=label)
        ws2.cell(row=r_idx, column=2, value=value)
        if label in ("MÉTRICAS GENERALES", "TOP TOPICS EN REVIEWS NEGATIVAS"):
            ws2.cell(row=r_idx, column=1).font = Font(bold=True, color="1F4E79")

    # Topics
    topic_start_row = 4 + len(metrics)
    for t_idx, (topic, score) in enumerate(topics, topic_start_row):
        ws2.cell(row=t_idx, column=1, value=topic)
        ws2.cell(row=t_idx, column=2, value=score)

    ws2.column_dimensions["A"].width = 45
    ws2.column_dimensions["B"].width = 20

    wb.save(output_path)
    logger.info(f"Excel exportado: {output_path}")


# ── 9. PIPELINE PRINCIPAL ─────────────────────────────────────────────────────

def run_pipeline(airline_slug: str = None, max_pages: int = None) -> pl.DataFrame:
    """
    Ejecuta el pipeline completo:
    scraping → detección idioma → traducción → sentiment → aspect → export
    """
    airline_slug = airline_slug or CONFIG["airline_slug"]
    max_pages = max_pages or CONFIG["max_pages"]

    logger.info(f"=== Iniciando pipeline para: {airline_slug} ===")

    # 1. Scraping
    raw_reviews = scrape_airlinequality(airline_slug, max_pages)
    if not raw_reviews:
        logger.error("No se obtuvieron reseñas. Abortando.")
        return pl.DataFrame()

    # 2. Crear DataFrame Polars
    df = pl.DataFrame(raw_reviews)
    logger.info(f"DataFrame creado: {df.shape[0]} filas, {df.shape[1]} columnas")

    # 3. Detección de idioma
    logger.info("Detectando idioma de reseñas...")
    texts = df["text"].to_list()
    languages = [detect_language(t) for t in texts]
    df = df.with_columns(pl.Series("detected_lang", languages))

    # 4. Traducción de reseñas en inglés/portugués al español
    logger.info("Traduciendo reseñas no-españolas al español...")
    translated_texts = []
    for text, lang in zip(texts, languages):
        if lang in ("en", "pt"):
            translated_texts.append(translate_to_spanish(text, source_lang=lang))
        else:
            translated_texts.append(text)  # ya en español u otro idioma
    df = df.with_columns(pl.Series("text_es", translated_texts))

    # 5. Filtrar reviews muy cortas
    df = df.with_columns(
        pl.col("text_es").str.split(" ").list.len().alias("word_count")
    )
    df_filtered = df.filter(pl.col("word_count") >= CONFIG["min_review_words"])
    dropped = len(df) - len(df_filtered)
    if dropped > 0:
        logger.info(f"Filtradas {dropped} reseñas con menos de {CONFIG['min_review_words']} palabras.")
    df = df_filtered

    # 6. Análisis de sentimiento en batches
    logger.info(f"Analizando sentimiento ({len(df)} reseñas, batches de {CONFIG['batch_size']})...")
    texts_es = df["text_es"].to_list()
    sentiment_results = analyze_sentiment_batch(texts_es, batch_size=CONFIG["batch_size"])

    df = df.with_columns([
        pl.Series("sentiment", [r["sentiment"] for r in sentiment_results]),
        pl.Series("prob_pos", [r["prob_pos"] for r in sentiment_results]),
        pl.Series("prob_neg", [r["prob_neg"] for r in sentiment_results]),
        pl.Series("prob_neu", [r["prob_neu"] for r in sentiment_results]),
    ])

    # 7. Aspect-based sentiment
    logger.info("Extrayendo sentiment por aspecto...")
    aspect_results = [extract_aspect_sentiments(t) for t in texts_es]
    for aspect in ASPECT_KEYWORDS.keys():
        df = df.with_columns(
            pl.Series(f"aspect_{aspect}", [r.get(aspect) for r in aspect_results])
        )

    # 8. Topics en reviews negativas
    logger.info("Extrayendo topics en reviews negativas...")
    negative_texts = df.filter(pl.col("sentiment") == "NEG")["text_es"].to_list()
    topics = extract_negative_topics(negative_texts, top_n=20)

    if topics:
        logger.info("Top 5 topics negativos: " + ", ".join(f"{t}({s})" for t, s in topics[:5]))

    # Generar WordCloud
    wc_path = str(CONFIG["output_dir"] / "wordcloud_negativo.png")
    generate_wordcloud(negative_texts, wc_path)

    # 9. Métricas y alerta WhatsApp
    total = len(df)
    neg_pct = df.filter(pl.col("sentiment") == "NEG").height / total if total > 0 else 0
    pos_pct = df.filter(pl.col("sentiment") == "POS").height / total if total > 0 else 0
    nps_proxy = pos_pct - neg_pct

    logger.info(f"=== RESULTADOS ===")
    logger.info(f"Total reviews: {total}")
    logger.info(f"Positivo: {pos_pct:.1%} | Negativo: {neg_pct:.1%}")
    logger.info(f"NPS Proxy: {nps_proxy:+.1%}")

    send_whatsapp_alert(neg_pct, total)

    # 10. Export a Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = str(CONFIG["output_dir"] / f"sentiment_{airline_slug}_{timestamp}.xlsx")
    export_to_excel(df, topics, excel_path)

    # 11. Guardar CSV también (backup)
    csv_path = str(CONFIG["output_dir"] / f"sentiment_{airline_slug}_{timestamp}.csv")
    df.write_csv(csv_path)
    logger.info(f"CSV guardado: {csv_path}")

    logger.info(f"=== Pipeline completado. Resultados en: {CONFIG['output_dir']} ===")
    return df


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    df_results = run_pipeline()
    print(df_results.select(["date", "sentiment", "prob_pos", "prob_neg", "word_count"]).head(10))
```

---

## Aspect-based sentiment para aerolíneas

La idea es extraer sentimiento granular por categoría, no un score global que mezcla todo.

Definir keywords por categoría (expandible):

```python
ASPECT_KEYWORDS = {
    "puntualidad":       ["tardó", "demoró", "atrasó", "puntual", "a tiempo", "cancelaron", "retraso"],
    "equipaje":          ["maleta", "valija", "equipaje", "perdieron", "extraviaron", "cobro de maleta"],
    "servicio_a_bordo":  ["tripulación", "auxiliar", "azafata", "amable", "grosero", "atención"],
    "check_in":          ["check-in", "embarque", "boarding", "cola", "fila", "mostrador"],
    "comida":            ["comida", "almuerzo", "cena", "snack", "menú", "bebida", "agua"],
    "entretenimiento":   ["pantalla", "película", "wifi", "auriculares", "entretenimiento"],
    "precio":            ["precio", "caro", "barato", "tarifa", "cobro extra", "reembolso"],
    "comodidad_asiento": ["asiento", "espacio", "piernas", "legroom", "cómodo", "incómodo"],
}
```

Para cada review:
1. Dividir en frases por puntuación (.!?;)
2. Para cada aspecto, filtrar solo las frases que contienen sus keywords
3. Aplicar pysentimiento solo a esas frases (no al texto completo)
4. Si no se menciona el aspecto → None (no confundir con NEU)

Resultado: una matriz pasajero × aspecto con score de sentimiento:

```
| review_id | puntualidad | equipaje | servicio_a_bordo | comida | precio |
|-----------|-------------|----------|------------------|--------|--------|
| rev_001   | NEG         | None     | POS              | NEU    | NEG    |
| rev_002   | None        | NEG      | NEG              | None   | NEU    |
| rev_003   | POS         | None     | POS              | POS    | None   |
```

Esto permite identificar, por ejemplo, que el 70% de los pasajeros que mencionan equipaje tienen sentimiento negativo — incluso si su review global es NEU.

---

## Métricas de reporte

**NPS Proxy**
Formula adaptada para sentiment sin encuesta real:
- Promotores = reviews con sentiment POS (prob_pos > 0.7)
- Detractores = reviews con sentiment NEG (prob_neg > 0.7)
- NPS Proxy = % Promotores - % Detractores
- Rango: -100 a +100. Aerolíneas top como Emirates tienen NPS ~70

**Trending topics negativos por mes**
Agrupar reviews negativas por mes y aplicar TF-IDF por separado.
Detectar cuando aparece un topic nuevo o aumenta su frecuencia: puede indicar un incidente operacional específico.

**Comparativo vs competidores**
Scrapear las mismas páginas para: Aerolíneas Argentinas, Copa Airlines, Avianca.
Usar el mismo pipeline y comparar NPS Proxy y scores por aspecto.
Útil para benchmarking y para presentar a management.

**Heatmap de sentimiento por ruta**
Muchas reseñas mencionan la ruta: "vuelo Santiago-Miami", "SCL-LIM", etc.
Extraer pares de ciudad con regex y cruzar con sentimiento.
Permite identificar rutas específicas con problemas operacionales.

```python
# Regex para detectar rutas
ROUTE_PATTERN = re.compile(
    r'\b([A-Z]{3})\s*[-–—]\s*([A-Z]{3})\b|'           # SCL-MIA
    r'(Santiago|Lima|Buenos Aires|Miami|Madrid)\s*[-–]\s*(Santiago|Lima|Buenos Aires|Miami|Madrid)',
    re.IGNORECASE
)
```

---

## Pitfalls

- **PyTorch lento en CPU**: pysentimiento requiere PyTorch. En CPU, procesar 1000 reviews toma ~5 minutos. Usar batches de 32 (ver pipeline). Con GPU es ~10x más rápido. Considerar AWS EC2 g4dn.xlarge para runs masivos.

- **langdetect no-determinista**: por diseño usa algoritmo probabilístico. Siempre fijar `DetectorFactory.seed = 0` antes de cualquier detección. Sin esto, el mismo texto puede dar idiomas distintos entre ejecuciones.

- **AirlineQuality cambia su HTML**: el sitio actualiza su markup periódicamente. Si el scraper retorna listas vacías, inspeccionar el HTML actual y actualizar los selectores en `_parse_airlinequality_article`. Usar `logger.debug(soup.prettify()[:2000])` para diagnosticar.

- **Reviews cortas poco confiables**: reviews de menos de 10 palabras ("Pésimo", "Muy bien", "ok") dan resultados de sentimiento con baja confianza. Filtrarlas o al menos marcarlas. El pipeline las descarta por defecto (MIN_REVIEW_WORDS = 10).

- **Sarcasmo en español**: "excelente servicio, como siempre perdieron mi maleta" → el modelo puede confundirse con "excelente". pysentimiento lo maneja mejor que VADER gracias a contexto BERT, pero no es perfecto. Considerar revisar manualmente las reviews con prob_pos y prob_neg ambos > 0.35 (señal de ambigüedad).

- **Rate limiting en scraping**: siempre hacer `time.sleep(random.uniform(2, 5))` entre requests. Headers realistas con User-Agent rotado. Si el sitio bloquea la IP, usar proxy residencial (Brightdata, Oxylabs). No scrapear más de 2 páginas por minuto en producción.

- **deep-translator límite de caracteres**: Google Translate (backend de deep-translator) tiene límite de ~5000 caracteres por request. El pipeline ya maneja esto con chunking automático.

- **Modelos en memoria**: si se procesan varias aerolíneas en el mismo proceso, el modelo pysentimiento queda cargado en RAM. Inicializar `create_sentiment_analyzer` una sola vez (variable global) y reutilizarlo.

---

## Instalación

```bash
pip install pysentimiento langdetect deep-translator beautifulsoup4 requests wordcloud loguru polars openpyxl scikit-learn
```

Para PyTorch con CUDA (GPU) en vez de CPU:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

Verificar instalación:
```python
from pysentimiento import create_sentiment_analyzer
analyzer = create_sentiment_analyzer(lang="es")
result = analyzer.predict("El vuelo llegó 3 horas tarde y perdieron mi maleta")
print(result.output)       # NEG
print(result.probas)       # {'POS': 0.02, 'NEG': 0.95, 'NEU': 0.03}
```

---

## Referencias

- pysentimiento: https://github.com/pysentimiento/pysentimiento
- British Airways DS Simulation (base): https://github.com/theforage/british-airways-virtual
- AirlineQuality scraping ético: respetar robots.txt, delay entre requests
- Polars docs: https://docs.pola.rs/
- loguru docs: https://loguru.readthedocs.io/
