---
name: nelson-react-doctor
description: "React Doctor v2: diagnóstico automático de errores en apps React. Detecta useState/useEffect innecesarios, prop drilling, problemas de accesibilidad y rendimiento. Integración con CI/CD del equipo Nelson."
category: software-development
tags: [react, frontend, code-quality, linting, performance, a11y]
related_skills: [nelson-frontend-stack, nelson-code-quality, nelson-frontend-testing]
---

# React Doctor v2 🤖⚕️

> **Trigger:** Cada vez que el equipo desarrolle o revise código React. También en CI/CD antes de mergear PRs.

**Repo:** https://github.com/millionco/react-doctor | 12.262 stars | MIT | commits diarios
**Descripción oficial:** "Your agent writes bad React. This catches it." — diseñado específicamente para detectar los errores que cometen los agentes IA al escribir React.

### Integración recomendada para el equipo Nelson
1. **Auditoría inicial de proyectos activos:** `npx react-doctor@latest` en ForestAI frontend, Bisonte frontend, etc.
2. **Skill para agentes:** `npx react-doctor@latest install` — inyecta reglas como skill en Claude Code, Cursor, Codex, Hermes. El agente aprende los patrones y no los repite.
3. **CI/CD:** GitHub Action que reporta SOLO los issues NUEVOS del PR (como Codecov para calidad). Ver sección CI abajo.
4. **LSP inline (experimental):** `react-doctor experimental-lsp --stdio` — errores inline en VS Code, Cursor, Zed, Neovim.

### Telemetría — deshabilitar en producción
```bash
npx react-doctor@latest --no-telemetry
```

## ¿Qué es?

