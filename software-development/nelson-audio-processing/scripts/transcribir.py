#!/usr/bin/env python3
"""
Transcribe audio con Whisper (OpenAI).
Uso: python3 transcribir.py <archivo_audio>
Soporta: mp3, ogg, wav, m4a, flac, etc.
"""
import sys
import whisper

if len(sys.argv) < 2:
    print("Uso: python3 transcribir.py <archivo_audio>")
    sys.exit(1)

audio_path = sys.argv[1]
print(f"Cargando modelo whisper base en GPU...")
model = whisper.load_model("base", device="cuda")
print(f"Transcribiendo: {audio_path}")
result = model.transcribe(audio_path, language="es")
print("\n" + "="*50)
print("TRANSCRIPCION:")
print("="*50)
print(result["text"])
print("="*50)
