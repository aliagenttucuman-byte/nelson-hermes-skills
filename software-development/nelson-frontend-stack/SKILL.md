---
name: nelson-frontend-stack
title: Frontend Stack - React + TypeScript + Vite + Tailwind
description: Stack frontend estandar del equipo Nelson. React 18, TypeScript, Vite, Tailwind CSS, React Query, Axios, React Router DOM. Convenciones de carpetas, hooks, patterns.
skill: nelson-frontend-stack
author: equipo-nelson
version: "2.0.0"
keywords: [react, typescript, vite, tailwind, react-query, axios, frontend]
dependencies: []
---

# Frontend Stack - Equipo Nelson

## Responsive Mobile — Patrón Probado (Fleet Optimizer)

Para hacer responsive una app de dashboard desktop, aplicar en este orden:

### 1. Header adaptable
```css
.header { flex-wrap: wrap; gap: 8px; padding: 10px 16px; }
@media (max-width: 480px) { .header-sub { display: none; } }
```

### 2. Stats row — grid auto-fill (no flex con min-width fijo)
```css
/* ❌ flex con min-width → scrollea en mobile */
/* ✅ */
.stats-row { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
.stat-card { min-width: 0; } /* crítico para que el grid funcione */
```

### 3. Tabs — scroll horizontal sin scrollbar visible
```css
.tabs { overflow-x: auto; scrollbar-width: none; -webkit-overflow-scrolling: touch; }
.tabs::-webkit-scrollbar { display: none; }
.tab-btn { white-space: nowrap; flex-shrink: 0; }
```

### 4. Layout dos columnas → stack vertical en mobile
```css
.two-col { grid-template-columns: 1fr 300px; }
@media (max-width: 768px) { .two-col { grid-template-columns: 1fr; height: auto; } }
```

### 5. Tablas — scroll horizontal
```css
.table-wrap { overflow-x: auto; }
.table { min-width: 600px; }
```

### 6. Grillas de 3 → 2 → 1 columna
```css
.grid-3 { grid-template-columns: 1fr 1fr 1fr; }
@media (max-width: 768px) { .grid-3 { grid-template-columns: 1fr 1fr; } }
@media (max-width: 480px) { .grid-3 { grid-template-columns: 1fr; } }
```

### 7. Panels flotantes — usar min() para no salirse de pantalla
```css
.panel { width: min(420px, calc(100vw - 24px)); height: min(580px, calc(100vh - 100px)); }
```

**Media queries estándar:** `768px` (tablet/mobile) y `480px` (mobile pequeño).

## Templates

- `templates/api-client.ts` — Axios client con baseURL relativa correcta (fallback `''`, no `localhost`). Usar como punto de partida para `src/api/client.ts`.

## Stack

| Capa | Libreria | Version |
|------|----------|---------|
| Framework | React | ^19.0 |
| Build | Vite | ^8.0 |
| Lenguaje | TypeScript | ^6.x |
| Estilos | Tailwind CSS | ^4.1 |
| Estado servidor | TanStack Query (React Query) | ^5.100 |
| HTTP | Axios | ^1.16 |
| Routing | React Router DOM | ^7.15 |
| UI Components | shadcn/ui (opcional) | latest |
| Iconos | Lucide React | ^1.16 |
| Charts | Recharts (default) / Chart.js (allowed por proyecto) | Recharts ^3.8 / Chart.js ^4.x |
| Diagnostico | React Doctor | ^2.0 |

## Estructura de Carpetas

```
frontend/src/
├── api/
│   ├── client.ts          # Axios instance con baseURL, interceptors
│   ├── auth.ts            # Endpoints de auth
│   └── generated/
│       └── api.ts         # Generado desde OpenAPI spec (NO TOCAR)
├── components/
│   ├── ui/                # Componentes base (Button, Input, Card)
│   └── layout/            # Layout, Navbar, Sidebar
├── hooks/
│   ├── useAuth.ts
│   └── useApi.ts          # Wrapper de React Query
├── lib/
│   └── utils.ts           # cn() para Tailwind + utilidades
├── pages/
│   ├── Home.tsx
│   ├── Login.tsx
│   └── Dashboard.tsx
├── types/
│   └── index.ts           # Types manuales (el resto viene de generated/)
├── context/
│   └── AuthContext.tsx
├── App.tsx
├── main.tsx
└── index.css
```

## Política SDD para selección de librerías

Cuando el proyecto define librerías frontend (zod, date-fns, tanstack-table, zustand, motion, etc.), documentarlas en estas fases:

1. **Constitución**: stack base y librerías permitidas/prohibidas.
2. **Specify (OpenAPI + User Stories)**: justificar la necesidad funcional (ej: hotkeys, drag-and-drop, gráficos).
3. **Plan**: decisión final por librería + alternativa descartada + riesgo.
4. **Checklist**: validar accesibilidad, performance, mantenibilidad y testing.

Regla: no sumar librerías por moda; cada librería debe estar trazada a una necesidad de negocio o UX.

## Convenciones

### Componentes
- Un componente por archivo, Named Export
- Props con interface arriba del componente
- `export function` (no default) para tree-shaking

```tsx
// pages/Home.tsx
import { useQuery } from '@tanstack/react-query';

interface HomeProps {
  title: string;
}

export function Home({ title }: HomeProps) {
  const { data, isLoading } = useQuery({ queryKey: ['items'], queryFn: fetchItems });

  if (isLoading) return <div className="p-4">Cargando...</div>;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
    </div>
  );
}
```

### API Client (Axios)

```ts
// api/client.ts
import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);
```

### React Query Patterns

```ts
// hooks/useItems.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';

export function useItems() {
  return useQuery({
    queryKey: ['items'],
    queryFn: async () => {
      const res = await api.get('/items');
      return res.data;
    },
  });
}

export function useCreateItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ItemCreate) => api.post('/items', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['items'] }),
  });
}
```

### Environment Variables

```
# .env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=ProyectoNelson
```

> Nota: Solo variables con prefijo `VITE_` son expuestas al frontend.

## Tailwind CSS v4

En Tailwind 4 no se usa `tailwind.config.js` ni `postcss.config.js`. Se configura directamente en CSS:

```css
/* src/index.css */
@import "tailwindcss";

body {
  margin: 0;
  min-height: 100vh;
  background-color: #0f172a;
  color: #e2e8f0;
}
```

Para personalizar temas, usar `@theme` en CSS:

```css
@import "tailwindcss";

@theme {
  --color-primary: #3b82f6;
  --color-secondary: #10b981;
  --font-sans: 'Inter', system-ui, sans-serif;
}
```

La utilidad `cn()` sigue igual:

```ts
// lib/utils.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

## Comandos

```bash
# Dev server
npm run dev

