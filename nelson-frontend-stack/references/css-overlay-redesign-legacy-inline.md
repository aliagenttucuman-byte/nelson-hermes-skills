# Redesign visual de UI legacy con inline styles — sin reescribir JSX

## Cuándo usar

PoC con componente React monolítico (500-2000 líneas) lleno de `style={{...}}` inline,
sin design system, y el usuario pide un rediseño visual completo ("UI de vanguardia",
"look profesional", "más Linear / Vercel / Bloomberg").

**No tocar la lógica.** El componente ya anduvo, ya pasó por iteraciones con el cliente,
romperlo por un facelift es inaceptable.

## Estrategia

Inyectar un único archivo `src/styles/design-system.css` que:

1. Define tokens CSS (`--bg-base`, `--brand-500`, `--text-primary`, etc.) en `:root`.
2. Aplica reglas base sobre `html, body, #root` y tipografía.
3. **Override quirúrgico por selectores de atributo** sobre los inline styles existentes.

Importar en `main.tsx`:

```tsx
import './styles/design-system.css'
```

Listo. Sin tocar el JSX. Reversible borrando 2 líneas.

## Cómo funciona el override por atributo

React serializa `style={{ background: '#fff' }}` como `style="background: rgb(255, 255, 255)"`
(rgb cuando es hex de 6, `#abc` si es 3) — los selectores CSS lo matchean:

```css
div[style*="background: rgb(255, 255, 255)"],
div[style*="background:#fff"],
div[style*="background: #fff"] {
  background: var(--bg-card) !important;
  color: var(--text-primary) !important;
  border-color: var(--border-default) !important;
}
```

**Siempre incluir las 3 variantes** (`rgb()`, `#fff` sin espacio, `# fff` con espacio)
porque distintas versiones de React/build emiten distinto formato.

`!important` es obligatorio — los inline styles ganan en specificity.

## Pitfalls

- **Hex de 3 dígitos vs 6**: `#fff` queda literal en algunos casos, `#ffffff` se serializa
  como `rgb(255, 255, 255)`. Cubrir las dos.
- **Espacios después de `:`**: el style serializado de React siempre lleva espacio
  (`background: rgb(...)`), pero si alguien escribió `style={{background:'#fff'}}` sin
  espacio en JS la propiedad CSS resultante puede variar — incluir ambas formas.
- **Box-shadow y focus**: agregar `:focus-visible { box-shadow: var(--shadow-glow) }` global
  para no perder accesibilidad cuando se sobreescriben bordes.
- **Tablas con `fontFamily` inline**: el override de `font-family` en `table { font-family: ... !important }`
  funciona si el inline NO definió fontFamily. Si lo definió, hay que matchear el style="" específico.
- **No re-renderizar componentes** — el archivo CSS se carga una vez, los cambios visuales son instantáneos.

## Estructura típica del design-system.css (orden importa)

1. `:root` con tokens (colores, tipografía, radius, shadows, motion)
2. Reset / base (`html, body, #root`)
3. Tipografía global (h1-h5, p, strong)
4. App shell wrapper (matchear `div[style*="maxWidth"]`)
5. Cards / panels — override de backgrounds claros → oscuros
6. Borders — `border: 1px solid #e2e8f0` → `var(--border-subtle)`
7. Buttons (primario, secundario, destructivo) — matchear por color de background
8. Inputs / selects — focus ring con `--shadow-glow`
9. Tables — `font-mono`, hover de filas, header oscuro
10. Scrollbars (`::-webkit-scrollbar`)
11. Animaciones de entrada (`fadeUp`)

## Verificación

```bash
cd <proyecto>/frontend && npm run build
# Si es Docker:
cd <proyecto> && docker compose up -d --build frontend nginx
# Si es spa_proxy directo:
# nada, el dist se recarga automáticamente
curl -s http://<host>:<puerto>/ | grep -E "index-.*\.(css|js)"
```

Probar visualmente en el browser del cliente — el server no tiene Chrome con sandbox.

## Cuándo NO usar esta técnica

- Si hay que cambiar **layout** (no solo colores/tipografía), inline styles ganan y hay que tocar JSX.
- Si el componente está hecho con clases Tailwind ya — directamente refactor de clases.
- Si la PoC es nueva (< 200 líneas), reescribir es más limpio que overlay.

## Referencia: el caso Bisonte (jun 2026)

- Componente: `HomePage.tsx` (1341 líneas, todo inline)
- Cambio: paleta clara → dark Linear/Bloomberg híbrido
- Archivos modificados:
  - `frontend/src/styles/design-system.css` (nuevo, ~280 líneas)
  - `frontend/src/main.tsx` (+1 línea de import)
  - `frontend/index.html` (+JetBrains Mono al link de Google Fonts)
- Tiempo total: < 10 min
- Lógica de negocio tocada: 0 líneas
