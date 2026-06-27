# Re-skin sin tocar JSX — CSS overlay via attribute selectors

## Cuándo usar

Cuando tenés un componente React con cientos/miles de líneas de **inline styles** (`style={{...}}`) y necesitás cambiar el look completo sin riesgo de romper lógica. Caso típico: PoCs ya entregadas y funcionando que el cliente acepta y ahora pide "darle un diseño de vanguardia".

Alternativa a reescribir el JSX (1000+ líneas) o introducir Tailwind retroactivamente. Más rápido y reversible.

## Principio

CSS moderno permite seleccionar elementos por substring de su atributo `style`:

```css
div[style*="background: rgb(255, 255, 255)"] {
  background: var(--bg-card) !important;
  color: var(--text-primary) !important;
}
```

Esto matchea cualquier `<div style="...; background: rgb(255, 255, 255); ...">`. El browser normaliza colores hex a `rgb()` cuando los expone en `style`, así que el selector debe usar la forma `rgb()` (o ambas variantes). React expone los inline styles tal como los pusiste — si escribiste `#fff`, el match es `background: rgb(255, 255, 255)` después del normalize del browser. Para robustez, incluir variantes:

```css
div[style*="background: rgb(255, 255, 255)"],
div[style*="background:#fff"],
div[style*="background: #fff"] {
  background: var(--bg-card) !important;
}
```

## Pasos

1. **Crear `src/styles/design-system.css`** con tokens CSS variables (colores, radios, sombras, motion, tipografía).
2. **Importar UNA VEZ en `main.tsx`:**
   ```ts
   import './styles/design-system.css'
   ```
3. **Override por attribute selector** para cada combinación de inline style que querés reskinizar:
   - Backgrounds claros → dark bg variants
   - Borders `#e2e8f0` → `var(--border-subtle)`
   - Botones primarios `#2563eb` → brand color
   - Texto gris `#64748b` → `var(--text-secondary)`
4. **Build + deploy** sin tocar componentes:
   ```bash
   cd frontend && npm run build
   # Si el SPA lo sirve un proxy desde dist/, ya está
   ```

## Tokens base recomendados (Linear × Bloomberg para apps operativas)

```css
:root {
  --bg-base: #08090b;
  --bg-elevated: #0e1014;
  --bg-card: #14171c;
  --bg-inset: #0b0d11;
  --border-subtle: #1f242c;
  --border-default: #2a313b;
  --text-primary: #f4f5f8;
  --text-secondary: #a1a7b3;
  --text-tertiary: #6b727e;
  --brand-500: #5e6ad2;   /* Linear violet */
  --brand-400: #7d88f0;
  --color-warning: #fbbf24;  /* Bloomberg amber para alertas (mejor que rojo agresivo) */
  --color-warning-bg: rgba(251, 191, 36, 0.10);
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', monospace;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --dur-fast: 120ms;
}
```

## Patrones clave

- **Tablas operativas:** `font-family: var(--font-mono)` + `font-variant-numeric: tabular-nums`. Headers en sans + uppercase + letter-spacing. Filas con `:hover` subtle.
- **Botones:** `transform: translateY(-1px)` en hover, `box-shadow` glow en focus-visible.
- **H1 con gradient:** `background: linear-gradient(180deg, #fff, #b8bcc9); -webkit-background-clip: text; -webkit-text-fill-color: transparent;` + barrita brand debajo con `::after`.
- **Fade-in al montar:** `@keyframes fadeUp` con `animation-delay` escalonado por `nth-child`.
- **Status semáforos:** VER DIF / errores → ámbar warning (`#fbbf24`), no rojo agresivo. El rojo solo para fallas críticas.

## Pitfalls

- **NO matchear con `style*="background:#fff"` solo** — depende de cómo se serialice. Incluir las 3 variantes: `rgb(255, 255, 255)`, `#fff`, `#FFFFFF`.
- **Tablas con `style={{ background: 'inherit' }}`** no matchean — los selectores no aplican y herencia funciona. Esto es deseable: el `tr` se pinta por hover y los `td` heredan.
- **`!important` es obligatorio** porque los inline styles ganan en cascade. Sin `!important` el override no aplica.
- **Specifity de tema vs componente:** si el archivo `index.css` original tiene `body { background: ... }` hardcodeado, debe sacarse o sobrescribirse explícitamente en el design-system.css.
- **No rompe la lógica** porque NO se toca el JSX. Pero verificar visualmente que no haya texto blanco sobre fondo blanco en algún rincón olvidado.

## Reversible

Para volver atrás: borrar `import './styles/design-system.css'` en `main.tsx`. Listo.
