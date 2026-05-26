# Evaluacion de NotebookLM para I+D+i

**Fecha:** 2025-05-13
**Skill:** nelson-ai-agents
**Estado:** Evaluado, NO adoptado para produccion automatica

---

## Que es NotebookLM

Google NotebookLM permite subir documentos (PDFs, URLs, texto) y generar automaticamente:
- Podcasts conversacionales (Audio Overview)
- Videos
- Slide decks (PDF/PPTX)
- Quizzes y flashcards
- Infografias
- Mapas mentales
- Reportes

## API no oficial: notebooklm-py

Repo: https://github.com/teng-lin/notebooklm-py (13K+ stars)

Permite acceso programatico completo via Python/CLI.

### Limitaciones descubiertas

| Limitacion | Severidad | Detalle |
|------------|-----------|---------|
| Auth fragil | Alta | Cookies de navegador expiran en ~30 min |
| Sin re-auth headless | Alta | Requiere browser interactivo para refresh |
| API no oficial | Alta | Google puede romper endpoints sin aviso |
| Tiempo generacion | Media | 5-15 min por podcast |
| Rate limits | Media | Fallos de red observados |

### Lecciones tecnicas

```python
# Auth: usar async with + AuthTokens.from_storage()
auth = await AuthTokens.from_storage()
async with NotebookLMClient(auth=auth) as client:
    ...

# Crear notebook
nb = await client.notebooks.create(title="...")

# Agregar fuente de texto
src = await client.sources.add_text(notebook_id=nb.id, content="...", title="...")

# Generar audio: usar audio_format= + audio_length= (no format= / length=)
from notebooklm.types import AudioFormat, AudioLength
audio_task = await client.artifacts.generate_audio(
    notebook_id=nb.id,
    audio_format=AudioFormat.DEEP_DIVE,
    audio_length=AudioLength.DEFAULT,  # SHORT, DEFAULT, LONG (no MEDIUM)
    language="es",
    instructions="Prompt personalizado..."
)
# Retorna GenerationStatus con .task_id (no .id)

# Esperar con timeout extendido (default 300s es insuficiente)
ready = await client.artifacts.wait_for_completion(
    notebook_id=nb.id,
    task_id=audio_task.task_id,
    timeout=900  # 15 min
)

# Descargar: listar audios primero, luego download_audio
audios = await client.artifacts.list_audio(notebook_id=nb.id)
await client.artifacts.download_audio(
    notebook_id=nb.id,
    artifact_id=audios[0].id,
    output_path="/ruta/salida.mp3"
)
```

### Cookie extraction de Epiphany (GNOME Web)

```python
import sqlite3

db = "/home/server/.local/share/epiphany/cookies.sqlite"
conn = sqlite3.connect(db)
cursor = conn.cursor()
# Tabla: moz_cookies (formato similar a Firefox)
cursor.execute("""
    SELECT host, name, value, path, expiry, isSecure, isHttpOnly, sameSite
    FROM moz_cookies
    WHERE host LIKE '%google%' OR host LIKE '%notebooklm%'
""")
# Convertir al formato Playwright storage_state.json
```

### Veredicto

**Para produccion automatica:** INVALIDADO. Auth demasiado fragil.

**Para uso manual:** VALIDADO. Excelente calidad de podcasts via UI web.

**Alternativa para audios automaticos:** `edge-tts` local (instantaneo, sin dependencias).

## Script de spike

Ver: `scripts/test-notebooklm-podcast.py` en esta skill.

---

*Referencia generada por JARVIS - Equipo Nelson*
