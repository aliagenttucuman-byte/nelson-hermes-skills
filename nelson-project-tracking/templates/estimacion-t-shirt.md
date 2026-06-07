# Guía de Estimación T-Shirt Size — Equipo Nelson

> **Para:** Gino, Luigi, Nelson, y cualquier agente del equipo
> **Cuándo usar:** al crear una tarea o en el sprint planning

## Por qué T-shirt size

- Es más rápido que planning poker para tareas individuales
- Evita la falsa precisión de "3.5 horas"
- Funciona bien para equipo chico (no necesitamos consenso estricto)

## Las 5 tallas

| Talla | Horas reales esperadas | Cuándo usarla | Puntos |
|-------|------------------------|----------------|--------|
| **XS** | <2h | Fix chico, cambio de config, una línea de código, un email | 1 |
| **S** | 2-4h | Tarea de un día, bien definida, sin ambigüedad | 2 |
| **M** | 0.5-1 día | Feature con un endpoint o componente, test incluido | 3 |
| **L** | 1-2 días | Feature mediana que toca 2-3 archivos o servicios | 5 |
| **XL** | **>2 días** | ⚠️ **Rompéla antes de aceptarla** | 8 (y dividido) |

## Ejemplos reales del equipo Nelson

### Tareas XS (1 punto)
- Cambiar el texto de un endpoint en el backend
- Agregar un campo a un schema Pydantic
- Renombrar una variable usada en 2 lugares
- Actualizar un README con info nueva
- Fix de typo en un config

### Tareas S (2 puntos)
- Implementar un endpoint CRUD simple
- Agregar validación a un formulario
- Migrar un endpoint de SQLite a PostgreSQL
- Configurar Cloudflare Tunnel para un servicio nuevo
- Escribir 3-4 tests unitarios para un módulo

### Tareas M (3 puntos)
- Feature chica end-to-end: endpoint + componente React + tests
- Integración con API externa: auth + 2 endpoints + manejo de errores
- Diseñar schema de DB y migración para una tabla nueva
- Setup de Celery + 1 task de background
- Configurar un nuevo servicio de monitoring

### Tareas L (5 puntos)
- Feature mediana que toca backend + frontend + DB
- Sistema de auth completo (login + signup + JWT + middleware)
- Migración de una PoC a multi-tenant (con tests anti-leak)
- Diseño + implementación de una skill nueva
- Setup de CI/CD para un proyecto desde cero

### Tareas XL (8 puntos) — hay que romperlas

Si decís "esto es XL", la pregunta es: **¿en qué 3-4 tareas M puedo dividirlo?**

| Tarea grande | División sugerida |
|--------------|-------------------|
| "Implementar notificaciones push" | (M) Diseñar arquitectura + (M) Endpoint subscribe + (M) Frontend prompt + (M) Service worker + (S) Tests |
| "Migrar a multi-tenant" | (M) Tabla tenants + columna tenant_id + (L) RLS + middleware + tests + (M) Qdrant filter + (S) Scripts onboard/offboard |
| "Setup de ForestAI desde cero" | (M) Backend FastAPI + (M) Frontend React + (L) Docker compose + (M) Celery + PostGIS + (M) Deploy + tunnel + (S) Docs |

## Reglas de oro

1. **Si decís XL, no aceptes la tarea. Dividila.**
2. **Si dudás entre dos tallas, elegí la más grande.** Es mejor sobre-estimar a la baja y sorprender que sub-estimar.
3. **Misma tarea, distinta persona = misma talla.** La estimación es del tamaño del trabajo, no de la velocidad de quien lo hace.
4. **Después de terminar, anotá el real.** Aunque no trackees tiempo formalmente, la comparación estimado/real se hace siempre.
5. **No re-estimés retroactivamente.** Si dijiste M y tardó XL, así queda. Es información valiosa.

## Cuándo migrar a horas explícitas

Después de 2-3 sprints con T-shirt:
- Si el equipo tiene intuición consistente ("siempre S" o "siempre L" para el mismo tipo de tarea) → migrar a horas explícitas
- Si las tareas son cada vez más del mismo tipo (ej: solo features de RAG) → migrar a horas
- Si Gino/Luigi necesitan reportar a clientes externos en horas facturables → migrar a horas

Para el equipo Nelson en 2026: **seguir con T-shirt size por ahora**.

## Errores comunes

- **"Es S porque es chico"** → no, S es 2-4h reales. Si es más chico, es XS.
- **"Es L porque tiene tests"** → no, los tests van incluidos. Si tenés que hacer tests Y código Y docs, puede ser L. Si solo es código, es M como mucho.
- **"Es XL porque no sé bien cómo se hace"** → no, XL es para tareas grandes pero conocidas. Si no sabés cómo se hace, es un spike (tarea de investigación) y vale XS o S por tiempo, no por tamaño.
