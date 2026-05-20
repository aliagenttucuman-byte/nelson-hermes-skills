---
name: nelson-generative-ui
description: "Shell reutilizable de Generative UI para demos y herramientas internas del equipo Nelson. OpenUI Lang + FastAPI con tools enchufables por proyecto."
version: 1.0.0
author: JARVIS
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [openui, generative-ui, demo, fastapi, nextjs, groq, llm, streaming]
    related_skills: [nelson-frontend-stack, nelson-llm-generation, spike]
---

# Nelson Generative UI Shell

Framework reutilizable para construir demos y herramientas internas con UI generativa. El chat renderiza componentes React (charts, KPIs, tablas) en tiempo real mientras el LLM hace streaming.

## Cuándo usar

- Demo para cliente o YPF que necesita impacto visual rápido
- Herramienta interna donde el usuario consulta datos en lenguaje natural
- Cualquier caso donde el output del agente no es texto plano sino componentes interactivos
- Alternativa a dashboards clásicos cuando querés armar algo en horas, no días

## Límite importante

OpenUI es **web únicamente**. No renderiza en WhatsApp. Para WA seguir con el flujo PNG (matplotlib → imagen → Baileys).

---

## Estructura del shell

```
jarvis-demo-shell/
├── frontend/          ← OpenUI (Next.js) — NUNCA cambia entre proyectos
│   ├── src/app/api/chat/route.ts   ← llama Groq SDK + consulta system prompt
│   └── src/app/layout.tsx          ← incluye polyfill crypto.randomUUID
└── backend/           ← FastAPI Python — cambia por proyecto
    ├── main.py
    ├── routers/chat.py
    └── tools/
        ├── registry.py   ← registro dinámico
        ├── demo.py        ← proyecto por defecto
        └── energia.py     ← ejemplo: datos PowerBI energía
```

**Ubicación en el servidor:** `~/jarvis-demo-shell/`

---

## Cómo levantar

```bash
# Backend (puerto libre, evitar 8000/8001/8002 — ocupados por otros servicios)
cd ~/jarvis-demo-shell/backend
python3 -m uvicorn main:app --reload --port 8765 --env-file .env

# Frontend
cd ~/jarvis-demo-shell/frontend
PORT=3789 npm run dev
```

Acceso Tailscale: `http://100.110.8.13:3789`

---

## Multi-proyecto simultáneo (patrón recomendado)

El registry carga **todos** los archivos en `tools/` automáticamente. El agente recibe las instrucciones combinadas de todos y elige la fuente correcta según la pregunta.

```python
# tools/registry.py — patrón clave
def load_all():
    for _, module_name, _ in pkgutil.iter_modules(tools_pkg.__path__):
        if module_name not in ("registry", "__init__"):
            importlib.import_module(f"tools.{module_name}")

def get_system_instructions() -> str:
    load_all()
    parts = ["Tenés acceso a múltiples fuentes de datos...\n"]
    for tool in _tools.values():
        parts.append(tool.get_system_instructions().strip())
    return "\n\n---\n\n".join(parts)
```

Agregar un proyecto = crear el archivo + decorar con `@register`. Sin tocar `.env` ni reiniciar nada (hot reload lo detecta).

La variable `ACTIVE_PROJECT` del `.env` queda **obsoleta** con este patrón — todos los proyectos se cargan siempre.

**Cómo embeber datos reales en el system prompt** (patrón empleo/energía):
- Pre-calcular los datos al momento de `get_system_instructions()`
- Incluir los JSON directamente en las instrucciones como contexto
- El agente los recibe como parte del prompt, sin necesitar function calling

```python
@register
class MiTool(BaseTool):
    def get_system_instructions(self) -> str:
        datos = cargar_datos_reales()   # DataFrame, CSV, JSON, API
        datos_json = json.dumps(datos[:10], ensure_ascii=False)
        return f\"\"\"\n# Fuente: Mi Dataset\n## Datos disponibles\n{datos_json}\n## Cómo responder\n```openui\nchart tipo=\"barra\" ...\ndatos={datos_json}\n```\n\"\"\"\n```

---

## Cómo agregar un nuevo proyecto

1. Crear `backend/tools/mi_proyecto.py`:

