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

## Stack

| Capa | Libreria | Version |
|------|----------|---------|
| Framework | React | ^19.0 |
| Build | Vite | ^6.0 |
| Lenguaje | TypeScript | ^5.7 |
| Estilos | Tailwind CSS | ^4.0 |
| Estado servidor | TanStack Query (React Query) | ^5.64 |
| HTTP | Axios | ^1.7 |
| Routing | React Router DOM | ^7.1 |
| UI Components | shadcn/ui (opcional) | latest |
| Iconos | Lucide React | ^0.474 |
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

## Pitfalls

- No usar `window.location.reload()` para navegar — usar `useNavigate()`
- No almacenar secrets en `.env` del frontend (todo se expone)
- Siempre tipar las respuestas de API (usar types generados desde spec)
- Invalidar queries despues de mutaciones
- **Verificar existencia de versiones antes de implementar:** el usuario puede pedir versiones que aun no existen (ej: React 22 no existe, la ultima estable es React 19). Siempre confirmar en npm/registry antes de actualizar.
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
- **NUNCA usar templates server-side (Jinja2, etc.) para UI cuando React esta disponible.** Para PoCs, demos o cualquier interfaz grafica, usar React desde el inicio. El backend debe exponer solo API REST (JSON), nunca HTML renderizado. Esta es la convencion del equipo Nelson.
- **VITE_API_URL fallback debe ser string vacío en proyectos con nginx proxy:** Cuando el frontend está Dockerizado detrás de nginx que hace proxy `/api → backend`, el fallback de `VITE_API_URL` debe ser `""` (string vacío), NO `"http://localhost:8010"`. Con localhost, las llamadas desde el browser de un cliente remoto (Tailscale, etc.) van al localhost del cliente y fallan. Con string vacío, las requests van a rutas relativas (`/api/analyses`) que nginx redirige internamente al backend:
  ```ts
  // ✅ Correcto — funciona desde cualquier host
  const BASE = import.meta.env.VITE_API_URL || "";
  
  // ❌ Incorrecto — solo funciona desde el servidor mismo
  const BASE = import.meta.env.VITE_API_URL || "http://localhost:8010";
  ```
  Aplicar a: `api/client.ts`, `App.tsx`, `StatsPanel.tsx`, y cualquier archivo que construya URLs de API.

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
