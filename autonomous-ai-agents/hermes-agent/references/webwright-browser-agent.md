# Webwright — Microsoft Browser Agent Skill

## Qué es

Webwright (github.com/microsoft/Webwright) es una **skill/plugin** de Microsoft Research
que convierte cualquier agente de IA (Claude Code, Codex, Hermes) en un agente de
navegador SOTA. No es una app separada — es una skill que se instala en el agente.

## Cómo funciona

El agente genera código Python+Playwright al vuelo, lo ejecuta via bash, toma
screenshots, los lee con visión nativa, y se auto-verifica contra un plan.md.
Un bash command por turno — sin servidor, sin MCP, sin protocolo especial.

## Diferencia con browser-use / Playwright MCP

| | Webwright | browser-use | Playwright MCP |
|---|---|---|---|
| Mecanismo | Genera código Python al vuelo | API Python directa | MCP tools sobre Playwright |
| Dependencias | Solo Playwright + LLM | browser-use lib | MCP server |
| Anti-fingerprint | Firefox por defecto | Chromium | Chromium |
| Evidencia | Screenshots por CP | Screenshots opcionales | No estructurado |
| Modo CLI | Sí (parámetros argparse) | No | No |

## Estructura del repo

```
skills/webwright/
├── SKILL.md                          # Skill principal
├── commands/
│   ├── craft.md                      # Modo CLI reutilizable
│   └── run.md                        # Modo one-shot
└── reference/
    ├── playwright_patterns.md        # Patrones canónicos de código
    ├── workflow.md                   # Loop de 6 pasos detallado
    └── cli_tool_mode.md              # Contrato de modo CLI
```

Plugins:
- `.claude-plugin/plugin.json` → para Claude Code
- `.codex-plugin/plugin.json` → para Codex CLI

## Integración en el equipo Nelson

Implementada como `nelson-browser-agent` en `software-development/`.

Firefox 148 instalado en servidor: `/home/server/.cache/ms-playwright/firefox-1511`

El loop Webwright adaptado para Hermes:
1. PLAN → plan.md con Critical Points
2. EXPLORE → scripts scratch Playwright
3. AUTHOR → final_script.py instrumentado  
4. EXECUTE → correr y guardar screenshots
5. VERIFY → leer PNGs con visión y validar cada CP

## Workspace Contract

```
outputs/<task_id>/
├── plan.md
├── screenshots/           # scratch (exploración)
└── final_runs/run_<N>/
    ├── final_script.py
    ├── final_script_log.txt
    └── screenshots/
        └── final_execution_<step>_<action>.png
```

## Pitfall: Firefox vs Chromium

Firefox resiste mejor Akamai y Cloudflare (TLS fingerprinting).
Chromium puede dar `ERR_HTTP2_PROTOCOL_ERROR` en sitios protegidos.
Siempre intentar Firefox primero; fallback a Chromium solo si Firefox falla.

## Pitfall: /openai/models vs deployments reales

Ver `references/azure-foundry-codex.md` — el catálogo global no implica
que el modelo esté deployado en tu recurso.
