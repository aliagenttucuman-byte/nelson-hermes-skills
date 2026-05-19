# RVC Training con Applio — Referencia Sesión May 2026

## Contexto
Objetivo: clonar voz de Lionel Messi para demo de I+D+I.
Hardware: GTX 1650 4GB VRAM, CUDA 12.2, Python 3.11.

## Por qué RVC sobre OpenVoice

OpenVoice captura timbre general pero no identidad vocal específica.
RVC hace conversión voz-a-voz profunda → resultado mucho más parecido a la persona target.
Regla: si OpenVoice "no suena parecido", usar RVC.

## Stack: Applio (fork RVC recomendado)

Repo: https://github.com/IAHispano/Applio
- Mantenido activamente
- Soporta Python 3.11 (a diferencia de rvc-python que usa fairseq incompatible)
- UI web en puerto 7860 para training y conversión

## Instalación en el servidor

```bash
git clone https://github.com/IAHispano/Applio.git /home/server/Applio
cd /home/server/Applio
python3 -m venv venv

# Paso 1: instalar torch manualmente (requirements.txt pide cu128 que no existe)
# CUDA 12.2 del servidor → usar cu121
venv/bin/pip install torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/cu121

# Paso 2: resto de dependencias
venv/bin/pip install -r requirements.txt --ignore-requires-python
```

## Preparación del Dataset de Audio

Pasos para obtener audio limpio de YouTube:

```bash
# Descargar entrevista como WAV
/home/server/openvoice-env/bin/yt-dlp \
  --extract-audio --audio-format wav --audio-quality 0 \
  -o "resources/persona_raw.%(ext)s" \
  "ytsearch1:NOMBRE entrevista habla"

# Limpiar: mono, 40kHz, filtros de ruido
ffmpeg -i persona_raw.wav \
  -af "highpass=f=80,lowpass=f=8000,afftdn=nf=-25" \
  -ar 40000 -ac 1 \
  persona_clean.wav
```

Mínimo recomendado: 5 minutos de audio limpio.
Óptimo: 10-20 minutos, sin música de fondo, sin entrevistador superpuesto.

## Entrenamiento

