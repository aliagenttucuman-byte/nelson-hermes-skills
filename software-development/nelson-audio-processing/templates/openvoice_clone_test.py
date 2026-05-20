"""
OpenVoice V2 - Test de clonación de voz
Clonar voz de un audio de referencia (ej: audio de WhatsApp del usuario).

Uso:
    cd /home/server/OpenVoice
    /home/server/openvoice-env/bin/python openvoice_clone_test.py

Prerequisitos:
    - Virtualenv en /home/server/openvoice-env con OpenVoice + MeloTTS instalados
    - Checkpoints en /home/server/OpenVoice/checkpoints_v2/
    - Audio de referencia en resources/nelson_reference.wav
      (convertir desde OGG: ffmpeg -y -i audio.ogg resources/nelson_reference.wav)
"""

import torch
import os
from openvoice import se_extractor
from openvoice.api import ToneColorConverter
from melo.api import TTS

ckpt_converter = 'checkpoints_v2/converter'
device = "cuda:0" if torch.cuda.is_available() else "cpu"
output_dir = 'outputs_v2'
os.makedirs(output_dir, exist_ok=True)

print(f"Device: {device}")

# 1. Cargar el converter
tone_color_converter = ToneColorConverter(f'{ckpt_converter}/config.json', device=device)
tone_color_converter.load_ckpt(f'{ckpt_converter}/checkpoint.pth')
print("Converter OK")

# 2. Extraer speaker embedding de la voz de referencia
reference_audio = 'resources/nelson_reference.wav'
print("Extrayendo embedding de referencia...")
# NOTA: get_se() SIEMPRE retorna tupla (se, audio_name). Usar desempaquetado.
target_se, audio_name = se_extractor.get_se(reference_audio, tone_color_converter, vad=True)
print(f"Embedding: {audio_name}")

# 3. Generar TTS base con MeloTTS en español
print("Generando TTS base...")
model = TTS(language='ES', device=device)
speaker_ids = model.hps.data.spk2id
speaker_id = list(speaker_ids.values())[0]

src_path = f'{output_dir}/tmp_es.wav'
text = "Hola, soy un sistema de inteligencia artificial. Esta es una prueba de clonación de voz."
model.tts_to_file(text, speaker_id, src_path, speed=1.0)
print("TTS base OK")

# 4. Extraer embedding del speaker base
# NOTA: usar desempaquetado aunque no se use audio_name — source_se debe ser Tensor, no tupla
source_se, _ = se_extractor.get_se(src_path, tone_color_converter, vad=False)

# 5. Convertir al timbre de referencia
output_path = f'{output_dir}/cloned_output.wav'
tone_color_converter.convert(
    audio_src_path=src_path,
    src_se=source_se,
    tgt_se=target_se,
    output_path=output_path,
    message="@OpenVoiceTest"
)
print(f"Audio clonado: {output_path}")

# 6. Convertir a OGG para envío por WhatsApp (usar libopus, NO vorbis)
import subprocess
ogg_path = output_path.replace('.wav', '.ogg')
subprocess.run([
    'ffmpeg', '-y', '-i', output_path,
    '-c:a', 'libopus', '-b:a', '128k',
    ogg_path
], check=True)
print(f"OGG listo: {ogg_path}")
