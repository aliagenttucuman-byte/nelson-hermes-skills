#!/usr/bin/env python3
"""
Spike minimo: NotebookLM Podcast Generator
Evalua si notebooklm-py puede generar podcasts automaticos de documentos.

Uso:
    python3 test-notebooklm-podcast.py

Requiere:
    - notebooklm-py instalado: pip install "notebooklm-py[browser]"
    - Login previo: notebooklm login (o storage_state.json en ~/.notebooklm/)
    - Gateway WhatsApp corriendo en localhost:3001
"""

import asyncio
import sys
from pathlib import Path

# Configuracion
WHATSAPP_URL = "http://localhost:3001/send"
RECIPIENT = "5493816240691"  # Pablo Terian
TEST_CONTENT = """
Meta ha anunciado Llama 4, su nuevo modelo de lenguaje con capacidades
de razonamiento extendido y comprension multimodal.

Caracteristicas principales:
- Razonamiento de cadena de pensamiento mejorado
- Ventana de contexto de 2 millones de tokens
- Disponible en versiones de 17B y 400B parametros
- Licencia open-source para investigacion y comercial
"""

async def main():
    # Verificar auth
    storage = Path.home() / ".notebooklm" / "profiles" / "default" / "storage_state.json"
    if not storage.exists():
        print("Error: No hay auth. Ejecute: notebooklm login")
        sys.exit(1)

    from notebooklm import NotebookLMClient
    from notebooklm.auth import AuthTokens
    from notebooklm.types import AudioFormat, AudioLength
    import httpx

    auth = await AuthTokens.from_storage()
    async with NotebookLMClient(auth=auth) as client:
        print("Auth OK - session_id:", auth.session_id[:10] + "...")

        # Crear notebook
        nb = await client.notebooks.create(title="Spike: Llama 4")
        print(f"Notebook: {nb.id}")

        # Agregar fuente
        src = await client.sources.add_text(
            notebook_id=nb.id,
            content=TEST_CONTENT,
            title="Llama 4 Announcement"
        )
        print(f"Fuente: {src.id}")

        # Generar audio
        print("Generando podcast... (puede tardar 5-15 min)")
        import time
        time.sleep(10)  # Esperar procesamiento inicial

        audio_task = await client.artifacts.generate_audio(
            notebook_id=nb.id,
            audio_format=AudioFormat.DEEP_DIVE,
            audio_length=AudioLength.DEFAULT,
            language="es",
            instructions="Conversacional, para desarrolladores senior."
        )
        print(f"Task: {audio_task.task_id} - Status: {audio_task.status}")

        # Esperar con timeout extendido
        print("Esperando...")
        try:
            ready = await client.artifacts.wait_for_completion(
                notebook_id=nb.id,
                task_id=audio_task.task_id,
                timeout=900  # 15 minutos
            )
        except TimeoutError:
            print("Timeout esperando audio. Abortando.")
            await client.notebooks.delete(nb.id)
            sys.exit(1)

        if ready.is_failed:
            print(f"Error: {ready.error}")
            await client.notebooks.delete(nb.id)
            sys.exit(1)

        # Descargar
        audios = await client.artifacts.list_audio(notebook_id=nb.id)
        output = Path(__file__).parent / "podcast_output.mp3"
        await client.artifacts.download_audio(
            notebook_id=nb.id,
            artifact_id=audios[0].id,
            output_path=str(output)
        )
        print(f"Descargado: {output} ({output.stat().st_size/1024/1024:.1f} MB)")

        # Enviar por WhatsApp
        print("Enviando por WhatsApp...")
        async with httpx.AsyncClient() as http:
            resp = await http.post(WHATSAPP_URL, json={
                "to": RECIPIENT,
                "message": f"🎙️ Podcast de I+D+i generado!\nTamaño: {output.stat().st_size/1024/1024:.1f} MB"
            })
            print(f"WhatsApp: {resp.json()}")

        # Limpiar
        await client.notebooks.delete(nb.id)
        print("Notebook borrado. Spike completado.")

if __name__ == "__main__":
    asyncio.run(main())
