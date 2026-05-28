# Benchmarks del Equipo Nelson — OptiLLM con Ollama Local

## Contexto

Fecha: 2026-05-15
Hardware: GTX 1650 4GB VRAM, CUDA 12.1
Modelos testeados: llama3.2:3b (3B params), llama3.1:8b (8B params)
Backend: Ollama local via endpoint OpenAI-compatible
Proxy: OptiLLM v0.3.15 en puerto 18000

## Problemas de Test

3 problemas clásicos de razonamiento, elegidos por tener respuestas verificables:

1. **Lobo/Oveja/Repollo** — Puzzle de transporte con restricciones
2. **Interruptores/Bombillas** — Problema lógico con uso de temperatura
3. **Trenes Cruzados** — Problema matemático con respuesta exacta: **280 km de Buenos Aires**

## Resultados — llama3.2:3b

| Técnica | Lobo/Oveja | Interruptores | Trenes | Overhead |
|---------|-----------|---------------|--------|----------|
| Directo | 13.3s | 15.4s | 14.1s | 1x |
| Passthrough | 11.3s | 15.4s | 15.4s | 1x |
| **MOA** | **58.4s** | **63.9s** | **64.1s** | **4-5x** |
| **MCTS** | **48.3s** | **54.3s** | **68.7s** | **4-5x** |

Tokens: MOA/MCTS consumen ~3x tokens vs directo.

### Calidad — llama3.2:3b

- **Lobo/Oveja**: Ninguna técnica acertó. Todos inventaron secuencias imposibles.
- **Interruptores**: Ninguna acertó. Directo y passthrough sin sentido. MOA se acercó vagamente. MCTS dijo "no se puede hacer".
- **Trenes**: Respuesta correcta = **280 km**.
  - Directo: 560 km (mal)
  - Passthrough: "no podemos determinarlo"
  - MOA: 14.58h de tiempo total (completamente mal)
  - MCTS: 2800 km (mal, pero usó ecuaciones formales)

**Veredicto 3B**: El modelo no tiene capacidad para razonamiento matemático. Las técnicas no compensan.

## Resultados — llama3.1:8b

| Técnica | Respuesta Trenes | Calidad |
|---------|-----------------|---------|
| Directo | 560 km | Calculó bien tiempo (3.5h) pero sumó mal al final |
| MOA | 350 km | El síntesis confundió respuestas intermedias |
| MCTS | Incompleta | Bien estructurado pero no terminó |
| CoT Reflection | 140 km | Llegó a 280 pero la reflexión lo hizo dudar |
| BON | ~290 km | Concepto erróneo desde el inicio |
| **Re2** | **280 km ✓** pero luego 260 km | ¡Llegó a la respuesta correcta! Pero no la mantuvo |

**Veredicto 8B**: Mejor estructura que 3B, pero ninguna técnica mejoró significativamente sobre directo en razonamiento matemático. CoT Reflection empeoró al hacer dudar al modelo de sus cálculos correctos.

## Conclusiones Clave

1. **OptiLLM funciona técnicamente perfecto** como proxy. Infraestructura lista para producción.

2. **Con modelos 3B-8B, técnicas complejas (MOA, MCTS) no mejoran razonamiento matemático.**
   - El problema es capacidad del modelo base, no falta de técnica
   - Es como ponerle turbo a un motor de 50cc

3. **MOA empeoró vs directo** en varios casos. El agente síntesis confundió respuestas intermedias.

4. **MCTS mostró mejor estructura** que MOA (uso de ecuaciones, pasos formales) pero no terminó.

5. **CoT Reflection fue contraproducente** en 8B: el modelo llegó a 280 km correcto, pero la fase de reflexión lo hizo dudar y recalcular mal.

6. **Re2 fue la única que llegó a la respuesta correcta** (280 km), aunque no la mantuvo al final.

## Recomendación para RAGs (preguntas sobre documentos)

- **OptiLLM como passthrough directo**: Útil. Unifica endpoint, sin overhead.
- **MOA en queries creativas/síntesis**: Podría mejorar respuestas que requieren diversidad de perspectivas sobre un documento.
- **Evitar MCTS/MOA en queries rápidas**: 4-5x más lento, 3x más tokens.
- **Embeddings directos a Ollama**: No pasar por OptiLLM.

## Próximos Pasos Recomendados

1. **Testear OptiLLM con queries reales de nuestros PDFs de RRHH** (no matemáticas)
2. **Re-evaluar con modelos 13B+** cuando estén disponibles
3. **Considerar BON o Re2** como técnicas "baratas" (1.5-2x overhead) para posible mejora sin el costo de MOA/MCTS
