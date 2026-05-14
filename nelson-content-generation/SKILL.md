---
name: nelson-content-generation
title: Content Generation - Generacion de Contenido con IA
description: Generacion de contenido multimodal con IA para el equipo Nelson. Podcasts, audio, slides, quizzes, resumenes. Integracion con NotebookLM, edge-tts, y herramientas locales.
skill: nelson-content-generation
author: equipo-nelson
version: 1.0.0
keywords: [content-generation, notebooklm, podcast, tts, audio, slides, quiz, multimodal]
dependencies: [nelson-llm-generation, nelson-audio-processing]
---

# Content Generation - Equipo Nelson

## Objetivo

Generar contenido de valor a partir de documentos tecnicos, noticias, y papers de IA. Formatos: podcasts, audio, slides, quizzes, flashcards, resumenes. Todo integrado con el stack del equipo.

## Herramientas Principales

| Herramienta | Uso | Self-hosted | Velocidad |
|-------------|-----|-------------|-----------|
| **NotebookLM** | Podcasts conversacionales, slides, quizzes | No (Google Cloud) | 5-10 min |
| **edge-tts** | Audio local rapido de textos | Si | Segundos |
| **Ollama** | Resumenes, analisis de contenido | Si (local) | Segundos |

---

## NotebookLM Integration

### Instalacion

```bash
# Core (sin navegador)
pip install notebooklm-py

# Con navegador para login
pip install "notebooklm-py[browser]"
python3 -m playwright install chromium

# Con soporte de cookies para importar desde navegadores
pip install "notebooklm-py[cookies]"
```

### Autenticacion

NotebookLM requiere cookies de sesion de Google. Dos caminos:

**Opcion A: Login via navegador (interactivo)**

```bash
notebooklm login
# Abre Chromium, hace login con Google, guarda cookies
```

**Opcion B: Importar cookies desde navegador existente (headless)**

Epiphany (Gnome Web) guarda cookies en:
```
~/.local/share/epiphany/cookies.sqlite  # Tabla: moz_cookies
```

Script para exportar cookies de Epiphany al formato Playwright:
```python
import sqlite3
import json
from pathlib import Path

def export_epiphany_cookies():
    src = Path.home() / ".local/share/epiphany/cookies.sqlite"
    conn = sqlite3.connect(str(src))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT host, name, value, path, expiry, isSecure, isHttpOnly, sameSite
        FROM moz_cookies
        WHERE host LIKE '%google%' OR host LIKE '%notebooklm%'
    """)
    cookies = []
    for row in cursor.fetchall():
        host, name, value, path, expiry, isSecure, isHttpOnly, sameSite = row
        sameSite_map = {0: "None", 1: "Lax", 2: "Strict"}
        expires = expiry / 1000000 if expiry and expiry > 9999999999 else expiry or -1
        domain = host if host.startswith('.') else '.' + host
        cookies.append({
            "name": name, "value": value, "domain": domain, "path": path or "/",
            "expires": expires, "httpOnly": bool(isHttpOnly),
            "secure": bool(isSecure), "sameSite": sameSite_map.get(sameSite, "Lax")
        })
    conn.close()
    
    out = Path.home() / ".notebooklm/profiles/default/storage_state.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"cookies": cookies, "origins": []}, indent=2))
    return out
```

Verificar auth:
```bash
notebooklm auth check --test --json
```

### API Asincrona - Patron Correcto

```python
import asyncio
from notebooklm import NotebookLMClient
from notebooklm.auth import AuthTokens
from notebooklm.types import AudioFormat, AudioLength

async def generate_podcast(text_content: str, title: str) -> str:
    auth = await AuthTokens.from_storage()
    
    async with NotebookLMClient(auth=auth) as client:
        # 1. Crear notebook
        nb = await client.notebooks.create(title=title)
        
        # 2. Agregar fuente (texto, URL, archivo)
        source = await client.sources.add_text(
            notebook_id=nb.id,
            content=text_content,
            title=title
        )
        
        # 3. Generar audio (podcast conversacional)
        # Tarda 5-10 minutos en Google Cloud
        status = await client.artifacts.generate_audio(
            notebook_id=nb.id,
            audio_format=AudioFormat.DEEP_DIVE,   # DEEP_DIVE | BRIEF | CRITIQUE | DEBATE
            audio_length=AudioLength.DEFAULT,      # SHORT | DEFAULT | LONG
            language="es",
            instructions="Hazlo conversacional. Explicale a un dev senior."
        )
        
        # 4. Esperar completion (timeout 300s por defecto)
        # Para audios largos, puede tardar mas. Hacer polling manual.
        import time
        for i in range(60):  # 15 min max
            audios = await client.artifacts.list_audio(notebook_id=nb.id)
            if audios and audios[0].status == "complete":
                break
            time.sleep(15)
        
        # 5. Descargar
        output_path = f"/tmp/{nb.id}.mp3"
        await client.artifacts.download_audio(
            notebook_id=nb.id,
            artifact_id=audios[0].id,
            output_path=output_path
        )
        
        # 6. Limpiar notebook temporal (no acumular en Google)
        await client.notebooks.delete(notebook_id=nb.id)
        
        return output_path

# Ejecutar
# asyncio.run(generate_podquet("texto...", "Titulo"))
```

