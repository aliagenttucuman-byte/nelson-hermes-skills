# OpenVoice — Instalación y Configuración

Repo: https://github.com/myshell-ai/openvoice | 31.7k stars | MyShell AI

## Qué es
Clonación de voz instantánea. Con un clip de audio corto como referencia, convierte cualquier audio al timbre de esa voz. No requiere entrenamiento.

Arquitectura:
- **MeloTTS**: motor base de síntesis de voz (TTS)
- **Tone Color Converter**: transfiere el "color" de voz del clip de referencia

## Modelos V2 disponibles (109M params c/u)
- EN, EN_V2, ZH, ZH_MIX_EN, JP, KR, SP (Español), FR
- Converter universal (Tone Color Converter)

Fuente: HuggingFace `myshell-ai/OpenVoiceV2` o AWS S3 de MyShell.

## Instalación paso a paso

### 1. Pre-requisito: librerías de desarrollo de FFmpeg
**CRÍTICO**: Sin esto, `pip install -e .` falla con "pkg-config could not find libraries [avformat, avcodec, ...]".

```bash
echo "srv2026" | sudo -S apt-get install -y \
  ffmpeg libavcodec-dev libavdevice-dev libavfilter-dev \
  libavformat-dev libavutil-dev libswresample-dev libswscale-dev
```

### 2. Clonar repo y crear virtualenv aislado
```bash
cd /home/server
git clone https://github.com/myshell-ai/OpenVoice.git
python3 -m venv openvoice-env
```

### 3. Instalar OpenVoice (con workarounds Python 3.11)

**ATENCIÓN**: `pip install -e .` falla en Python 3.11 por incompatibilidades de Cython en `av`, `wavmark` y `faster-whisper`. Usar el flujo manual:

```bash
cd /home/server/OpenVoice

# 3a. Instalar av nueva (compatible con Python 3.11) ANTES de cualquier otra cosa
/home/server/openvoice-env/bin/pip install "av>=11.0.0"

# 3b. Instalar paquetes problemáticos SIN sus dependencias
/home/server/openvoice-env/bin/pip install wavmark==0.0.3 --no-deps
/home/server/openvoice-env/bin/pip install faster-whisper==0.9.0 --no-deps
/home/server/openvoice-env/bin/pip install whisper-timestamped==1.14.2 --no-deps

# 3c. Instalar el resto de dependencias (sin los conflictivos)
/home/server/openvoice-env/bin/pip install \
  "librosa==0.9.1" "pydub==0.25.1" "numpy" \
  "eng_to_ipa==0.0.2" "inflect==7.0.0" "unidecode==1.3.7" \
  "pypinyin==0.50.0" "cn2an==0.5.22" "jieba==0.42.1" \
  "langid==1.1.6" "openai" "python-dotenv"

# 3d. Instalar PyTorch con CUDA 12.1 (compatible con driver del servidor)
/home/server/openvoice-env/bin/pip install torch torchaudio \
  --index-url https://download.pytorch.org/whl/cu121

# 3e. Instalar el paquete openvoice en sí (sin reinstalar deps)
/home/server/openvoice-env/bin/pip install -e . --no-deps
```

**Por qué falla `pip install -e .` directo:**
- `wavmark==0.0.3` trae `av` viejo que tiene código Cython incompatible con Python 3.11
- `faster-whisper==0.9.0` exige `av==10.*` que también falla con Py 3.11
- `whisper-timestamped==1.14.2` arrastra numpy <3.11 y scipy <3.11
- Solución: instalar todos con `--no-deps` y manejar `av` manualmente con versión >=11

### 4. Instalar dependencias runtime que faltan (crítico para importar openvoice)

Tras instalar el paquete base, el import falla en cadena por módulos faltantes. Instalar todos de una vez:

```bash
/home/server/openvoice-env/bin/pip install \
  ctranslate2 \
  tokenizers \
  transformers \
  openai-whisper \
  dtw-python \
  huggingface-hub
```

**Por qué faltan (raíz del problema):** Se instalaron faster-whisper, wavmark y whisper-timestamped con `--no-deps`, así que sus dependencias runtime nunca se instalaron automáticamente.

Errores en cadena que aparecen si no se instalan:
1. `ModuleNotFoundError: No module named 'ctranslate2'` → faster-whisper lo necesita
2. `ModuleNotFoundError: No module named 'tokenizers'` → faster-whisper lo necesita
3. `ModuleNotFoundError: No module named 'whisper'` → whisper-timestamped lo necesita (paquete `openai-whisper`)
4. `ModuleNotFoundError: No module named 'dtw'` → whisper-timestamped lo necesita (paquete `dtw-python`)
5. `wavmark requires huggingface-hub` → wavmark lo necesita

