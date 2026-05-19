# Benchmark OptiLLM — Mayo 2026

## Contexto

Fecha: 15 de mayo de 2026
Modelos testeados: llama3.2:3b, llama3.1:8b
Hardware: GTX 1650 4GB VRAM
Proxy: OptiLLM v0.3.15 apuntando a Ollama local

## Problema 1: Trenes cruzados (respuesta exacta: 280 km de Buenos Aires)

| Variante | Respuesta | Tokens | Tiempo | Calidad |
|----------|-----------|--------|--------|---------|
| Ollama directo llama3.2:3b | 560 km | 547 | 14.1s | ❌ Calculó 3.5h bien pero usó mal velocidad relativa |
| OptiLLM passthrough 3b | Incompleto | 600 | 15.4s | ❌ Calculó bien tiempo pero no supo qué hacer después |
| OptiLLM MOA 3b | 350 km | 1594 | 58.4s | ❌ Inventó "450 km" y "0,5" |
| OptiLLM MCTS 3b | Incompleto | 1543 | 48.3s | ❌ Confundió secuencia |
| Ollama directo llama3.1:8b | 560 km | 420 | 14.1s | ❌ Calculó bien pero sumó 280+280 |
| OptiLLM passthrough 8b | Incompleto | 600 | 15.4s | ❌ No terminó |
| OptiLLM MOA 8b | 350 km | 1551 | 64.1s | ❌ Inventó tiempos para recorrer toda la distancia |
| OptiLLM MCTS 8b | Incompleto | 2152 | 68.7s | ⚠️ Mejor estructura (ecuaciones) pero resolvió mal |
| OptiLLM CoT Reflection 8b | 140 km | 600 | ~60s | ❌ Llegó a 280 pero la reflexión lo hizo dudar |
| OptiLLM BON 8b | ~290 km | 602 | ~60s | ❌ Concepto erróneo desde el inicio |
| **OptiLLM Re2 8b** | **280 km ✅** | 567 | ~50s | ✅ **¡Única que acertó!** Pero luego dijo 260 km |

## Problema 2: Lobo, oveja y repollo

Ninguna variante (directo, MOA, MCTS) resolvió correctamente con 3B ni 8B. Todos inventaron secuencias imposibles.

## Problema 3: Interruptores y bombillas

Ninguna variante dio la solución clásica (usar temperatura como segundo indicador). MOA se acercó más al concepto.

## Problema 4: RAG real — Manual de RRHH

### Pregunta 1: ¿Cuántos días de licencia por paternidad?

| Variante | Respuesta | Tokens | Tiempo | Calidad |
|----------|-----------|--------|--------|---------|
| Directo 3b | "30 días corridos... no se especifica cuántos días por período" | 84 | 7.4s | ✅ Correcto pero agregó disclaimer innecesario |
| Passthrough 3b | "30 días corridos con goce de sueldo" | 28 | 4.3s | ✅ **Perfecto y conciso** |
| MOA 3b | "30 días corridos... se extiende a 180 días en prematurez" | 484 | 20.2s | ❌ **Alucinación**: mezcló dato de maternidad |

### Pregunta 2: ¿Cuáles son todos los beneficios económicos?

| Variante | Respuesta | Tokens | Tiempo | Calidad |
|----------|-----------|--------|--------|---------|
| Directo 3b | Lista de 6 ítems correcta + disclaimer | 334 | 12.0s | ✅ Correcto, verboso |
| Passthrough 3b | Lista de 6 ítems correcta + "cobertura significativa" | 194 | 8.5s | ✅ Correcto, conciso |
| MOA 3b | Lista de 6 ítems correcta | 900 | 34.3s | ✅ Correcto pero 4x más lento |

### Pregunta 3: 7 tardanzas en un mes, ¿qué pasa?

| Variante | Respuesta | Tokens | Tiempo | Calidad |
|----------|-----------|--------|--------|---------|
| Directo 3b | "Descuento proporcional... no se especifica cuánto" | 50 | 4.8s | ✅ Correcto con disclaimer |
| Passthrough 3b | "Aviso escrito" | 28 | 4.3s | ❌ **FALLÓ: dijo aviso escrito (es para 4-6)** |
| MOA 3b | "Descuento proporcional... según evaluación de desempeño" | 691 | 26.5s | ✅ Correcto pero agregó info irrelevante de evaluación |

## Conclusiones

1. **OptiLLM es infraestructura lista.** Proxy estable, técnicas funcionan técnicamente.
2. **Con 3B-8B, las técnicas complejas no valen la pena.** MOA/MCTS consumen 4-5x recursos sin mejorar calidad.
3. **MOA alucina datos.** En RAG de RRHH mezcló maternidad con paternidad. Riesgoso para documentos legales.
4. **Passthrough es más rápido que directo** pero con riesgo de errores ocasionales (falló en 1 de 3 preguntas).
5. **Re2 (rereading) fue la única técnica que mejoró matemáticas en 8B.** Pero aún así no mantuvo la coherencia hasta el final.
6. **Para modelos grandes (13B+), hay que re-evaluar.** Es probable que MOA/MCTS sí muestren valor ahí.

## Recomendación

- **Mantener OptiLLM corriendo en `localhost:18000`** como infraestructura I+D+I.
- **No integrar en producción** hasta tener modelo 13B+ y nuevo benchmark favorable.
- **Cuando lleguen minimax2.7, kimi2.6, qwen3**: repetir este benchmark exacto y comparar.
