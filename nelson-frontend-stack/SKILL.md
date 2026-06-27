---
name: nelson-frontend-stack
title: Frontend Stack - React + TypeScript + Vite + Tailwind
description: Stack frontend estandar del equipo Nelson. React 18, TypeScript, Vite, Tailwind CSS, React Query, Axios, React Router DOM. Convenciones de carpetas, hooks, patterns.
skill: nelson-frontend-stack
author: equipo-nelson
version: 1.0.0
keywords: [react, typescript, vite, tailwind, react-query, axios, frontend]
dependencies: []
---

# Frontend Stack - Equipo Nelson

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
| Charts | Recharts | ^3.8 |
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

## UI Design — Feedback Primero

Nelson rechazó una UI completa rediseñada sin su input con "no me gusta para nada". Regla:

1. Antes de rediseñar una UI, pedir: screenshot actual + estilo deseado (minimalista, GIS técnico, dashboard con cards, mapa flotante, etc.)
2. Si no puede mandar screenshot (servidor sin pantalla), describir las opciones concretas y dejar que elija.
3. No asumir que un dark theme genérico va a satisfacer — preguntar primero.

## Referencias de soporte

- `references/dashboard-mapa-websocket-chat.md` — Template completo: dashboard React con Leaflet + WebSocket live + chat IA flotante (validado FleetOptimizer PoC)
- `references/css-overlay-redesign-legacy-inline.md` — Rediseño visual completo de PoC con inline styles legacy sin tocar JSX. Inyectar `design-system.css` global + override por selectores de atributo (`div[style*="background: rgb(255, 255, 255)"]`). Validado en Bisonte (1341 LoC HomePage.tsx, 0 líneas de lógica tocadas).
- `references/css-overlay-reskinning.md` — Rediseño visual de apps React con inline styles masivos SIN tocar JSX. Patrón overlay CSS via attribute selectors `[style*="..."]`. Estilo Linear × Bloomberg incluido (validado Bisonte PoC jun 2026).
- `references/css-overlay-reskin.md` — Re-skin completo de un componente React con cientos de inline styles SIN tocar JSX, usando CSS attribute selectors + design tokens. Patrón "Linear × Bloomberg" para apps operativas (Bisonte). Reversible borrando 1 import.
- `references/excel-pipeline-operational-mode.md` — Guía de UI mínima operativa para pipelines Excel (sin IA/demo), con foco en conteo de filas útiles.
- `references/excel-poc-white-screen-500-debug.md` — Postmortem corto: pantalla blanca por Axios multipart global + 500 en merge encadenado; fixes y checks de verificación.
- `references/white-screen-triage-cloudflare.md` — Runbook rápido para "pantalla blanca" en demos por tunnel (verificación HTML/JS/API + secuencia de recuperación)
- `references/prompt-first-excel-automation.md` — Patrón UI/API para automatización de Excel orientada a usuarios no técnicos (objetivo en lenguaje natural → plan sugerido → ejecución → guardado de procedimiento).
- `references/prompt-first-workflow-pattern.md` — Patrón para UX no técnica: Objetivo → Plan sugerido → Ejecutar + guardado de procedimientos reutilizables.

## Deploy estático en Docker (nginx)

Cuando el frontend corre como contenedor Docker con nginx (ej: `forestai-poc-frontend-1`), **no hay hot reload**. El flujo correcto para ver cambios:

```bash
# 1. Editar los .tsx en el host
# 2. Build
cd ~/proyectos/forestai-poc/frontend && npm run build
# 3. Copiar dist al container nginx
docker cp dist/. <container-name>:/usr/share/nginx/html/
# 4. Usuario hace Ctrl+Shift+R en el browser
```

⚠️ Trampa frecuente: editar el código, buildear, y asumir que el browser lo levantó — pero el tunnel apunta al container Docker que sigue sirviendo el build viejo. Verificar SIEMPRE a qué puerto apunta el tunnel (`cat /tmp/cf_*.log`) para saber si es Docker o serve estático.

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

## Pitfalls

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

- **docker compose restart no aplica cambios de código en frontend estático:** El contenedor de frontend usa nginx sirviendo un build estático. `restart` solo reinicia nginx — no reconstruye el build. Siempre hacer `docker compose build frontend` primero, luego `docker restart <container>`. IMPORTANTE: `docker restart` tampoco recrea el contenedor con la nueva imagen — solo reinicia el proceso dentro del contenedor antiguo. Para que tome la imagen recién buildeada hay que destruir y recrear el contenedor:
  ```bash
  # Flujo correcto para aplicar nueva imagen buildeada
  docker compose build frontend
  docker rm -f <nombre-contenedor>
  docker run -d --name <nombre-contenedor> --network <red-docker> -p 3010:80 <imagen>:latest
  # Verificar que tomó la nueva imagen: el nombre del JS bundle debe cambiar
  docker exec <contenedor> ls /usr/share/nginx/html/assets/
  ```
  Con docker compose el equivalente es `docker compose up -d --force-recreate frontend`.
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

