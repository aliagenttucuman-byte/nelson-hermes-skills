# Hardware IoT para Monitoreo de Flota en Tiempo Real

> Referencia para cualquier PoC/producto de flota donde el dashboard simula datos hoy
> pero necesita conectar hardware real mañana.

---

## Stack Mínimo Viable por Camión

| Componente | Hardware ejemplo | Costo estimado |
|---|---|---|
| GPS + SIM 4G | Teltonika FMB920 | USD 80-120 |
| Interfaz J1939 (datos motor) | Teltonika FMB125 o dongle | USD 80-150 |
| SIM IoT (12 meses) | Personal/Claro/Movistar AR | USD 60-120/año |
| Instalación eléctrica | Electricista automotriz | USD 50-80 |
| **TOTAL por camión** | | **USD 280-440** |

Para 10 camiones: ~USD 3.000-4.500 instalación + ~USD 800/año datos.

---

## Protocolo J1939 — Datos disponibles en camiones pesados

> **Importante:** camiones medianos/pesados usan J1939 (bus CAN 29-bit), NO OBD-II de autos.

| Dato del motor | PGN J1939 | Campo en el modelo |
|---|---|---|
| Velocidad vehículo | 65265 | `velocidad` |
| RPM motor | 61444 | — |
| Carga motor % | 61443 | — |
| Temperatura refrigerante | 65262 | `temperatura` |
| Nivel combustible % | 65276 | `combustible` |
| Consumo instantáneo L/h | 65266 | `consumo_actual_l100km` |
| Odómetro ECU | 65248 | `km_total` |
| Presión aceite | 65263 | — |
| Peso en ejes (suspensión neumática) | 65229 | `peso_carga_kg` |
| Códigos DTC (fallas activas) | 65226 | `alerta` |

> En camiones con suspensión neumática (Actros, Scania R, Volvo FH), el peso real ya está en J1939 PGN 65229. No hace falta sensor adicional.

---

## Arquitectura de integración

```
[Camión]
  Teltonika FMB920/FMB125
       │
       │ MQTT / HTTP POST (JSON — Codec 8)
       ▼
[Backend FastAPI]
  POST /api/telemetry/{truck_id}   ← parsea Codec 8 → actualiza trucks_state
       │
       │ actualiza trucks_state[] en memoria
       ▼
[WebSocket /ws/...]
       │
       ▼
[Frontend React — Dashboard en tiempo real]
```

El 100% de los campos del modelo simulado tienen equivalente en J1939/GPS real.

---

## Roadmap de integración hardware

| Fase | Descripción | Esfuerzo estimado |
|---|---|---|
| 0 (actual) | PoC simulado | ✅ Listo |
| 1 | Endpoint `/api/telemetry/{id}` + parser Teltonika Codec 8 | 1 semana |
| 2 | MQTT broker (Mosquitto/EMQX Docker) + modo híbrido real/sim | 1 semana |
| 3 | Piloto 1 camión real | 2-3 semanas |
| 4 | Rollout flota completa | Según cantidad |

---

## Parser Teltonika Codec 8 (Python)

```bash
pip install teltonika-iot-codec  # open source
```

Mapeo AVL ID → campo del modelo:
- AVL 9 → `ignition` (ON/OFF)
- AVL 16 → `velocidad` (km/h)
- AVL 24 → `velocidad_gps`
- AVL 66 → `combustible` (%)
- AVL 67 → `temperatura_motor` (°C)

---

## Alternativa low-cost: celular del conductor

| Dato | Disponible en celular | Limitación |
|---|---|---|
| GPS / posición | ✅ | Requiere app corriendo en background |
| Velocidad | ✅ | Menos preciso que sensor ECU |
| Combustible | ❌ | Requiere hardware J1939 |
| RPM / motor | ❌ | Ídem |
| Peso | ❌ | Ídem |
| Temperatura motor | ❌ | Ídem |

> El celular sirve SOLO para tracking de posición. Para datos técnicos del motor es obligatorio hardware J1939.

---

## Referencias externas

- [Teltonika FMB920 datasheet](https://teltonika-gps.com/products/trackers/fmb920)
- [SAE J1939 PGN list — CSS Electronics](https://www.csselectronics.com/pages/j1939-explained-simple-intro)
- [Python teltonika-iot-codec](https://github.com/entelect/teltonika-iot-codec)
- [EMQX MQTT broker Docker](https://www.emqx.io/docs/en/latest/deploy/install-docker.html)