# Build produccion
npm run build

# Preview build local
npm run preview

# Type check
npx tsc --noEmit

# Lint (ESLint)
npm run lint

# Diagnostico React Doctor
npx react-doctor@latest
npx react-doctor@latest --format json --output report.json
```

## Modo Operativo (limpieza de demo/IA cuando el usuario lo pide)

Cuando el usuario diga explícitamente “dejá solo lo operativo” o “limpiemos la UI de X”, aplicar limpieza de pantalla completa, no parcial.

Checklist rápido para este caso:
1. Remover bloques legacy de demo/prueba (botones, cards, headings y textos de ejemplo).
2. Remover controles de IA si el flujo pasa a lógica determinística (selectors de modelo, prompts, wizard de plan sugerido).
3. Dejar una sola CTA principal orientada a operación real (ej: ejecutar pipeline estático).
4. Mantener únicamente: carga de archivos, ejecución, resultado, descarga y preview relevante.
5. Rebuild obligatorio y verificación textual en el archivo (`search_files`) para confirmar que no quedaron etiquetas legacy.

Pitfall frecuente:
- Borrar botones pero dejar texto/estado legacy (“demo”, “modelo IA”, “plan sugerido”) en tipos, labels o mensajes de error. Hay que limpiar UI + tipos + copy.

## React Doctor — Diagnóstico de Calidad React

> "Your agent writes bad React. This catches it."
> 12k stars — MIT — activo (commits diarios) — https://github.com/millionco/react-doctor

Herramienta de diagnóstico estático para React. Detecta issues en state & effects,
performance, arquitectura, seguridad y accesibilidad. Compatible con Next.js, Vite,
TanStack, React Native, Expo.

### Modos de uso

**1. Auditoría rápida (un solo comando, sin install):**
```bash
npx react-doctor@latest
# Con output JSON para parsear:
npx react-doctor@latest --format json --output report.json
# Sin telemetría:
npx react-doctor@latest --no-telemetry
```

**2. Instalación para agentes (Mercedes / JARVIS):**
```bash
# Correr en la raíz del proyecto frontend
npx react-doctor@latest install
```
Esto inyecta las reglas como skill en el agente (Claude Code, Cursor, Codex, OpenCode).
El agente aprende los patrones y no los repite en el futuro.
→ Correr esto en CADA proyecto React nuevo del equipo.

**3. CI/CD — GitHub Actions (solo issues nuevos en el PR):**
```yaml
# .github/workflows/react-doctor.yml
name: React Doctor
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
permissions:
  contents: read
  pull-requests: write
  issues: write
  statuses: write
concurrency:
  group: react-doctor-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
jobs:
  react-doctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0
      - uses: millionco/react-doctor@v2
```
IMPORTANTE: `fetch-depth: 0` es necesario para comparar contra el base commit.
Solo reporta issues NUEVOS que introduce el PR — no los pre-existentes (como Codecov).

**4. LSP — diagnóstico inline en el editor (experimental):**
```bash
react-doctor experimental-lsp --stdio
```
Compatible con VS Code, Cursor, Zed, Neovim, Sublime, Emacs, Helix.

**5. Configuración custom (`doctor.config.ts`):**
```ts
// doctor.config.ts en la raíz del proyecto
import type { ReactDoctorConfig } from "react-doctor/api";
export default {
  lint: true,
  rules: {
    "react-doctor/no-array-index-as-key": "off",  // deshabilitar regla específica
  },
} satisfies ReactDoctorConfig;
```

### Cuándo correrlo

| Momento | Comando |
|---|---|
| Al arrancar un proyecto nuevo | `npx react-doctor@latest install` (para agentes) |
| Antes de cada demo o entrega | `npx react-doctor@latest` |
| En PR automático | GitHub Action (ver arriba) |
| Durante desarrollo | LSP experimental |

### Reglas más comunes detectadas

- `no-array-index-as-key` — usar array.index como key en listas (causa re-renders)
- `no-jsx-element-type` — tipos JSX incorrectos
- Issues de useEffect (dependencias faltantes, efectos sin cleanup)
- Problemas de TanStack Query (query-destructure-result, etc.)

### Pitfall — telemetría activa por default

React Doctor envía métricas anónimas a Sentry. Para desactivar en entornos de PoC
con datos sensibles:
```bash
npx react-doctor@latest --no-telemetry
```
O agregar a `doctor.config.ts`:
```ts
export default { telemetry: false } satisfies ReactDoctorConfig;
```

---

## UI Design — Feedback Primero

Nelson rechazó una UI completa rediseñada sin su input con "no me gusta para nada". Regla:

1. Antes de rediseñar una UI, pedir: screenshot actual + estilo deseado (minimalista, GIS técnico, dashboard con cards, mapa flotante, etc.)
2. Si no puede mandar screenshot (servidor sin pantalla), describir las opciones concretas y dejar que elija.
3. No asumir que un dark theme genérico va a satisfacer — preguntar primero.

### Modo operativo (quitar ruido de demo)

Cuando el usuario pida "dejarlo en pipeline/front" y limpiar elementos viejos:
- Priorizar UI operativa mínima (subida de archivo + ejecutar flujo + descargar resultado + preview).
- Remover/ocultar acciones de demo y bloques exploratorios (ej: botones demo, selectores de modelo IA, asistentes de plan) para evitar confusión en uso diario.
- Si el flujo está en producción operativa, mostrar métricas concretas de ejecución (filas de entrada/salida) en vez de texto marketing.

### Patrón de navegación para dashboard operativo (Orchestrator)

Cuando el dashboard mezcla operación + múltiples proyectos, usar este patrón por defecto:

1. En el menú principal, priorizar primero módulos de **gestión operativa** (Dashboard, Orquestador, Presupuesto, Resumen PM, Taxonomía).
2. Dejar **Proyectos** al final del menú como bloque separado.
3. Unificar páginas de proyecto en **una sola solapa** (`/projects`) con selector interno (`?project=forestai|fleet|...`) en lugar de una ruta por proyecto en el menú.
4. Mantener compatibilidad con rutas antiguas (`/forestai`, `/fleet`) redirigiendo a la página unificada con query params.

Objetivo: reducir ruido en navegación, sostener foco en "qué misión ejecutar" y cambiar de proyecto sin perder contexto/metricas.

## Patrón UX: Automatización de Excel para usuario no técnico (prompt-first)

Cuando el usuario final no conoce términos técnicos (join/concat/groupby), la UI debe esconder la implementación y exponer solo intención de negocio.

Flujo recomendado:
1. **Subir archivos** (múltiples, incremental)
2. **Definir objetivo en lenguaje natural** (qué resultado espera)
3. **Generar plan sugerido** (pasos en español simple)
4. **Ejecutar plan**
5. **Guardar procedimiento exitoso** para reuso

Reglas UX:
- No exponer etiquetas internas tipo `join_type`, `concat`, `left/right` en la interfaz principal.
- Mostrar pasos con lenguaje humano: "Cruzar archivo 2 por DNI", "Combinar archivo 3".
- Incluir feedback rápido: preview del resultado + descarga.
- Incluir biblioteca de procedimientos guardados con orden manual (↑/↓) y botón "Usar".

Persistencia recomendada en PoC:
- Guardar automáticamente procedimientos cuando una ejecución termina OK.
- Campos mínimos: `name`, `objective`, `expected_result`, `model`, `run_count`, `sort_order`, timestamps.
- Endpoints mínimos: `list`, `create/update`, `reorder`, `mark-used`.

## Prompt-first UX para usuarios no técnicos (automatización operativa)

Cuando el usuario final **no domina términos técnicos** (join/concat/groupby), la UI debe ocultar ese vocabulario y usar flujo asistido:

1. **Subir archivos** (multi-Excel)
2. **Describir objetivo en lenguaje natural** ("qué quiero lograr")
3. **Mostrar plan sugerido** (pasos explicados en español simple)
4. **Ejecutar y validar** (preview + descarga)

Patrón recomendado de API para este caso:
- `POST /plan/suggest` → recibe `file_ids + objective` y devuelve pasos sugeridos
- `POST /merge` → ejecuta pasos + prompt de negocio opcional

Regla UX:
- En vista usuario: usar textos como "Cruzar", "Combinar", "Consolidar".
- Reservar `join`, `concat`, `suffix`, etc. para modo debug interno (equipo técnico).

Ver guía operativa: `references/prompt-first-excel-automation.md`.

## Referencias de soporte

Cuando el frontend usa CSS custom (no Tailwind), este es el patrón responsive validado en Fleet Optimizer:

**Stats row:** usar `grid` con `auto-fill` en lugar de `flex` con `min-width` fijo:
```css
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
  padding: 12px 16px;
}
/* Los cards se adaptan solos — no necesitan flex-shrink ni overflow-x */
```

**Tabs con scroll horizontal en mobile:**
```css
.tabs {
  display: flex;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}
