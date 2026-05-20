# Opciones para Enviar Mensajes WhatsApp desde Scripts/Automatizaciones

> Fecha: 2025-05-13  
> Contexto: Nelson quiere que scripts Python puedan enviar resúmenes de IA a números de WhatsApp arbitrarios.

## Opción 1: Conexión Hermes Nativa (existente)

**Cuándo usar:** El destinatario ya tiene chat activo con Hermes (como el chat actual de Nelson).

**Cómo funciona:**
- Hermes ya tiene una conexión de WhatsApp activa.
- Los cron jobs y scripts pueden entregar output directamente al chat usando `deliver=origin` o `platform:chat_id`.
- No requiere instalar nada adicional.

**Limitación:** No se puede enviar a un número arbitrario que no esté previamente configurado en Hermes. No puedo "abrir" un chat nuevo sobre la marcha.

## Opción 2: WhatsApp Business API (oficial de Meta)

**Cuándo usar:** Se necesita solución 100% oficial, escalable, para producción empresarial.

**Requisitos:**
1. Negocio verificado en Meta Business Manager
2. Número de teléfono fijo verificado
3. Aprobación de uso de la API
4. Pago por mensaje enviado (modelo conversacional)

**Pros:** Oficial, no corre riesgo de bloqueo, permite templates aprobados, analíticas.
**Contras:** Burocrático, costo por mensaje, no es inmediato.

## Opción 3: Gateway Propio con Baileys

**Cuándo usar:** Se necesita flexibilidad total, sin costo por mensaje, y se acepta que sea una conexión no oficial.

**Stack técnico:**
- Node.js + `@whiskeysockets/baileys`
- Servidor Express que expone endpoints HTTP (`POST /send-message`)
- Scripts Python hacen `requests.post()` al servidor local

**Flujo de vinculación:**
1. Ejecutar script Node.js que inicia Baileys
2. Baileys genera un **código de emparejamiento de 8 dígitos** (o un QR en terminal/imagen)
3. En el celular: WhatsApp → Vincular dispositivo → Ingresar código (o escanear QR)
4. Baileys guarda la sesión en archivo local (`auth_info_baileys/`)
5. De ahora en más, el servidor queda corriendo en segundo plano

**Código de emparejamiento vs QR:**
- El código numérico es más cómodo en GNOME porque no requiere escanear desde pantalla
- El QR se puede guardar como PNG y abrir con visor de imágenes

**Pros:** Gratis, flexible, cualquier número, sin aprobación.
**Contras:** No es oficial, puede ser bloqueado por WhatsApp si detectan uso automatizado, requiere mantener el servidor Node.js corriendo.

## Decisión: ¿Cuál elegir?

| Escenario | Recomendación |
|---|---|
| Solo necesito mandar a mi propio chat (como ahora) | **Hermes nativo** — ya funciona |
| Necesito mandar a socios/clientes específicos | **Baileys** — más rápido de implementar |
| Producto final para clientes externos masivo | **Business API** — oficial y escalable |

## Estado actual del proyecto

- Paso 1 completado (2025-05-13): Node.js v24.15.0 y Baileys instalados en `~/brainstorming/2025-05-13-ai-news-aggregator/whatsapp-gateway/`
- Pendiente: crear script de conexión, generar código de emparejamiento, exponer API HTTP
