# TEM-1 — Torre de Energía Mixta · Análisis de Viabilidad

**Fecha:** 2026-05-20  
**Fuente:** Executive Summary enviado por Pedro Alejandro Lopez Peñalva (Founder, Arachné Systems)  
**Contexto:** Nelson recibió el doc y pidió análisis de viabilidad + potencial sinergia con ForestAI  
**Estado:** Pre-análisis (sin prototipo verificado, sin datos técnicos duros)

---

## ¿Qué es TEM-1?

Sistema modular de generación/captación energética off-grid, diseñado para infraestructura crítica en zonas remotas o con redes eléctricas poco confiables. Opera bajo arquitectura "black box" (la tecnología específica no se revela en el doc).

**Mercados objetivo declarados:**
- Centros de datos / HPC / IA
- Minería de alta montaña (San Juan, Cordillera)
- Petróleo y gas remoto (Vaca Muerta)
- Telecomunicaciones en zonas rurales

**Modelo de negocio propuesto:**
- Energy-as-a-Service (EaaS) — contrato mensual por flujo garantizado
- Licenciamiento tecnológico a integradores

**Estado legal:** Trámite INPI en curso (Arachné Systems). La ronda ángel financia las tasas de patentamiento.

---

## Análisis JARVIS (2026-05-20)

### 🔴 Señales de alerta

1. **Tecnología "Black Box" sin datos duros.** El doc no menciona wattios, eficiencia, rendimiento en condiciones extremas, ni principio físico claro. "Arquitectura geométrica integrada" y "vectores térmicos y dinámicos en ciclo físico continuo" no son descripciones técnicas verificables.

2. **Ronda ángel solo para pagar INPI.** Piden inversión para patentar algo que aún no demostraron que funciona. El orden correcto es: prototipo → validación → patente → inversión.

3. **Sin métricas de mercado.** No hay TAM/SAM/SOM, no hay comparativos con tecnologías existentes (solar + BESS, eólico micro, generadores H2).

4. **Sin tracción.** Las "Cartas de Intención ya estructuradas" no se adjuntan ni se mencionan con quién son.

### 🟡 Lo rescatable

1. **Dolor de mercado real.** Vaca Muerta y minería en altura tienen un problema energético genuino y costoso. El gasoil en logística remota es un OPEX brutal.
2. **Segmento de telecomunicaciones rural.** Argentina tiene miles de nodos de antenas/repetidoras en zonas sin red. Hay demanda no cubierta.
3. **Tendencia macro.** La demanda de energía off-grid para data centers de IA y edge computing crece exponencialmente.

### 🟢 Potencial sinergia con ForestAI

**Conexión posible pero indirecta:**

| Escenario | Descripción | Viabilidad |
|-----------|-------------|-----------|
| Estaciones de monitoreo forestal autónomas | Sensores IoT + cámara en bosque nativo que transmiten sin red eléctrica | Alta si TEM-1 funciona a escala pequeña |
| Base de drones off-grid | Punto de carga/aterrizaje autónomo para drones de inventario forestal en zonas remotas | Media-alta — problema real en ForestAI |
| Integración producto | ForestAI + TEM-1 como solución "llave en mano" para forestación remota | Baja hasta que TEM-1 tenga prototipo validado |

**Conclusión sinergia:** La conexión más natural sería una base de drones off-grid con TEM-1 como fuente de energía. Pero es secundaria y depende totalmente de que TEM-1 exista como producto real.

---

## Preguntas clave antes de avanzar

1. ¿Tienen prototipo funcional? ¿Se puede ver?
2. ¿Qué principio físico usa? ¿Solar? ¿Eólico? ¿Piezoeléctrico? ¿Otra cosa?
3. ¿Cuántos kW genera la unidad estándar?
4. ¿Cuáles son las "Cartas de Intención" mencionadas y con quién?
5. ¿Por qué la patente va antes de la validación técnica?

---

## Archivos

- `executive-summary-original.pdf` — Documento original enviado por Pedro Lopez Peñalva