.tabs::-webkit-scrollbar { display: none; }
.tab-btn { white-space: nowrap; flex-shrink: 0; }
```

**Mapa + lista: grid que se apila en mobile:**
```css
.mapa-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 14px;
  height: calc(100vh - 230px);
  min-height: 400px;
}
@media (max-width: 768px) {
  .mapa-layout { grid-template-columns: 1fr; height: auto; }
  .map-container { height: 55vw; min-height: 240px; }
  .truck-list { max-height: 320px; }
}
```

**Chat panel flotante que no se sale de la pantalla:**
```css
.chat-panel {
  width: min(420px, calc(100vw - 24px));
  height: min(580px, calc(100vh - 100px));
}
```

**Tabla financiero — scroll horizontal en mobile:**
```css
.fin-table-wrap { overflow-x: auto; }
.fin-table { min-width: 600px; }
```

**Breakpoints del equipo:** 768px (tablet) y 480px (mobile pequeño).

**Pitfall:** FastAPI + StaticFiles sirve el `dist/` directamente — después de `npm run build` los cambios se ven en la próxima carga sin reiniciar el backend.

## PM / Project tabs — desglose financiero visible

Cuando el usuario pide “desglose de números”, no alcanza con responder en chat: hay que reflejarlo en las solapas operativas (ProjectView + PM) con métricas derivadas visibles.

Checklist recomendado:
- Extender tipos TS de `project_valuation` antes de renderizar nuevos campos (`operational_cost_4m_usd`, `clients_per_year`, `price_per_year_usd`, etc.).
- Mostrar bloques de desglose: desarrollo, OPEX 4m, OPEX mensual derivado, % mix, horas derivadas y hitos 30/40/30.
- Si en un branch JSX condicional se agregan múltiples bloques hermanos, envolver en fragment `<>...</>` para evitar `TS2657`.
- Cerrar con `npm run build` y validar que strings clave existan en `dist/assets/*.js` cuando se necesite prueba rápida de presencia del cambio.

## Operative Mode for Data Pipelines (Excel / Cobranzas)

Cuando el usuario pide pasar de demo a operación real, el frontend debe simplificarse al flujo mínimo:

1) Subir archivo base real.
2) Ejecutar pipeline estático.
3) Descargar resultado operativo.

Aplicar estas reglas:
- Quitar/ocultar botones demo y elementos de IA (modelo, prompt, "plan sugerido") si ya no aportan al flujo operativo.
- Mostrar un CTA principal único y explícito (ej: `Ejecutar pipeline estático CDO/PF`).
- Mostrar métricas de volumen con **filas útiles** (sin fila de título tipo `Informe: ...` ni cabecera), porque en operación real los libros suelen ser grandes y el conteo debe coincidir con lo que mira el usuario en Excel.
- Etiquetar claramente input vs output (ej: `CDO Sistema`, `PTE Fact Sistema`, `CDO Trabajada`, `PF Trabajada`).

Checklist rápido antes de compartir URL:
- No quedan textos de demo en pantalla (`demo`, `plan sugerido`, `modelo IA`) cuando el usuario pidió modo operativo.
- Los contadores visibles coinciden con filas útiles esperadas del archivo real.
- El botón de descarga entrega exactamente las hojas operativas requeridas por negocio.

## Referencias de soporte

- `references/dashboard-mapa-websocket-chat.md` — Template completo: dashboard React con Leaflet + WebSocket live + chat IA flotante (validado FleetOptimizer PoC)
- `references/excel-pipeline-operational-mode.md` — Guía de UI mínima operativa para pipelines Excel (sin IA/demo), con foco en conteo de filas útiles.
- `references/excel-poc-white-screen-500-debug.md` — Postmortem corto: pantalla blanca por Axios multipart global + 500 en merge encadenado; fixes y checks de verificación.
- `references/white-screen-triage-cloudflare.md` — Runbook rápido para "pantalla blanca" en demos por tunnel (verificación HTML/JS/API + secuencia de recuperación)
- `references/prompt-first-excel-automation.md` — Patrón UI/API para automatización de Excel orientada a usuarios no técnicos (objetivo en lenguaje natural → plan sugerido → ejecución → guardado de procedimiento).
- `references/prompt-first-workflow-pattern.md` — Patrón para UX no técnica: Objetivo → Plan sugerido → Ejecutar + guardado de procedimientos reutilizables.

## Deploy estático en Docker (nginx)

Cuando el frontend corre como contenedor Docker con nginx (ej: `forestai-poc-frontend-1`), **no hay hot reload**. El flujo correcto para ver cambios:

```bash
# 1. Editar los .tsx en el host
# 2. Build en el HOST (no dentro del Docker — evita cache de layers)
cd ~/proyectos/forestai-poc/frontend && npm run build
# 3. Copiar dist al contenedor nginx
docker cp dist/. <container-name>:/usr/share/nginx/html/
# 4. Recargar nginx (sin reiniciar contenedor)
docker exec <container-name> nginx -s reload
# 5. Verificar que el nuevo bundle esté presente
docker exec <container-name> ls /usr/share/nginx/html/assets/
# 6. Usuario hace Ctrl+Shift+R en el browser
```

⚠️ Trampa frecuente: `docker compose build --no-cache` puede igualmente usar layer cache del COPY si los timestamps no cambiaron. **El build en el HOST + docker cp es el método más confiable** para iterar rápido.

⚠️ Trampa frecuente: editar el código, buildear, y asumir que el browser lo levantó — pero el tunnel apunta al container Docker que sigue sirviendo el build viejo.

### nginx client_max_body_size para uploads grandes
Ortomosaicos de drone pesan 60-200MB. El nginx del frontend rechaza con 413 por defecto.
```nginx
server {
    client_max_body_size 500m;
    ...
}
```
Aplicar sin reiniciar: `docker cp nginx.conf container:/etc/nginx/conf.d/default.conf && docker exec container nginx -s reload`
Verificar: `docker exec container nginx -T | grep client_max_body`

### Ruta /demo para demos limpias (sin exponer stack interno)
```tsx
// main.tsx — routing por pathname sin tocar App.tsx
const isDemo = window.location.pathname.startsWith("/demo");
createRoot(document.getElementById("root")!).render(
  isDemo ? <DemoPage /> : <App />
);
```
nginx: agregar `location /demo { try_files $uri $uri/ /index.html; }`
El componente Demo es independiente — no importa nada de la app principal.

## SPA servida desde backend (sin servidor propio)

Cuando el frontend se buildea como estático y el backend lo sirve como SPA:

```ts
// vite.config.ts — solo build, no servidor separado
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: { outDir: 'dist' },
  // server config solo para dev local, el backend sirve dist/ en prod
})
```

```
.env
VITE_API_URL=http://localhost:<PUERTO_BACKEND>
```

El backend debe tener una ruta catch-all que sirva `dist/index.html` para todas las rutas no-API, y montar `dist/` como directorio de archivos estáticos.

## Patrón de instalación npm en terminal

`npm install -D` y `npm install --save-dev` son incorrectamente detectados como procesos servidor.
Usar siempre `background=true` para installs de devDependencies:

```python
# CORRECTO — no falla
terminal(background=True, command="npm install --save-dev tailwindcss @tailwindcss/vite 2>&1; echo DONE")
process(action="wait", session_id=...)

# FALLA — se interrumpe como si fuera un servidor
terminal(command="npm install -D tailwindcss")
```

## Patrón: Vista dedicada por proyecto (ProjectView)

Cuando hay múltiples proyectos/productos en el dashboard (ej: ForestAI + Fleet),
crear un componente genérico `ProjectView` parametrizado con una config por proyecto.

```tsx
// Definir config estática por proyecto
type ProjectConfig = {
  id: string; label: string; icon: React.ElementType
  color: string; accent: string; keywords: string[]
  stack: string[]; milestones: { name: string; done: boolean }[]
}
const PROJECTS: Record<string, ProjectConfig> = {
  forestai: { ... },
  fleet: { ... },
}

// Componente genérico
export function ProjectView({ projectKey }: { projectKey: keyof typeof PROJECTS }) {
  const cfg = PROJECTS[projectKey]
  // buscar match en PM instances por keywords
  const match = allProjects.find(p =>
    cfg.keywords.some(kw => p.name.toLowerCase().includes(kw))
  )
  // renderizar con datos reales + fallback si no hay match
}

// Exports específicos
export function ForestAIPage() { return <ProjectView projectKey="forestai" /> }
export function FleetPage()    { return <ProjectView projectKey="fleet" /> }
```

Ventaja: agregar un proyecto nuevo = agregar una entrada al objeto PROJECTS y un export.
Sin duplicar código de UI.

## Patrón: Sidebar con secciones (dividers)

Para organizar navegación con grupos, usar items con `divider: true` en el array de nav:

```tsx
const nav = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { divider: true, label: 'Proyectos' },
  { to: '/forestai', icon: TreePine, label: 'ForestAI' },
  { divider: true, label: 'Gestión' },
  { to: '/pm', icon: KanbanSquare, label: 'Resumen PM' },
]
// En el render:
nav.map((item, idx) => {
  if ('divider' in item) return <p key={idx} className="text-[10px] text-slate-600 uppercase">{item.label}</p>
  const { to, icon: Icon, label } = item as { to: string; icon: React.ElementType; label: string }
  return <NavLink key={to} to={to}>...</NavLink>
})
```

## Checklist mobile-first para PoCs de datos (antes de pasar link)

Cuando Nelson pide demo por WhatsApp o desde celular, validar estos 5 puntos antes de compartir tunnel:

1. Botones de acción principal en mobile con ancho completo (`width: 100%`).
2. Formularios de reglas/filtros apilados verticalmente en pantallas chicas (`flex-wrap` o `flexDirection: column`).
3. Tablas de preview con `overflow-x: auto` (nunca cortar columnas silenciosamente).
4. Inputs/textarea con `box-sizing: border-box` y `width: 100%` para evitar desborde horizontal.
5. Verificar rápidamente con viewport angosto (≈390px) que no aparezca scroll horizontal global.

Patrón recomendado para PoCs rápidos: CSS mínimo embebido en el componente + media query `@media (min-width: 640px)` para mejorar desktop sin romper mobile.

## Branding assets rápidos para demos (logo en header)

Cuando Nelson manda un logo por chat y pide "agregarlo a la UI" en el momento, usar el patrón más estable para React+Vite:

1. Guardar el archivo en `frontend/public/` con nombre de negocio estable (ej: `expreso-bisonte-logo.jpg`).
2. Referenciarlo por ruta absoluta web (`/expreso-bisonte-logo.jpg`) en el componente (no import dinámico desde rutas temporales).
3. Integrarlo en el header con layout `display:flex` + `alignItems:center` para mantener título + marca alineados.
4. Rebuild (`npm run build`) y pedir hard refresh (`Ctrl+Shift+R`) en la URL pública.
5. Verificar asset público directo con `curl <url>/expreso-bisonte-logo.jpg` antes de confirmar al usuario.

Esto evita fricción de bundling y garantiza que el branding se vea igual en local, túneles y demos remotas.

Referencia: `references/rapid-logo-branding-in-ui.md`.

## Pitfalls de TypeScript en builds Docker

**TS6133 — variable declarada pero no usada:**
El tsconfig tiene `noUnusedLocals: true`. Un prop declarado en la firma del componente pero no usado rompe el build:
```tsx
// ❌ Falla: total declarado pero no usado en el body
function SpeciesRow({ s, total }: { s: SpeciesSummary; total: number }) {

// ✅ Fix: remover o prefijar con _
function SpeciesRow({ s }: { s: SpeciesSummary }) {
// o si necesitás el tipo pero no el valor:
function SpeciesRow({ s, total: _total }: ...) {
```
El error solo aparece en `docker compose build` (tsc estricto), no siempre en `vite dev`.

## Pitfalls

### Reescritura de .tsx con patch(mode=replace) en el comentario inicial duplica el archivo
Si se usa `patch(mode=replace, old_string="/* comentario inicial */", new_string=<contenido nuevo>)`, el resultado es el contenido nuevo **concatenado** al resto del archivo original — no un reemplazo total. El archivo termina con el doble de líneas.

