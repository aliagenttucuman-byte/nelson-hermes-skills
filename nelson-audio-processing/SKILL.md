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
  - rvc
  - voice conversion
  - clonar voz
  - voice cloning
  - messi voz
  - entrenar voz
  - applio
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

## Supertonic — TTS On-Device Multilingüe

Supertonic es un motor TTS de 99M parámetros que corre 100% local vía ONNX Runtime. Es el complemento ideal de Whisper (STT): Whisper escucha, Supertonic habla.

**Repositorio:** https://github.com/supertone-inc/supertonic  
**Modelos:** https://huggingface.co/Supertone/supertonic-3

| Aspecto | Detalle |
|---|---|
| **Idiomas** | 31 incluyendo español (`es`). Tag `lang="na"` para autodetección |
| **Calidad** | 44.1kHz 16-bit WAV sin upsampler externo |
| **Velocidad** | Sintetiza una página web en <1 segundo |
| **Tamaño** | 99M params vs 0.7B–2B de otros TTS open source |
| **Voice Builder** | Clona tu voz propia y genera JSON permanente |
| **Expresiones** | Tags inline: `<laugh>`, `<breath>`, `<sigh>` |
| **Servidor HTTP** | `supertonic serve` con endpoint `/v1/audio/speech` compatible OpenAI |

### Instalación

```bash
pip install supertonic
# o con servidor:
pip install 'supertonic[serve]'
```

### Uso básico

```python
from supertonic import TTS

tts = TTS(auto_download=True)
style = tts.get_voice_style(voice_name="M1")

wav, duration = tts.synthesize(
    text="Hola Tony, soy JARVIS.",
    lang="es",
    voice_style=style,
    total_steps=8,   # 5=baja, 8=media, 12=alta
    speed=1.05,
)
tts.save_audio(wav, "output.wav")
```

### Servidor HTTP local

```bash
supertonic serve --host 127.0.0.1 --port 7788
# Endpoint OpenAI-compatible: POST /v1/audio/speech
```

### Relación con herramientas existentes

| Herramienta | Rol | vs Supertonic |
|---|---|---|
| **Whisper** (daemon puerto 5001) | STT: voz → texto | Supertonic es el espejo: texto → voz |
| **Applio/RVC** | Conversión de voz / canto | No lo reemplaza; Applio es RVC, Supertonic es TTS generativo |
| **Edge-TTS** | TTS online Microsoft | Supertonic es local, más rápido, clonable |

### Pitfall: Supertonic NO reemplaza Applio/RVC

Supertonic genera voz desde texto (TTS). Applio/RVC convierte una voz existente en otra voz (voice conversion). Son complementarios, no sustitutos. Para clonar la voz de una persona específica y hacerla "hablar" cualquier texto, se necesita RVC (o OpenVoice). Supertonic es para TTS genérico productivo.

## TTS en idiomas distintos al español

edge-tts falla al generar OGG directamente para idiomas como ruso (`ru-RU-DmitryNeural`, `ru-RU-SvetlanaNeural`). El workaround validado es generar MP3 primero y convertir a Opus con ffmpeg:

```bash
edge-tts --voice ru-RU-DmitryNeural \
  --text "Ваш текст здесь" \
  --write-media /tmp/salida.mp3

ffmpeg -y -i /tmp/salida.mp3 -c:a libopus -b:a 64k /tmp/salida.ogg
```

Voces disponibles para ruso:
- `ru-RU-DmitryNeural` — Male, Friendly
- `ru-RU-SvetlanaNeural` — Female, Friendly

Para listar voces de cualquier idioma:
```bash
edge-tts --list-voices | grep "ru-RU"
```

**Pitfall:** No usar `--write-media *.ogg` directo con voces no-latinas — produce archivo vacío sin error visible. Siempre MP3 → ffmpeg → OGG.

## Pitfalls

