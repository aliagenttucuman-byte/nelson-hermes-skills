# Bisonte IA — Dark Theme (jun 2026)

## Paleta aplicada

| Token       | Hex       | Uso                             |
|-------------|-----------|----------------------------------|
| Background  | #0f172a   | Fondo general de la app         |
| Surface     | #1e293b   | Navbar, cards, inputs           |
| Border      | #334155   | Bordes sutiles                  |
| Accent      | #3b82f6   | Botones activos, highlights     |
| Text        | #e2e8f0   | Texto principal                 |
| Muted       | #64748b   | Labels, subtítulos              |
| Success     | #22c55e   | bg: #052e16                     |
| Danger      | #f87171   | bg: #2d0a0a                     |
| Warning     | #fbbf24   | bg: #271d00                     |

## Estructura del layout

- Navbar sticky 56px con logo real
- Content: `maxWidth: 1200px`, `padding: 1.5rem`, centrado
- Cards: border `#334155`, background `#1e293b`, `borderRadius: 12px`
- Stats cards: número grande `1.8rem 800w` + label `uppercase 0.72rem 0.05em tracking`
- Botón ejecutar: `linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)` activo / `#1e293b` deshabilitado

## Tipografía

Inter desde Google Fonts — agregar en `index.html`:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```
fontFamily en root: `"'Inter', 'system-ui', sans-serif"`

## Logo

- Ruta: `/frontend/public/expreso-bisonte-logo.jpg`
- Se sirve como: `/expreso-bisonte-logo.jpg` (vite sirve public/ en raíz)
- En navbar: `<img src="/expreso-bisonte-logo.jpg" style={{ height: 38, borderRadius: '6px' }} />`

## ⚠️ Pitfall: logo perdido en rediseños

Al hacer rediseño de navbar, el logo puede quedar huérfano si se reemplaza el bloque entero.
Siempre buscar ANTES de reescribir:
```bash
find /path/to/project -name "*.jpg" -o -name "*.png" -o -name "*.svg"
grep -n "logo\|img\|src=" frontend/src/pages/HomePage.tsx | head -20
```

## Regla de colores — instrucción explícita del cliente

> "no pintemos todas las filas, sino pintemos la columna correspondiente a la regla"

Coloreo por CELDA, no por fila. Las celdas que se colorean son:
- `DIAS_ATRASO` — rojo si supera tolerancia (tolerancia=0 para sucdest=CC, tolerancia=7 para el resto)
- `OBSERVACIÓN` — rojo si contiene "VER DIF"
- `fechaedit` — rojo si DIAS_ATRASO supera tolerancia

Campo clave para sucursal: `sucdest` (NO `succobro` — ese venía siempre 'BA').

## Archivos modificados en el rediseño

- `frontend/src/pages/HomePage.tsx` — layout principal, navbar, upload zone, stats cards
- `frontend/src/components/ContadoTable.tsx` — tabla con tema oscuro
- `frontend/public/index.html` — Inter font import
- Workflow: `npm run build` → `cp -r dist/* ../backend/static/` → sin reiniciar backend