Herramienta de código abierto (https://github.com/millionco/react-doctor) que escanea apps React
y detecta problemas comunes de manera automática. **Diseñado específicamente para errores que
cometen los agentes de IA al escribir React** — útil para revisar output de JARVIS, Julian, Mercedes.

- ✅ `useState` y `useEffect` innecesarios
- ✅ Errores de accesibilidad (a11y)
- ✅ Problemas de rendimiento
- ✅ Prop drilling evitable con Context
- ✅ Imports no usados
- ✅ Dependencias de efectos incorrectas
- ✅ Reglas TanStack Query (query-destructure-result, etc.)
- ✅ JSX element types incorrectos
- ✅ Funciona con Next.js, Vite, TanStack, React Native, Expo

## Instalación

### One-shot (sin instalar globalmente)

```bash
npx react-doctor@latest
```

### Instalación local en proyecto

```bash
npm install --save-dev react-doctor@latest
```

### Verificar versión

```bash
npx react-doctor --version
```

### Desactivar telemetría (Sentry)

Por default, React Doctor envía métricas anónimas a Sentry. Para PoCs o entornos sensibles:

```bash
npx react-doctor@latest --no-telemetry
```

O en `react-doctor.config.js` / `doctor.config.ts`:

```ts
export default { telemetry: false } satisfies ReactDoctorConfig;
```

## Modo Agente (entrenar a JARVIS/Mercedes)

`npx react-doctor@latest install` inyecta las reglas como skill dentro del agente
(Claude Code, Cursor, Codex, OpenCode). El agente aprende los patrones y deja de
cometerlos. **Correr en cada proyecto React nuevo.**

```bash
# En la raíz del proyecto
npx react-doctor@latest install
```

## Modo CI — solo issues nuevos en el PR

GitHub Action oficial. A diferencia del modo `npx` (escanea todo), el Action
diferencia contra el merge-base y reporta **solo lo que el PR introduce**, más
un delta new/fixed. Como Codecov pero para calidad React.

```yaml
# .github/workflows/react-doctor.yml
name: React Doctor
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
permissions:
  contents: read
  pull-requests: write
  issues: write
  statuses: write
concurrency:
  group: react-doctor-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
jobs:
  react-doctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0  # OBLIGATORIO: para que pueda diffear contra el base commit
      - uses: millionco/react-doctor@v2
```

`fetch-depth: 0` es crítico. Sin suficiente history, la Action cae al modo
"reportar todo" en los archivos modificados, no solo lo nuevo.

## Modo LSP (experimental, útil en IDE)

```bash
react-doctor experimental-lsp --stdio
```

Integra con VS Code, Cursor, Zed, Neovim, Sublime, Emacs, Helix.
Diagnosticos inline + hovers + quick-fixes en tiempo real.

## Configuración moderna (`doctor.config.ts`)

El config moderno es `doctor.config.ts` (TypeScript). El legacy `react-doctor.config.js`
sigue andando pero `doctor.config.ts` es la vía oficial.

```ts
// doctor.config.ts
import type { ReactDoctorConfig } from "react-doctor/api";

export default {
  lint: true,
  rules: {
    "react-doctor/no-array-index-as-key": "off",  // deshabilitar regla específica
  },
} satisfies ReactDoctorConfig;
```

## Uso básico

### Analizar todo el proyecto

```bash
npx react-doctor@latest
# o
npx react-doctor@latest --dir ./src
```

### Analizar un archivo específico

```bash
npx react-doctor@latest ./src/components/UserProfile.tsx
```

### Salida en formato JSON (para CI / parser)

```bash
npx react-doctor@latest --format json --output report.json
```

### Solo errores críticos

```bash
npx react-doctor@latest --severity error
```

### Solo archivos modificados (git staged)

```bash
npx react-doctor@latest --staged
```

### Con fix automático donde sea posible

```bash
npx react-doctor@latest --fix
```

## Integración con CI/CD

### Pre-commit hook (husky)

```json
// .husky/pre-commit
npx react-doctor@latest --staged
```

### GitHub Actions

```yaml
# .github/workflows/react-doctor.yml
name: React Doctor Check
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx react-doctor@latest --format json
```

### Script del equipo

```bash
# scripts/check-react.sh
#!/bin/bash
set -e

echo "🤖⚕️ Corriendo React Doctor..."
npx react-doctor@latest --format json --output .reports/react-doctor.json

# Si hay errores críticos, falla el pipeline
if grep -q '"severity": "error"' .reports/react-doctor.json; then
  echo "❌ Errores críticos encontrados. Revisa .reports/react-doctor.json"
  exit 1
fi

echo "✅ React Doctor pasó sin errores críticos"
```

## Reglas principales detectadas

| Regla | Descripción | Severidad |
|---|---|---|
| `unnecessary-useState` | `useState` que podría ser una constante | warning |
| `unnecessary-useEffect` | `useEffect` que no maneja side effects | warning |
| `prop-drilling` | Props pasadas más de 3 niveles sin Context | warning |
| `missing-key-prop` | Elementos de lista sin `key` | error |
| `useEffect-missing-deps` | Dependencias faltantes en `useEffect` | error |
| `unused-imports` | Imports no utilizados | warning |
| `accessibility-missing-alt` | Imágenes sin `alt` | error |
| `performance-memo-missing` | Componentes que deberían usar `memo` | info |
| `context-over-prop-drilling` | Situación candidata para Context | suggestion |

## Configuración

### Archivo de config `react-doctor.config.js`

```javascript
module.exports = {
  extends: ['recommended'],
  rules: {
    'unnecessary-useState': 'warn',
    'unnecessary-useEffect': 'warn',
    'prop-drilling': 'warn',
    'missing-key-prop': 'error',
    'useEffect-missing-deps': 'error',
    'unused-imports': 'warn',
    'accessibility-missing-alt': 'error',
    'performance-memo-missing': 'info',
  },
  ignorePatterns: [
    '**/*.test.{js,jsx,ts,tsx}',
    '**/*.spec.{js,jsx,ts,tsx}',
    '**/node_modules/**',
    '**/dist/**',
  ],
};
```

## Flujo del equipo Nelson

```
1. Nuevo proyecto React
   └─> npx react-doctor@latest install   (entrena al agente)
2. Desarrollador/agente escribe código React
3. Antes de commitear: npx react-doctor@latest (verifica local)
4. Si hay errores críticos: corrige antes de pushear
5. PR abre → CI corre GitHub Action
   └─> solo issues nuevos en el PR (no los pre-existentes)
6. Inline comments en las líneas cambiadas + summary sticky
7. Merge solo si pasa todas las validaciones
```

## Cuándo correrlo

| Momento | Comando |
|---|---|
| Nuevo proyecto React | `npx react-doctor@latest install` (modo agente) |
| Pre-commit local | `npx react-doctor@latest` |
| Pre-PR / pre-demo | `npx react-doctor@latest --format json` (parsea el output) |
| En PR automático | GitHub Action `millionco/react-doctor@v2` |
| Durante desarrollo | LSP experimental (`react-doctor experimental-lsp --stdio`) |

## Pitfalls

- **NO correr en `node_modules`** — React Doctor escanea todo el árbol por defecto. Usar `--ignore-pattern` o `react-doctor.config.js`.
- **No sustituye testing** — Detecta patrones de código, no bugs de lógica. Sigue usando jest/react-testing-library.
- **Revisar `suggestion` antes de aplicar** — Algunas sugerencias de "usar Context" pueden ser overkill para props simples.
- **Versión lock** — En CI, usar `react-doctor@latest` o versionar en `package.json` para consistencia.
- **No fijar `Content-Type: multipart/form-data` global en Axios** — rompe endpoints JSON (`422` en FastAPI/Pydantic). Dejar que Axios infiera headers y usar multipart solo en requests de upload.
- **Error UI "pantalla blanca" por renderizar objetos de error** — si `error.response.data.detail` viene como array/objeto, convertirlo a string antes de `setState` o JSX. Evita `Minified React error #31`.

### Pitfalls reales detectados en PoCs (white screen)

- **No setear `Content-Type: multipart/form-data` global en Axios**.
  - Si el cliente HTTP lo define a nivel global, requests JSON (`POST /plan/suggest`, `POST /merge`) se envían mal y FastAPI responde 422.
  - Fix: dejar Axios sin `Content-Type` global y enviarlo solo en uploads con `FormData`.
- **Error detail de FastAPI puede venir como array de objetos**.
  - `err.response.data.detail` a veces no es string; si se renderiza directo en React puede romper con `Minified React error #31` (pantalla blanca).
  - Fix: normalizar errores (`string | object | array`) antes de `setError`.
- **Cuando aparece white screen al ejecutar flujo**, verificar en este orden:
  1) Console y `pageerror` del navegador.
  2) Payload y `Content-Type` real del request que falla.
  3) Respuesta API (`422` vs `500`) y mensaje backend.
  4) Si hay `500`, encapsular excepciones backend en `HTTPException(400/422)` con mensaje amigable para no tumbar UX.

## Comandos rápidos


## Comandos rápidos

```bash
# Diagnóstico completo
npx react-doctor@latest

# Solo archivos modificados (git staged)
npx react-doctor@latest --staged

# Reporte HTML
npx react-doctor@latest --format html --output report.html

# Ignorar archivos de test
npx react-doctor@latest --ignore-pattern "**/*.test.tsx"

# Con fix automático donde sea posible
npx react-doctor@latest --fix
```

## Links

- npm: `npx react-doctor@latest`
- Categoría: code-quality, frontend, react
- Troubleshooting real: `references/white-screen-422-react31.md` (Axios headers + React #31)
- Referencia de incidente (pantalla blanca en acción): `references/white-screen-api-and-error-state.md`