1. **pip no disponible**: En algunos entornos Python, `pip` no esta instalado. Solucion: `python3 -m ensurepip --upgrade`.
2. **ffmpeg no instalado**: Whisper depende de ffmpeg para decodificar audio. Si falla con errores de formato, instalar: `sudo apt-get install -y ffmpeg`.
3. **Librerías de desarrollo de FFmpeg faltantes (OpenVoice / librosa / pydub con av)**: Instalar solo `ffmpeg` no alcanza cuando se compilan paquetes como `av` (usado por librosa/pydub y OpenVoice). Si `pip install` falla con `pkg-config could not find libraries ['avformat', 'avcodec', ...]`, instalar los headers de desarrollo: `sudo apt-get install -y ffmpeg libavcodec-dev libavdevice-dev libavfilter-dev libavformat-dev libavutil-dev libswresample-dev libswscale-dev`.
4. **OpenVoice + Python 3.11 — NO usar `pip install -e .` directo**: `wavmark==0.0.3`, `faster-whisper==0.9.0` y `whisper-timestamped==1.14.2` traen `av` viejo con código Cython incompatible con Python 3.11. Instalar esos tres con `--no-deps` e instalar `av>=11.0.0` manualmente antes. Después instalar manualmente los runtime deps faltantes: `ctranslate2`, `tokenizers`, `transformers`, `openai-whisper`, `dtw-python`, `huggingface-hub`. Ver `references/openvoice-install.md` para el flujo completo.
6. **OpenVoice — los módulos faltan en cascada tras instalar con `--no-deps`**: Al importar `openvoice`, aparecen hasta 5 errores en cadena (`ctranslate2` → `tokenizers` → `whisper` → `dtw` → `huggingface-hub`). Instalar todos los runtime deps de una sola vez antes de verificar el import.
7. **OpenVoice + MeloTTS — MeCab no encuentra el diccionario unidic**: `from melo.api import TTS` falla con `RuntimeError: [ifs] no such file or directory: .../unidic/dicdir/mecabrc`. MeCab ignora el flag `-d` de MeloTTS y busca siempre en `site-packages/unidic/dicdir/`. Fix: copiar el diccionario de `unidic_lite` (que ya viene instalado) al path que busca MeCab y crear un `mecabrc` mínimo. Ver `references/openvoice-install.md` paso 5 para el fix completo. NO ejecutar `python -m unidic download` — cuelga indefinidamente en este servidor.
3. **Driver NVIDIA vs PyTorch CUDA**: Si `torch.cuda.is_available()` devuelve `False` a pesar de tener GPU, verificar que la version de CUDA de PyTorch coincida con la del driver. Ver seccion "Solucion de Problemas CUDA" arriba.
4. **Modelo descargado por primera vez**: La primera vez que se usa un modelo, se descarga desde internet (~139MB para `base`, ~461MB para `small`). Guardar en cache local en `~/.cache/whisper/`.
5. **Archivos muy largos**: Para audios de mas de 30 minutos, usar `whisper.load_model("base").transcribe()` con `condition_on_previous_text=True` (default) para mantener coherencia.
6. **Transcripcion del sistema falla**: Cuando la plataforma solo muestra `[audio received]` sin texto, los audios de WhatsApp se guardan en `/home/server/.hermes/audio_cache/aud_*.ogg` y pueden transcribirse localmente con Whisper.
7. **Bridge falla al descargar audio tras reconexion**: Si el bridge de WhatsApp (Baileys) se reconecto recientemente, puede aparecer `Failed to download audio: fetch failed`. Baileys necesita completar el sync inicial antes de poder descargar media. Solucion: esperar ~30-60s a que se estabilice la conexion, o reintentar el audio.
8. **Daemon debe estar siempre corriendo**: El daemon de Whisper (`whisper_daemon.py`) no debe arrancarse bajo demanda desde el bridge. Debe mantenerse como proceso persistente. Si el bridge intenta arrancarlo durante una reconexion, puede fallar por race condition.
9. **Precision del modelo `base` insuficiente**: Para espanol argentino, el modelo `base` comete errores frecuentes en nombres propios y vocabulario tecnico. Usar `small` como minimo en produccion.
10. **Modelo RVC con pocas épocas suena tenue o sin carácter**: El modelo Messi entrenado con solo 49 épocas (best epoch checkpoint) produce conversión audible pero con timbre débil. Para parecido convincente con una persona específica se necesitan mínimo 100-200 épocas. Si el resultado "suena raro" o sin identidad, la primera causa a revisar es el número de épocas.
11. **Flujo completo TTS → RVC para WhatsApp**: Generar audio TTS con edge-tts (MP3), pasarlo por `run_infer_script`, convertir WAV resultante a OGG con `ffmpeg -c:a libopus` y enviarlo. El bridge de WhatsApp acepta OGG/Opus como voice note nativa.

## OpenVoice V2 — Clonación de Voz Instantánea

Para clonación de voz sin entrenamiento, OpenVoice V2 usa MeloTTS como motor base y un Tone Color Converter para transferir el timbre de una referencia. Ver `references/openvoice-install.md` para instalación paso a paso en el servidor.

