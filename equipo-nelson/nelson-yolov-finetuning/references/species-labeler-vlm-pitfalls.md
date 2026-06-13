# Species Labeler — VLM Pitfalls (sesión 2026-06-11)

## Problema: todo sale como "Otro"

### Causa 1 — detail:low en gpt-4o-mini
OpenAI comprime la imagen a resolución muy baja con detail:low.
Las copas de árboles son indistinguibles → el modelo responde "Otro" en el 100% de los casos.
**Fix:** usar `detail:high` — pero ver causa 2.

### Causa 2 — gpt-4o-mini no tiene conocimiento botánico del NOA
Incluso con detail:high y crops de 600x500px, gpt-4o-mini responde:
"La imagen no proporciona suficiente información para identificar la especie con certeza."
confianza: 0.5 en todos los casos.

El mismo crop con Claude Sonnet (vision_analyze):
- Cebil colorado: 45%
- Horco quebracho: 30%
- Quebracho blanco: 15%
Con razonamiento detallado sobre textura foliar, densidad de dosel, forma de copa.

**Fix:** usar Azure Anthropic Claude Sonnet (ya configurado en ForestAI):
```python
# En species_labeler.py — reemplazar OpenAI por Anthropic
import anthropic
client = anthropic.Anthropic(
    base_url=os.environ["AZURE_ANTHROPIC_BASE_URL"],
    api_key=os.environ["AZURE_ANTHROPIC_API_KEY"],
)
resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=150,
    messages=[{"role":"user","content":[
        {"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":b64}},
        {"type":"text","text":prompt}
    ]}]
)
```

### Causa 3 — TIFs subexpuestos dan crops oscuros/grises
Pix4Dfields genera TIFs con mean ~60/255. Sin stretch de contraste, los tiles (y los crops)
salen oscuros. El VLM ve una imagen gris en vez de verde.
**Fix:** stretch p2-p98 por canal en tiler.py antes de guardar el JPEG.
Verificar con: `img.mean()` — debe ser ~120, no ~60.

## Alternativa: prior geográfico + VLM confirma/descarta

Para zona urbana de Tucumán (Avellaneda, 9deJulio):
Las 3 especies más comunes son Tipa blanca, Lapacho rosado, Palo borracho.
El VLM solo necesita confirmar o asignar a una de esas 3 + "Otro".
Reduce el problema de 13 clases a 4 → mejor confianza con cualquier modelo.

```python
ESPECIES_ZONA_URBANA = ["Tipa blanca", "Lapacho rosado", "Palo borracho", "Otro"]
```

## Campo correcto en detecciones: `confidence` no `conf`

`run_inference()` en detector.py devuelve:
```python
{"tile_filename": ..., "x1": ..., "y1": ..., "x2": ..., "y2": ...,
 "global_x1": ..., "global_y1": ..., "global_x2": ..., "global_y2": ...,
 "confidence": float}   # ← confidence, NO conf
```
Al ordenar: `sorted(dets, key=lambda d: d.get("confidence", 0.0), reverse=True)`
