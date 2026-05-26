---
name: nelson-demo-script
description: Guía de conversación para mostrar PoCs a stakeholders (Pablo, clientes). Qué decir, qué mostrar, cómo manejar objeciones. Patrón probado en demos del equipo Nelson.
category: software-development
tags: [demo, stakeholder, presentacion, pablo, ventas, poc, comunicacion]
related_skills: [nelson-project-bootstrap, nelson-pricing-model, nelson-cloudflare-tunnel-deploy]
---

# Guía de Demo — Equipo Nelson

> **Trigger:** Cuando Nelson tenga que mostrar una PoC a Pablo, a un cliente, o a cualquier stakeholder no técnico.

## Principios

1. **Menos es más.** No mostrar código. No explicar arquitectura. Mostrar el problema y la solución.
2. **El stakeholder no quiere entender cómo funciona.** Quiere ver que funciona.
3. **Siempre empezar con el problema.** Si no entienden el problema, no valoran la solución.
4. **Una demo sin interacción del stakeholder es una presentación.** Que toquen, suban un archivo, hagan una pregunta.
5. **Preparar 3 niveles de profundidad:** 30 segundos (elevator pitch), 5 minutos (demo rápida), 20 minutos (demo completa).

---

## Estructura de la Demo (20 minutos)

### 1. Setup (2 min)

| Qué decir | Qué mostrar |
|-----------|-------------|
| "Esto lo podés probar desde tu celular ahora" | Abrir la URL en el celular del stakeholder |
| "Todo está corriendo local, sin depender de internet más que esta conexión temporal" | Mostrar que es una URL pública temporal |

### 2. El Problema (3 min)

| Qué decir | Qué mostrar |
|-----------|-------------|
| "Imaginate que tenés [X cantidad] de [recurso] y necesitás [objetivo]" | Pantalla en blanco o diagrama simple |
| "Hoy esto se hace así [proceso manual/lento/error-prone]" | Mencionar el dolor sin exagerar |

Ejemplo (ForestAI):
> "Tenés 10 mil hectáreas de bosque. Hoy mandás un equipo a caminarlas. Tardan semanas. El informe llega en PDF. Si querés saber cuántos pinos tenés, buscás en el PDF."

### 3. La Solución en Acción (10 min)

| Qué decir | Qué mostrar |
|-----------|-------------|
| "Veamos cómo funciona" | Interfaz del sistema |
| "Subamos un [archivo/dato] de prueba" | El stakeholder sube algo real o de prueba |
| "En [X segundos/minutos], tenemos [resultado]" | Procesamiento en tiempo real |
| "Ahora preguntemosle algo al sistema" | Chat IA, dashboard, o lo que sea |

Ejemplo (RAG PoC):
> "Subamos este contrato... Listo, ahora preguntemos: ¿Cuál es la cláusula de rescisión?" → El sistema responde con cita al documento.

### 4. Valor Tangible (3 min)

| Qué decir | Qué mostrar |
|-----------|-------------|
| "Esto te ahorra [tiempo/recursos] porque..." | Comparativa antes/después |
| "La diferencia clave es [diferenciador]" | Lo que no hace la competencia |

### 5. Cierre y Próximos Pasos (2 min)

| Qué decir | Qué mostrar |
|-----------|-------------|
| "Esto es una PoC — demuestra que funciona. El siguiente paso es [escalar/integrar/deploy]" | Roadmap simple de 3 pasos |
| "¿Qué te parece? ¿Querés que profundicemos en algo?" | Abrir al diálogo |

---

## Demo Rápida (5 minutos)

Para cuando "tengo 5 minutos, mostrame algo":

1. **Problema (30 seg):** "Tenés X problema, ¿sí?"
2. **Solución (3 min):** Mostrar la interacción clave. Una sola. La más impactante.
3. **Valor (1 min):** "Esto te ahorra Y. ¿Querés ver más?"

---

## Elevator Pitch (30 segundos)

> "Armamos un sistema que [hace X] usando IA. En [tiempo] hace lo que hoy te lleva [tiempo/mucho más]. Es una PoC funcional — el siguiente paso es escalarlo a producción. ¿Te interesa ver una demo de 5 minutos?"

---

## Manejo de Objeciones

### "Esto ya existe / ya lo hace [competencia]"

