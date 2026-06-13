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
