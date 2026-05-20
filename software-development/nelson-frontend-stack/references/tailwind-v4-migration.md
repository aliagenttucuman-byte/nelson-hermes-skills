# Tailwind CSS v4 - Notas de Migracion

## Cambios principales vs v3

| Aspecto | v3 | v4 |
|---------|-----|-----|
| Configuracion | `tailwind.config.js` + `postcss.config.js` | Directamente en CSS |
| Import CSS | `@tailwind base; @tailwind components; @tailwind utilities;` | `@import "tailwindcss";` |
| Theme custom | Objeto JS en tailwind.config.js | `@theme` block en CSS |
| Plugin PostCSS | Requerido | No requerido |

## Archivos a eliminar al migrar de v3 a v4

```bash
rm tailwind.config.js
rm postcss.config.js
```

## CSS de entrada actualizado

```css
/* Antes (v3) */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Ahora (v4) */
@import "tailwindcss";

/* Personalizar tema */
@theme {
  --color-primary: #3b82f6;
  --color-secondary: #10b981;
  --font-sans: 'Inter', system-ui, sans-serif;
}
```

## package.json actualizado

```json
{
  "dependencies": {
    "tailwindcss": "^4.0.0"
  },
  "devDependencies": {
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49"
  }
}
```

Nota: `autoprefixer` y `postcss` pueden seguir en devDependencies si otros tools los usan, pero Tailwind 4 ya no los requiere explicitamente.

## Comando de instalacion

```bash
npm install tailwindcss@^4.0.0
```

## Troubleshooting

- Si Vite no procesa el CSS, verificar que `@import "tailwindcss"` sea la primera linea del archivo
- Los plugins de Tailwind (typography, forms, etc.) se configuran diferente en v4 — consultar docs especificos de cada plugin
