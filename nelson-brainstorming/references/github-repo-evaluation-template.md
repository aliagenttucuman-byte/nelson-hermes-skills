# Evaluación de Repos GitHub — Template

> Usar cuando Nelson pregunta “¿nos sirve?” sobre un repo, librería, o herramienta open-source.

## Flujo (siempre en este orden)

1. **Recolectar métricas rápidas vía GitHub API**
   ```bash
   curl -s https://api.github.com/repos/OWNER/REPO | jq -r '{name, description, stargazers_count, forks_count, open_issues_count, language, updated_at, license: .license.name}'
   ```
   - Stars, forks, issues abiertos → indicador de madurez/comunidad
   - Última actualización → ¿está vivo?
   - Lenguaje principal → ¿match con stack Nelson (Python + React)?
   - Licencia → Apache/MIT = OK; GPL/SSPL = warn

2. **Escanear README (primeros 200 líneas)**
   - ¿Qué problema resuelve?
   - ¿Qué piezas tiene (tracing, eval, registry, gateway, deploy)?
   - ¿Hay integraciones con nuestro stack?

3. **Veredicto ejecutivo — una sola frase**
   Formato: **Veredicto: NO/SÍ/RADAR. [una razón de una línea].**
   
   Nelson odia la ambigüedad. Nunca “puede ser útil en ciertos casos”. Es NO, SÍ, o RADAR (apto en X meses si pasa Y condición).

4. **Tabla Por qué NO hoy**
   - 3-5 bullets concretos de incompatibilidad con la etapa actual del equipo I+D+I (PoCs, stack Python+React, infra mínima)
   - Citar skills existentes que ya cubren esa función (ej. “Ya tenemos nelson-eval-harness para evaluación”)

5. **Tabla Cuándo SÍ**
   - Condiciones claras que cambiarían el veredicto a SÍ
   - Ej: “Tengamos 3+ modelos LLM en producción simultáneos”

6. **Piezas sueltas reutilizables**
   - Si hay módulos aislados que podrían usarse sin todo el monolito, listarlos.

7. **Conclusión de una línea**
   Formato: **Radar: SÍ/NO. Integrar hoy: SÍ/NO. Re-evaluar en N meses.**

## Reglas de estilo

- **Honesto y directo**. “NO, overkill” es mejor que 5 párrafos de hedging.
- **Comparar con stack existente**. Siempre mencionar qué skill/patrón ya cubre esa función.
- **NO evaluar por FOMO**. 26k stars no es razón para adoptar si no hay caso de uso hoy.
- **Documentar siempre** en `~/brainstorming/YYYY-MM-DD-nombre-proyecto-eval/`
- **Subir al repo** `nelson-brainstorming` antes de pasar página.

## Ejemplo canónico (MLflow v3.13.0)

**Veredicto: NO por ahora. Overkill para nuestra etapa.**

Por qué NO hoy:
1. Peso de infraestructura — servidor MLflow + UI + backend. Para PoCs es otra pieza Docker.
2. Duplicación — ya tenemos `nelson-eval-harness` y `nelson-monitoring-observability`.
3. No usamos sus integraciones — no estamos con LangChain/DSPy/CrewAI.
4. Gateway propio — ya tenemos patrón nginx reverso.
5. Prompt registry — hoy versionamos en git. Suma valor con 10+ prompts en prod.

Cuándo SÍ:
- 3+ modelos LLM en producción
- Tracing distribuido cross-service
- A/B testing de prompts a escala
- Stakeholder pida dashboard de evaluación sin código

Conclusión: **Radar: SÍ. Integrar hoy: NO. Re-evaluar en 6-12 meses.**
