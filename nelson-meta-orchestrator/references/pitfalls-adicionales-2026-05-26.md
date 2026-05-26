# Pitfalls adicionales detectados en sesión 2026-05-26

## 11. dry_run y el verifier son incompatibles si el resultado es trivial

**Problema:** `dry_run=True` retornaba `"[dry-run] Agente: X | Categoría: Y"` — una sola línea sin keywords técnicas. El verifier la penalizaba (< 20 palabras, 0 keywords) → score 0% → el loop iteraba innecesariamente antes de fallar.

**Fix:** El executor en dry_run genera un resultado simulado usando `EXPECTED_KEYWORDS[cat]` para producir un texto con keywords reales de la categoría. Cualquier cambio al formato del dry_run debe verificarse contra umbral del verifier (score ≥ 0.5, longitud ≥ 20 palabras).

## 12. TypeScript verbatimModuleSyntax y re-exports de tipos

**Problema:** `import { MyType } from './module'` falla con `TS1484: 'MyType' is a type and must be imported using a type-only import` cuando `verbatimModuleSyntax` está habilitado en tsconfig.

**Fix:** Siempre separar tipos de valores: `import type { MyType } from './module'`. Si el componente usa `export default function`, importarlo con `import Component from '...'` (no `import { Component }`). Verificar con `grep -n 'export' archivo.tsx` antes de importar.

## 13. Estado de implementación 2026-05-26

100% implementado y corriendo en producción:
- ✅ Executor real (hermes CLI + simulación fallback)
- ✅ Persistencia SQLite del task graph
- ✅ Paralelismo de batches (ThreadPoolExecutor)
- ✅ Verifier 3 capas (estructural, keywords, longitud)
- ✅ Notifier WhatsApp via bridge :3000
- ✅ WebSocket /ws en el backend (eventos en tiempo real)
- ✅ Hook useOrchestratorWS + LiveFeed en dashboard
- ✅ AuthGuard con PIN en dashboard (default: 741852, override: VITE_DASHBOARD_PIN)
- ✅ Systemd service file + install-service.sh
- ✅ Estimador de presupuesto (POST /estimate)

Ver detalle completo en `references/implementacion-completa-2026-05-26.md`.
