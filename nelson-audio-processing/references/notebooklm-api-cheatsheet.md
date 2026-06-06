# NotebookLM API Cheatsheet

## Client Initialization

```python
from notebooklm import NotebookLMClient
from notebooklm.auth import AuthTokens

auth = await AuthTokens.from_storage()
async with NotebookLMClient(auth=auth) as client:
    # ... use client
```

## Notebooks

```python
# Create
nb = await client.notebooks.create(title="My Notebook")

# List
notebooks = await client.notebooks.list()

# Delete
await client.notebooks.delete(notebook_id=nb.id)
```

## Sources

```python
# Add text
source = await client.sources.add_text(notebook_id=nb.id, content="...", title="...")

# Add URL
source = await client.sources.add_url(notebook_id=nb.id, url="https://...")

# Add file
source = await client.sources.add_file(notebook_id=nb.id, file_path="./doc.pdf")

# List
sources = await client.sources.list(notebook_id=nb.id)

# Delete
await client.sources.delete(notebook_id=nb.id, source_id=source.id)
```

## Artifacts - Generation

```python
from notebooklm.types import AudioFormat, AudioLength, VideoFormat, VideoStyle

# Audio (podcast)
status = await client.artifacts.generate_audio(
    notebook_id=nb.id,
    audio_format=AudioFormat.DEEP_DIVE,  # DEEP_DIVE | BRIEF | CRITIQUE | DEBATE
    audio_length=AudioLength.DEFAULT,     # SHORT | DEFAULT | LONG
    language="es",
    instructions="Custom prompt"
)

# Video
status = await client.artifacts.generate_video(
    notebook_id=nb.id,
    video_format=VideoFormat.EXPLAINER,  # EXPLAINER | BRIEF | CINEMATIC
    video_style=VideoStyle.WHITEBOARD,   # WHITE_BOARD | etc
    language="es"
)

# Slide Deck
status = await client.artifacts.generate_slide_deck(notebook_id=nb.id)

# Quiz
status = await client.artifacts.generate_quiz(notebook_id=nb.id)

# Flashcards
status = await client.artifacts.generate_flashcards(notebook_id=nb.id)

# Infographic
status = await client.artifacts.generate_infographic(notebook_id=nb.id)

# Mind Map
status = await client.artifacts.generate_mind_map(notebook_id=nb.id)

# Data Table
status = await client.artifacts.generate_data_table(notebook_id=nb.id)

# Report
status = await client.artifacts.generate_report(notebook_id=nb.id)
```

## Artifacts - Polling & Download

```python
# Wait for completion (300s timeout)
result = await client.artifacts.wait_for_completion(
    notebook_id=nb.id,
    task_id=status.task_id
)

# Or manual polling
import asyncio
for i in range(60):
    audios = await client.artifacts.list_audio(notebook_id=nb.id)
    if audios and audios[0].status == "complete":
        break
    await asyncio.sleep(15)

# Download
await client.artifacts.download_audio(
    notebook_id=nb.id,
    artifact_id=audios[0].id,
    output_path="./podcast.mp3"
)

# Batch download all
artifacts = await client.artifacts.list(notebook_id=nb.id)
```

## Types Reference

### AudioFormat
- `DEEP_DIVE`
- `BRIEF`
- `CRITIQUE`
- `DEBATE`

### AudioLength
- `SHORT`
- `DEFAULT`
- `LONG`

### VideoFormat
- `EXPLAINER`
- `BRIEF`
- `CINEMATIC`

### VideoStyle
- `WHITE_BOARD`
- (otros estilos visuales)

### GenerationStatus
- `task_id: str`
- `status: str` (pending | in_progress | complete | failed)
- `is_complete()`
- `is_failed()`
- `is_in_progress()`
- `error: str | None`

## Auth

```bash
# Check auth
notebooklm auth check --test --json

# Storage state path
~/.notebooklm/profiles/default/storage_state.json
```
