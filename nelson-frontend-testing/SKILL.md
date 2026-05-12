---
name: nelson-frontend-testing
title: Frontend Testing - Vitest + React Testing Library + Playwright
description: Testing del frontend para el equipo Nelson. Unit tests con Vitest, component tests con React Testing Library, E2E con Playwright. Configuracion y convenciones.
skill: nelson-frontend-testing
author: equipo-nelson
version: 1.0.0
keywords: [vitest, testing-library, playwright, e2e, frontend-testing, react-testing]
dependencies: [nelson-frontend-stack]
---

# Frontend Testing - Equipo Nelson

## Stack

| Tipo | Herramienta | Version |
|------|-------------|---------|
| Unit/Integration | Vitest | ^3.0 |
| Component Testing | React Testing Library | ^16.2 |
| Mocking | MSW (Mock Service Worker) | ^2.7 |
| E2E | Playwright | ^1.49 |
| Coverage | @vitest/coverage-v8 | ^3.0 |

## Vitest + React Testing Library

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom @vitest/coverage-v8
```

```ts
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/test/', '**/*.d.ts'],
    },
  },
});
```

```ts
// src/test/setup.ts
import '@testing-library/jest-dom/vitest';

// Mock de matchMedia (usado por algunos componentes)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
```

## Estructura de Tests

```
frontend/src/
├── components/
│   ├── Button.tsx
│   └── Button.test.tsx      # Test junto al componente
├── hooks/
│   ├── useAuth.ts
│   └── useAuth.test.ts
├── pages/
│   ├── Home.tsx
│   └── Home.test.tsx
└── test/
    ├── setup.ts              # Setup global
    └── mocks/
        ├── handlers.ts       # MSW handlers
        └── server.ts         # MSW server
```

## Ejemplos de Tests

### Componente

```tsx
// components/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from './Button';

describe('Button', () => {
  it('renderiza el texto', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('llama onClick al hacer click', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    fireEvent.click(screen.getByText('Click'));
    expect(handleClick).toHaveBeenCalledOnce();
  });

  it('esta deshabilitado cuando loading=true', () => {
    render(<Button loading>Cargando</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

### Hook

```ts
// hooks/useAuth.test.ts
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { useAuth } from './useAuth';

describe('useAuth', () => {
  it('inicia sin usuario', () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('login setea el usuario', () => {
    const { result } = renderHook(() => useAuth());
    act(() => {
      result.current.login({ id: 1, email: 'test@test.com' });
    });
    expect(result.current.user).toEqual({ id: 1, email: 'test@test.com' });
  });
});
```

### Pagina con API mocking (MSW)

```ts
// test/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/items', () => {
    return HttpResponse.json([
      { id: 1, name: 'Item 1' },
      { id: 2, name: 'Item 2' },
    ]);
  }),

  http.post('/api/items', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: 3, ...body }, { status: 201 });
  }),
];
```

```ts
// test/mocks/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

```ts
// test/setup.ts
import { beforeAll, afterAll, afterEach } from 'vitest';
import { server } from './mocks/server';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

```tsx
// pages/Home.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Home } from './Home';

describe('Home', () => {
  it('muestra items despues de cargar', async () => {
    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('Item 1')).toBeInTheDocument();
    });
    expect(screen.getByText('Item 2')).toBeInTheDocument();
  });
});
```

## Playwright (E2E)

```bash
npm install -D @playwright/test
npx playwright install
```

```ts
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:8080',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
  webServer: {
    command: 'npm run preview',
    url: 'http://localhost:8080',
    reuseExistingServer: !process.env.CI,
  },
});
```

```ts
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test('usuario puede loguearse', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('h1')).toContainText('Dashboard');
});

test('muestra error con credenciales invalidas', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'wrong@example.com');
  await page.fill('[name="password"]', 'wrong');
  await page.click('button[type="submit"]');
  await expect(page.locator('[role="alert"]')).toContainText('incorrectos');
});
```

## Scripts package.json

```json
{
  "scripts": {
    "test": "vitest",
    "test:ci": "vitest run",
    "test:coverage": "vitest run --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  }
}
```

## CI GitHub Actions

```yaml
# .github/workflows/frontend-test.yml
name: Frontend Tests

on: [push, pull_request]

jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "22" }
      - run: cd frontend && npm ci
      - run: cd frontend && npm run test:ci
      - run: cd frontend && npm run test:coverage

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "22" }
      - run: cd frontend && npm ci
      - run: cd frontend && npx playwright install --with-deps
      - run: cd frontend && npm run test:e2e
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

## Checklist

- [ ] Vitest configurado con jsdom
- [ ] MSW handlers para todos los endpoints usados en tests
- [ ] Playwright config con baseURL correcta
- [ ] Tests de componentes criticos (auth, forms, listados)
- [ ] Al menos 1 test E2E del flujo principal (login -> accion -> logout)
- [ ] Coverage minimo 70% (ideal 80%)

## Pitfalls

- MSW v2 cambio la API; usar `http.get()` no `rest.get()`
- `waitFor` es necesario para elementos async (React Query)
- Playwright en CI necesita `playwright install --with-deps`
- No testear implementacion, testear comportamiento (RTL philosophy)
- `screen.debug()` para ver el DOM cuando un test falla
