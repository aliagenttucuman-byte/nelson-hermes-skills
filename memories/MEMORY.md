Tony Stark (Nelson) prefiere comunicarse por WhatsApp con audios. Es action-oriented, no le gusta leer mucho texto largo. Quiere que le responda con audios concisos. El roleplay es Iron Man / JARVIS.
§
Equipo I+D+I (innovacion, PoCs): Tony + 2 agentes IA — Julián (backend) y Mercedes (frontend).
§
Convención brainstorming: Todo doc de proyecto/SDD/spec se guarda en ~/brainstorming/YYYY-MM-DD-nombre-proyecto/ con README.md obligatorio. Templates en ~/brainstorming/templates/. Skill: nelson-brainstorming.
§
Nelson prefiere probar cosas solo primero antes de compartir con Pablo/equipo ("envíamelo a mí nomás"). Es proactive con recursos del sistema (avisó sobre limpieza de disco). Interesado en consumir tech news via audio/podcast (runner, manos libres).
§
Servidor Linux. GTX 1650 4GB VRAM. Whisper:5001, OptiLLM:18000→Ollama:11434. OpenCode Zen: https://opencode.ai/zen/v1, key ~/secrets/opencode.env. Top modelos: claude-sonnet-4, gpt-5.4-nano, kimi-k2.6. NVIDIA NIM keys: ~/secrets/nvidia_nim_keys.env (mistral-medium-3.5-128b, gemma-4-31b, qwen3-coder-480b, glm-5.1, minimax-m2.7). Skill: nvidia-nim-free-api.
§
Nelson: si técnica falla 2-3 veces, parar y consultar para revaluar. No insistir en loops.
§
Regla de oro del stack: Backend SIEMPRE Python, Frontend SIEMPRE React. Aplica a todos los equipos (Central e I+D+I). Pueden variar librerias/frameworks dentro de ese stack (FastAPI vs Flask, Vite vs Next.js), pero el lenguaje y framework base son innegociables. Documentado en skills nelson-spec-driven-workflow y nelson-project-constitution.
§
Tailscale cuenta aliagenttucuman@gmail.com. IP servidor (ai-server): 100.110.8.13. Windows Nelson (nelsondev): 100.76.143.33. SSH: ssh server@100.110.8.13 pass srv2026. Android: instalar Tailscale + JuiceSSH/Termius con mismos datos.