---
name: spike
description: "Throwaway experiments to validate an idea before build."
version: 1.0.0
author: Hermes Agent (adapted from gsd-build/get-shit-done)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spike, prototype, experiment, feasibility, throwaway, exploration, research, planning, mvp, proof-of-concept]
    related_skills: [sketch, writing-plans, subagent-driven-development, plan]
---

# Spike

Use this skill when the user wants to **feel out an idea** before committing to a real build — validating feasibility, comparing approaches, or surfacing unknowns that no amount of research will answer. Spikes are disposable by design. Throw them away once they've paid their debt.

Load this when the user says things like "let me try this", "I want to see if X works", "spike this out", "before I commit to Y", "quick prototype of Z", "is this even possible?", or "compare A vs B".

## When NOT to use this

- The answer is knowable from docs or reading code — just do research, don't build
- The work is production path — use `writing-plans` / `plan` instead
- The idea is already validated — jump straight to implementation

## Regla de oro: Validar antes de integrar (Nelson)

**Antes de incorporar cualquier librería de terceros a un proyecto**, hacer un spike de 15 minutos en el entorno REAL donde va a correr (host o Docker, según el proyecto).

Checklist mínimo del spike de validación:
- [ ] La librería está disponible en el entorno target (pip install funciona)
- [ ] La llamada básica devuelve datos reales (no solo "no da error")
- [ ] No hay bloqueo de red (especialmente si corre en Docker)
- [ ] El entorno (host vs container) es el correcto para el tipo de llamada

Esto ahorra 1-2 horas de debugging en caliente. Si el spike falla, evaluar con Nelson antes de continuar (regla de los 3 intentos).

## If the user has the full GSD system installed

If `gsd-spike` shows up as a sibling skill (installed via `npx get-shit-done-cc --hermes`), prefer **`gsd-spike`** when the user wants the full GSD workflow: persistent `.planning/spikes/` state, MANIFEST tracking across sessions, Given/When/Then verdict format, and commit patterns that integrate with the rest of GSD. This skill is the lightweight standalone version for users who don't have (or don't want) the full system.

## Core method

Regardless of scale, every spike follows this loop:

```
decompose  →  research  →  build  →  verdict
   ↑__________________________________________↓
                  iterate on findings
```

### 1. Decompose

Break the user's idea into **2-5 independent feasibility questions**. Each question is one spike. Present them as a table with Given/When/Then framing:

| # | Spike | Validates (Given/When/Then) | Risk |
|---|-------|----------------------------|------|
| 001 | websocket-streaming | Given a WS connection, when LLM streams tokens, then client receives chunks < 100ms | High |
| 002a | pdf-parse-pdfjs | Given a multi-page PDF, when parsed with pdfjs, then structured text is extractable | Medium |
| 002b | pdf-parse-camelot | Given a multi-page PDF, when parsed with camelot, then structured text is extractable | Medium |

**Spike types:**
- **standard** — one approach answering one question
- **comparison** — same question, different approaches (shared number, letter suffix `a`/`b`/`c`)

**Good spike questions:** specific feasibility with observable output.
**Bad spike questions:** too broad, no observable output, or just "read the docs about X".

**Order by risk.** The spike most likely to kill the idea runs first. No point prototyping the easy parts if the hard part doesn't work.

**Skip decomposition** only if the user already knows exactly what they want to spike and says so. Then take their idea as a single spike.

### 2. Align (for multi-spike ideas)

Present the spike table. Ask: "Build all in this order, or adjust?" Let the user drop, reorder, or re-frame before you write any code.

### 3. Research (per spike, before building)

Spikes are not research-free — you research enough to pick the right approach, then you build. Per spike:

1. **Brief it.** 2-3 sentences: what this spike is, why it matters, key risk.
2. **Surface competing approaches** if there's real choice:

   | Approach | Tool/Library | Pros | Cons | Status |
   |----------|-------------|------|------|--------|
   | ... | ... | ... | ... | maintained / abandoned / beta |

3. **Pick one.** State why. If 2+ are credible, build quick variants within the spike.
4. **Skip research** for pure logic with no external dependencies.

Use Hermes tools for the research step:

- `web_search("python websocket streaming libraries 2025")` — find candidates
- `web_extract(urls=["https://websockets.readthedocs.io/..."])` — read the actual docs (returns markdown)
- `terminal("pip show websockets | grep Version")` — check what's installed in the project's venv

For libraries without docs pages, clone and read their `README.md` / `examples/` via `read_file`. Context7 MCP (if the user has it configured) is also a good source — `mcp_*_resolve-library-id` then `mcp_*_query-docs`.

### 4. Build

One directory per spike. Keep it standalone.

```
spikes/
├── 001-websocket-streaming/
│   ├── README.md
│   └── main.py
├── 002a-pdf-parse-pdfjs/
│   ├── README.md
│   └── parse.js
└── 002b-pdf-parse-camelot/
    ├── README.md
    └── parse.py
```