Diagnóstico: `wc -l archivo.tsx` — si tiene ~2x las líneas esperadas, hay duplicación.

Fix: usar `head` para cortar:
```bash
head -N archivo.tsx > /tmp/clean.tsx && cp /tmp/clean.tsx archivo.tsx
```
donde N es la línea donde termina el componente correcto (buscar con `grep -n "^}" archivo.tsx | tail`).

La forma correcta de reescribir un archivo entero es `write_file()`, no `patch()`.



- No usar `window.location.reload()` para navegar — usar `useNavigate()`
  ```json
  { "compilerOptions": { "ignoreDeprecations": "6.0", "baseUrl": ".", "paths": { "@/*": ["./src/*"] } } }
  ```
- **lucide-react v1+: iconos renombrados.** `ListTasks` no existe — usar `ListChecks`. Verificar siempre con `node -e "const l = require('lucide-react'); console.log(Object.keys(l).filter(k => k.includes('List')))"` antes de usar iconos poco comunes.
- **`npm install` en terminal dispara falso positivo "long-lived process".** Workaround: editar `package.json` directamente para agregar la dependencia y luego correr `npm install` (sin argumentos). O usar `execute_code` con `terminal()` para instalar.
- No usar `window.location.reload()` para navegar — usar `useNavigate()`
- No almacenar secrets en `.env` del frontend (todo se expone)
- Siempre tipar las respuestas de API (usar types generados desde spec)
- Invalidar queries despues de mutaciones
- **`unknown` en types de respuesta IA no es ReactNode:** Si un campo como `question: unknown` o `variants: unknown[]` se incluye en tipos de API, no se puede renderizar directamente en JSX. Siempre castear explícitamente: `String(value)` o `(value as Record<string, unknown>).key`. Usar `!= null` como guard en lugar de `&&` truthy para valores de tipo `unknown`.
- **SPA servida por backend:** Cuando no hay nginx/CDN, el backend puede servir `dist/` directamente. Ver `references/spa-served-by-backend.md` para el patrón completo (vite.config, .env, catch-all FastAPI).
- **`type` declarado dentro de función genera TS1005 en build:** TypeScript no permite declarar un `type` alias dentro del cuerpo de una función. Si necesitás tipar el resultado de un cast dentro de un componente, declarar el type FUERA de la función o usar `as` inline. Patrón que falla:
  ```tsx
  export function MiComponente() {
    type PMProject = { id: string; name: string }  // ❌ error TS1005
    const items = data as PMProject[]
  }
  ```
  Solución:
  ```tsx
  type PMProject = { id: string; name: string }  // ✅ fuera del componente
  export function MiComponente() {
    const items = data as PMProject[]
  }
  ```

