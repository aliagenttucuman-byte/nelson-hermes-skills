# Arduino/IoT: Opciones para el Area I+D+i

**Fecha:** 2025-05-13
**Autor:** JARVIS
**Estado:** Propuesta para aprobacion
**Destinatario:** Tony Stark (Nelson Acosta)

---

## Vision

Integrar Arduino + sensores + FastAPI + dashboards como una **capacidad producto** de la consultora. Empezar con proyectos internos y demos, luego ofrecer como servicio a clientes (incluyendo YPF).

> *"Todo lo que se puede medir, se puede mejorar."*

---

## Opcion 1: Estacion IoT Ambiental (Recomendada para empezar)

**Que es:** Arduino Uno/Nano + sensor DHT22 (temp/humedad) + sensor MQ-135 (calidad aire/CO2). Manda datos via WiFi (ESP8266) a una API FastAPI. Dashboard en React.

**Complejidad:** Baja
**Costo:** ~$15-20 USD
**Tiempo:** 1 dia armado + 1 dia software

**Aplicaciones:**
- Monitoreo de oficina/sala de servidores
- Laboratorios YPF (temperatura ambiental, calidad de aire)
- Demos para clientes de la consultora

**Stack:**
- Arduino Nano 33 IoT o ESP32 (tiene WiFi integrado)
- Sensor DHT22 (temp + humedad)
- Sensor MQ-135 (calidad del aire)
- FastAPI + PostgreSQL + Qdrant (si queremos busqueda historica)
- React dashboard (graficos en tiempo real)

**Demo visual:** Dashboard web con grafico de temperatura en vivo. Impresiona.

---

## Opcion 2: Brazo Robotico Educativo

**Que es:** 4 servomotores + Arduino Uno + joystick o control por voz (via WhatsApp/API). Mueve objetos pequenos.

**Complejidad:** Media
**Costo:** ~$30-40 USD
**Tiempo:** 2 dias armado + 1 dia software

**Aplicaciones:**
- Demos en presentaciones de la consultora
- Intro a robotica para capacitaciones
- Base para proyectos industriales (pick & place)

**Stack:**
- Arduino Uno R3
- 4x servomotores SG90
- Fuente de alimentacion externa (los servos consumen)
- Estructura 3D impresa o kit armable
- FastAPI endpoint: POST /brazo/mover {angulo1, angulo2, angulo3, angulo4}
- WhatsApp: "mover brazo a posicion A" -> JARVIS traduce -> API

---

## Opcion 3: Control de Acceso RFID/NFC

**Que es:** Arduino + lector RFID RC522 + relé + cerradura electrica. Lee tarjeta, consulta API, abre o deniega.

**Complejidad:** Media
**Costo:** ~$20-25 USD
**Tiempo:** 2 dias armado + 2 dias software

**Aplicaciones:**
- Control de acceso a oficina de la consultora
- Trazabilidad: quien entro, cuando
- Integracion con sistema de empleados
- Directamente aplicable a plantas YPF (control de acceso a areas restringidas)

**Stack:**
- Arduino Uno + Ethernet shield o ESP32 (WiFi)
- Lector RFID RC522
- Modulo rele 5V
- Cerradura electrica (opcional para demo)
- FastAPI + base de empleados + logs de acceso

---

## Comparativa Rapida

| | Ambiental | Brazo Robotico | RFID Acceso |
|---|---|---|---|
| Costo | $15-20 | $30-40 | $20-25 |
| Tiempo | 2 dias | 3 dias | 4 dias |
| Dificultad | Baja | Media | Media |
| Demo visual | Dashboard | Movimiento fisico | Led verde/rojo |
| Aplicacion YPF | Alta | Media | Alta |
| Venta a clientes | Alta (IoT) | Media (educativo) | Alta (seguridad) |

---

## Roadmap Propuesto

| Etapa | Proyecto | Entregable |
|-------|----------|------------|
| 1 | Estacion IoT ambiental | Sensor funcional + API + dashboard |
| 2 | Integrar con WhatsApp | "Temperatura oficina?" -> responde en vivo |
| 3 | Brazo robotico | Control por API y por WhatsApp |
| 4 | RFID acceso | Sistema completo de control |
| 5 | Documentar como skill | `nelson-arduino-iot` para el equipo |

---

## Primer Paso Inmediato (Si aprueba)

Si me dice "vamos", armo:

1. **Lista de compras exacta** (con links a MercadoLibre o tiendas de electronica)
2. **Sketch Arduino** (codigo C++ para leer sensor y mandar por WiFi)
3. **API FastAPI** (endpoint POST /iot/reading para recibir datos)
4. **Dashboard React** (grafico en tiempo real, 3 componentes)

Todo versionado en el repo del area I+D+i.

---

*Propuesta generada por JARVIS -- Equipo Nelson*
