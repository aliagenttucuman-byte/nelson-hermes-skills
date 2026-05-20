"""
OpenVoice V2 - Clonación de voz en múltiples idiomas
Genera audio en 6 idiomas usando la voz de referencia del usuario.

Uso:
    cd /home/server/OpenVoice
    /home/server/openvoice-env/bin/python openvoice_multilang_clone.py

Prerrequisitos:
    - Virtualenv en /home/server/openvoice-env con OpenVoice + MeloTTS instalados
    - Checkpoints en /home/server/OpenVoice/checkpoints_v2/
    - Audio de referencia en resources/nelson_reference.wav
      (convertir desde OGG: ffmpeg -y -i audio.ogg resources/nelson_reference.wav)

Idiomas soportados por MeloTTS V2: EN, ES, FR, ZH, JP, KR
"""

import torch
import os
import subprocess
from openvoice import se_extractor
from openvoice.api import ToneColorConverter
from melo.api import TTS

ckpt_converter = 'checkpoints_v2/converter'
device = "cuda:0" if torch.cuda.is_available() else "cpu"
output_dir = 'outputs_v2/multilang'
os.makedirs(output_dir, exist_ok=True)

print(f"Device: {device}")

# Cargar converter
tone_color_converter = ToneColorConverter(f'{ckpt_converter}/config.json', device=device)
tone_color_converter.load_ckpt(f'{ckpt_converter}/checkpoint.pth')

# Embedding de la voz de referencia del usuario
reference_audio = 'resources/nelson_reference.wav'
target_se, _ = se_extractor.get_se(reference_audio, tone_color_converter, vad=True)
print("Embedding de referencia extraído OK")

# Textos por idioma — personalizar según necesidad
texts = {
    'EN': ("English",  "Hello, I am an artificial intelligence system. This is a voice cloning test, pretty cool right?"),
    'ES': ("Español",  "Che, soy un sistema de inteligencia artificial. Esta es una prueba de clonación de voz, ¿entendés?"),
    'FR': ("Français", "Bonjour, je suis un système d'intelligence artificielle. Ceci est un test de clonage vocal."),
    'ZH': ("中文",      "你好，我是一个人工智能系统。这是一个声音克隆测试，很厉害吧？"),
    'JP': ("日本語",    "こんにちは、私は人工知能システムです。これは音声クローニングのテストです。"),
    'KR': ("한국어",    "안녕하세요, 저는 인공지능 시스템입니다. 이것은 음성 복제 테스트입니다."),
}

results = []
for lang_code, (lang_name, text) in texts.items():
    print(f"\n→ Generando {lang_name} ({lang_code})...")
    try:
        model = TTS(language=lang_code, device=device)
        speaker_ids = model.hps.data.spk2id
        speaker_id = list(speaker_ids.values())[0]

        src_path = f'{output_dir}/tmp_{lang_code}.wav'
        model.tts_to_file(text, speaker_id, src_path, speed=0.95)

        # NOTA: get_se() siempre retorna tupla — desempaquetar siempre
        source_se, _ = se_extractor.get_se(src_path, tone_color_converter, vad=False)

        out_wav = f'{output_dir}/cloned_{lang_code}.wav'
        tone_color_converter.convert(
            audio_src_path=src_path,
            src_se=source_se,
            tgt_se=target_se,
            output_path=out_wav,
            message="@JARVIS"
        )

        # Exportar a OGG con libopus (NO usar vorbis — produce audio silencioso)
        out_ogg = f'{output_dir}/cloned_{lang_code}.ogg'
        subprocess.run([
            'ffmpeg', '-y', '-i', out_wav,
            '-c:a', 'libopus', '-b:a', '128k', out_ogg
        ], capture_output=True, check=True)

        print(f"  ✓ {lang_name} → {out_ogg}")
        results.append((lang_name, out_ogg))

    except Exception as e:
        print(f"  ✗ ERROR en {lang_name}: {e}")

print("\n=== RESULTADOS ===")
for lang, path in results:
    print(f"  {lang}: {path}")