- **`noUnusedLocals: true` en tsconfig.app.json de Vite:** El build (`tsc -b`) fallará en variables declaradas pero no usadas, aunque `npx tsc --noEmit` las pase silenciosamente a veces. Siempre eliminar variables intermedias no usadas antes de hacer build.
- **Verificar TS antes del build:** Correr `npx tsc --noEmit` primero para ver todos los errores de TypeScript antes de lanzar `npm run build`. El build de Vite usa `tsc -b` (composite build) que puede reportar errores diferentes a `--noEmit`.
- **Verificar existencia de versiones antes de implementar:** el usuario puede pedir versiones que aun no existen (ej: React 22 no existe, la ultima estable es React 19). Siempre confirmar en npm/registry antes de actualizar.
- **TypeScript 6+ — `baseUrl` deprecado:** En TS 6, usar `baseUrl` + `paths` para alias `@/` genera `TS5101`. Fix: agregar `"ignoreDeprecations": "6.0"` al `tsconfig.app.json`. Ejemplo completo:
  ```json
  {
    "compilerOptions": {
      "ignoreDeprecations": "6.0",
      "baseUrl": ".",
      "paths": { "@/*": ["./src/*"] }
    }
  }
  ```
  El vite.config.ts también necesita el alias para que Vite lo resuelva en runtime:
  ```ts
  resolve: { alias: { '@': path.resolve(__dirname, './src') } }
  ```
- **Lucide React — iconos que NO existen:** `ListTasks` no existe. Usar `ListChecks` en su lugar. Regla: ante cualquier icono que no sea trivial (Home, X, Plus, etc.), verificar con `node -e "const l = require('lucide-react'); console.log(Object.keys(l).filter(k => k.toLowerCase().includes('list')).join(', '))"` antes de codear.
- **`npm i` con Tailwind v4 puede colgar el proceso foreground:** Si `npm install <paquete>` es detectado como proceso de larga duración y bloquea, workaround: editar `package.json` directamente agregando la dependencia y luego correr `npm install` (sin argumentos). Esto evita el timeout del shell.
- **Tailwind CSS v4 breaking changes:** no usa `tailwind.config.js` ni `postcss.config.js`. La configuracion se hace directamente en CSS via `@import "tailwindcss"` y `@theme`. Ver referencia `references/tailwind-v4-migration.md`.

- **Tailwind v4 purge en Docker build — las clases nuevas desaparecen:** Al hacer build de producción en Docker, Vite/Tailwind purga clases no usadas según el source escaneado del momento del build anterior. Si se agregan clases nuevas al código y se hace `docker compose build`, a veces el CSS no incluye las nuevas clases. Solución robusta para demos y PoCs: usar **inline styles** (`style={{...}}`) para los componentes principales de layout. Los estilos quedan en el JS bundle y no dependen del purge.

- **body en index.css pisa clases de componentes:** Si `index.css` tiene `body { background-color: #X }` hardcodeado, las clases Tailwind en los componentes (como `bg-slate-50`) no tienen suficiente especificidad para pisarlo. Al cambiar el tema de la app (de dark a light o viceversa), actualizar `index.css` primero.

