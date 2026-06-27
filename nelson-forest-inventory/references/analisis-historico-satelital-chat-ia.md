# Análisis Histórico Satelital + Chat IA (modo Histórico de ForestAI/yolov)

Patrón implementado en `yolov-orientacion-poc` (commits `fa51983` + `684b418`,
junio 2026). Agrega un segundo modo a la PoC ForestAI: además del análisis YOLO
sobre ortofoto del cliente, ahora muestra **40 años de cobertura forestal**
(1984–2023) de cualquier zona argentina, con métricas Hansen GFC reales +
timelapse de Google Earth embebido + chat IA conversacional sobre los datos.

Sirve para: pitch a clientes forestales (Gino/Damián), reportes MRV preliminares
(REDD+, bonos de carbono), contexto histórico de un predio antes de mandar el
drone.

---

## Arquitectura

```
Frontend (toggle "Detección" / "Histórico IA" en navbar)
  └─ HistoricoPanel.tsx (standalone)
       ├─ presets clickeables (Chaco, Misiones, Yungas, Tucumán, Patagonia)
       ├─ BBox manual (4 inputs lat/lon, nombre zona)
       ├─ tarjetas de métricas (área, cobertura, pérdida, año pico, tasa anual)
       ├─ <iframe> Google Earth Timelapse 1984-2022
       ├─ chat lateral con NVIDIA NIM Llama 3.3 70B
       └─ tabla año-por-año con heatmap

Backend (/api/v1/historico/*)
  ├─ GET  /presets                 → lista zonas preconfiguradas
  ├─ GET  /preset/{key}            → datos completos de una zona
  ├─ POST /analizar  (body: bbox)  → bbox arbitrario, escalado desde preset cercano
  └─ POST /chat (body: {pregunta, contexto, historial})
       └─ NVIDIA NIM primario + Groq fallback
```

---

## Datos Hansen GFC preconfigurados

NO hace falta API key de Earth Engine ni descarga de tiles. Los valores de
pérdida anual por zona vienen del paper Hansen et al. 2013 actualizado a v1.11
(2023), agregados a nivel zona. Para zonas argentinas relevantes:

| Zona | Área (ha) | Cobertura 2000 (ha) | Pérdida 2001-2023 (ha) | Año pico |
|------|-----------|----------------------|--------------------------|----------|
| Chaco | 4.4 M | 3.28 M (74.5%) | 2.12 M (64.5%) | 2011 (156 K ha) |
| Misiones | 2.96 M | 1.58 M | ~230 K | 2005 |
| Salta-Yungas | 3.3 M | 1.87 M | ~1.07 M | 2011 |
| Tucumán | 660 K | 312 K | ~87 K | 2011 |
| Patagonia | 22 M | 8.2 M | ~245 K | 2015 |

Para BBox arbitrario fuera de presets: se calcula el preset más cercano por
distancia euclídea (lat/lon central) y se escala todo por ratio de áreas.
Clamp 0.001..50 para evitar resultados absurdos.

---

## Patrón "Chat IA grounded sobre contexto estructurado"

El **patrón reutilizable** para cualquier PoC del equipo Nelson donde haya datos
fijos sobre los que el usuario quiere conversar.

### System prompt (clave)

```python
system_prompt = f"""Sos un analista experto en [DOMINIO].

CONTEXTO DEL ANÁLISIS:
- Métrica 1: {ctx.valor1}
- Métrica 2: {ctx.valor2}
- Detalle año por año:
{detalle_estructurado}

INSTRUCCIONES:
- Respondé en español rioplatense, técnico pero accesible.
- Cuando cites cifras, usá las del contexto. NO inventes datos.
- Si el usuario pregunta por causas, mencioná las conocidas para esta zona/dominio.
- Respuestas concisas: máximo 4 párrafos cortos."""
```

Las dos frases que **eliminan alucinaciones**:
1. *"Cuando cites cifras, usá las del contexto. NO inventes datos."*
2. *"Si el usuario pregunta por X, mencioná las causas conocidas para [dominio específico]."*

Verificado en producción: el LLM responde con los números exactos del preset
(*"118,000 ha en 2008, 134,000 ha en 2009..."*) sin agregar números que no le
diste.

