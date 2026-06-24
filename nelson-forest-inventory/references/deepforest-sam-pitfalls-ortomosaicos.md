# DeepForest + SAM — Pitfalls en Ortomosaicos de Drone (Tucumán, jun 2026)

## Caso real: 9deJulio.rgb.tif (59MB) y Avellaneda.rgb.tif (36MB)
- Software: Pix4Dfields 2.12.1
- Resolución: ~6 cm/px
- CRS: EPSG:32720 (UTM zona 20S)
- Bandas: 4 (RGBA uint8) — NO multiespectrales. NDVI no aplica.
- Dimensiones: 17094×11327 px (9deJulio), 12622×7887 px (Avellaneda)

---

## Pitfall 1: score_thresh=0.4 detecta casi nada

DeepForest default `score_thresh=0.4` falla en ortomosaicos Pix4D 6cm/px.
El modelo está entrenado en NEON dataset (bosques EEUU, ~1m/px desde avión).
Los scores son ~0.12–0.19 → con threshold=0.4 filtra todo.

**Fix obligatorio para ortofotos drone:**
```python
model.config["score_thresh"] = 0.15
```

Resultado real con Avellaneda:
- threshold=0.4 → 3 árboles
- threshold=0.15 → 71 árboles (correcto)

---

## Pitfall 2: TIFFs medianos (20–178M px) no entran al tiling

Si `TILING_THRESHOLD = PIL_MAX_PIXELS = 178M px`, ortomosaicos de 99M px
(como Avellaneda 12622×7887) no se tilean → DeepForest procesa entero → falla.

**Fix:**
```python
PIL_MAX_PIXELS    = 178_956_970  # solo para decompression bomb check
TILING_THRESHOLD  = 20_000_000   # >20M px → tiling siempre
TILE_SIZE         = 4096         # px por tile
```

Regla práctica: cualquier ortomosaico de drone (>20M px) debe ir por tiling.

Pipeline de tiling probado:
```python
# Para cada tile (x0, y0, tw, th):
#   1. Leer con rasterio.Window → numpy RGB
#   2. Guardar como PNG temporal
#   3. model.predict_image(path=tile_path)
#   4. Sumar offset (x0, y0) a las coords de las detecciones
#   5. Concatenar todos los DataFrames con pd.concat
```

Resultado 9deJulio (17094×11327 = 12 tiles de 4096px): 154 árboles detectados.

---

## Pitfall 3: SSL error al subir TIFFs grandes por túnel Cloudflare Free

`ERR_SSL_BAD_RECORD_MAC_ALERT` al hacer POST multipart de 30–60MB via trycloudflare.com.
El túnel free no soporta bodies grandes confiablemente.

**Solución: spa_proxy.py + acceso por Tailscale**
```python
# spa_proxy.py en la raíz del proyecto
# Sirve frontend dist/ estático
# Rutea /api/* → backend :8010
# Sin límite de tamaño, sin SSL local
# Puerto: 3011
```
Acceso: `http://<tailscale-ip>:3011/`
IP Tailscale de ai-server: 100.110.8.13 (verificar con `tailscale ip`)

---

## Pitfall 4: VLM no se activa (vlm_used=False siempre)

El vlm_classifier.py original leía `OPENCODE_API_KEY` hardcodeado.
Si el container no tiene esa var (o la key está inválida), VLM se saltea silenciosamente.

**Fix: agregar Azure Anthropic como prioridad:**
```python
AZURE_ANTHROPIC_BASE_URL = os.getenv("AZURE_ANTHROPIC_BASE_URL", "")
AZURE_ANTHROPIC_API_KEY  = os.getenv("AZURE_ANTHROPIC_API_KEY", "")
AZURE_ANTHROPIC_MODEL    = os.getenv("AZURE_ANTHROPIC_MODEL", "claude-sonnet-4-6")
```

En `_classify_one`:
- Si `AZURE_ANTHROPIC_BASE_URL` y `AZURE_ANTHROPIC_API_KEY` presentes → Anthropic Messages API nativo
- Si no → fallback OpenCode / OpenAI-compatible

**Formato Anthropic Messages API nativo (NO OpenAI-compatible):**
```python
# Headers:
{"x-api-key": KEY, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}

# Payload:
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 120,
  "system": SYSTEM_PROMPT,
  "messages": [{
    "role": "user",
    "content": [
      {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
      {"type": "text", "text": "Classify this tree canopy. Respond with JSON only."}
    ]
  }]
}

# Response: data["content"][0]["text"]  (NO data["choices"][0]["message"]["content"])
```

**Azure URL para ForestAI:**
- Base: `https://yizlafclc001.services.ai.azure.com/anthropic`
- Endpoint messages: `{BASE_URL}/v1/messages`
- Key en `.env`: `AZURE_ANTHROPIC_API_KEY`

---

## Modelos VLM disponibles (OpenAI key) para clasificación de especies

| Modelo | Precio/1M tok | Calidad visión | Recomendación |
|---|---|---|---|
| gpt-4o-mini | ~$0.15 | Buena | ⭐ Mejor costo/beneficio |
| gpt-4.1-nano | ~$0.10 | Básica | Más barato |
| gpt-4.1-mini | ~$0.40 | Mejor | Punto medio |
| claude-sonnet-4-6 (Azure) | ~$3 | Excelente | Ya configurado |

Para 71 copas/ortomosaico (top 10 por tamaño): gpt-4o-mini cuesta <$0.01 por análisis.

---

## Advertencia NetFlora para Tucumán

NetFlora (Embrapa/JBS) está entrenado en **72 especies amazónicas**:
Açaí, Paxiúba, Burití, Castanheira, Copaíba, Cedro amazónico...

En Tucumán las especies nativas son: Quebracho, Tipa, Cebil, Lapacho, Algarrobo, Palo Blanco.
**Ninguna está en el catálogo de NetFlora.**

Para KPI "detección de especie" en Tucumán:
- NetFlora → solo para demo conceptual ("así funcionaría con especies locales")
- VLM por copa (Claude / GPT-4o) → approach real, funciona bien con descripción textual
- Fine-tune DeepForest local → correcta pero requiere dataset etiquetado propio (meses)
