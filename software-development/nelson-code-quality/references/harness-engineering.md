# Harness Engineering (Martin Fowler)

> Fuente: https://martinfowler.com/articles/harness-engineering.html

## Concepto

Un **harness** es todo lo que rodea a un agente de IA, excepto el modelo en si.
Es el codigo, la configuracion, los prompts, las validaciones que nosotros armamos.

## Componentes

### 1. Feedforward Guides (Guias preventivas)
Instrucciones y patrones ANTES de que el agente genere codigo.

- Skills de desarrollo
- Prompts de system
- Conventions y estandares
- Templates de arquitectura

### 2. Feedback Sensors (Sensores de verificacion)
Verificacion DESPUES de que el agente genera codigo.

**Computacionales** (deterministicos, baratos):
- Linters (Ruff, ESLint)
- Type checkers (mypy, TypeScript)
- Tests (pytest, vitest)
- Architecture checks (imports, dependencias)

**Inferenciales** (LLM-based, semanticos):
- Revision de over-engineering
- Deteccion de codigo duplicado semantico
- Analisis de complejidad innecesaria
- Verificacion de nombres y clean code

## Key Insights

1. **Dos capas de defensa**: Feedforward evita errores antes de que ocurran.
   Feedback los detecta despues. Ambas son necesarias.

2. **Balance de costos**: Sensores computacionales son rapidos y baratos.
   Sensores inferenciales son lentos y caros. Usar los primeros como filtro.

3. **Self-correction loops**: Cuando un sensor falla, el agente deberia poder
   arreglar el problema automaticamente sin intervencion humana.

4. **Harness templates**: Bundles de guias + sensores para un tipo de proyecto.
   El `nelson-template` es exactamente esto.

5. **Intervencion humana dirigida**: Un buen harness no elimina la intervencion
   humana, la dirige a donde mas importa.

## Metricas de calidad del harness

- **Harness coverage**: Que porcentaje del codigo esta cubierto por guias y sensores
- **False positive rate**: Cuanto ruido generan los sensores
- **Auto-fix rate**: Que porcentaje de issues se arreglan solos
- **Human intervention rate**: Cuanto tiene que intervenir un humano

## Aplicacion en el Equipo Nelson

| Componente | Tipo | Implementacion |
|-----------|------|----------------|
| Spec-driven dev | Feedforward | `spec-driven-development` skill |
| Type hints estrictos | Feedforward | `nelson-senior-practices` skill |
| Ruff + mypy | Feedback computacional | Pre-commit + CI |
| Architecture checks | Feedback computacional | `nelson-structural-check.py` |
| Alma 2.0 | Feedback inferencial | `alma-reviewer.py` (Ollama LLM) |
| Self-fix | Self-correction | `nelson-self-fix.py` |
