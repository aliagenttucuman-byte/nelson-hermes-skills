"""
Template: TTS → RVC voice conversion → OGG para WhatsApp
Uso: generar un audio con voz clonada por RVC y entregarlo por WhatsApp.

Prerequisitos:
- Applio instalado en /home/server/Applio con su venv
- Modelo entrenado en /home/server/Applio/logs/<modelo>/<modelo>_<N>e_<S>s_best_epoch.pth
- edge-tts disponible en el venv de hermes-agent

IMPORTANTE: verificar firma actual con:
  from core import run_infer_script; import inspect; print(inspect.signature(run_infer_script))
"""

import asyncio
import sys
import subprocess

sys.path.insert(0, '/home/server/Applio')

# ── Configuración ──────────────────────────────────────────────────────────────
TEXTO = "Hola, acá el saludo de prueba."
VOICE_TTS = "es-AR-TomasNeural"  # Edge TTS voice
MODEL_PTH = "/home/server/Applio/logs/messi/messi_49e_4802s_best_epoch.pth"
MODEL_INDEX = "/home/server/Applio/logs/messi/messi.index"
TMP_TTS = "/tmp/rvc_tts_base.mp3"
TMP_WAV = "/tmp/rvc_output.wav"
OUTPUT_OGG = "/tmp/rvc_output.ogg"
# ──────────────────────────────────────────────────────────────────────────────


async def generar_tts(texto: str, voice: str, output_path: str):
    """Genera audio TTS con edge-tts."""
    import edge_tts
    communicate = edge_tts.Communicate(texto, voice=voice)
    await communicate.save(output_path)
    print(f"TTS generado: {output_path}")


def correr_rvc(input_path: str, output_path: str, pth: str, index: str):
    """Corre inferencia RVC con Applio."""
    from core import run_infer_script
    import inspect

    # Verificar firma (cambia entre versiones de Applio)
    sig = inspect.signature(run_infer_script)
    print(f"Firma actual: {sig}")

    result = run_infer_script(
        pitch=0,
        index_rate=0.75,
        volume_envelope=1,
        protect=0.33,
        f0_method='rmvpe',          # rmvpe = mejor calidad, más lento
        input_path=input_path,
        output_path=output_path,
        pth_path=pth,
        index_path=index,
        split_audio=False,
        f0_autotune=False,
        f0_autotune_strength=1.0,
        proposed_pitch=False,
        proposed_pitch_threshold=155.0,
        clean_audio=True,
        clean_strength=0.7,
        export_format='WAV',
        embedder_model='contentvec',
        sid=0,
    )
    print(f"RVC result: {result}")
    return output_path


def wav_a_ogg(wav_path: str, ogg_path: str):
    """Convierte WAV a OGG Opus para WhatsApp."""
    subprocess.run(
        ['ffmpeg', '-i', wav_path, '-c:a', 'libopus', ogg_path, '-y'],
        check=True,
        capture_output=True,
    )
    print(f"OGG generado: {ogg_path}")
    return ogg_path


if __name__ == "__main__":
    import os
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

    # Paso 1: TTS
    asyncio.run(generar_tts(TEXTO, VOICE_TTS, TMP_TTS))

    # Paso 2: RVC
    correr_rvc(TMP_TTS, TMP_WAV, MODEL_PTH, MODEL_INDEX)

    # Paso 3: WAV → OGG
    wav_a_ogg(TMP_WAV, OUTPUT_OGG)

    print(f"\nListo para enviar por WhatsApp: {OUTPUT_OGG}")
    # En Hermes: MEDIA:/tmp/rvc_output.ogg
