# Orchestrator Dashboard + API (Quick Tunnel)

Contexto validado en sesión 2026-05-29.

- UI Vite: `:5174`
- API meta-orchestrator: `:8744`
- Tunnel para UI debe apuntar a `:5174`.

Verificación:
`/api/orchestrate/health` y `/api/orchestrate/status` vía URL del tunnel de UI.