- **PITFALL — `async function*` (generator) con `await` queda colgado para siempre:** Si una función SSE se declara como `async function*` (con asterisco) pero el consumer la llama con `await fn(...)` sin iterarla con `for await`, el cuerpo del generator **nunca se ejecuta**. El `fetch` no se dispara, el callback no se llama, el chat queda con el spinner girando indefinidamente. Síntoma típico: backend responde 200 con todos los tokens en curl directo, pero la UI nunca recibe nada y el botón send queda en estado loading. **Fix:** si la función usa callback (`onToken`) en vez de `yield`, declararla como `async function` normal sin asterisco. Si usa `yield`, el consumer DEBE usar `for await (const chunk of fn(...))`. Confirmar el fix mirando el hash del bundle `dist/assets/index-<hash>.js` — si cambió tras el rebuild, el código nuevo se desplegó.
  ```js
  // ❌ Bug — generator nunca se ejecuta con await
  chat: async function*(message, history, onToken) {
    const res = await fetch(...)  // nunca llega
    ...
  }
  await api.chat(msg, hist, onToken)  // resuelve instantáneo sin correr nada
  
  // ✅ Fix — función normal con callback
  chat: async function(message, history, onToken) {
    const res = await fetch(...)
    ...
  }
  ```
  Caso real: PoC farmacia (`nelson-farmacia-poc`), 2026-06-25.

- **⚠️ `async function*` con callback = UI colgada sin error.** Si una función SSE usa callback (`onToken`) PERO está declarada como async generator (`async function*` con asterisco), y el componente la llama con `await api.chat(...)` (no con `for await`), el cuerpo NUNCA se ejecuta — `await` resuelve al instante devolviendo el iterator. Fetch jamás se dispara, callback jamás se llama, UI queda esperando para siempre. Backend funciona perfecto vía curl, frontend solo cuelga. Fix: sacar el asterisco. Ver caso farmacia-poc en `references/sse-chat-pattern.md` (sección anti-pattern). Diagnóstico rápido: `grep "async function\*" frontend/src/api*`.
- **SSE (Server-Sent Events) en React:** Para consumir streaming desde FastAPI, usar `fetch` nativo con `res.body.getReader()` — NO usar Axios (no soporta streaming). Leer chunks con `decoder.decode(value)`, splitear por `\n`, filtrar lineas `data: `, parsear JSON. Ver pattern en `references/sse-streaming-pattern.md`.

- **Proxy Vite para SSE:** El proxy de Vite funciona bien con SSE pero hay que asegurarse de que el path mas especifico va primero. Ejemplo: `/api/chat/speak` queda cubierto por `/api/chat` → verificar que el rewrite no rompa la sub-ruta.

- **`axios` baseURL fallback nunca debe ser `localhost` hardcodeado:** El patrón `baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8030'` es una trampa. Si `VITE_API_URL` está vacío en el `.env` de build, el fallback se hornea en el JS y rompe el deploy vía tunnel o en producción. Usar siempre `|| ''` como fallback (URLs relativas). El `.env` de desarrollo puede tener `VITE_API_URL=http://localhost:PORT` pero el build para deploy debe usar `VITE_API_URL=` (vacío).
  ```ts
  // ✅ Correcto
  baseURL: import.meta.env.VITE_API_URL || '',
  // ❌ Incorrecto — se hornea en el build
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8030',
  ```
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

- **Vite `allowedHosts` al exponer via tunnel (cloudflared/ngrok/serveo):** El dev server de Vite bloquea hosts desconocidos con `403 Blocked request`. Si se usa un tunel para demos remotas, agregar `allowedHosts: true` en `vite.config.ts`:
  ```ts
  export default defineConfig({
    server: {
      host: '0.0.0.0',
      allowedHosts: true,  // Permite cualquier host (cloudflared, ngrok, etc.)
    },
  });
  ```
  Alternativa mas restrictiva: listar los hosts explicitos con `allowedHosts: ['xxxx.trycloudflare.com']`.
  Ver referencia `references/tunneling-demos.md` para patrones de exposicion remota.
- **Proxy dual en Vite (múltiples backends):** Cuando el frontend habla con dos servicios distintos (ej: Task Memory :8742 y Router :8743), configurar múltiples entradas en `server.proxy` con prefijos `/api/X` y `rewrite` para quitar el prefijo antes de forwarded al backend. Ver template `templates/vite.config.dual-proxy.ts`.
