# Supertonic — TTS On-Device Multilingüe

**Fecha:** 18 de mayo de 2026  
**Estado:** Idea validada — pendiente de spike técnico  
**Iniciativa:** I+D+I — Nelson Acosta

---

## Resumen Ejecutivo

Supertonic es un motor de texto-a-voz (TTS) de 99M parámetros que corre 100% local/on-device vía ONNX Runtime. 31 idiomas, salida 44.1kHz, sin llamadas a la nube. Ideal para integrar en agentes, apps y demos del equipo.

**Repositorio:** https://github.com/supertone-inc/supertonic  
**Modelos:** https://huggingface.co/Supertone/supertonic-3

---

## Por qué es relevante para el equipo

| Aspecto | Detalle |
|---|---|
| **Privacidad** | Todo local, sin API externa |
| **Liviano** | 99M params vs 0.7B–2B de otros TTS open source |
| **Rápido** | Sintetiza una página web completa en <1 segundo |
| **Idiomas** | 31 incluyendo español (`es`). Tag `lang="na"` para autodetección |
| **Edge** | Corre en CPU, Raspberry Pi, navegador (WebGPU), móvil |
| **Servidor HTTP** | `supertonic serve` con endpoint `/v1/audio/speech` compatible OpenAI |
| **Voice Builder** | Clona tu voz propia y genera un JSON permanente para deploy |
| **Expresiones** | Tags inline: `<laugh>`, `<breath>`, `<sigh>`, etc. |

---

## Stack / SDKs disponibles

Python, Node.js, Browser (WebGPU), Java, C++, C#, Go, Swift, iOS, Rust, Flutter.

**Para nuestro stack (Python/FastAPI backend + React frontend):**
```bash
pip install supertonic
# o con servidor:
pip install 'supertonic[serve]'
supertonic serve --host 127.0.0.1 --port 7788
```

---

## Casos de uso para el equipo

1. **TTS productivo en demos/apps** — narración automática sin depender de servicios cloud
2. **Complemento de Whisper** — Whisper escucha, Supertonic habla: ciclo voz completo local
3. **Voice cloning para proyectos** — voz custom del cliente o del equipo
4. **Notificaciones habladas** — en dashboards, alertas, etc.

---

## Relación con herramientas existentes

| Herramienta | Rol | vs Supertonic |
|---|---|---|
| **Whisper** (daemon puerto 5001) | STT: voz → texto | Supertonic es el espejo: texto → voz |
| **Applio/RVC** | Conversión de voz / canto | No lo reemplaza; Applio es RVC, Supertonic es TTS generativo |
| **Edge-TTS** | TTS online Microsoft | Supertonic es local, más rápido, clonable |

---

## Próximos pasos

- [ ] Spike técnico: instalar y probar `supertonic serve` en el servidor
- [ ] Evaluar calidad de voz en español argentino
- [ ] Probar Voice Builder con voz propia
- [ ] Integrar endpoint `/v1/audio/speech` en alguna demo del equipo

---

## Notas

- Recomendado por Tony el 18/05/2026
- Empresa coreana (Supertone Inc.), modelo open-weight
- Actualización reciente (18/05/2026): servidor HTTP con API OpenAI-compatible
