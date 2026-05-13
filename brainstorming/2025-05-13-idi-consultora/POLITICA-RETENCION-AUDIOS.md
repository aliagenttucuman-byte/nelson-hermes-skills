# Politica de Retencion de Archivos de Audio

**Fecha:** 2025-05-13
**Autor:** JARVIS
**Estado:** Activa

---

## Problema

Los audios generados (TTS, podcasts, notas de voz) se acumulan y pueden llenar el disco del servidor.

## Solucion

### 1. Cache de TTS (audios de JARVIS)
- **Ubicacion:** `~/.hermes/audio_cache/`
- **Retencion:** 3 dias
- **Cleanup:** Cronjob diario a las 2:00 AM

### 2. Podcasts y spikes temporales
- **Ubicacion:** `~/brainstorming/` (archivos .mp3, .mp4)
- **Retencion:** 24 horas
- **Cleanup:** Mismo cronjob

### 3. Archivos importantes
- Los audios que Nelson quiera guardar deben moverse manualmente a `~/audios-guardados/`
- Los podcasts del aggregator I+D+i se envian por WhatsApp y luego se borran del servidor

## Script de cleanup

`~/.hermes/scripts/cleanup-audio-cache.sh`

```bash
# Ejecutar manualmente:
~/.hermes/scripts/cleanup-audio-cache.sh

# Ver estado del cronjob:
cronjob action='list'
```

## Cronjob

| Campo | Valor |
|-------|-------|
| ID | `81b446dfce9b` |
| Schedule | `0 2 * * *` (2 AM diario) |
| Script | `cleanup-audio-cache.sh` |

---

*Documento generado por JARVIS*
