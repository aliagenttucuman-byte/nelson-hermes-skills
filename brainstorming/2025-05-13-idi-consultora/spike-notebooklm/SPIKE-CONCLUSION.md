# Spike: NotebookLM Podcast Generator

**Fecha:** 2025-05-13
**Estado:** COMPLETADO — Evaluado, NO adoptado para producción
**Responsable:** JARVIS
**Solicitante:** Tony Stark (Nelson Acosta)

---

## Objetivo del Spike

Evaluar si `notebooklm-py` (API no oficial de Google NotebookLM) puede generar podcasts automáticos a partir de noticias de IA, integrado con el área I+D+i de la consultora.

## Hipótesis

> *"Podemos automatizar la generación de podcasts de novedades de IA usando NotebookLM y enviarlos por WhatsApp a Nelson para consumo mientras entrena."*

---

## Resultados

| Paso | Resultado | Tiempo |
|------|-----------|--------|
| Instalar `notebooklm-py` | ✅ OK | ~2 min |
| Extraer cookies de Epiphany (GNOME Web) | ✅ OK | ~10 min |
| Autenticación inicial válida | ✅ OK | ~5 min |
| Crear notebook por API | ✅ OK | ~2 seg |
| Agregar fuente de texto | ✅ OK | ~5 seg |
| Enviar generación de podcast | ✅ OK | ~2 seg |
| Esperar procesamiento en Google | ⚠️ ~10 min | Tarda pero funciona |
| Descargar MP3 | ❌ FALLÓ | Auth expirada |
| Auth durable | ❌ NO | Expira rápidamente |

---

## Problemas Encontrados

### 1. Autenticación No Durable
Las cookies extraídas de un navegador (Epiphany) funcionan temporalmente pero Google las invalida después de pocas peticiones. Requiere re-login frecuente.

### 2. API No Oficial = Fragilidad
`notebooklm-py` usa APIs internas no documentadas de Google. Pueden cambiar en cualquier momento sin aviso.

### 3. Tiempo de Generación
Los podcasts tardan 5-15 minutos en generarse (dos voces IA conversando). No es viable para flujos en tiempo real.

### 4. Dependencia de Infraestructura Externa
100% dependiente de Google. Sin conexión, sin servicio. Sin Google, sin servicio.

---

## Lecciones Aprendidas

1. **NotebookLM es potente** para uso manual: genera podcasts de calidad, flashcards, quizzes, slides.
2. **No es viable para automatización** crítica por la fragilidad de la auth y la API no oficial.
3. **Para audios automáticos**, `edge-tts` local es superior: instantáneo, sin dependencias, sin costo.
4. **Si se necesita podcast conversacional**, usar NotebookLM manualmente desde el navegador ocasionalmente.

---

## Decisión

❌ **NO adoptar** `notebooklm-py` para producción en el área I+D+i.

✅ **Sí mantener** como herramienta manual ocasional si Nelson quiere generar un podcast conversacional de un paper específico.

✅ **Seguir usando** `edge-tts` local para todos los audios automáticos del equipo (noticias, resúmenes, alertas).

---

## Artefactos del Spike

- `test_notebooklm.py` — script de prueba
- `storage_state.json` — cookies exportadas (expiradas, no reutilizar)
- Este documento de conclusión

---

*Spike completado pasito a pasio — Equipo Nelson*