**Nota:** ctranslate2 4.x es incompatible con `faster-whisper==0.9.0` (que pide <4), pero en la práctica funciona igual para los propósitos de OpenVoice.

### 5. Instalar MeloTTS (motor TTS base)
```bash
/home/server/openvoice-env/bin/pip install git+https://github.com/myshell-ai/MeloTTS.git
```

**NO ejecutar `python -m unidic download`** — el comando cuelga indefinidamente en este servidor.
MeloTTS importa MeCab que necesita el diccionario `unidic`. Por defecto busca en
`site-packages/unidic/dicdir/mecabrc` que no existe. Fix: copiar diccionario lite al path que busca MeCab:

```bash
UNIDIC_DIR=/home/server/openvoice-env/lib/python3.11/site-packages/unidic/dicdir
LITE_DIR=/home/server/openvoice-env/lib/python3.11/site-packages/unidic_lite/dicdir

mkdir -p $UNIDIC_DIR
cp -r $LITE_DIR/* $UNIDIC_DIR/

# mecabrc apunta al dicdir
echo "dicrc: $UNIDIC_DIR/dicrc" > $UNIDIC_DIR/mecabrc
```

**Por qué:** MeCab ignora el flag `-d` que le pasa MeloTTS y siempre busca en el path de `unidic` (el pesado). `unidic_lite` ya viene instalado con MeloTTS y tiene los archivos necesarios — solo hay que copiarlos al lugar que MeCab espera encontrarlos.

### 6. Descargar checkpoints
Desde HuggingFace (método recomendado, descarga automática):

```python
# Ejecutar dentro del virtualenv
from huggingface_hub import snapshot_download
snapshot_download(repo_id='myshell-ai/OpenVoiceV2', local_dir='checkpoints_v2')
print('Descarga completa!')
```

O manual desde: https://huggingface.co/myshell-ai/OpenVoiceV2/tree/main
Guardar en: `/home/server/OpenVoice/checkpoints_v2/converter/`

## Uso básico (V2)
```python
import torch
from openvoice import se_extractor
from openvoice.api import ToneColorConverter
from melo.api import TTS

device = "cuda:0" if torch.cuda.is_available() else "cpu"

# Cargar converter
tone_color_converter = ToneColorConverter('checkpoints_v2/converter/config.json', device=device)
tone_color_converter.load_ckpt('checkpoints_v2/converter/checkpoint.pth')

# Generar audio base con MeloTTS
model = TTS(language='ES', device=device)
speaker_ids = model.hps.data.spk2id
model.tts_to_file("Hola, soy el asistente.", list(speaker_ids.values())[0], 'tmp.wav', speed=1.0)

# Clonar voz del speaker de referencia
# IMPORTANTE: se_extractor.get_se() retorna SIEMPRE una tupla (se, audio_name)
# Usar desempaquetado en AMBAS llamadas, incluso si no se usa audio_name
source_se, _ = se_extractor.get_se('tmp.wav', tone_color_converter, vad=False)
target_se, audio_name = se_extractor.get_se('referencia.mp3', tone_color_converter, vad=True)
tone_color_converter.convert(
    audio_src_path='tmp.wav',
    src_se=source_se,
    tgt_se=target_se,
    output_path='output_clonado.wav'
)

# Para el audio de referencia del usuario se puede usar el audio de WhatsApp:
# 1. Agarrar el OGG más reciente de /home/server/.hermes/audio_cache/aud_*.ogg
# 2. Convertir a WAV: ffmpeg -y -i audio.ogg referencia.wav
# 3. Usar referencia.wav como referencia de voz
```

## Entorno del servidor
- GTX 1650 4GB VRAM — suficiente para los modelos de 109M params
- Python 3.11, virtualenv en `/home/server/openvoice-env`
- Repo en `/home/server/OpenVoice`

## Pitfalls
- Instalar **siempre** los headers libav-dev antes de `pip install -e .`
- Usar virtualenv separado para no contaminar el entorno de Hermes
- **`se_extractor.get_se()` siempre retorna tupla `(se, audio_name)`** — si se asigna a variable simple (sin desempaquetar) y luego se pasa a `tone_color_converter.convert()` como `src_se`, falla con `TypeError: zeros_like(): argument 'input' must be Tensor, not tuple`. Siempre usar `se, _ = get_se(...)` o `se, name = get_se(...)`.
- **Exportar el audio clonado a OGG con el codec correcto**: `ffmpeg -c:a vorbis` produce OGG vacío/silencioso. Usar `ffmpeg -c:a libopus -b:a 128k` para OGG reproducible, o enviar directamente el WAV.
- Licencia MIT solo para investigación; uso comercial requiere licencia de MyShell
