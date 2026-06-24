# DeepForest + SAM — Pitfalls con Ortomosaicos de Alta Resolución (Tucumán)

Aprendizajes de la sesión de junio 2026 con ortomosaicos reales Pix4D de Tucumán.

## Características de los TIFFs

| Archivo | Dimensiones | Píxeles | Bandas | Resolución | Software |
|---|---|---|---|---|---|
| 9deJulio.rgb.tif | 17094×11327 | 193M | 4 (RGBA) uint8 | ~6 cm/px | Pix4Dfields 2.12.1 |
| Avellaneda.rgb.tif | 12622×7887 | 99M | 4 (RGBA) uint8 | ~6 cm/px | Pix4Dfields 2.12.1 |

- CRS: EPSG:32720 (UTM zona 20S) — correcto para Tucumán
- Fecha vuelo: 16/05/2026
- Son RGB + alpha, NO multiespectrales → NDVI no calculable

## Pitfall 1 — score_thresh demasiado alto

**Síntoma:** Avellaneda detectaba 3 árboles cuando visualmente hay 70+.

**Causa:** DeepForest usa score_thresh=0.4 por default. Entrenado en dataset NEON
(bosques templados EEUU, copas grandes, vistas desde 100m+). Ortomosaicos Pix4D
de Tucumán a 6 cm/px tienen copas muy texturadas → scores de 0.10-0.25.

**Fix:**
```python
model.config["score_thresh"] = 0.15  # para ortomosaicos latinoamericanos alta resolución
```

Resultado verificado con threshold=0.15:
- 9deJulio: 154 árboles (17094×11327px, 59MB)
- Avellaneda: 71 árboles en 8 tiles (12622×7887px, 36MB)

## Pitfall 2 — tiling incorrecto para imágenes de ~100M píxeles

**Síntoma:** Avellaneda (99M px) no entraba en el path de tiling, DeepForest la procesaba
completa y detectaba casi nada.

**Causa:** El threshold de tiling estaba seteado al límite PIL (178M px). Avellaneda con
99M px < 178M px → procesada sin tiling → el modelo no separa las copas bien.

**Fix:** Usar un TILING_THRESHOLD separado del límite PIL:
```python
PIL_MAX_PIXELS = 178_956_970    # límite PIL decompression bomb
TILING_THRESHOLD = 20_000_000   # >20M px → siempre tile (ortomosaicos de drone)
TILE_SIZE = 4096

needs_tiling = (w * h) > TILING_THRESHOLD  # NO usar PIL_MAX_PIXELS aquí
```

Verificación tile por tile de Avellaneda (12622×7887) con threshold correcto:
```
tile 1 (0,0)+4096x4096     → 7 árboles
tile 2 (4096,0)+4096x4096  → 10 árboles
tile 3 (8192,0)+4096x4096  → 13 árboles
tile 4 (12288,0)+334x4096  → 3 árboles
tile 5 (0,4096)+4096x3791  → 7 árboles
tile 6 (4096,4096)+4096x3791 → 15 árboles
tile 7 (8192,4096)+4096x3791 → 16 árboles
tile 8 (12288,4096)+334x3791 → 0 árboles
TOTAL: 71 árboles
```

## Pitfall 3 — Carga de TIFFs grandes desde browser vía Cloudflare

**Síntoma:** `ERR_SSL_BAD_RECORD_MAC_ALERT` al subir TIFF de 59MB por el túnel Cloudflare.

**Causa:** Cloudflare free tunnels cortan requests con body grande (límite ~50MB en la práctica).

**Fix:** Usar spa_proxy.py en :3011 accesible por Tailscale sin SSL ni límite de tamaño:
```
http://100.110.8.13:3011/
```
spa_proxy.py sirve el frontend estático y rutea /api/* → backend :8010.

## Pipeline VLM para especies (KPI 2)

Orden de prioridad en `vlm_classifier.py`:
1. **OpenAI gpt-4o-mini** — primario. Costo centavos por ortomosaico. `"detail": "low"`.
2. **Azure Anthropic Claude Sonnet 4.6** — fallback.
3. **OpenCode** — fallback de último recurso.

Variables de entorno necesarias:
```
OPENAI_API_KEY=sk-proj-...
AZURE_ANTHROPIC_BASE_URL=https://yizlafclc001.services.ai.azure.com/anthropic
AZURE_ANTHROPIC_API_KEY=...
AZURE_ANTHROPIC_MODEL=claude-sonnet-4-6
```

## Pitfall 4 — Reescritura de .env destruye passwords enmascaradas

**Síntoma:** Backend crashea con `password authentication failed for user "forestai"`.

**Causa:** El terminal enmascara secrets con `***`. Un script que lea el `.env` como string
y lo reescriba puede reemplazar los valores reales por literal `***`.

**Fix:** Escribir el script Python a un archivo y ejecutarlo — nunca inline:
```python
# /tmp/fix_env.py
import re
path = '/home/server/proyectos/forestai-poc/.env'
with open(path) as f:
    content = f.read()
# Solo tocar la línea específica que querés cambiar
content = re.sub(r'DATABASE_URL=postgresql://forestai:[^@]*@db',
                 'DATABASE_URL=postgresql://forestai:forestai2024@db', content)
with open(path, 'w') as f:
    f.write(content)
```

Verificar longitud de keys después de escribir:
```python
for line in content.splitlines():
    if 'API_KEY' in line or 'DATABASE' in line:
        k, _, v = line.partition('=')
        print(f"{k}= len={len(v)} prefix={v[:8]}")
```

Si la password de postgres se pierde, resetear desde dentro del container:
```bash
docker exec forestai-poc-db-1 psql -U forestai -d forestai \
  -c "ALTER USER forestai WITH PASSWORD 'forestai2024';"
```

## Pitfall 5 — `docker compose rm -f backend` + recrear rompe conexión postgres

Preferir `docker compose restart backend` para cambios de código/env.
Solo usar `stop + rm + up` cuando sea estrictamente necesario.
Al recrear, el nuevo container puede recibir un .env stale si el archivo no se leyó bien.
Siempre verificar con `docker exec <container> env | grep KEY` después de recrear.