**Bias toward something the user can interact with.** Spikes fail when the only output is a log line that says "it works." The user wants to *feel* the spike working. Default choices, in order of preference:

1. A runnable CLI that takes input and prints observable output
2. A minimal HTML page that demonstrates the behavior
3. A small web server with one endpoint
4. A unit test that exercises the question with recognizable assertions

**Depth over speed.** Never declare "it works" after one happy-path run. Test edge cases. Follow surprising findings. The verdict is only trustworthy when the investigation was honest.

**Avoid** unless the spike specifically requires it: complex package management, build tools/bundlers, Docker, env files, config systems. Hardcode everything — it's a spike.

**Building one spike** — a typical tool sequence:

```
terminal("mkdir -p spikes/001-websocket-streaming")
write_file("spikes/001-websocket-streaming/README.md", "# 001: websocket-streaming\n\n...")
write_file("spikes/001-websocket-streaming/main.py", "...")
terminal("cd spikes/001-websocket-streaming && python3 main.py")
# Observe output, iterate.
```

**Parallel comparison spikes (002a / 002b) — delegate.** When two approaches can run in parallel and both need real engineering (not 10-line prototypes), fan out with `delegate_task`:

```
delegate_task(tasks=[
    {"goal": "Build 002a-pdf-parse-pdfjs: ...", "toolsets": ["terminal", "file", "web"]},
    {"goal": "Build 002b-pdf-parse-camelot: ...", "toolsets": ["terminal", "file", "web"]},
])
```

Each subagent returns its own verdict; you write the head-to-head.

### 5. Verdict

Each spike's `README.md` closes with:

```markdown
## Verdict: VALIDATED | PARTIAL | INVALIDATED

### What worked
- ...

### What didn't
- ...

### Surprises
- ...

### Recommendation for the real build
- ...
```

**VALIDATED** = the core question was answered yes, with evidence.
**PARTIAL** = it works under constraints X, Y, Z — document them.
**INVALIDATED** = doesn't work, for this reason. This is a successful spike.

## Comparison spikes

When two approaches answer the same question (002a / 002b), build them **back to back**, then do a head-to-head comparison at the end:

```markdown
## Head-to-head: pdfjs vs camelot

| Dimension | pdfjs (002a) | camelot (002b) |
|-----------|--------------|----------------|
| Extraction quality | 9/10 structured | 7/10 table-only |
| Setup complexity | npm install, 1 line | pip + ghostscript |
| Perf on 100-page PDF | 3s | 18s |
| Handles rotated text | no | yes |

**Winner:** pdfjs for our use case. Camelot if we need table-first extraction later.
```

## Special case: APIs de datos gubernamentales (Argentina)

APIs como `datos.gob.ar` (Secretaría de Energía) tienen quirks específicos:

1. **SSL roto** — certificado inválido. `curl`/`wget`/`requests` fallan por defecto. Usar `--no-check-certificate` o `verify=False`.
2. **Último período siempre incompleto** — el mes/año más reciente suele tener solo 1-5 registros mientras el resto tienen 40-70. Calcular market shares o totales sobre ese período da resultados absurdos (>100%).

   **Fix obligatorio:**
   ```python
   counts = df.groupby('fecha').size()
   fecha_completa = counts[counts >= 20].index.max()  # umbral según dataset
   ```

3. **Encoding UTF-8 con BOM** — leer siempre con `pd.read_csv(..., encoding='utf-8-sig')`.

Ver `nelson-brainstorming/references/datos-energia-argentina.md` para endpoints y pipeline completo del spike de energía (petróleo/gas por empresa, 2009-presente).

## Special case: servicios que usan APIs internas (Power BI, Looker, etc.)

Cuando el spike necesita extraer datos de un servicio SaaS que los muestra en browser pero no expone una API pública directa, usar **Playwright network interception** para capturar las llamadas internas que hace el JS del servicio.

**Patrón general:**
```python
async def intercept_api_calls(url: str, filter_fn):
    from playwright.async_api import async_playwright
    captured = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox'])
        page = await (await browser.new_context()).new_page()
        
        async def on_response(response):
            if filter_fn(response.url):
                body = await response.body()
                captured.append({'url': response.url, 'body': json.loads(body)})
        
        page.on('response', on_response)
        try:
            await page.goto(url, wait_until='networkidle', timeout=45000)
        except: pass
        await asyncio.sleep(8)  # lazy queries
        await browser.close()
    return captured
```

**Aplicado a Power BI público:** filtrar `querydata` en `analysis.windows.net` → captura datos en formato DSR. Ver `nelson-external-integrations` → `references/powerbi-public-embed-wabi.md` para parser DSR completo y ejemplo validado con datos del gobierno argentino.

**Por qué urllib/requests directo NO funciona:** estos servicios hacen fingerprinting de TLS + headers + cookies. Sin el handshake de browser real, devuelven `403` o `Remote end closed`.