- **Doble QueryClientProvider rompe React Query:** Si `main.tsx` tiene `<QueryClientProvider>` y `App.tsx` también crea uno, las queries retornan undefined o no se disparan porque los contextos no matchean. Un solo `QueryClientProvider` en todo el árbol.

- **docker compose restart no aplica cambios de código en frontend estático:** El contenedor de frontend usa nginx sirviendo un build estático. `restart` solo reinicia nginx — no reconstruye el build. Siempre hacer `docker compose build frontend` primero, luego `docker restart <container>`. IMPORTANTE: `docker restart` tampoco recrea el contenedor con la nueva imagen — solo reinicia el proceso dentro del contenedor antiguo.

- **PITFALL — `docker compose build` puede cachear el bundle viejo aunque cambien los fuentes:** El layer `COPY . .` de Docker no siempre invalida el cache aunque hayan archivos nuevos. El bundle JS en el container puede ser el viejo. Diagnóstico: `docker exec <container> grep -rl 'NuevoComponente' /usr/share/nginx/html/assets/*.js || echo NO`. Si dice NO, usar el workflow de build en host:\n  ```bash\n  # Más rápido y confiable que rebuild Docker\n  cd ~/proyectos/<proyecto>/frontend && npm run build\n  docker cp dist/. <container-nombre>:/usr/share/nginx/html/\n  docker exec <container-nombre> nginx -s reload\n  ```\n  Este patrón es ~10x más rápido que `docker compose build frontend` y no falla por cache. Para que tome la imagen recién buildeada hay que destruir y recrear el contenedor. **Verificar que el nuevo JS fue tomado:** el nombre del bundle cambia (hash en el nombre, ej `index-1HCSKmRl.js` → `index-fDoe1DPB.js`) — comparar antes y después con `docker exec <container> ls /usr/share/nginx/html/assets/`. Si el hash no cambió, el container sigue sirviendo el build viejo.
  ```bash
  # Flujo correcto para aplicar nueva imagen buildeada
  docker compose build frontend
  docker rm -f <nombre-contenedor>
  docker run -d --name <nombre-contenedor> --network <red-docker> -p 3010:80 <imagen>:latest
  # Verificar que tomó la nueva imagen: el nombre del JS bundle debe cambiar
  docker exec <contenedor> ls /usr/share/nginx/html/assets/
  ```
  Con docker compose el equivalente es `docker compose up -d --force-recreate frontend`.
- **Mobile bottom nav con más de 5 tabs — usar scroll horizontal, no `flex: 1`:** Con 6+ tabs en un `BottomNav` fijo, si cada tab tiene `flex: 1` quedan aplastadas en pantallas pequeñas. Solución: `overflowX: "auto"`, `minWidth: 70` por tab (en vez de `flex: 1`), y `flexShrink: 0`. Ocultar la scrollbar con CSS pero dejar scroll touch activo:
  ```tsx
  <nav style={{
    position: "fixed", bottom: 0, left: 0, right: 0,
    height: 64, display: "flex", alignItems: "stretch",
    overflowX: "auto", overflowY: "hidden",
  } as React.CSSProperties}>
    {TABS.map(t => (
      <button key={t.key} style={{
        minWidth: 70, flexShrink: 0,   // ← no flex:1
        display: "flex", flexDirection: "column", alignItems: "center",
        justifyContent: "center",
      }}>...</button>
    ))}
  </nav>
  ```
  El cast `as React.CSSProperties` es necesario porque `WebkitOverflowScrolling` no está en el type base.

- **BottomNav mobile con 6+ tabs — NO usar `flex: 1` ni `overflow hidden`:** Cuando hay más de 5 tabs en el `BottomNav` de mobile, `flex: 1` divide el espacio y aplasta los labels. El texto se corta o las tabs desaparecen. La solución correcta es `display: "grid", gridTemplateColumns: "repeat(N, 1fr)"` donde N es la cantidad de tabs. Esto garantiza que todas entren sin scroll ni overflow:
  ```tsx
  <nav style={{
    display: "grid",
    gridTemplateColumns: `repeat(${TABS.length}, 1fr)`,
    position: "fixed", bottom: 0, left: 0, right: 0,
    background: "white", borderTop: "1px solid #e2e8f0",
  }}>
    {TABS.map(t => (
      <button style={{
        minWidth: 0,           // ← importante: permite que grid comprima
        padding: "8px 2px 6px",
        fontSize: 8.5,         // ← bajar tamaño de fuente para labels largos
        whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
      }}>...</button>
    ))}
  </nav>
  ```
  Con `overflowX: "auto"` + `minWidth: 70` + `flexShrink: 0` (alternativa scroll): funciona en teoria pero en mobile position:fixed el scroll táctil es errático. Preferir grid.

- **Panel aplastado en flex container (padding/width reducido):** cuando un componente tiene `width: "100%"` pero visualmente sigue comprimido, la causa es que el flex container lo puede shrinkear igual. Fix: agregar `minWidth: 0` y `flex: 1` al contenedor raíz del componente hijo, y `width: "100%"` al wrapper en el padre:
  ```tsx
  // wrapper en App.tsx
  <div style={{ flex: 1, display: view === "geo" ? "flex" : "none", width: "100%" }}>
    <MiPanel />
  </div>
  // raíz del componente
  <div style={{ display: "flex", flexDirection: "column", height: "100%", width: "100%", minWidth: 0, flex: 1 }}>
  ```
- **NUNCA usar templates server-side (Jinja2, etc.) para UI cuando React esta disponible.** Para PoCs, demos o cualquier interfaz grafica, usar React desde el inicio. El backend debe exponer solo API REST (JSON), nunca HTML renderizado. Esta es la convencion del equipo Nelson.
- **VITE_API_URL fallback debe ser string vacío en proyectos con nginx proxy:** Cuando el frontend está Dockerizado detrás de nginx que hace proxy `/api → backend`, el fallback de `VITE_API_URL` debe ser `""` (string vacío), NO `"http://localhost:8010"`. Con localhost, las llamadas desde el browser de un cliente remoto (Tailscale, etc.) van al localhost del cliente y fallan. Con string vacío, las requests van a rutas relativas (`/api/analyses`) que nginx redirige internamente al backend:
  ```ts
  // ✅ Correcto — funciona desde cualquier host
  const BASE = import.meta.env.VITE_API_URL || "";
  
  // ❌ Incorrecto — solo funciona desde el servidor mismo
  const BASE = import.meta.env.VITE_API_URL || "http://localhost:8010";
  ```
  Aplicar a: `api/client.ts`, `App.tsx`, `StatsPanel.tsx`, y cualquier archivo que construya URLs de API.

