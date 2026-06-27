# Bisonte UI — Navbar y Logo

## Ubicación del logo
El logo real de Bisonte está en múltiples paths del proyecto:
- `/home/server/proyectos/excel-merger-poc/backend/static/expreso-bisonte-logo.jpg`
- `/home/server/proyectos/excel-merger-poc/backend/app/static/expreso-bisonte-logo.jpg`
- `/home/server/proyectos/excel-merger-poc/frontend/dist/expreso-bisonte-logo.jpg`
- `/home/server/proyectos/excel-merger-poc/frontend/public/expreso-bisonte-logo.jpg`

Referencia desde el frontend: `src="/expreso-bisonte-logo.jpg"` (sirve el backend static).

## Pitfall crítico — Rediseño de navbar
Cuando se hace un rediseño de UI que incluye un navbar nuevo, el logo existente
en `renderHeader()` puede quedar tapado o reemplazado por un placeholder genérico.

**Patrón que falló:** se creó un navbar con `<div>B</div>` como placeholder, ignorando
que el logo real ya existía en `renderHeader()` line ~633.

**Patrón correcto:**
1. Antes de crear un navbar nuevo, buscar el logo existente:
   `grep -n "logo\|expreso-bisonte" HomePage.tsx`
2. Usar el logo real desde el primer momento:
```tsx
<img
  src="/expreso-bisonte-logo.jpg"
  alt="Expreso Bisonte"
  style={{ height: 38, width: 'auto', borderRadius: '6px', objectFit: 'contain' }}
/>
<span style={{ fontWeight: 700, fontSize: '1rem', color: '#f1f5f9' }}>
  Bisonte <span style={{ color: '#3b82f6' }}>IA</span>
</span>
```

## Tema oscuro actual (jun 2026)
- Background: `#0f172a`
- Cards/panels: `#1e293b`
- Borders: `#334155`
- Texto: `#f1f5f9` / `#e2e8f0`
- Acento azul: `#3b82f6`
- Acento naranja: `#f97316`
- Fuente: Inter (Google Fonts)

## Navbar fijo
El navbar está en `position: fixed, top: 0, zIndex: 100`. El contenido debajo
necesita `paddingTop: '64px'` para no quedar tapado.