```python
from tools.registry import BaseTool, register

@register
class MiProyectoTool(BaseTool):
    name = "mi_proyecto"
    description = "Descripción"

    def get_system_instructions(self) -> str:
        return """
        # Mi Proyecto
        Contexto para el agente...
        Qué datos tiene disponibles...
        Cómo usar OpenUI Lang para los componentes...
        """
```

2. En `backend/.env`:
```
ACTIVE_PROJECT=mi_proyecto
```

3. Reiniciar el backend. El frontend no se toca.

---

## OpenUI Lang — sintaxis correcta (funcional, no declarativa)

OpenUI Lang es un lenguaje **funcional**: cada línea define una variable que se pasa a un componente. Los nombres de componentes son PascalCase y deben coincidir exactamente con el catálogo. Componentes como `chart`, `kpi`, `tabla` NO existen — causan `unknown-component` silencioso.

### Componentes disponibles (nombres exactos del catálogo)

Charts multiserie: `BarChart`, `LineChart`, `AreaChart`, `HorizontalBarChart`, `RadarChart`
Charts 1D: `PieChart`, `RadialChart`, `SingleStackedBarChart`
Datos: `Series`, `Table`, `Col`
Layout: `Card`, `CardHeader`, `Stack`, `Tabs`, `TabItem`
Texto: `TextContent`, `TextCallout`, `MarkDownRenderer`

### KPI (valor destacado)
```openui
root = Stack([title, value, sub])
title = TextContent("Puestos de Trabajo — Argentina", "small")
value = TextContent("6,595,449", "large-heavy")
sub = TextContent("Empleo Formal — actualizado 23/01/2024", "small")
```

### BarChart (barras verticales — labels cortos)
```openui
root = Card([header, chart])
header = CardHeader("Producción por Empresa")
labels = ["YPF", "Pan American", "Vista Energy"]
s1 = Series("m3/día", [60257, 15568, 11900])
chart = BarChart(labels, [s1])
```

### HorizontalBarChart (barras horizontales — ideal para nombres largos)
```openui
root = Card([header, chart])
header = CardHeader("Top Provincias por Empleo")
labels = ["Buenos Aires", "CABA", "Santa Fe", "Córdoba"]
s1 = Series("Puestos", [2109000, 1596000, 543000, 537000])
chart = HorizontalBarChart(labels, [s1])
```

### BarChart agrupado (múltiples series)
```openui
root = Card([header, chart])
header = CardHeader("Empleo por Género")
labels = ["Buenos Aires", "CABA", "Santa Fe"]
s1 = Series("Mujeres", [694865, 616673, 166410])
s2 = Series("Varones", [1413254, 979724, 376948])
chart = BarChart(labels, [s1, s2], "grouped")
```

### LineChart (tendencia temporal)
```openui
root = Card([header, chart])
header = CardHeader("Producción Mensual 2026")
labels = ["Ene", "Feb", "Mar", "Abr"]
s1 = Series("m3/día", [58000, 60000, 61500, 60257])
chart = LineChart(labels, [s1])
```

### PieChart (distribución — necesita NÚMEROS, no objetos)
```openui
root = Card([header, chart])
header = CardHeader("Market Share Petróleo")
labels = ["YPF", "Pan American", "Vista", "Otros"]
chart = PieChart(labels, [60257, 15568, 11900, 29752])
```

### Tabs con múltiples vistas
```openui
root = Card([header, tabs])
header = CardHeader("Producción Energética")
t1 = TabItem("petroleo", "Petróleo", [HorizontalBarChart(labels_p, [s_p])])
t2 = TabItem("gas", "Gas", [HorizontalBarChart(labels_g, [s_g])])
tabs = Tabs([t1, t2])
```

---

## Pitfalls críticos

### 1. crypto.randomUUID solo funciona en HTTPS o localhost

**Síntoma:** `TypeError: crypto.randomUUID is not a function` al enviar el primer mensaje.

**Causa:** El browser bloquea `crypto.randomUUID` en HTTP con IP externa (Tailscale).

**Fix** — agregar en `frontend/src/app/layout.tsx` dentro de `<head>`:

