#!/usr/bin/env python3
"""
Template: Generate podcast from text content using NotebookLM.
Copy and modify for specific use cases.
"""

import asyncio
from pathlib import Path
from notebooklm import NotebookLMClient
from notebooklm.auth import AuthTokens
from notebooklm.types import AudioFormat, AudioLength


async def generate_podcast(
    text_content: str,
    title: str,
    output_path: str | None = None,
    audio_format: AudioFormat = AudioFormat.DEEP_DIVE,
    audio_length: AudioLength = AudioLength.DEFAULT,
    language: str = "es",
    instructions: str = "Hazlo conversacional y cercano."
) -> str:
    """
    Generate a podcast from text content using NotebookLM.
    
    Returns path to downloaded MP3 file.
    """
    auth = await AuthTokens.from_storage()
    
    async with NotebookLMClient(auth=auth) as client:
        # Create notebook
        nb = await client.notebooks.create(title=title)
        
        try:
            # Add source
            source = await client.sources.add_text(
                notebook_id=nb.id,
                content=text_content,
                title=title
            )
            
            # Generate audio
            status = await client.artifacts.generate_audio(
                notebook_id=nb.id,
                audio_format=audio_format,
                audio_length=audio_length,
                language=language,
                instructions=instructions
            )
            
            # Poll for completion (up to 15 min)
            for i in range(60):
                audios = await client.artifacts.list_audio(notebook_id=nb.id)
                if audios and audios[0].status == "complete":
                    break
                await asyncio.sleep(15)
            else:
                raise TimeoutError("Audio generation timed out")
            
            # Download
            out = Path(output_path or f"{nb.id}.mp3")
            await client.artifacts.download_audio(
                notebook_id=nb.id,
                artifact_id=audios[0].id,
                output_path=str(out)
            )
            
            return str(out)
            
        finally:
            # Always cleanup notebook
            await client.notebooks.delete(notebook_id=nb.id)


if __name__ == "__main__":
    # Example usage
    sample_text = """
    Meta ha anunciado Llama 4, su nuevo modelo de lenguaje con capacidades
    de razonamiento extendido y comprension multimodal.
    """
    
    path = asyncio.run(generate_podcast(
        text_content=sample_text,
        title="Spike: Llama 4 Overview",
        output_path="./podcast.mp3"
    ))
    print(f"Podcast saved to: {path}")
