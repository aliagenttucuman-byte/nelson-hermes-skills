# ForestAI — Demo ReforestLatam (ruta /demo)

## Contexto

Nelson necesita una vista separada para mostrar ForestAI a stakeholders externos (ReforestLatam) sin revelar la tecnología interna. Razón: compliance y acuerdos comerciales pendientes.

## Reglas de la demo — lo que NO debe aparecer

- NO mencionar "DeepForest", "SAM", "RetinaNet", "VLM", "claude-haiku", "HuggingFace" en ningún texto visible
- NO mostrar pasos del pipeline durante el loading
- NO mostrar filtros de confianza ni sliders
- NO mostrar el header interno del TreeDetectionPanel ("DeepForest + SAM · Detección y segmentación de copas")
- NO mostrar columna izquierda (controles, filtros, textos explicativos)
- Loading state: solo spinner doble (🌲 girando) + texto "Procesando..."

## Implementación

- URL: `http://[host]:3010/demo`
- Archivo: `frontend/src/pages/DemoReforestLatam.tsx`
- Routing en `main.tsx`:
```typescript
const isDemo = window.location.pathname.startsWith('/demo');
// ...
{isDemo ? <DemoReforestLatam /> : <App />}
```
- nginx.conf necesita:
```nginx
location /demo {
    try_files $uri $uri/ /index.html;
}
```

## Estructura del DemoReforestLatam

La demo es un componente AUTÓNOMO — NO importa TreeDetectionPanel ni componentes del App.
Incluye su propio PolygonCanvas, lógica de upload, polling y resultados.

Por qué autónomo: TreeDetectionPanel tiene columna izquierda con filtros y header con nombre de modelos. Ocultarlos con CSS es frágil. Lo más limpio es una página independiente que reutiliza solo la lógica de API.

Elementos visibles:
1. Header: solo logo 🌲 + "ForestAI — Detección de Árboles"
2. Upload drag&drop centrado (siempre visible cuando no hay loading)
3. Loading: spinner doble + "Procesando..."
4. Resultados: 3 stats (árboles, confianza, copas) + PolygonCanvas + tabla de especies

## PolygonCanvas autónomo en la demo

El componente PolygonCanvas debe estar inlineado en DemoReforestLatam.tsx (no importado):

```tsx
function PolygonCanvas({ result }: { result: DetectionResult }) {
  const imgRef = useRef<HTMLImageElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [dims, setDims] = useState({ w: 0, h: 0, scaleX: 1, scaleY: 1 });
  const [imgLoaded, setImgLoaded] = useState(false);

  const updateDims = useCallback(() => {
    const img = imgRef.current;
    if (!img) return;
    const rect = img.getBoundingClientRect();
    setDims({ w: rect.width, h: rect.height,
      scaleX: rect.width / result.image_width,
      scaleY: rect.height / result.image_height });
  }, [result.image_width, result.image_height]);

  useEffect(() => {
    if (imgLoaded) updateDims();
    window.addEventListener("resize", updateDims);
    return () => window.removeEventListener("resize", updateDims);
  }, [imgLoaded, updateDims]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || dims.w === 0) return;
    canvas.width = dims.w; canvas.height = dims.h;
    const ctx = canvas.getContext("2d")!;
    ctx.clearRect(0, 0, dims.w, dims.h);
    result.trees.forEach((tree) => {
      const poly = tree.polygon;
      if (poly && poly.length >= 3) {
        const scaled = poly.map(([x, y]) => [x * dims.scaleX, y * dims.scaleY]);
        ctx.beginPath();
        ctx.moveTo(scaled[0][0], scaled[0][1]);
        scaled.slice(1).forEach(([x, y]) => ctx.lineTo(x, y));
        ctx.closePath();
        ctx.fillStyle = "rgba(16,185,129,0.2)";
        ctx.fill();
        ctx.strokeStyle = "rgba(5,150,105,0.9)";
        ctx.lineWidth = 1.5; ctx.stroke();
      } else {
        const x1 = tree.xmin * dims.scaleX, y1 = tree.ymin * dims.scaleY;
        const w = (tree.xmax - tree.xmin) * dims.scaleX, h = (tree.ymax - tree.ymin) * dims.scaleY;
        ctx.strokeStyle = "rgba(5,150,105,0.9)"; ctx.lineWidth = 1.5;
        ctx.strokeRect(x1, y1, w, h);
      }
    });
  }, [result.trees, dims]);

  return (
    <div style={{ position: "relative", display: "inline-block", width: "100%" }}>
      <img ref={imgRef} src={`data:image/png;base64,${result.annotated_image_b64}`}
        alt="Detección" style={{ width: "100%", display: "block", borderRadius: 8 }}
        onLoad={() => { setImgLoaded(true); updateDims(); }} />
      {imgLoaded && dims.w > 0 && (
        <canvas ref={canvasRef} style={{
          position: "absolute", top: 0, left: 0, width: "100%", height: "100%", borderRadius: 8,
        }} />
      )}
    </div>
  );
}
```