```tsx
<script
  dangerouslySetInnerHTML={{
    __html: `
      if (typeof crypto !== 'undefined' && typeof crypto.randomUUID !== 'function') {
        crypto.randomUUID = function() {
          return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, function(c) {
            return (c ^ (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (c / 4)))).toString(16);
          });
        };
      }
    `,
  }}
/>
```

### 2. El stream SSE crudo rompe el parser de OpenUI

**Síntoma:** `SyntaxError: Unexpected token 'd', "data: {"id"... is not valid JSON`

**Causa:** OpenUI espera el formato del **SDK de OpenAI** (objeto ReadableStream del SDK), no bytes SSE crudos con prefijo `data: `. Si el frontend hace proxy a un backend que reenvía el stream de Groq directamente, el parser explota.

**Fix correcto:** El `route.ts` del frontend debe llamar **directamente al SDK de OpenAI** con `baseURL` apuntando a Groq, y solo consultar al backend para obtener el `systemPrompt` del proyecto activo:

```typescript
// route.ts — patrón correcto
const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: "https://api.groq.com/openai/v1",
});

// 1. Obtener system prompt del proyecto activo
const res = await fetch(`${BACKEND_URL}/api/system-prompt`);
const { systemPrompt } = await res.json();

// 2. Llamar al SDK — produce el formato que OpenUI espera
const response = await client.chat.completions.create({
  model: "llama-3.3-70b-versatile",
  messages: [{ role: "system", content: systemPrompt }, ...messages],
  stream: true,
});

// 3. response.toReadableStream() → formato correcto para OpenUI
return new Response(response.toReadableStream(), { ... });
```

**Lo que NO funciona:** hacer proxy al backend que re-emite los bytes crudos de Groq. Aunque el MIME type sea `text/event-stream`, el SDK de OpenAI-compatible del frontend no puede procesar SSE crudo.

### 3. Puertos 8000, 8001, 8002 siempre ocupados en el servidor

Usar puertos alternativos: `8765`, `8880`, `9000`, `9001`.

### 5. `unknown-component` silencioso en consola

**Síntoma:** El chat responde texto pero no renderiza ningún componente visual. La consola del browser muestra: `[openui] parser/unknown-component: Unknown component "KPI" — not found in catalog or builtins`

**Causa:** El LLM generó un nombre de componente que no existe en el catálogo de OpenUI (ej: `KPI`, `Chart`, `kpi`, `chart`, `tabla`). El parser lo ignora silenciosamente.

**Fix:** Asegurarse que el system prompt de cada tool use los nombres PascalCase exactos del catálogo: `BarChart`, `HorizontalBarChart`, `LineChart`, `PieChart`, `Card`, `TextContent`, `Table`, `Series`. Ver sección "OpenUI Lang — sintaxis correcta" arriba.

**Regla:** En el system prompt de cada tool, siempre incluir un bloque de ejemplo con la sintaxis exacta de los componentes que el agente debe generar. El LLM imita el ejemplo — si el ejemplo usa `chart tipo="barra"`, el LLM lo copia igual.

### 6. scaffold OpenUI model hardcodeado a gpt-5.2

El `npx @openuidev/cli@latest create` genera `route.ts` con `model: "gpt-5.2"`. Siempre reemplazar por el modelo correcto del proveedor elegido.

---

## Proyectos registrados

| Proyecto | Archivo | Descripción |
|----------|---------|-------------|
| `demo` | `tools/demo.py` | Genérico — instrucciones base del agente + componentes OpenUI |
| `energia` | `tools/energia.py` | Producción petróleo/gas AR — datos.gob.ar (datos reales 2026) |
| `empleo` | `tools/empleo.py` | Empleo formal AR — PowerBI Ministerio de Trabajo (6.5M puestos, 24 provincias) |

Ver `references/openui-shell-architecture.md` para diagrama detallado del flujo.

Templates reutilizables:
- `templates/registry.py` — registry multi-proyecto completo (copiar a `backend/tools/registry.py`)
- `templates/chat-route.ts` — route.ts del frontend con patrón correcto Groq + system-prompt (copiar a `frontend/src/app/api/chat/route.ts`)
- `templates/tool-with-real-data.py` — tool con datos reales embebidos + sintaxis OpenUI Lang correcta (copiar a `backend/tools/mi_proyecto.py`)