### Tipos de Contenido Soportados

| Tipo | Metodo API | Duracion tipica |
|------|------------|-----------------|
| Audio Overview (podcast) | `generate_audio()` | 5-10 min |
| Video | `generate_video()` | 10-15 min |
| Slide Deck | `generate_slide_deck()` | 3-5 min |
| Infographic | `generate_infographic()` | 2-4 min |
| Quiz | `generate_quiz()` | 1-2 min |
| Flashcards | `generate_flashcards()` | 1-2 min |
| Data Table | `generate_data_table()` | 1-2 min |
| Mind Map | `generate_mind_map()` | 1-2 min |

### Consideraciones para el Equipo Nelson

- **Recursos**: NotebookLM corre en Google Cloud, no consume VRAM local
- **Latencia**: 5-10 min por podcast. No es sincrono. Usar background jobs.
- **Limpieza**: Siempre borrar notebooks temporales despues de descargar
- **Auth**: Las cookies expiran. Si falla, re-exportar desde Epiphany
- **Rate limits**: Google puede throtlear uso intensivo

---

## edge-tts (Audio Local Rapido)

Para textos cortos o cuando NotebookLM es overkill:

```bash
# Instalar
pip install edge-tts

# Generar audio
edge-tts --text "Resumen de noticias de IA" --voice es-AR-TomasNeural --write-media output.mp3
```

Ver skill `nelson-audio-processing` para mas detalles.

---

## Pipeline Recomendado: Noticia -> Podcast -> WhatsApp

```
1. AI News Aggregator levanta noticia
    |
2. Filtro: interesante para I+D+i?
    |
3. NotebookLM: genera podcast (async, background)
    |
4. Cuando listo: descarga MP3
    |
5. WhatsApp Gateway: envia a Nelson
    |
6. Cleanup: borra MP3 local + notebook cloud
```

---

## Politica de Retencion de Archivos

Todo contenido generado es **temporal por defecto**:

| Tipo | Retencion | Metodo |
|------|-----------|--------|
| Cache TTS | 3 dias | Cronjob diario 2am |
| Podcasts/MP3 | 24 horas | Mismo cronjob |
| Notebooks cloud | Inmediato | Borrar post-descarga |
| Audios guardados | Indefinido | Mover a ~/audios-guardados/ manualmente |

Script de cleanup: `~/.hermes/scripts/cleanup-audio-cache.sh`

---

## Checklist

- [ ] Auth de NotebookLM validado (`notebooklm auth check`)
- [ ] Cookies exportadas desde Epiphany si es headless
- [ ] Notebook creado y fuente agregada
- [ ] Audio generado con formato/length correctos
- [ ] Polling de estado hasta `complete`
- [ ] Descarga exitosa verificada
- [ ] Notebook temporal borrado
- [ ] Archivo local borrado o movido a guardados

## Pitfalls

- `NotebookLMClient` requiere `async with` context, no instanciar directo
- `generate_audio()` devuelve `GenerationStatus` con `task_id`, no `id`
- `AudioLength.MEDIUM` no existe. Valores validos: `SHORT`, `DEFAULT`, `LONG`
- `wait_for_completion()` tiene timeout de 300s. Podcasts pueden tardar mas; usar polling manual
- No usar `time.sleep()` en codigo async sin `await asyncio.sleep()`
- Google detecta navegadores automatizados (Playwright) y bloquea login. Usar import de cookies

## Referencias

- `references/notebooklm-api-cheatsheet.md` - Metodos y enums completos
- `scripts/export-epiphany-cookies.py` - Script para extraer cookies de Epiphany
- `scripts/generate-podcast.py` - Spike completo: noticia -> podcast -> MP3