## PITFALL — build en host, no en Docker

`docker compose build --no-cache frontend` puede cachear el bundle viejo aunque los archivos fuente cambien. El layer `COPY . .` de Docker no detecta cambios en algunos casos.

**Workflow correcto:**
```bash
# 1. Build en host
cd /home/server/proyectos/forestai-poc/frontend && npm run build

# 2. Verificar que el nuevo código está en el bundle
grep -l "NombreNuevoComponente" dist/assets/*.js

# 3. Copiar al container y recargar nginx (sin recrear container)
docker cp dist/. forestai-poc-frontend-1:/usr/share/nginx/html/
docker exec forestai-poc-frontend-1 nginx -s reload
```

Este workflow es 5x más rápido que rebuild Docker y 100% confiable.

## PITFALL — HuggingFace cache no persiste entre recreaciones del container

El modelo DeepForest (124MB, `weecology/deepforest-tree`) vive en `/root/.cache/huggingface` DENTRO del container celery_worker. Si se hace `docker compose down` o `--force-recreate`, se pierde y hay que repetir la descarga manual.

**Fix permanente — agregar al docker-compose.yml:**
```yaml
celery_worker:
  volumes:
    - /home/server/.cache/huggingface:/root/.cache/huggingface
```

**Estado 2026-06-09:** volumen NO agregado aún. Si se recrea el container repetir:
```bash
# Limpiar incompletos y forzar descarga
docker exec forestai-poc-celery_worker-1 sh -c \
  "find /root/.cache/huggingface -name '*.incomplete' -delete"

docker exec forestai-poc-celery_worker-1 python3 -c "
import os; os.environ['HF_HUB_DISABLE_XET'] = '1'
from huggingface_hub import hf_hub_download
hf_hub_download(repo_id='weecology/deepforest-tree', filename='model.safetensors', local_dir='/tmp/df_dl')
print('OK')
"

BLOB='d37a7af0b5ba2754282a80d41b4c7b66e8c7149234df5bf3f41bdaf57d329fc8'
SNAP='/root/.cache/huggingface/hub/models--weecology--deepforest-tree/snapshots/cc21436bc5d572dde8ff5f93c1e71a32f563cace'
docker exec forestai-poc-celery_worker-1 sh -c "
cp /tmp/df_dl/model.safetensors /root/.cache/huggingface/hub/models--weecology--deepforest-tree/blobs/$BLOB
ln -sf '../../blobs/$BLOB' $SNAP/model.safetensors
ls -lh /root/.cache/huggingface/hub/models--weecology--deepforest-tree/blobs/
"
```

## Resultado segunda sesión 2026-06-09

Imagen Avellaneda (12622×7887px, 8 tiles 4096px):
- 173 árboles detectados tras NMS
- SAM refinó 173 copas
- VLM clasificó especies (Eucalipto saludable, Acacia estresada)
- Tiempo total: ~5-7 min CPU

Imagen chica (62 árboles):
- Tiempo total: 38 segundos (sin tiling — imagen < 20Mpx)
