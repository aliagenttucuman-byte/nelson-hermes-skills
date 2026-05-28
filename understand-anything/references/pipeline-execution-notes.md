# /understand Pipeline Execution Notes

Lessons learned from running the pipeline directly via Hermes Agent (not delegated to Claude Code or Codex). Applicable to any future `/understand` run on this server.

---

## scan-result.json structure (Phase 1 output)

The `scan-result.json` produced by `project-scanner` has this shape:

```json
{
  "name": "project-name",
  "description": "...",
  "languages": ["python", "javascript", "css"],
  "frameworks": ["React", "FastAPI"],
  "files": [
    {
      "path": "backend/main.py",
      "language": "python",
      "sizeLines": 939,
      "fileCategory": "code"
    }
  ]
}
```

Note: `files` is an array of **objects** with a `path` key, NOT plain strings. This matters when building `fingerprint-input.json` — iterate `f['path']` not `f` directly.

---

## build-fingerprints.mjs — correct invocation

```bash
# WRONG — fails with EISDIR:
node build-fingerprints.mjs /path/to/project

# CORRECT — pass a JSON input file:
node build-fingerprints.mjs /path/to/project/.understand-anything/tmp/fingerprint-input.json
```

Input JSON structure:
```json
{
  "projectRoot": "/absolute/path/to/project",
  "sourceFilePaths": ["/absolute/path/to/project/backend/main.py", "..."],
  "gitCommitHash": ""
}
```

The script writes `fingerprints.json` to `<projectRoot>/.understand-anything/`. If tree-sitter WASM parsers aren't loaded for the target languages (Python, JSX, etc.), it silently returns "Fingerprints baseline: 0 files" with exit code 0 — this is acceptable, not an error.

---

## ua-inline-validate.cjs — must be written at runtime

This file does NOT exist in the plugin. Phase 6 of the SKILL.md correctly says to write it to `$PROJECT_ROOT/.understand-anything/tmp/ua-inline-validate.cjs` first, then execute it. Never look for it in `SKILL_DIR` or the plugin root.

Alternative: inline Python validation works equally well for catching dangling edges and missing fields, and doesn't require writing a Node script.

---

## Direct Hermes Agent execution vs. subagent delegation

When running `/understand` directly via Hermes Agent (not via Claude Code or Codex delegation):
- Phases 3-5 (assemble-reviewer, architecture-analyzer, tour-builder) cannot truly "dispatch a subagent"
- Instead: implement them inline — write the architecture.json, tour.json directly using the LLM's analysis of the assembled-graph.json
- The merge script (Phase 2) and compute-batches (Phase 1.5) still run normally via `node` and `python`
- Output quality is equivalent when done inline with care

---

## fleet-optimizer/poc analysis results (2026-05-28)

Project: **FleetOptimizer AR** — FastAPI + React 19 PoC for Argentine fleet management

Stats:
- Files analyzed: 22
- Nodes: 35 (file:11, function:18, class:2, document:3, config:1)
- Edges: 50 (contains:23, calls:11, imports:5, configures:5, related:4, documents:1, depends_on:1)
- Layers: 3 (Frontend, Backend, Configuration & Assets)
- Tour steps: 10
- Graph size: 42,296 bytes

Key architectural patterns identified:
1. Real-Time Fleet Telemetry — WebSocket push every 1.5s
2. 3-Pass OCR Pipeline — EasyOCR → regex → Ollama qwen2.5:3b (x2 passes)
3. Streaming AI Chat (JARVIS) — NVIDIA NIM Llama 3.3-70B via SSE

Knowledge graph: `~/brainstorming/2026-05-22-fleet-optimizer/poc/.understand-anything/knowledge-graph.json`
