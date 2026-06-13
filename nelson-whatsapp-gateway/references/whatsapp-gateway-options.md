# Opciones para Enviar Mensajes WhatsApp desde Scripts/Automatizaciones

> Contexto: Nelson quiere que scripts Python puedan enviar resúmenes de IA a números de WhatsApp arbitrarios.

## Opción 1: Conexión Hermes Nativa (existente)

**Cuándo usar:** El destinatario ya tiene chat activo con Hermes (como el chat actual de Nelson).

- Los cron jobs pueden entregar output directamente al chat usando `deliver=origin` o `platform:chat_id`.
- No requiere instalar nada adicional.

**Limitación:** No se puede enviar a un número arbitrario que no esté previamente configurado en Hermes.

## Opción 2: WhatsApp Business API (oficial de Meta)

**Cuándo usar:** Solución 100% oficial, escalable, para producción empresarial.

**Requisitos:** Negocio verificado en Meta, número fijo verificado, aprobación de API, pago por mensaje.

**Pros:** Oficial, no corre riesgo de bloqueo, permite templates aprobados.
**Contras:** Burocrático, costo por mensaje.

## Opción 3: Gateway Propio con Baileys (recomendado para el equipo)

**Cuándo usar:** Flexibilidad total, sin costo por mensaje, acepta ser no oficial.

**Pros:** Gratis, flexible, cualquier número, sin aprobación.
**Contras:** No es oficial, puede ser bloqueado si detectan uso automatizado.

## Decisión: ¿Cuál elegir?

| Escenario | Recomendación |
|---|---|
| Solo necesito mandar a mi propio chat | **Hermes nativo** |
| Necesito mandar a socios/clientes específicos | **Baileys** |
| Producto final para clientes externos masivo | **Business API** |
