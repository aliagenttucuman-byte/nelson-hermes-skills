# Harness Engineering (Martin Fowler)

> Fuente: https://martinfowler.com/articles/harness-engineering.html
> Session: 2026-05-11

## Que es un Harness

Todo lo que rodea a un agente de IA **excepto el modelo mismo**. Es el sistema de controles que guia y verifica el trabajo del agente.

## Dos componentes del Harness

### 1. Feedforward Guides (Guias preventivas)

Reglas que se aplican **ANTES** de que el agente empiece a codear. Previenen errores.

**Ejemplos en nuestro equipo:**
- Spec OpenAPI antes del codigo (`spec-driven-development`)
- Repository pattern, SOLID (`nelson-senior-practices`)
- Type hints estrictos, mypy (`nelson-code-quality`)
- Estructura de carpetas fija (`nelson-project-bootstrap`)

### 2. Feedback Sensors (Sensores de verificacion)

Verificaciones que se aplican **DESPUES** de que el agente codea. Detectan errores.

**Tipos:**

| Tipo | Naturaleza | Costo | Ejemplos en nuestro stack |
|------|-----------|-------|---------------------------|
| **Computacionales** | Deterministicos | Baratos | Ruff, mypy, pytest, ESLint, Playwright |
| **Inferenciales** | LLM-based, semanticos | Caros | Revision de PR por agente (over-engineering, codigo duplicado semantico) |

**Por que necesitas AMBOS:**
- Solo guias -> el agente nunca sabe si funciono
- Solo sensores -> el agente repite los mismos errores

## Harness Templates

Bundles de guias + sensores para un tipo especifico de proyecto. Es exactamente lo que creamos con `nelson-template`.

## Mejoras identificadas para nuestro equipo

### Agregar sensores inferenciales (Alma 2.0)

Un agente reviewer que revise PRs buscando:
- Over-engineering (soluciones mas complejas de lo necesario)
- Codigo duplicado semantico (no sintactico, sino logica repetida)
- Features innecesarias (el agente agrego algo que no se pidio)
- Complejidad ciclomatica excesiva
- Violaciones de arquitectura (API importando models directamente)

### Tests estructurales

Verificar la arquitectura, no solo el comportamiento:
- La capa API no importa directamente de models
- No hay dependencias circulares
- Repository pattern se respeta
- Cada modulo tiene un solo proposito

### Self-correction loops

Cuando un sensor falla, el agente deberia poder arreglarlo automaticamente:
1. Ruff detecta error -> agente corre `ruff check --fix`
2. mypy detecta type error -> agente corrige los tipos
3. Test falla -> agente analiza el error y ajusta el codigo

### Harness coverage

Medir cuanto del codigo esta cubierto por guias y sensores:
- Que % de funciones tienen docstrings?
- Que % de endpoints tienen tests?
- Que % del codigo pasa mypy strict?
- Que % de archivos tienen type hints?

## Frase clave

> "Un buen harness no busca eliminar la intervencion humana, sino dirigirla a donde mas importa."

## Diferencia agente vs humano

| Humanos | Agentes IA |
|---------|-----------|
| Memoria organizacional | No tienen |
| Intuicion de "esto esta mal" | No tienen |
| Responsabilidad social (nombre en el commit) | No tienen |
| Saben que deuda tecnica es tolerable | No saben |
| Van en pasos pequenos, reflexionan | Generan todo de golpe |

Las skills intentan externalizar lo que los humanos aportan implicitamente.
