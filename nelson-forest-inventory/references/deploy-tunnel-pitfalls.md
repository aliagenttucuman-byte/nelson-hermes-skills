# ForestAI Deploy & Tunnel Pitfalls

## Arquitectura real de ports/tunnels (2026-05-23)

| Port | Sirve | Tunnel CF | Código fuente |
|------|-------|-----------|---------------|
| 3010 | Docker nginx (`forestai-poc-frontend-1`) | `pins-mountains-doom-washington.trycloudflare.com` | `~/proyectos/forestai-poc/frontend/` |
| 3011 | `npx serve dist` estático | `controversy-email-toward-athens.trycloudflare.com` | `~/proyectos/forestai-3d/frontend/` |
| 3012 | `npx serve dist` estático | — | `~/proyectos/forestai-poc/frontend/dist/` |

## Pitfall crítico: cambios no visibles en el tunnel principal

**Problema**: El tunnel que Pablo y usuarios externos usan apunta al port 3010 (Docker).
Si hacés cambios en `forestai-3d/frontend/` y buildeas, los cambios **NO se ven** en el tunnel.

**Fix obligatorio después de cada build**:
```bash
cd ~/proyectos/forestai-3d/frontend
npm run build
docker cp dist/. forestai-poc-frontend-1:/usr/share/nginx/html/
```

**Siempre verificar** en qué tunnel está el usuario antes de deployar:
```bash
cat /tmp/cf_forestai.log | grep trycloudflare | head -3
```

## Build estático sin hot reload

El frontend se sirve como `dist/` compilado. No hay dev server con hot reload.
Cambios en `.tsx` requieren:
1. `npm run build` (tarda ~5s)
2. Si aplica: `docker cp` al container
3. Hard refresh en browser: **Ctrl+Shift+R**

Sin Ctrl+Shift+R el browser sirve versión cacheada aunque el dist ya cambió.

## Pitfall crítico: Docker build vs restart — cuándo usar cada uno

El `Dockerfile` del frontend hace `npm run build` **dentro del container** (`COPY . . && RUN npm run build`).
Esto significa:

| Acción | ¿Incluye cambios de código? |
|--------|----------------------------|
| `docker restart <container>` | ❌ No — re-usa el layer cacheado del build anterior |
| `docker compose up -d --force-recreate` | ❌ No — recrea con la misma imagen |
| `docker compose build frontend` + `up -d --force-recreate` | ✅ Sí — reconstruye imagen desde fuente |

**Secuencia correcta para deployar cambios de código al container frontend:**
```bash
cd ~/proyectos/forestai-poc
docker compose build frontend        # rebuild image con nuevo código
docker compose up -d --force-recreate frontend  # recrear container con nueva imagen
sleep 3 && curl -s -o /dev/null -w "%{http_code}" http://localhost:3010/  # verificar 200
```

**Verificar que el JS nuevo llegó al container:**
```bash
docker exec forestai-poc-frontend-1 grep -rc "NombreComponente" /usr/share/nginx/html/assets/
# Si devuelve 0 o vacío → el build viejo está adentro → hacer docker compose build
```

## Bottom nav mobile con 6+ tabs — usar grid no flex

Con `display: flex` en un `position: fixed` nav y 6 tabs, los botones se comprimen hasta quedar
invisibles en pantallas de 390px (iPhone). Ni `overflowX: auto` ni `minWidth` fijo lo resuelven
de forma confiable en mobile.

**Solución correcta: `display: grid, gridTemplateColumns: repeat(N, 1fr)`**
```tsx
<nav style={{
  display: "grid",
  gridTemplateColumns: "repeat(6, 1fr)",
  position: "fixed", bottom: 0, left: 0, right: 0,
  background: "white", borderTop: "1px solid #e2e8f0",
}}>
  <button style={{ minWidth: 0, display: "flex", flexDirection: "column",
    alignItems: "center", padding: "8px 2px 6px" }}>
    <span style={{ fontSize: 18 }}>{icon}</span>
    <span style={{ fontSize: 8.5, whiteSpace: "nowrap", overflow: "hidden",
      textOverflow: "ellipsis", maxWidth: "100%", padding: "0 2px" }}>{label}</span>
  </button>
</nav>
```
`minWidth: 0` en el botón es clave — sin él el grid no puede achicarlo.

## React Flex Layout — padding aplastado

Cuando un panel tiene `width: "100%"` pero visualmente sigue aplastado en un flex container:

```tsx
// ❌ Insuficiente — el flex container puede aplastar igual
<div style={{ width: "100%", height: "100%" }}>

// ✅ Correcto — minWidth: 0 previene el shrink, flex: 1 expande
<div style={{ width: "100%", height: "100%", minWidth: 0, flex: 1 }}>
```

También verificar que el **wrapper padre** en App.tsx tenga `width: "100%"`:
```tsx
<div style={{ flex: 1, display: view === "geo" ? "flex" : "none", overflow: "hidden", width: "100%" }}>
  <GeoPanel />
</div>
```

Sin `width: "100%"` en el wrapper, el hijo no sabe cuánto espacio tomar.