### Idiomas soportados y VRAM (GTX 1650 4GB)

| Código | Idioma   | GPU OK | Notas |
|--------|----------|--------|-------|
| EN     | Inglés   | ✓      | Necesita `nltk.download('averaged_perceptron_tagger_eng')` |
| ES     | Español  | ✓      | El acento argentino lo aporta el embedding de referencia, no el modelo base |
| FR     | Francés  | ✓      |       |
| JP     | Japonés  | ✓      |       |
| ZH     | Chino    | ⚠ OOM  | Usar `device='cpu'` si hay otros procesos en GPU |
| KR     | Coreano  | ⚠ OOM  | Usar `device='cpu'` si hay otros procesos en GPU |

Si se cargan todos los idiomas en secuencia en el mismo proceso, la VRAM se acumula; reiniciar entre idiomas o correr ZH/KR en un proceso separado con CPU.

### Clonar voz de referencia desde YouTube

```bash
/home/server/openvoice-env/bin/yt-dlp \
  --extract-audio --audio-format wav --audio-quality 0 \
  --match-filter "duration < 300" \
  -o "resources/celebridad_raw.%(ext)s" \
  "ytsearch1:NOMBRE entrevista español 2023"
```

Nota: uso interno/experimental únicamente. No publicar audio clonado de terceros.

## Voice Conversion con RVC (Retrieval-based Voice Conversion)

RVC es superior a OpenVoice para clonación de voz cuando se quiere parecido real a una persona específica. OpenVoice captura timbre general; RVC hace conversión profunda voz-a-voz.

### Firma correcta de run_infer_script (Applio actual)

La firma de `run_infer_script` **no tiene** `filter_radius` ni `hop_length`. Firma validada en producción:

```python
from core import run_infer_script

result = run_infer_script(
    pitch=0,
    index_rate=0.75,
    volume_envelope=1,
    protect=0.33,
    f0_method='rmvpe',
    input_path='/tmp/entrada.mp3',
    output_path='/tmp/salida.wav',
    pth_path='/home/server/Applio/logs/MODELO/MODELO_Xe_Ys_best_epoch.pth',
    index_path='/home/server/Applio/logs/MODELO/MODELO.index',
    split_audio=False,
    f0_autotune=False,
    f0_autotune_strength=1,
    proposed_pitch=False,
    proposed_pitch_threshold=155.0,
    clean_audio=True,
    clean_strength=0.7,
    export_format='WAV',
    embedder_model='contentvec',
    sid=0
)
```

Pitfall: pasar `filter_radius=` o `hop_length=` lanza `TypeError: unexpected keyword argument`. Verificar siempre con `inspect.signature(run_infer_script)` si hay dudas sobre la versión instalada.

### Stack recomendado: Applio

