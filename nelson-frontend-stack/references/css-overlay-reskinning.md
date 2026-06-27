# CSS Overlay Re-skinning — re-diseñar React apps con inline styles SIN tocar JSX

## Cuándo usar este patrón

Tenés una app React legacy con **inline styles masivos** (`style={{...}}`) repartidos en 1000+ líneas de JSX. Nelson pide rediseño visual urgente para una demo o entrega a cliente. Reescribir todo el JSX a className es:
- Lento (horas)
- Riesgoso (rompe lógica que ya anda)
- Innecesario para una demo

**Solución**: inyectar una capa CSS global que sobrescribe los inline styles via attribute selectors. Cambio visual completo en 1 archivo CSS + 1 import. **Reversible borrando 2 líneas.**

Verificado jun 2026 en Expreso Bisonte PoC — HomePage.tsx 1341 líneas inline, transformado a tema Linear×Bloomberg sin tocar el JSX.

## Cómo funciona

CSS soporta selectores por substring de atributo:

```css
/* Cualquier div con `background: #fff` o `background: rgb(255, 255, 255)` en su style inline */
div[style*="background: rgb(255, 255, 255)"],
div[style*="background:#fff"],
div[style*="background: #fff"] {
  background: var(--bg-card) !important;
  color: var(--text-primary) !important;
}
```

Esto matchea inline styles que React serializa como string en el atributo `style` del DOM.

## Anatomía del archivo design-system.css

```
:root { /* tokens: colores, tipografía, radius, shadow, motion */ }

/* 1. Reset / base — body, html, scrollbar */

/* 2. Background overrides — por substring de color hex */
div[style*="background: #fff"] { background: var(--bg-card) !important; }
div[style*="background: #f8fafc"] { background: var(--bg-card) !important; }
div[style*="background: #1e293b"] { background: var(--bg-elevated) !important; }

/* 3. Border overrides */
*[style*="1px solid #e2e8f0"] { border-color: var(--border-subtle) !important; }

/* 4. Buttons primarios — match por background hex */
button[style*="background: #2563eb"] {
  background: var(--brand-500) !important;
  /* añadir hover, focus-visible, transition */
}

/* 5. Tables — typeface monoespaciada para números */
table { font-family: var(--font-mono) !important; }
thead th { background: var(--bg-elevated) !important; text-transform: uppercase; }

/* 6. Estados semánticos — VER DIF, errores, success */
td[style*="background-color: #fee2e2"] {
  background: var(--color-warning-bg) !important;
}

/* 7. Tipografía — H1 con gradient, mark debajo */
h1 {
  background: linear-gradient(180deg, #fff, #b8bcc9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 8. Animaciones de mount — fadeUp en cards */
@keyframes fadeUp { from { opacity:0; transform: translateY(4px); } to {...} }
```

## Patrón paso a paso

1. **Leer el JSX rápidamente** para identificar los colores hex inline más usados (`grep -oP 'background[: ][^;,"}]+' file.tsx | sort -u`).
2. **Crear `src/styles/design-system.css`** con tokens en `:root` + reglas override por substring.
3. **Importar en `main.tsx`**: `import './styles/design-system.css'`.
4. **Build + verificar**: `npm run build` y revisar visualmente. Si una superficie no cambió, agregar selector adicional.

## Trampas

- **`!important` es necesario** — los inline styles tienen mayor especificidad por default.
- **Hex y rgb son strings distintos** — incluir ambos: `[style*="#fff"]` Y `[style*="rgb(255, 255, 255)"]`.
- **Espacios en el style** — React puede serializar `background: #fff` o `background:#fff`. Incluir las dos variantes.
- **Order de cascada** — los selectores más específicos (`button[style*="..."]`) deben ir después de los genéricos (`*[style*="..."]`).
- **No rompe la lógica** — porque NO tocás JSX. Pero si querés revertir, basta con borrar el import en `main.tsx`.

## Cuándo NO usar

- Si la app ya usa Tailwind o className correctamente — extender el design system existente, no agregar overlay.
- Si el proyecto va a producción largo plazo — el overlay es deuda técnica visible (los inline styles siguen en el JSX). Para producción, planificar refactor a className/Tailwind.
- Para apps que se sirven detrás de nginx Docker sin rebuild — verificar primero que tenés flujo de rebuild operativo.

## Referencia visual del estilo aplicado (Linear × Bloomberg)

- **Linear (base)**: dark mode `#08090b`, fondo radial gradient sutil, Inter con `letter-spacing: -0.005em`, H1 con gradient blanco→gris, scrollbars finos, fadeUp en mount, micro-interacciones (`transform: translateY(-1px)` en button hover + glow focus-visible).
- **Bloomberg (densidad)**: tablas en JetBrains Mono 12.5px, `font-variant-numeric: tabular-nums`, headers caps + `letter-spacing: 0.06em`, hover de filas, semáforos por estado (warning amber para celdas críticas en vez de rojo agresivo).
- **Brand violet** `#5e6ad2` (Linear-ish) reemplazando azul genérico `#2563eb` en CTAs primarios.

## Tokens recomendados para reutilizar

```css
:root {
  --bg-base:        #08090b;
  --bg-elevated:    #0e1014;
  --bg-card:        #14171c;
  --border-subtle:  #1f242c;
  --border-default: #2a313b;
  --text-primary:   #f4f5f8;
  --text-secondary: #a1a7b3;
  --brand-500:      #5e6ad2;
  --color-warning:  #fbbf24;
  --color-success:  #4ade80;
  --color-danger:   #f87171;
  --font-sans: 'Inter', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', monospace;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
}
```

## Implementación de referencia completa

Archivo real en producción (Expreso Bisonte PoC, jun 2026):
`/home/server/proyectos/excel-merger-poc/frontend/src/styles/design-system.css`

~450 líneas de CSS. Cubre: backgrounds (claros y oscuros), borders, buttons (primary, secondary, destructive), inputs/selects, tables (incluyendo VER DIF), scrollbars, header logo, tabs activos, fade-in, dropzone, status pills, jerarquía de texto.
