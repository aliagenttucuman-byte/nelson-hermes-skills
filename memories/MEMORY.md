Tony Stark (Nelson) prefiere comunicarse por WhatsApp con audios. Es action-oriented, no le gusta leer mucho texto largo. Quiere que le responda con audios concisos. El roleplay es Iron Man / JARVIS.
§
Equipo I+D+I (innovacion, PoCs): Tony + 2 agentes IA — Julián (backend) y Mercedes (frontend).
§
Convención brainstorming: Todo doc de proyecto/SDD/spec se guarda en ~/brainstorming/YYYY-MM-DD-nombre-proyecto/ con README.md obligatorio. Templates en ~/brainstorming/templates/. Skill: nelson-brainstorming.
§
Dashboard PIN: 123456
§
Regla de oro del stack: Backend Python, Frontend React. Innegociable. Skills: nelson-spec-driven-workflow, nelson-project-constitution.
§
Tailscale cuenta aliagenttucuman@gmail.com. IP servidor (ai-server): 100.110.8.13. Windows Nelson (nelsondev): 100.76.143.33. SSH: ssh server@100.110.8.13 pass srv2026. Android: instalar Tailscale + JuiceSSH/Termius con mismos datos.
§
HU schema de Nelson: "CREEMOS QUE [hipótesis], RESULTARÁ en [output concreto], CRITERIOS DE ACEPTACION [lista verificable]". Usar siempre este formato para historias de usuario.
§
CF tunnels: ForestAI (:3010) /tmp/cf_forestai.log. Fleet (:8020) /tmp/cf_fleet.log. EduAI (:8030) /tmp/cf_eduplatform.log — backend en ~/brainstorming/2026-05-27-edu-platform-ia/backend/, arrancar con venv Hermes. Orquestador :5174+:8000 /home/server/nelson/. Repo skills: github.com/aliagenttucuman-byte/nelson-hermes-skills.
§
Azure Foundry yiazlafoc001: Claude ✅. Codex gpt-5.3-codex-2026-02-20 ❌ deployment no creado — crear en portal (AI Foundry → Deployments). URL: cognitiveservices.azure.com/openai/responses?api-version=2025-04-01-preview. Config: codex_responses + extra_params.api_version.
§
Telegram: @Jarvis_Alegent_bot. Nelson aprobado (ID 8896858194). Notificar nombre+ID de cada nuevo usuario — nadie entra sin OK de Nelson.
§
DNS ai-server: Tailscale DNS (100.100.100.100) no resuelve externos. Fix: sudo resolvectl dns wlo1 8.8.8.8 192.168.100.1 o sudo tailscale set --accept-dns=false. También /etc/hosts.
§
Nelson usa Coderbyte/HackerRank. Flujo: foto WA → JARVIS devuelve solución. Skill: nelson-coding-challenges. Fix Vite+tunnel: VITE_API_URL='' siempre — nunca localhost hardcodeado.