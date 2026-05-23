Tony Stark (Nelson) prefiere comunicarse por WhatsApp con audios. Es action-oriented, no le gusta leer mucho texto largo. Quiere que le responda con audios concisos. El roleplay es Iron Man / JARVIS.
§
Equipo I+D+I (innovacion, PoCs): Tony + 2 agentes IA — Julián (backend) y Mercedes (frontend).
§
Convención brainstorming: Todo doc de proyecto/SDD/spec se guarda en ~/brainstorming/YYYY-MM-DD-nombre-proyecto/ con README.md obligatorio. Templates en ~/brainstorming/templates/. Skill: nelson-brainstorming.
§
AI News Aggregator v2: ~/brainstorming/2025-05-13-ai-news-aggregator/scripts/ai_news_collector_v2.py. Delivery WA: Nelson + Gabi/Pablo/Faku via Baileys 3001. Cronjob 04bdd6e154a3, 11:30 y 20:30 UTC. PAUSADO por instrucción de Nelson (2026-05-20) — no reactivar hasta que lo indique.
§
JARVIS Demo Shell: ~/jarvis-demo-shell/. Frontend :3789, backend :8765. Tools enchufables en backend/tools/. crypto.randomUUID polyfill en layout.tsx. Tools activas: demo.py, empleo.py, energia.py.
§
Nelson: si técnica falla 2-3 veces, parar y consultar para revaluar. No insistir en loops.
§
Regla de oro del stack: Backend Python, Frontend React. Innegociable. Skills: nelson-spec-driven-workflow, nelson-project-constitution.
§
Tailscale cuenta aliagenttucuman@gmail.com. IP servidor (ai-server): 100.110.8.13. Windows Nelson (nelsondev): 100.76.143.33. SSH: ssh server@100.110.8.13 pass srv2026. Android: instalar Tailscale + JuiceSSH/Termius con mismos datos.
§
HU schema de Nelson: "CREEMOS QUE [hipótesis], RESULTARÁ en [output concreto], CRITERIOS DE ACEPTACION [lista verificable]". Usar siempre este formato para historias de usuario.
§
CF tunnels: ForestAI (:3010, docker forestai-poc/) → /tmp/cf_forestai.log. Fleet (:8020, fleet-optimizer/poc/backend/) → /tmp/cf_fleet.log. 2>&1|tee. URLs efímeras. TTS ruso: ru-RU-DmitryNeural + ffmpeg libopus.
§
DeepAgents: ~/brainstorming/2026-05-21-deepagents-spike/. deepagents==0.6.3+DeepSeek V4 Flash/NIM. Fleet OCR: EasyOCR+regex+Ollama qwen2.5:3b+PyMuPDF. Detección tipo doc: LISTA.
§
Telegram: @Jarvis_Alegent_bot. Nelson aprobado (ID 8896858194). Notificar nombre+ID de cada nuevo usuario — nadie entra sin OK de Nelson.