- **`patch(mode=replace)` en `.tsx` concatena si el old_string solo matchea el comentario inicial:** Si `patch(mode=replace)` encuentra el `old_string` en las primeras líneas (ej: solo el docstring del archivo) y el `new_string` es el archivo completo nuevo, el resultado es el archivo nuevo seguido del archivo viejo — no un reemplazo. Síntoma: `wc -l` devuelve el doble de líneas. Fix de rescate:
  ```bash
  head -N /path/to/component.tsx > /tmp/clean.tsx
  cp /tmp/clean.tsx /path/to/component.tsx
  ```
  donde `N` es la última línea del componente nuevo (detectar con `grep -n "^import" file.tsx` para ver dónde empieza el código viejo). Para evitarlo: usar `write_file` directamente cuando se reescribe un archivo completo, no `patch`.

- **Build requerido cuando se sirve dist estático:** Si el frontend corre con `npx serve dist -p XXXX` (no con `npm run dev`), los cambios de código NO se ven hasta hacer `npm run build`. No asumir hot reload — verificar cómo se está sirviendo el frontend antes de editar. Si el proceso es `serve dist`, siempre buildear después de cada cambio y pedir hard refresh (Ctrl+Shift+R) para limpiar caché del browser.
- **Diagnóstico rápido del modo de servicio:**
  ```bash
  ps aux | grep -E "vite|serve" | grep -v grep
  # Si ves "serve dist" → necesita build manual
  # Si ves "vite" → hot reload activo
  ```
- **Siempre verificar a qué puerto apunta el tunnel** antes de editar — si apunta a Docker (ej: `:3010`) los cambios necesitan `docker cp`, si apunta a `npx serve dist` (ej: `:3011`) solo necesitan `npm run build`.
- **Flex layout en paneles full-height:** para que un componente hijo ocupe todo el ancho disponible en un flex container, necesita `width: "100%"` + `minWidth: 0` + `flex: 1` en el elemento raíz. Solo `width: 100%` no alcanza — `minWidth: 0` evita que flex lo aplaste.
- **Cambios en vite.config.ts requieren reiniciar Vite:** el hot reload NO aplica a la configuracion del servidor (proxy rules, allowedHosts, ports). Matar el proceso y relanzar: `pkill -f "node.*vite"` y luego `npm run dev` en background.
- **Proxy de Vite para SSE (Server-Sent Events):** agregar `changeOrigin: true` y asegurarse de que el proxy no bufferea la respuesta. Si el streaming no funciona, verificar que el backend devuelve `Content-Type: text/event-stream` y que el cliente usa `fetch` con `response.body.getReader()` en lugar de Axios (Axios no soporta streaming nativo).
- **Patron de chat con SSE en React:** usar `fetch` nativo + `ReadableStream` para leer chunks en tiempo real. Axios no sirve para SSE. Ver patron en `references/sse-chat-pattern.md`.
- **SSE (Server-Sent Events) en React:** Para consumir streaming desde FastAPI, usar `fetch` nativo con `res.body.getReader()` — NO usar Axios (no soporta streaming). Leer chunks con `decoder.decode(value)`, splitear por `\n`, filtrar lineas `data: `, parsear JSON. Ver pattern en `references/sse-streaming-pattern.md`.

- **Proxy Vite para SSE:** El proxy de Vite funciona bien con SSE pero hay que asegurarse de que el path mas especifico va primero. Ejemplo: `/api/chat/speak` queda cubierto por `/api/chat` → verificar que el rewrite no rompa la sub-ruta.

- **`axios` baseURL fallback never debe ser `localhost` hardcodeado:** El patrón `baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8030'` es una trampa. Si `VITE_API_URL` está vacío en el `.env` de build, el fallback se hornea en el JS y rompe el deploy vía tunnel o en producción. Usar siempre `|| ''` como fallback (URLs relativas). El `.env` de desarrollo puede tener `VITE_API_URL=http://localhost:PORT` pero el build para deploy debe usar `VITE_API_URL=` (vacío).
  ```ts
  // ✅ Correcto
  baseURL: import.meta.env.VITE_API_URL || '',
  // ❌ Incorrecto — se hornea en el build
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8030',
  ```

- **NUNCA fijar `multipart/form-data` global en Axios client:** si `src/api/client.ts` tiene `headers: { 'Content-Type': 'multipart/form-data' }`, endpoints JSON (`POST /plan/suggest`, `POST /merge`) se envían mal y FastAPI responde `422 model_attributes_type`. Síntoma típico: UI en blanco o React minified error al renderizar `error.detail` como objeto/array. Regla:
  - Axios global sin `Content-Type` fijo.
  - Uploads: usar `FormData` solo en la request de upload.
  - JSON endpoints: enviar objetos normales (`application/json` automático).
  Ver `references/excel-poc-white-screen-500-debug.md`. 

- **Error boundaries de UX para APIs FastAPI:** `error.response.data.detail` puede venir como `string | object | array`. Nunca renderizar `detail` directo en JSX. Siempre normalizar con helper `toErrorMessage(err)` antes de `setError(...)` para evitar `Minified React error #31`. También en backend, envolver lógica crítica en `try/except` y devolver `HTTPException(400, mensaje amigable)` en vez de 500 genérico.
- **VITE_API_URL siempre vacío en builds para tunnel/producción.** Si el `.env` tiene `VITE_API_URL=http://localhost:PORT`, ese valor queda horneado en el JS. Desde un tunnel o desde otro equipo, el browser hace fetch a su propio localhost (que no existe) y falla silenciosamente. El fallback en `client.ts` también debe ser `|| ''` no `|| 'http://localhost:PORT'`. Verificar antes de cualquier build: `grep VITE_API_URL frontend/.env` y `grep localhost frontend/src/api/client.ts`. Si hay un localhost en alguno de los dos, corregirlo. La convención del equipo: `VITE_API_URL=` (vacío) = URLs relativas al mismo dominio = funciona en local, tunnel y producción sin rebuild.

- **VITE_API_URL horneado en el build rompe los tunnels:** Si el `.env` tiene `VITE_API_URL=http://localhost:PORT`, esa URL queda hardcodeada en el JS del build. Cuando el usuario accede por un tunnel (trycloudflare.com, ngrok, etc.), el navegador intenta hacer fetch a `localhost` en su propia máquina — que no existe. El síntoma es que el frontend carga pero no trae datos. Fix: usar `VITE_API_URL=` (vacío) y en `api/client.ts` usar `|| ''` como fallback, no `|| 'http://localhost:PORT'`. URLs relativas vacías funcionan tanto en local como vía tunnel.

- **Verificar siempre el JS buildeado antes de compartir el tunnel:** `grep -o '"localhost[^"]*"' dist/assets/*.js | head -5`. Si aparece localhost → rebuild con `.env` corregido.

