#!/usr/bin/env python3
"""
Spike: NotebookLM Podcast Generator
Prueba de concepto para generar podcasts de novedades de IA.

Uso:
    python3 test_notebooklm.py

Requiere:
    - notebooklm-py instalado
    - storage_state.json en ~/.notebooklm/profiles/default/
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Verificar auth
STORAGE_PATH = Path.home() / ".notebooklm" / "profiles" / "default" / "storage_state.json"
if not STORAGE_PATH.exists():
    print(f"Error: No existe {STORAGE_PATH}")
    print("Necesita hacer login primero con: notebooklm login")
    sys.exit(1)

print("Auth encontrado. Procediendo...")

# Datos de prueba: una noticia de IA
TEST_SOURCE = {
    "title": "Meta lanza Llama 4 con razonamiento multimodal",
    "summary": """
Meta ha anunciado Llama 4, su nuevo modelo de lenguaje con capacidades 
de razonamiento extendido y comprension multimodal. El modelo puede 
procesar texto, imagenes y video en una sola secuencia, marcando un 
avance significativo sobre Llama 3.3.

Caracteristicas principales:
- Razonamiento de cadena de pensamiento mejorado
- Ventana de contexto de 2 millones de tokens
- Disponible en versiones de 17B y 400B parametros
- Licencia open-source para investigacion y comercial
- Benchmarks superiores a GPT-4o en matematicas y codigo

El modelo esta disponible via HuggingFace, Ollama y la API de Meta.
Para desarrolladores con recursos limitados, la version 17B ofrece 
un balance entre rendimiento y eficiencia, corriendo en GPUs 
consumer como RTX 4090 o incluso con cuantizacion en 16GB VRAM.
"""
}

async def main():
    """Crear notebook, agregar fuente, generar podcast."""
    
    from notebooklm import NotebookLMClient
    from notebooklm.auth import AuthTokens
    
    print("Inicializando NotebookLM client...")
    auth = await AuthTokens.from_storage()
    
    async with NotebookLMClient(auth=auth) as client:
        print("Auth OK - session_id:", auth.session_id[:10] + "...")
        
        # Crear notebook
        print("Creando notebook de prueba...")
        notebook = await client.notebooks.create(
            title=f"Spike I+D+i: {TEST_SOURCE['title'][:40]}"
        )
        notebook_id = notebook.id
        print(f"Notebook creado: {notebook_id}")
        
        # Agregar fuente (texto directo)
        print("Agregando fuente...")
        source = await client.sources.add_text(
            notebook_id=notebook_id,
            content=TEST_SOURCE["summary"],
            title=TEST_SOURCE["title"]
        )
        print(f"Fuente agregada: {source.id}")
        
        # Esperar a que la fuente se procese
        print("Esperando procesamiento de fuente...")
        import time
        time.sleep(10)
        
        # Generar Audio Overview (podcast)
        print("Generando podcast (Audio Overview)...")
        print("Esto puede tardar 3-8 minutos...")
        
        from notebooklm.types import AudioFormat, AudioLength
        
        audio = await client.artifacts.generate_audio(
            notebook_id=notebook_id,
            audio_format=AudioFormat.DEEP_DIVE,
            audio_length=AudioLength.DEFAULT,
            language="es",
            instructions="Hazlo conversacional y cercano. Explicale a un desarrollador senior las implicancias tecnicas."
        )
        
        print(f"Podcast generado: {audio.task_id}")
        print(f"Estado inicial: {audio.status}")
        
        # Esperar a que esté listo
        print("Esperando que el audio esté listo...")
        audio_ready = await client.artifacts.wait_for_completion(
            notebook_id=notebook_id,
            task_id=audio.task_id
        )
        print(f"Estado final: {audio_ready.status}")
        
        if audio_ready.is_failed:
            print(f"Error: {audio_ready.error}")
            return
        
        # Listar audios para obtener el artifact_id
        audios = await client.artifacts.list_audio(notebook_id=notebook_id)
        if not audios:
            print("No se encontró audio generado")
            return
        
        latest_audio = audios[-1]  # El último generado
        print(f"Audio listo: {latest_audio.id}")
        
        # Descargar
        output_path = Path(__file__).parent / "podcast_spike_test.mp3"
        print(f"Descargando a {output_path}...")
        
        await client.artifacts.download_audio(
            notebook_id=notebook_id,
            artifact_id=latest_audio.id,
            output_path=str(output_path)
        )
        
        print(f"Listo! Podcast guardado en: {output_path}")
        print(f"Tamano: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
        
        # Limpiar notebook temporal
        print("Borrando notebook temporal...")
        await client.notebooks.delete(notebook_id=notebook_id)
        print("Notebook temporal borrado.")
        
        return str(output_path)

if __name__ == "__main__":
    try:
        podcast_path = asyncio.run(main())
        print(f"\nExitoso! Podcast en: {podcast_path}")
        print("IMPORTANTE: Este archivo es temporal. Se borrara automaticamente en 24h.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