Applio (https://github.com/IAHispano/Applio) es el fork RVC más mantenido. Usar Applio en lugar de `rvc-python` (que tiene fairseq incompatible con Python 3.11).

```bash
# Instalación
git clone https://github.com/IAHispano/Applio.git /home/server/Applio
cd /home/server/Applio
python3 -m venv venv

# IMPORTANTE: requirements.txt pide torch==2.7.1+cu128 que NO existe en pip estándar.
# Instalar torch manualmente primero con el wheel correcto para CUDA 12.x:
venv/bin/pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Luego el resto de requirements:
venv/bin/pip install -r requirements.txt --ignore-requires-python
```

### Flujo de entrenamiento (modelo propio desde audio)

Cuando no hay modelo pre-entrenado disponible, entrenar con audio propio:

```bash
# 1. Preparar audio limpio (mono, 40kHz, filtrado)
ffmpeg -i audio_raw.wav \
  -af "highpass=f=80,lowpass=f=8000,afftdn=nf=-25" \
  -ar 40000 -ac 1 \
  audio_clean.wav

# 2. Lanzar Applio y entrenar desde UI web
cd /home/server/Applio
venv/bin/python app.py  # Abre en http://localhost:7860
```

Con 8+ minutos de audio limpio se puede entrenar un modelo básico en ~30-40 min en GTX 1650.

### Modelos pre-entrenados de HuggingFace

**Problema crítico**: HuggingFace eliminó la mayoría de modelos RVC de figuras públicas (Messi, famosos, etc.) por copyright. Repos que aparecen en búsquedas suelen devolver "Repository not found" al intentar descargar.

**Alternativas para buscar modelos:**
1. weights.gg — tiene colección activa de modelos RVC (requiere cuenta gratuita)
2. applio.org/models — directorio comunitario
3. Entrenar propio con audio descargado de YouTube (más confiable a largo plazo)

**Descarga con autenticación HF:**
```bash
curl -L -H "Authorization: Bearer $HF_TOKEN" \
  -o modelo.pth \
  "https://huggingface.co/USER/REPO/resolve/main/modelo.pth"
```

### Pitfalls RVC

1. **rvc-python + Python 3.11**: `fairseq` (dependencia de rvc-python) falla con `ValueError: mutable default ... is not allowed` en Python 3.11. Usar Applio en su lugar.
2. **torch==2.7.1+cu128 no existe**: El requirements.txt de Applio puede pedir versiones de torch con sufijo CUDA que no existen en PyPI estándar. Instalar torch manualmente con el índice oficial de PyTorch y luego `--ignore-requires-python` para el resto.
3. **Modelos HF de famosos eliminados**: Los repos de figuras públicas en HuggingFace son eliminados frecuentemente. Si wget/curl devuelve 20 bytes con "Repository not found", el repo fue borrado. No insistir — ir a weights.gg o entrenar propio.
4. **OpenVoice vs RVC**: OpenVoice clona el timbre general (bueno para voces genéricas o TTS). RVC hace conversión real de identidad vocal (necesario para imitar una persona específica convincentemente). Si el resultado de OpenVoice "no suena parecido", cambiar a RVC.
5. **`run_infer_script` firma cambiante**: La firma de `run_infer_script` en Applio cambia entre versiones. En versiones recientes (2026) **NO existen** los parámetros `filter_radius` ni `hop_length`. Verificar siempre con `inspect.signature(run_infer_script)` antes de llamar. Parámetros requeridos actuales: `pitch, index_rate, volume_envelope, protect, f0_method, input_path, output_path, pth_path, index_path, split_audio, f0_autotune, f0_autotune_strength, proposed_pitch, proposed_pitch_threshold, clean_audio, clean_strength, export_format, embedder_model`.
6. **Archivos `.pth` de 20 bytes en `rvc_models/`**: Los archivos en `/home/server/rvc_models/<modelo>/` pueden ser placeholders vacíos (20 bytes). El modelo real entrenado con Applio vive en `/home/server/Applio/logs/<modelo>/<modelo>_<epoch>e_<steps>s_best_epoch.pth`. Siempre usar el path de `logs/` para inferencia.
7. **Inferencia completa TTS→RVC→WAV→OGG**: El flujo probado y funcional es: (1) generar TTS con edge-tts a `/tmp/input.mp3`, (2) llamar `run_infer_script` con el `.pth` de `logs/`, output a `/tmp/output.wav`, (3) convertir con `ffmpeg -i output.wav -c:a libopus output.ogg`. Ver template `templates/rvc_infer_tts.py`.

### Referencias

- `references/rvc-training.md` — Flujo completo de entrenamiento RVC con Applio, incluyendo preparación de dataset y parámetros recomendados para GTX 1650

## Verificacion

Para probar que todo funciona:

```bash
python3 -c "import whisper; m = whisper.load_model('base'); print('OK')"
```

## Referencias

- `scripts/transcribir.py` — Script CLI reutilizable para transcripcion de audio manual
- `references/bridge-whisper-integration.md` — Documentacion completa de la integracion WhatsApp Bridge + Whisper Daemon, con codigo, problemas conocidos y flujo de datos
- `references/openvoice-install.md` — Instalación completa de OpenVoice V2 en el servidor (clonación de voz, MeloTTS, pitfall libav-dev, uso básico con español, pitfall tupla get_se, pitfall OGG codec)
- `templates/openvoice_clone_test.py` — Script completo para testear clonación de voz: carga converter, extrae embeddings, genera TTS en español, clona voz y exporta a OGG
- `templates/openvoice_multilang_clone.py` — Clonación de voz en los 6 idiomas soportados (EN, ES, FR, ZH, JP, KR) usando la voz de referencia del usuario; incluye exportación a OGG con libopus
- `references/rvc-training.md` — Flujo completo de entrenamiento RVC con Applio: preparación de dataset, parámetros, pitfalls CUDA y modelos pre-entrenados
- `templates/rvc_infer_tts.py` — Pipeline completo TTS→RVC→OGG listo para usar; incluye verificación de firma de `run_infer_script` y conversión final a OGG Opus para WhatsApp
- Daemon en produccion: `/home/server/whisper_daemon.py`
- Bridge modificado: `/home/server/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js`
