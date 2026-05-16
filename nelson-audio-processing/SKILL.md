---
name: nelson-audio-processing
title: Audio Processing para el Equipo Nelson
description: Transcripcion local de audio con Whisper y generacion de audio TTS. Procesamiento de archivos de voz sin depender de servicios en la nube.
triggers:
  - transcribir audio
  - speech to text
  - stt
  - whisper
  - convertir audio a texto
  - generar audio
  - texto a voz
  - tts
  - audio mp3
  - audio ogg
  - recibi un audio
  - transcribir archivo de voz
  - transcripcion de whatsapp
---

# Audio Processing para el Equipo Nelson

## Transcripcion Automatica de Audios de WhatsApp (Bridge + Whisper Daemon)

El bridge de WhatsApp ahora transcribe audios automaticamente antes de entregarlos al agente.

**Arquitectura:**
- `bridge.js` recibe audio → descarga → conecta al daemon Whisper en `127.0.0.1:5001` → transcribe → entrega texto al agente
- El daemon mantiene el modelo `base` cargado en GPU para transcripciones <1s

**Componentes:**
- Daemon: `/home/server/whisper_daemon.py` (debe estar siempre corriendo como servicio)
- Script CLI legacy: `/home/server/transcribir.py` (para uso manual/debug)

**Arranque del daemon (systemd o manual):**
```bash
# Verificar que esta corriendo
python3 -c "import socket; s=socket.socket(); s.connect(('127.0.0.1',5001)); s.close(); print('OK')"

# Si no esta corriendo, arrancarlo:
python3 /home/server/whisper_daemon.py &
```

## Transcripcion Local con OpenAI Whisper

Cuando el servicio de transcripcion de voz a texto de la plataforma falla (muestra `[audio received]` sin texto), o cuando se necesita transcripcion de calidad sin limites de servicio, usar **OpenAI Whisper** corriendo localmente.

### Instalacion Rapida

```bash
# 1. Asegurar que pip esta disponible
python3 -m ensurepip --upgrade

# 2. Instalar whisper
python3 -m pip install openai-whisper

# 3. Verificar que ffmpeg esta instalado (requerido por whisper)
which ffmpeg || sudo apt-get install -y ffmpeg
```

### Script de Transcripcion Reutilizable

Usar el script ubicado en `/home/server/transcribir.py`:

```bash
python3 /home/server/transcribir.py /ruta/al/audio.ogg
```

Soporta formatos: mp3, ogg, wav, m4a, flac, webm, mp4, mov, mkv, m4v.

El script usa el modelo `base` (139MB) que transcribe en espanol automaticamente.

### Modelos Disponibles

| Modelo | Tamano | VRAM | Uso Recomendado |
|--------|--------|------|-----------------|
| tiny | 39MB | ~1GB | Pruebas rapidas, menor precision |
| base | 139MB | ~1GB | Desarrollo/testing |
| small | 461MB | ~2GB | **Recomendado para produccion** - mejor precision en espanol argentino |
| medium | 1.5GB | ~5GB | Alta precision, requiere mas VRAM |
| large | 2.9GB | ~10GB | Maxima precision, muy lento en CPU |

**Nota de precision:** El modelo `base` tiene precision insuficiente para espanol argentino y nombres propios (ej: transcribe "JARVIS" como "les llavis"). Para produccion usar `small` como minimo. Una GTX 1650 4GB banca `small` sin problemas.

### Deteccion Automatica de GPU vs CPU

Whisper detecta automaticamente si hay GPU disponible:
- **Con GPU NVIDIA**: usa FP16, 5-10x mas rapido
- **Sin GPU / driver viejo**: fallback a CPU con FP32
- Mensaje esperado si el driver es viejo: `FP16 is not supported on CPU; using FP32 instead` — esto es normal y funciona igual.

**Forzar uso de GPU (cuando esta disponible):**
```python
import whisper
model = whisper.load_model("base", device="cuda")
```

En el script `/home/server/transcribir.py`, el modelo se carga con `device="cuda"` para garantizar que use la GPU.

### Solucion de Problemas CUDA (PyTorch vs Driver)

Si aparece el error: `CUDA initialization: The NVIDIA driver on your system is too old`, significa que PyTorch fue compilado para una version de CUDA mayor a la que soporta el driver.

**Caso real resuelto en esta sesion:**
- Driver NVIDIA: 535.288.01 con **CUDA 12.2**
- PyTorch instalado: **2.11.0+cu130** (CUDA 13.0) → incompatible
- Fix: desinstalar PyTorch, reinstalar version **cu121** compatible con CUDA 12.x