---

## Special case: spikes con OpenUI (Generative UI)

Al hacer spikes del framework `thesysdev/openui`, hay dos pitfalls que aparecen inmediatamente:

**1. crypto.randomUUID bloqueado en HTTP externo**
El browser bloquea `crypto.randomUUID` en HTTP con IP no-localhost (ej: Tailscale). El error es `TypeError: crypto.randomUUID is not a function`. Fix: agregar polyfill en `layout.tsx`. Ver skill `nelson-generative-ui` para el código exacto.

**2. Stream SSE crudo rompe el parser de OpenUI**
Si el `route.ts` del frontend hace proxy a un backend que re-emite bytes SSE crudos, el parser de OpenUI falla con `SyntaxError: Unexpected token 'd', "data: {"id"... is not valid JSON`. OpenUI espera el formato del SDK de OpenAI (`response.toReadableStream()`), no SSE crudo.
Fix: el frontend debe llamar directamente al SDK de OpenAI con `baseURL` del proveedor, y solo consultar al backend para el `systemPrompt`. Ver skill `nelson-generative-ui`.

**3. Scaffold hardcodea modelo gpt-5.2**
`npx @openuidev/cli@latest create` genera `model: "gpt-5.2"`. Cambiar siempre por el modelo correcto.

**Groq es compatible con OpenAI SDK** — `baseURL: "https://api.groq.com/openai/v1"`, modelo validado: `llama-3.3-70b-versatile`.

---

## Special case: evaluating unofficial/third-party APIs

When spiking a wrapper, unofficial SDK, or community project that reverse-engineers a proprietary service (e.g. `notebooklm-py` for Google NotebookLM), add these specific checks to the standard loop:

| Check | Why it matters | How to test |
|-------|---------------|-------------|
| **Auth durability** | Unofficial APIs often rely on scraped cookies or undocumented OAuth flows that expire quickly. | Verify the auth survives >1 hour and multiple API calls. Log the exact expiry behavior. |
| **Rate limits / throttling** | Reverse-engineered endpoints usually have hidden, undocumented limits. | Hammer the endpoint gently: 5-10 sequential calls, observe any `429`, `403`, or sudden `302` redirects. |
| **ToS / legal risk** | Using unofficial APIs may violate the provider's terms. | Document the ToS clause explicitly in the verdict; flag if client-facing. |
| **Single point of failure** | If the provider changes one endpoint, the wrapper breaks with no notice. | Check when the wrapper's last commit was, how active maintainers are, and whether the project has a track record of fast fixes. |
| **Production readiness** | A spike that works once is not production-ready. | Require the spike to run end-to-end twice, with a clean re-auth in between. |

### Verdict format for unofficial-API spikes

```markdown
## Verdict: VALIDATED | PARTIAL | INVALIDATED

### Auth durability
- Cookie/session lifetime: X minutes/hours/days
- Re-auth required every: ...
- Headless login possible: yes/no

### API stability
- Endpoints tested: ...
- Failures observed: ...
- Rate limit hit at: ...

### Production risk
- Provider can break this tomorrow: yes/no
- Wrapper maintenance status: active/stale/abandoned
- Recommended use: production / internal-only / manual-only / do not use

### Surprises
- ...
```

**Example:** The NotebookLM spike (`references/notebooklm-spike.md`) invalidated production use because Google invalidated scraped cookies after ~30 minutes, and the wrapper relied on undocumented internal endpoints.

---

## Frontier mode (picking what to spike next)

If spikes already exist and the user says "what should I spike next?", walk the existing directories and look for:

- **Integration risks** — two validated spikes that touch the same resource but were tested independently
- **Data handoffs** — spike A's output was assumed compatible with spike B's input; never proven
- **Gaps in the vision** — capabilities assumed but unproven
- **Alternative approaches** — different angles for PARTIAL or INVALIDATED spikes

Propose 2-4 candidates as Given/When/Then. Let the user pick.

## Output

- Create `spikes/` (or `.planning/spikes/` if the user is using GSD conventions) in the repo root
- One dir per spike: `NNN-descriptive-name/`
- `README.md` per spike captures question, approach, results, verdict
- Keep the code throwaway — a spike that takes 2 days to "clean up for production" was a bad spike

## Reference: thesysdev/openui

See `references/openui-thesysdev.md` for full notes on the Generative UI framework (OpenUI Lang, quick start, stack, diferencias con wandb/openui). Spike scaffolded en `~/spikes/001-openui/genui-chat-app/`.

## Attribution

Adapted from the GSD (Get Shit Done) project's `/gsd-spike` workflow — MIT © 2025 Lex Christopherson ([gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)). The full GSD system offers persistent spike state, MANIFEST tracking, and integration with a broader spec-driven development pipeline; install with `npx get-shit-done-cc --hermes --global`.