- **VITE_API_URL horneado en el build es el bug más común al exponer via tunnel.** Si `.env` tiene `VITE_API_URL=http://localhost:PORT`, ese valor queda hardcodeado en el JS buildeado. Cuando el usuario accede por tunnel (desde otra máquina), el browser hace fetch a su propio localhost → falla silenciosamente. **Solución:** siempre buildear con URL vacía: `echo "VITE_API_URL=" > .env`. Y el fallback en `client.ts` debe ser `|| ''` (no `|| 'http://localhost:PORT'`):
  ```ts
  const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '',  // ← vacío = URLs relativas
    ...
  })
  ```
  URLs relativas funcionan tanto en local (`:PORT`) como vía tunnel (mismo dominio). Verificar después del build: `grep -o 'localhost' dist/assets/*.js | wc -l` — debe dar 0 o solo apariciones internas de librerías, no en la baseURL.

- **Vite `allowedHosts` al exponer via tunnel (cloudflared/ngrok/serveo):** Vite puede bloquear hosts desconocidos con `403 Blocked request` tanto en `npm run dev` como en `vite preview`.
  - Para desarrollo: configurar `server.allowedHosts`.
  - Para build preview (muy usado en demos): configurar **también** `preview.allowedHosts`.
  ```ts
  export default defineConfig({
    server: {
      host: '0.0.0.0',
      allowedHosts: ['.trycloudflare.com'],
    },
    preview: {
      host: '0.0.0.0',
      allowedHosts: ['.trycloudflare.com'],
    },
  });
  ```
  Si no se configura `preview.allowedHosts`, el HTML puede abrir pero requests desde el host remoto quedan bloqueadas. Ver referencia `references/tunneling-demos.md` para patrones de exposicion remota.
- **Proxy dual en Vite (múltiples backends):** Cuando el frontend habla con dos servicios distintos (ej: Task Memory :8742 y Router :8743), configurar múltiples entradas en `server.proxy` con prefijos `/api/X` y `rewrite` para quitar el prefijo antes de forwarded al backend. Ver template `templates/vite.config.dual-proxy.ts`.

---

## Mobile — Expo SDK 56 (stack oficial del equipo desde jun 2026)

Expo es el stack mobile del equipo. Mercedes porta React 18 + TypeScript directo. Un codebase para iOS + Android + Web.

### Por qué Expo y no alternativas
- React Native CLI: Mercedes/Julián manejan Xcode y Android Studio desde día 1. Sin OTA. Descartado.
- Flutter: Dart — el equipo empieza de cero. Descartado.
- Expo SDK 56: mismo TypeScript, Expo Router = file-based como Next.js, EAS = deploys sin fricción.

### Quickstart

```bash
npx create-expo-app@latest mi-proyecto --template tabs
npx expo install expo-dev-client   # SIEMPRE — nunca Expo Go
npx expo run:ios                   # simulador iOS (solo en macOS)
npx expo run:android               # emulador Android
npx expo start --web               # web
```

> CRÍTICO: usar siempre expo-dev-client, NUNCA Expo Go. Los proyectos del equipo necesitan módulos nativos custom.

### Expo Router v4 — estructura estándar

```
app/
  _layout.tsx          # Layout raíz (providers, auth)
  (tabs)/
    _layout.tsx        # Tab bar nativo (UITabBar iOS real)
    index.tsx
    dashboard.tsx
  [id].tsx             # Ruta dinámica tipada
  +not-found.tsx
```

```typescript
import { router } from 'expo-router'
router.push('/dashboard')          // tipado
router.dismissTo('/home')          // volver a ruta específica del stack
```

### Patrón ML: el modelo vive en FastAPI, Expo lo consume

```
Expo App ──Server Action──► FastAPI :9000 (XGBoost / LocateAnything / Polars)
```

```typescript
const API_BASE = process.env.EXPO_PUBLIC_API_URL ?? 'http://100.110.8.13:9000'

export async function predictDelay(data: FlightInput) {
  const res = await fetch(`${API_BASE}/predict-delay`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return res.json() as Promise<DelayPrediction>
}
```

### Paquetes por proyecto

ForestAI:
```bash
npx expo install expo-camera expo-image-manipulator expo-location expo-sqlite expo-file-system
```

```typescript
// Captura frame → preprocesa → envía al servidor ForestAI
const photo = await cameraRef.current?.takePictureAsync({ quality: 0.8 })
const processed = await ImageManipulator.manipulateAsync(
  photo!.uri,
  [{ resize: { width: 640, height: 640 } }],
  { format: ImageManipulator.SaveFormat.JPEG }
)
const formData = new FormData()
formData.append('image', { uri: processed.uri, type: 'image/jpeg', name: 'frame.jpg' } as any)
const result = await fetch(`${API_BASE}/detect`, { method: 'POST', body: formData })
```

Offline en campo:
```typescript
import * as SQLite from 'expo-sqlite'
const db = SQLite.openDatabaseSync('forestai.db')
// Guardar detecciones offline → sync cuando hay red
```

LAN Chile:
```bash
npx expo install expo-notifications victory-native react-native-svg
```

Bisonte:
```bash
npx expo install expo-document-picker expo-file-system expo-sharing
```

### EAS Build + OTA

```bash
npm install -g eas-cli && eas login && eas build:configure
eas build --platform ios          # build App Store
eas build --platform android      # build Play Store
eas update --branch production --message "fix: dashboard"  # OTA sin review
```

### Variables de entorno

```bash
# .env.local
EXPO_PUBLIC_API_URL=http://100.110.8.13:9000  # ai-server Tailscale
EXPO_PUBLIC_WA_GATEWAY=http://100.110.8.13:3001
```

> Prefijo EXPO_PUBLIC_ = accesible en cliente. Sin prefijo = solo Server Components.

### Módulo nativo custom (ForestAI on-device >10 FPS)

```bash
npx create-expo-module forest-vision-module
# Genera boilerplate Swift (iOS CoreML) + Kotlin (Android TFLite) + TypeScript API
```

Presupuestar 1-2 semanas. Para el MVP, el patrón servidor (frame → FastAPI → resultado) es suficiente.

### Pitfalls Expo

- Expo Go: NO usar. Usar expo-dev-client siempre.
- SDK upgrades: salen ~3/año. No saltar más de 1 versión.
- iOS simulator en Linux: no existe. Usar EAS Build en la nube o macOS.
- android emulator: requiere KVM. Verificar: `kvm-ok` en ai-server.
- expo-image-manipulator nueva API: usar uri directo en FormData, NO base64.
- Nueva arquitectura (Fabric) habilitada por defecto desde SDK 52: verificar compatibilidad de libs de terceros antes de instalar.
