# Case Study: NotebookLM Podcast Generator Spike

**Date:** 2025-05-13
**Spike ID:** notebooklm-podcast-eval
**Verdict:** INVALIDATED for production use
**Agent:** JARVIS / Equipo Nelson

---

## What was tested

Whether `notebooklm-py` (unofficial Python wrapper for Google NotebookLM) could automatically generate podcasts from AI news summaries and integrate into the I+D+i area's daily workflow.

## Approach

1. Installed `notebooklm-py` via pip
2. Extracted cookies from Epiphany (GNOME Web) browser where user was already logged into Google
3. Programmatically created a notebook, added a text source, triggered audio generation
4. Attempted download after processing

## Results

| Step | Result |
|------|--------|
| Install package | ✅ OK |
| Cookie extraction from Epiphany | ✅ Worked (36 cookies exported) |
| Auth initial validation | ✅ Passed `notebooklm auth check` |
| Create notebook via API | ✅ OK |
| Add text source | ✅ OK |
| Trigger audio generation | ✅ Task submitted (`bc89b798-...`) |
| Wait for processing | ⏳ ~10 min timeout |
| Download MP3 | ❌ Auth expired before completion |
| Auth durability | ❌ Failed — cookies invalidated after ~30 min |

## Key findings

### Auth fragility
- Epiphany cookies (`SID`, `__Secure-1PSID`, etc.) worked temporarily
- Google's token rotation invalidated the session after a few API calls
- `notebooklm-py`'s `AuthTokens.from_storage()` could not refresh without a live browser
- No headless re-auth path available on a server without display

### API wrapper quirks
- `NotebookLMClient` requires `async with` context manager (not obvious from docs)
- `ArtifactsAPI.generate_audio()` uses `audio_format=` / `audio_length=` kwargs (not `format=` / `length=`)
- Returns `GenerationStatus` object with `.task_id`, not `.id`
- `AudioLength` enum values are `SHORT`, `DEFAULT`, `LONG` (not `MEDIUM`)

### Processing time
- Audio generation submitted successfully but took >10 minutes
- Wrapper's `wait_for_completion()` has 300s default timeout — insufficient

## Production risk assessment

| Risk | Level | Notes |
|------|-------|-------|
| Auth breakage | HIGH | Google can invalidate cookies anytime |
| API breakage | HIGH | Undocumented internal endpoints |
| Rate limiting | MEDIUM | Observed network failures mid-spike |
| Maintenance | MEDIUM | Active repo (13K stars) but single maintainer |
| Legal/ToS | MEDIUM | Unofficial, violates Google's ToS |

## Verdict

**INVALIDATED for automated production use.**

**But:** NotebookLM remains useful as a **manual tool** accessed via browser. If Nelson wants a conversational podcast of a specific paper, he can use the web UI directly.

**Alternative:** For automated audio, use local `edge-tts` (instant, no dependencies, already integrated).

## References

- Wrapper repo: https://github.com/teng-lin/notebooklm-py
- Spike script: `~/brainstorming/2025-05-13-idi-consultora/spike-notebooklm/test_notebooklm.py`
- Conclusions doc: `~/brainstorming/2025-05-13-idi-consultora/spike-notebooklm/SPIKE-CONCLUSION.md`
