# SDD para I+D+I — Flujo Simplificado

**Fecha:** 2026-05-14
**Equipo:** I+D+I (Tony + 2 agentes IA)

---

## Principio

I+D+I experimenta. No produce código para clientes. Valida hipótesis rápido.

**Regla:** Si en 2 días no funciona, se corta. Sin culpa.

## Regla de Oro del Stack

- **Backend:** Siempre **Python** (FastAPI, Flask, Django, Litestar, etc.)
- **Frontend:** Siempre **React** (Vite, Next.js, Remix, etc.)

El lenguaje y framework base NO se negocian. Lo que varía son librerías, patrones y arquitecturas dentro de ese stack.

## Flujo en 3 pasos

```
1. ESPECIFICAR (30 min)     → README.md con hipótesis y criterio de éxito
2. PLANEAR   (30 min)     → 3-5 tareas, stack Python/React, sin estimaciones
3. IMPLEMENTAR (1-2 días)  → Codear rápido, push directo, sin tests salvo necesarios
4. DEMO      (15 min)     → Tony ve resultado. Si gusta → archivar como PoC.
```

## Diferencias con Central

| Aspecto | Central (producción) | I+D+I (experimentos) |
|---|---|---|
| Fases | 8 | 3 |
| Documentación | CONSTITUTION + specs + plan + ADRs | README.md |
| Tests | 80% cobertura obligatoria | Solo si ayudan |
| Code review | PR obligatorio | Push directo |
| Stack backend | Python (FastAPI rígido) | Python (libre: FastAPI, Flask, Django, etc.) |
| Stack frontend | React (Vite rígido) | React (libre: Next.js, Remix, etc.) |
| Tiempo máx | Deadline cliente | 2-3 días |
| Done | Código + tests + docs + deploy | "Funciona para demo" |

## Reglas

1. **2 días máximo.** Si no funciona, se corta.
2. **Sin culpa.** Fallar es información.
3. **Stack base fijo.** Backend Python, Frontend React. Siempre.
4. **Variaciones permitidas.** Frameworks, librerías, ORMs, state managers, UI kits dentro de Python/React.
5. **Sin tests obligatorios.** Solo si validan la hipótesis.
6. **Promoción.** Si funciona y Tony quiere producción → equipo Central lo rebuild con flujo completo.

## Ejemplo

"Probar Zustand vs React Query para estado global"
→ README: hipótesis + criterio
→ Plan: 3 tareas (scaffold, migrar feature, comparar)
→ Implementar en 1 día (React + Python mock backend)
→ Demo con comparación
→ Si gusta: archivar como PoC para posible adopción