> "Seguro. La diferencia es que nosotros [diferenciador específico]. Esta PoC demuestra exactamente eso. ¿Querés que comparemos?"

### "No tenemos presupuesto para IA"

> "Entiendo. Esta PoC corre en hardware que ya tenés — no necesitás GPU ni servicios de nube. El costo es casi cero para empezar. El presupuesto se necesita solo para escalar."

### "Es muy técnico, no lo voy a entender"

> "No hace falta entender cómo funciona adentro. Es como un auto: no necesitás saber de motores para manejar. Subí un archivo y hacé una pregunta — eso es todo."

### "No creo que funcione con nuestros datos reales"

> "Probemos con un archivo tuyo. Ahora. Si no funciona, lo arreglamos en el momento."

### "¿Cuánto tiempo lleva implementar esto en producción?"

> "Depende del alcance. Con esta PoC como base, una versión MVP sería [X semanas]. Te preparo una estimación detallada si querés."

### "Me parece que le falta [feature X]"

> "Buen punto. Eso no está en la PoC porque la armamos para validar [Y]. Feature X es el siguiente paso natural. ¿Es crítico para vos?"

---

## Checklist Pre-Demo

- [ ] URL pública funciona desde el celular del stakeholder
- [ ] Datos de prueba cargados y listos
- [ ] El sistema responde en < 3 segundos
- [ ] Backup plan: si falla internet, mostrar video/grabación
- [ ] Saber quién está en la demo (técnico vs no técnico vs decisor)
- [ ] Tener la estimación de costos a mano (skill: nelson-pricing-model)

---

## Tipos de Stakeholder

| Tipo | Cómo hablarle | Qué mostrarle | Qué evitar |
|------|--------------|---------------|-----------|
| **Técnico** (dev, arquitecto) | "Esto usa [stack] con [patrón]" | Arquitectura, código si pide | No simplificar demasiado |
| **Operativo** (COO, gerente) | "Esto te ahorra X horas por semana" | Dashboard, métricas, reportes | Detalles técnicos |
| **Ejecutivo** (CEO, director) | "Esto reduce costos / aumenta ingresos" | ROI, escalabilidad, roadmap | Código, implementación |
| **Pablo (COO + referente)** | "Mirá lo que armamos con [tiempo/esfuerzo]" | Todo funcional, que toque | Teoría sin demo |

---

## Ejemplos Reales del Equipo

### ForestAI (Drones + Inventario Forestal)

**Problema:** Inventario forestal manual toma semanas.
**Demo:** Subir imagen aérea → detectar árboles → contar → ver en mapa.
**Cierre:** "Esto te ahorra 3 semanas de campo. ¿Querés ver el reporte?"

### Fleet Optimizer (Rutas + Flota)

**Problema:** No sabés dónde están los camiones ni si llegan a tiempo.
**Demo:** Ver mapa con camiones en tiempo real → hacer una pregunta al chat → ver alerta de demora.
**Cierre:** "El sistema predice demoras antes de que pasen."

### RAG Documentos (Preguntar PDFs)

**Problema:** Buscar info en contratos/PDFs es lento y error-prone.
**Demo:** Subir PDF → preguntar en lenguaje natural → ver respuesta con cita al párrafo exacto.
**Cierre:** "Encontrás cualquier cláusula en segundos, no en horas."

---

## Frases que Funcionan

- "Mirá esto..." → Mostrar algo, no explicarlo.
- "Probemos con tus datos" → El stakeholder se siente involucrado.
- "Esto es una PoC, no es el producto final" → Maneja expectativas.
- "El siguiente paso es..." → Siempre dejar un camino claro.
- "¿Qué te parece?" → Cerrar con pregunta, no con afirmación.

---

## Frases que NO Funcionan

- "Esto usa FastAPI con async/await y Qdrant para embeddings..." → Cero. Nadie le importa.
- "El modelo tiene 3 mil millones de parámetros..." → Solo confunde.
- "Después podemos agregar..." → Suena a que no está listo.
- "Es complicado de explicar pero..." → Ya perdiste.

---

## Referencias

- Skill: nelson-pricing-model — estimaciones de costo para cerrar demos
- Skill: nelson-cloudflare-tunnel-deploy — cómo exponer la PoC públicamente
- Skill: nelson-project-bootstrap — cómo armar la PoC antes de la demo
- Plantilla: ~/brainstorming/templates/demo-package-README.md