Con la UI de Applio (http://localhost:7860):
- Epochs recomendados para GTX 1650: 150-300
- Pitch algorithm: rmvpe (mejor calidad)
- Index rate: 0.75

Tiempo estimado GTX 1650: ~30-40 min para 200 epochs con 8 min de audio.

## Modelos Pre-entrenados en HuggingFace

**PROBLEMA CONOCIDO**: HuggingFace elimina modelos de figuras públicas constantemente.
Repos que aparecen en búsqueda suelen estar borrados al intentar descargar.

Repos encontrados en sesión (TODOS eliminados al momento de esta sesión):
- TheStinger/Lionel_Messi → "Repository not found"
- ryansama/Lionel-Messi-v2-RVC-Model → "Repository not found"
- Blane187/messi → "Repository not found"

**Alternativas:**
1. weights.gg — colección más activa, requiere cuenta gratuita
2. applio.org/models — directorio comunitario con búsqueda
3. Entrenar propio (más confiable, siempre disponible)

## Descarga autenticada de HF

```bash
# Con token de HF (read-only suficiente)
curl -L -H "Authorization: Bearer $HF_TOKEN" \
  -o modelo.pth \
  "https://huggingface.co/USER/REPO/resolve/main/modelo.pth"

# Verificar que no es error (los archivos reales son >50MB)
ls -lh modelo.pth  # Si pesa 20 bytes → "Repository not found"
cat modelo.pth     # Confirmar que no es mensaje de error
```

## API de Applio core.py — Firmas Exactas (verificadas May 2026)

```python
from core import run_preprocess_script, run_extract_script, run_train_script

# Preprocesamiento del dataset
run_preprocess_script(
    model_name='messi',
    dataset_path='assets/datasets/messi',  # carpeta con WAVs
    sample_rate=40000,
    cpu_cores=4,
    cut_preprocess='Simple',     # SIEMPRE 'Simple' o 'Automatic' — 'Skip' genera un solo chunk y rompe todo
    process_effects=False,
    noise_reduction=True,
    clean_strength=0.5,
    chunk_len=3.0,
    overlap_len=0.3,
    normalization_mode='none'
)

# Extracción de features — NOTA: NO tiene parámetro rvc_version ni pitch_guidance ni hop_length
run_extract_script(
    model_name='messi',
    f0_method='rmvpe',           # rmvpe = mejor calidad
    cpu_cores=4,
    gpu=0,                       # int, no string
    sample_rate=40000,
    embedder_model='contentvec',
    embedder_model_custom=None,
    include_mutes=2
)
```

**PITFALL CRÍTICO**: `run_extract_script` NO acepta `rvc_version`, `pitch_guidance`, ni `hop_length` como kwargs. Lanzar con esos argumentos da `TypeError: unexpected keyword argument`. Usar SOLO los parámetros de la firma de arriba.

El dataset debe copiarse a `assets/datasets/<model_name>/` dentro del directorio de Applio antes de llamar a `run_preprocess_script`.

## Inferencia Programática con VoiceConverter (verificado May 17 2026)

El modelo entrenado puede usarse directamente desde Python sin levantar la UI web.
Resultado de esta sesión: modelo `messi_9e_882s_best_epoch.pth` (9 épocas, 882 steps, ~55MB).

```python
import sys
sys.path.insert(0, '/home/server/Applio')
from rvc.infer.infer import VoiceConverter

vc = VoiceConverter()
vc.convert_audio(
    audio_input_path='/tmp/input.ogg',       # cualquier formato de audio
    audio_output_path='/tmp/output.wav',
    model_path='logs/NOMBRE/NOMBRE_Xe_YYYs_best_epoch.pth',
    index_path='logs/NOMBRE/NOMBRE.index',
    pitch=0,                  # 0 = sin cambio de tono
    f0_method='rmvpe',
    index_rate=0.75,
    clean_audio=True,
    clean_strength=0.5,
    export_format='WAV'
)
```

**Tiempo de conversión:** ~5 segundos para un audio de ~10 segundos en GTX 1650.
**Vocoder:** HiFi-GAN (seleccionado automáticamente).
**IMPORTANTE:** Correr con el CWD en `/home/server/Applio` y activar el venv antes, o usar `sys.path.insert`.

### Flujo completo TTS → RVC para demostrar una voz

```bash
# 1. Generar TTS con edge-tts o Hermes TTS
# 2. Pasar por VoiceConverter con el modelo entrenado
# 3. El resultado es un WAV listo para enviar por WhatsApp
```

Los archivos .pth e .index del modelo entrenado quedan en:
- `logs/<model_name>/<model_name>_Xe_Ys_best_epoch.pth`
- `logs/<model_name>/<model_name>.index`

El modelo también puede copiarse a `/home/server/rvc_models/<nombre>/` para organización.

## Pitfalls Conocidos

1. **fairseq + Python 3.11**: `rvc-python` usa fairseq que falla con dataclass error en Python 3.11. No usar `rvc-python`, usar Applio.
2. **torch cu128 inexistente**: requirements.txt de Applio puede referenciar wheels de CUDA que no existen. Instalar torch manualmente con cu121 para CUDA 12.x.
3. **20 bytes = repo eliminado**: curl de HF exitoso (exit 0) pero archivo de 20 bytes significa "Repository not found". Verificar tamaño SIEMPRE después de descargar.
4. **wget exit code 6 en HF**: wget falla con código 6 (auth) en repos HF. Usar curl con header Authorization en su lugar.
5. **cut_preprocess='Skip' genera UN SOLO chunk**: Si se pasa `cut_preprocess='Skip'`, el preproceso crea un único archivo WAV gigante (ej: 80MB). La extracción de features "termina OK" pero no genera ningún archivo en `f0/`, `f0_voiced/`, ni `extracted/` — falla silenciosamente. Usar SIEMPRE `cut_preprocess='Simple'` (o 'Automatic') para que el audio se corte en chunks de ~3 segundos. El entrenamiento también falla con "Not enough data" si hay un solo chunk.
6. **rmvpe.pt no descargado automáticamente**: Si los directorios `f0/` y `extracted/` quedan vacíos después de la extracción, probablemente falta el modelo predictor. La excepción se silencia en el código de Applio. Verificar con:
   ```bash
   ls /home/server/Applio/rvc/models/predictors/rmvpe.pt
   ```
   Si no existe, descargarlo:
   ```bash
   mkdir -p /home/server/Applio/rvc/models/predictors
   curl -L -H "Authorization: Bearer $HF_TOKEN" \
     -o /home/server/Applio/rvc/models/predictors/rmvpe.pt \
     "https://huggingface.co/IAHispano/Applio/resolve/main/Resources/predictors/rmvpe.pt"
   ```
7. **torchfcpe y torchcrepe no están en requirements.txt de Applio**: La extracción falla con `ModuleNotFoundError`. Instalar ambos antes de intentar extraer features:
   ```bash
   venv/bin/pip install torchfcpe torchcrepe
   ```
8. **Extracción silenciosa sin output**: Si `run_extract_script` devuelve "extracted successfully" pero los directorios están vacíos, correr el script directamente para ver el error real:
   ```bash
   cd /home/server/Applio
   venv/bin/python -c "
   from rvc.train.extract.extract import FeatureInput, load_audio_16k
   import glob, os
   fe = FeatureInput(f0_method='rmvpe', device='cuda:0')
   # Testear un archivo manualmente para ver la excepción
   "
   ```
