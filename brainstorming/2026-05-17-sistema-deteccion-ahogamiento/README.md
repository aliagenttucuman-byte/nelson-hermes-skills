# Sistema de Detección de Ahogamiento en Piletas

**Fecha de brainstorming:** 17 de mayo de 2026  
**Estado:** Idea validada — pendiente de avanzar  
**Iniciativa:** I+D+I — Nelson Acosta

---

## Resumen Ejecutivo

Sistema de detección de ahogamiento en piletas (públicas, privadas, countries, hoteles) usando visión por computadora con IA. Alerta automática en tiempo real al detectar una persona en riesgo.

**Gap de mercado clave:** No existe competidor local en Argentina. Los sistemas internacionales son caros (8k-60k EUR), dejando espacio para una solución accesible.

---

## Competidores Internacionales

| Empresa | País | Precio aprox. |
|---|---|---|
| Lynxight | Israel | USD 15k-40k/año |
| Poseidon Technologies | Francia/USA | EUR 20k-60k |
| AngelEye | Italia | EUR 8k-25k (3,000+ instalaciones) |
| Aqua Alert | Australia | - |
| CPool Safety | España | - |
| Seal Innovation | Corea del Sur | - |
| NoPanic System | Alemania | - |
| Sentry Aquatic | Canadá | - |

**En Argentina:** Ningún competidor identificado → ventana de oportunidad.

---

## Stack Tecnológico Recomendado

- **Detección:** YOLOv8/v11 (Ultralytics)
- **Pose estimation:** MediaPipe
- **Tracking:** ByteTrack / DeepSORT
- **Análisis temporal:** LSTM o reglas (persona inmóvil >20 segundos)
- **Backend:** Python + FastAPI
- **Datasets:** Roboflow Universe ("drowning detection")
- **Papers:** IEEE y arXiv sobre drowning detection con deep learning

---

## Estimativo de Mercado Argentina

- **Universo total:** ~12,000 piletas comerciales/colectivas (hoteles, countries, clubes, sindicatos, gimnasios)
- **Precio propuesto:** USD 900 integración + USD 300/año mantenimiento

| Escenario | % Mercado | Clientes | Ingreso Instalación | Mantenimiento Anual | Total Año 1 |
|---|---|---|---|---|---|
| Conservador | 1% | 120 | USD 108,000 | USD 36,000 | USD 144,000 |
| Base | 2% | 240 | USD 216,000 | USD 72,000 | USD 288,000 |
| Optimista | 5% | 600 | USD 540,000 | USD 180,000 | USD 720,000 |

---

## Gaps Identificados (Diferencial)

1. Precio: los internacionales son inaccesibles para el mercado argentino
2. Soporte local: nadie da soporte en Argentina
3. Falla en aguas turbias: oportunidad técnica
4. Falsos positivos: resolver esto es clave para adopción

---

## Estado / Próximos Pasos

- [ ] Definir si es un producto propio o servicio para un cliente
- [ ] Conseguir dataset de entrenamiento (Roboflow Universe)
- [ ] Spike técnico: probar YOLO + MediaPipe en video de pileta
- [ ] Modelo de negocio detallado (VAN/TIR)
- [ ] Prototipo mínimo funcional

---

## Notas

- Brainstorming original: sesión WhatsApp 17/05/2026
- Investigación de mercado completa disponible en session_search "proyecto cámaras visión"