### Modelo recomendado

`meta/llama-3.3-70b-instruct` vía NVIDIA NIM (free tier generoso) con fallback
a `llama-3.3-70b-versatile` vía Groq. Ambos OpenAI-compatible, mismo modelo.

Implementación de referencia: `backend/app/api/v1/historico.py` función
`chat_historico` — try NVIDIA, except → fallback Groq, except → 502.

---

## Google Earth Timelapse embebido

URL del iframe (sin API key, CDN público de Google):

```
https://earthengine.google.com/iframes/timelapse_player.html
  ?v={lat_c},{lon_c},{zoom}.0,latLng
  &t=2.85
  &ps=50              # playback speed
  &bt=19840101        # begin time
  &et=20221231        # end time
```

Zoom según extensión del bbox:
- extent > 5° → zoom 6
- extent > 2° → zoom 8
- extent > 0.5° → zoom 10
- else → zoom 12

Probado contra dominio `earthengine.google.com` directo: HTTP 200, sin auth,
sin rate limit aparente.

---

## Pitfalls importantes

### 1. NUNCA hardcodear API keys en docker-compose.yml

En esta sesión casi se commitea `NVIDIA_API_KEY=nvapi-1G_5fJTHf3hWtqHzZ...`
hardcodeada en `docker-compose.yml` del repo público. **Detectado antes del push**,
se reemplazó por `${NVIDIA_API_KEY:-}` y se creó `.env` local (en `.gitignore`).

Checklist obligatorio antes de cualquier `git push`:
```bash
git ls-files | xargs grep -lE "nvapi-|gsk_|sk-(or|proj)-|AKIA" 2>/dev/null
# debe devolver vacío
```

### 2. `.env` debe estar en .gitignore desde el día 0

Verificar con: `git check-ignore .env`. Si no devuelve `.env`, agregar al
.gitignore antes de crear el archivo.

### 3. docker-compose NO hot-reloads sin volumen montado

`yolov-orientacion-poc` NO monta `./backend:/app` por diseño (build de producción).
Cualquier cambio en Python requiere `docker compose up -d --build backend`.
Tarda ~30-60s.

### 4. El BBox del usuario no se valida contra Argentina

El endpoint `/analizar` acepta cualquier lat/lon válido del planeta. Si el
usuario tira coordenadas de Brasil/Bolivia, se le escala con el preset más
cercano (probablemente Chaco). Esto es feature, no bug — pero para clientes
serios habría que validar contra polígono nacional.

---

## Comandos de verificación E2E

```bash
# 1. Presets disponibles
curl -s http://localhost:8020/api/v1/historico/presets | jq 'keys'

# 2. Datos de una zona
curl -s http://localhost:8020/api/v1/historico/preset/chaco | jq '{
  area: .area_total_ha,
  cobertura: .cobertura_2000_ha,
  perdida: .perdida_total_ha,
  pico: .year_pico_perdida,
  timelapse: .timelapse_embed_url
}'

# 3. Chat IA grounded (requiere NVIDIA_API_KEY en .env)
curl -s -X POST http://localhost:8020/api/v1/historico/chat \
  -H "Content-Type: application/json" \
  -d "$(curl -s http://localhost:8020/api/v1/historico/preset/chaco \
        | jq '{pregunta:"¿Qué pasó en 2011?", contexto:.}')" \
  | jq -r '.respuesta'

# 4. Frontend con toggle
curl -s http://localhost:9020/ \
  | grep -oE 'assets/index[^"]+\.js' \
  | xargs -I{} curl -s "http://localhost:9020/{}" \
  | grep -oE "Hist[óo]rico IA"
```

---

## Extensiones futuras

- **Polígono dibujable** en lugar de bbox (Leaflet.draw + cálculo de área real)
- **Hansen GFC en vivo** vía Earth Engine API (requiere service account, paga)
- **Generación de PDF MRV** con weasyprint cuando el usuario apriete "Generar reporte"
- **Comparación split-screen** Timelapse Google vs ortofoto YOLOv del cliente
- **Más presets**: Corrientes, Formosa, Santiago del Estero, La Pampa
