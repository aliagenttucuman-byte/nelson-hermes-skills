# CSS Override Layer — Redesigning Legacy Inline-Styled React Apps

## Cuándo usar

PoC heredada con 1000+ líneas de JSX, todos los estilos `style={{...}}` inline, sin design system. Cliente quiere "rediseño de vanguardia" pero NO hay que romper la lógica de negocio que ya anduvo. Riesgo de regresión alto si reescribís componentes.

**Estrategia**: capa CSS global única con tokens + selectores de atributo que sobreescriben los inline styles existentes. Cambio visual completo sin tocar JSX. Reversible borrando 1 import en `main.tsx`.

## Verificado en producción

- Expreso Bisonte PoC (jun 2026): rediseño Linear×Bloomberg sobre `HomePage.tsx` de 1341 líneas inline-styled. Tiempo total ~15 min. Cero regresiones funcionales. Solo 2 archivos modificados (CSS nuevo + 1 import).

## El patrón

1. **Crear `src/styles/design-system.css`** con:
   - CSS custom properties (tokens de color/spacing/motion/radius)
   - Resets globales (`html, body, #root`)
   - Selectores de atributo `[style*="..."]` que matchean cada color/bg inline conocido y lo overridean con `!important`
   - Selectores de tag (`button`, `select`, `table`, `td`, `thead`) para comportamiento base

2. **Importar en `src/main.tsx`** una sola línea:
   ```tsx
   import './styles/design-system.css'
   ```

3. **Buildear** y verificar que el bundle nuevo se sirve (`grep -E "index-.*\.css" en el HTML servido`).

## Anatomía del override por atributo

React serializa `style={{ background: '#fff' }}` como `style="background: rgb(255, 255, 255)"` en el DOM. Tu selector tiene que matchear el formato serializado, NO el código fuente:

```css
/* Esto matchea el JSX style={{ background: '#fff' }} */
div[style*="background: rgb(255, 255, 255)"],
div[style*="background:#fff"],
div[style*="background: #fff"] {
  background: var(--bg-card) !important;
}
```

Reglas que descubrí:
- React normaliza `#fff` → `rgb(255, 255, 255)` en navegadores modernos, pero algunos browsers/SSR preservan hex. Cubrir AMBOS formatos.
- `style*=` (contains) es más robusto que `=` (exact match) — el inline puede tener múltiples props.
- Borders: `*[style*="1px solid #e2e8f0"]` matchea tanto `border:` como `borderBottom:`.

## Lista de patrones reutilizables

Cuando un repo usa Tailwind palette (slate/blue/teal/red, los defaults de docs), estos selectores cubren ~95% del visual:

```css
/* Backgrounds claros → dark card */
div[style*="background: rgb(255, 255, 255)"],
div[style*="background:#fff"],
div[style*="background: rgb(248, 250, 252)"]  /* slate-50 */ { ... }

/* Backgrounds slate dark → bg elevated */
div[style*="background: rgb(30, 41, 59)"]   /* slate-800 */,
div[style*="background: rgb(15, 23, 42)"]   /* slate-900 */ { ... }

/* Accents pasteles → tinted */
div[style*="background: rgb(239, 246, 255)"]  /* blue-50 */ { ... }
div[style*="background: rgb(236, 253, 245)"]  /* emerald-50 */ { ... }
div[style*="background: rgb(254, 242, 242)"]  /* red-50 */ { ... }

/* Botones primarios (blue-600) → brand */
button[style*="background: rgb(37, 99, 235)"] { ... }

/* Texto secundario (slate-500/600) → text-secondary */
*[style*="color: rgb(100, 116, 139)"],
*[style*="color: rgb(71, 85, 105)"] { ... }
```

## Pitfalls

**1. Specificity wars con `!important`**
Si el inline style tiene `!important` (raro en React) tu CSS no va a ganar. React solo emite `!important` si lo pasás explícito. En la práctica no pasa.

**2. Pseudo-selectors no funcionan con inline styles**
`:hover`, `:focus`, `::before` SÍ funcionan en tu capa CSS porque van por encima del inline. Aprovecharlos para micro-interacciones que el JSX no tenía.

**3. Animaciones globales pueden romper UX en listas grandes**
`#root > div > div { animation: fadeUp ... }` se aplica a todos los children. Si hay 400+ items renderizados, lag perceptible. Limitar con `:nth-child(-n+10)` o quitar.

**4. h1 con gradient text rompe accesibilidad**
`-webkit-background-clip: text` requiere fallback `color:` para lectores. Mantener el `color` heredado antes del gradient.

**5. Fonts mono en tablas requieren `tabular-nums`**
Si querés que los números aliñen tipo Bloomberg, `font-variant-numeric: tabular-nums` en `td, th` (incluso con JetBrains Mono que ya es mono — algunas glyphs no son tabulares por default).

**6. Tablas con scroll horizontal: header sticky se rompe**
Si la tabla original usa `position: sticky` en `<thead>` con overflow padre, tu CSS no debe cambiar `position` ni `display`. Solo color/border/font.

## Cuándo NO usar este patrón

- App ya tiene Tailwind o CSS modules organizados → refactorizá normalmente.
- Cambio implica restructurar layout (no solo colores/spacing) → tenés que tocar JSX.
- App va a producción seria y vas a iterar mucho → meté un design system real (radix-ui + tailwind o panda-css).

Este patrón es **deuda técnica intencional** para PoCs que ya están en uso. Una vez que el cliente firma y el proyecto entra en mantenimiento, refactor a CSS modules o tailwind.

## Combo recomendado para PoCs operacionales

**Base Linear** (typography, dark, motion sutil, micro-interacciones) +
**Densidad Bloomberg** (mono fonts en datos, semáforos por estado, hover de filas).

Sweet spot para herramientas internas donde un humano mira datos densos horas seguidas.

Tokens probados:
```css
--brand-500: #5e6ad2;        /* Linear violet shifted */
--bg-base: #08090b;          /* casi negro */
--bg-card: #14171c;          /* card surface */
--color-warning: #fbbf24;    /* Bloomberg amber para alertas (no rojo agresivo) */
--font-mono: 'JetBrains Mono', 'SF Mono', monospace;
```

Para alertas operacionales (ej: "VER DIF" en Bisonte) usar `--color-warning` ámbar, no `--color-danger` rojo. El rojo se reserva para errores irrecuperables. Ámbar = "mirá esto, decidí". Rojo = "algo está roto".
