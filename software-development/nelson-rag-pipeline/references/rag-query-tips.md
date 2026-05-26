# Tips de Formulacion de Preguntas para RAG

> Basado en sesion de pruebas 12-may-2026 con documento PDF de RRHH.

## Leccion principal

La formulacion EXACTA de la pregunta afecta drasticamente la calidad del retrieval. 
Los embeddings semanticos son robustos pero no magicos: sinonimos lejanos o terminos 
no presentes en el texto original pueden fallar.

## Caso de estudio: Licencia por paternidad

| Intento | Pregunta | Resultado | Score max |
|---------|----------|-----------|-----------|
| 1 | "Cuantos dias de licencia por paternidad corresponden?" | "No tengo info" | 0.68 |
| 2 | "Que dice el manual sobre la licencia por paternidad?" | "No tengo info" | 0.71 |
| 3 | "Que licencias tiene un empleado segun el manual?" | "No tengo info" | 0.73 |
| 4 | "Cuantos dias de licencia le corresponden a un padre por el nacimiento de un hijo?" | "30 dias corridos, fraccionables" | 0.64 |

**Analisis**: El documento usa "Licencia por Paternidad" como titulo de seccion, pero 
describe el beneficio como "dias que le corresponden a un padre por el nacimiento". 
El embedding de la query debe matchar semanticamente con el CONTENIDO del chunk, no solo 
con el titulo.

## Recomendaciones

1. **Probar reformulaciones**: si una pregunta falla, reformular usando sinonimos o 
   descripciones mas largas del concepto.

2. **Usar terminos del documento**: si se sabe como esta redactado el texto original, 
   usar esas palabras clave en la pregunta.

3. **Evitar terminos muy genericos**: "paternidad" solo puede ser ambiguo. 
   "Dias de licencia para un padre nuevo" es mas descriptivo.

4. **Verificar scores**: si el score del top result es < 0.65, el retrieval esta 
   teniendo problemas. Aumentar top_k de 5 a 8 puede ayudar.

5. **HyDE como fallback**: para preguntas que fallan consistentemente, generar una 
   respuesta hipotetica con el LLM y usar ESE texto como query de retrieval.

## Prompt de system para RAG en espanol (testeado)

```
Sos un asistente util. Responde la pregunta del usuario usando UNICAMENTE la 
informacion proporcionada en el contexto. Si la respuesta no esta en el contexto, 
deci "No tengo suficiente informacion para responder."
```

Este prompt con llama3.2:3b produjo respuestas concisas y fieles al documento.