**Diagnostico:**
```bash
nvidia-smi  # Ver CUDA Version del driver (ej: 12.2)
python3 -c "import torch; print(torch.version.cuda)"  # Ver CUDA de PyTorch (ej: 13.0)
python3 -c "import torch; print(torch.cuda.is_available())"  # False = problema
```

**Fix — Reinstalar PyTorch compatible:**
```bash
python3 -m pip uninstall -y torch torchvision torchaudio
python3 -m pip install torch --index-url https://download.pytorch.org/whl/cu121
```

Luego verificar:
```bash
python3 -c "import torch; print(torch.cuda.is_available())"  # Debe imprimir True
python3 -c "import torch; print(torch.cuda.get_device_name(0))"  # NVIDIA GeForce GTX 1650
```

**Regla de compatibilidad:**
| Driver CUDA | PyTorch wheel a instalar |
|-------------|--------------------------|
| 12.x        | `cu121`                  |
| 11.8        | `cu118`                  |
| CPU only    | `cpu`                    |

**Resultado tras el fix:** transcripcion de audio paso de varios segundos en CPU a **< 2 segundos en GPU**.

### Uso Programatico

```python
import whisper

model = whisper.load_model("base")  # o "small", "medium"
result = model.transcribe("audio.ogg", language="es")
print(result["text"])
```

## Generacion de Audio (TTS)

El sistema usa **edge-tts** para generar audios en espanol (TomasNeural, es-AR) que se envian por WhatsApp.

```python
from edge_tts import Communicate
import asyncio

async def generar_audio(texto, ruta_salida):
    communicate = Communicate(texto, voice="es-AR-TomasNeural")
    await communicate.save(ruta_salida)
```

## Pitfalls

1. **pip no disponible**: En algunos entornos Python, `pip` no esta instalado. Solucion: `python3 -m ensurepip --upgrade`.
2. **ffmpeg no instalado**: Whisper depende de ffmpeg para decodificar audio. Si falla con errores de formato, instalar: `sudo apt-get install -y ffmpeg`.
3. **Driver NVIDIA vs PyTorch CUDA**: Si `torch.cuda.is_available()` devuelve `False` a pesar de tener GPU, verificar que la version de CUDA de PyTorch coincida con la del driver. Ver seccion "Solucion de Problemas CUDA" arriba.
4. **Modelo descargado por primera vez**: La primera vez que se usa un modelo, se descarga desde internet (~139MB para `base`, ~461MB para `small`). Guardar en cache local en `~/.cache/whisper/`.
5. **Archivos muy largos**: Para audios de mas de 30 minutos, usar `whisper.load_model("base").transcribe()` con `condition_on_previous_text=True` (default) para mantener coherencia.
6. **Transcripcion del sistema falla**: Cuando la plataforma solo muestra `[audio received]` sin texto, los audios de WhatsApp se guardan en `/home/server/.hermes/audio_cache/aud_*.ogg` y pueden transcribirse localmente con Whisper.
7. **Bridge falla al descargar audio tras reconexion**: Si el bridge de WhatsApp (Baileys) se reconecto recientemente, puede aparecer `Failed to download audio: fetch failed`. Baileys necesita completar el sync inicial antes de poder descargar media. Solucion: esperar ~30-60s a que se estabilice la conexion, o reintentar el audio.
8. **Daemon debe estar siempre corriendo**: El daemon de Whisper (`whisper_daemon.py`) no debe arrancarse bajo demanda desde el bridge. Debe mantenerse como proceso persistente. Si el bridge intenta arrancarlo durante una reconexion, puede fallar por race condition.
9. **Precision del modelo `base` insuficiente**: Para espanol argentino, el modelo `base` comete errores frecuentes en nombres propios y vocabulario tecnico. Usar `small` como minimo en produccion.

## Verificacion

Para probar que todo funciona:

```bash
python3 -c "import whisper; m = whisper.load_model('base'); print('OK')"
```

## Referencias

- `scripts/transcribir.py` — Script CLI reutilizable para transcripcion de audio manual
- `references/bridge-whisper-integration.md` — Documentacion completa de la integracion WhatsApp Bridge + Whisper Daemon, con codigo, problemas conocidos y flujo de datos
- Daemon en produccion: `/home/server/whisper_daemon.py`
- Bridge modificado: `/home/server/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js`
