Tony Stark (Nelson) prefiere comunicarse por WhatsApp con audios. Es action-oriented, no le gusta leer mucho texto largo. Quiere que le responda con audios concisos. El roleplay es Iron Man / JARVIS.
§
Equipo I+D+I (innovacion, PoCs): Tony + 2 agentes IA — Julián (backend) y Mercedes (frontend).
§
Convención brainstorming: Todo doc de proyecto/SDD/spec se guarda en ~/brainstorming/YYYY-MM-DD-nombre-proyecto/ con README.md obligatorio. Templates en ~/brainstorming/templates/. Skill: nelson-brainstorming.
§
Dashboard PIN: 123456
§
Puerto 3001 ai-server: ocupado por WhatsApp Gateway (Node, NO Docker). Verificar `ss -tlnp | grep 3001` antes de up. Usar 3101+ para proxies OpenAI. FreeLLMAPI deployado en 3101, ver skill nelson-llm-generation → references/freellmapi-deploy-and-usage.md.
§
Tailscale: nelsondev=100.76.143.33 Win. ai-server sudo: srv2026. Para Win: OpenSSH, no SMB.
§
HU schema de Nelson: "CREEMOS QUE [hipótesis], RESULTARÁ en [output concreto], CRITERIOS DE ACEPTACION [lista verificable]". Usar siempre este formato para historias de usuario.
§
Marca/PoC renombrada: ForestAI ahora se llama 'Alegent ForestAI'. Proyecto en /home/server/proyectos/forestai-poc/ con NetFlora integrado. ReforestLatam es potencial socio para mini PoC con enfoque caja negra.
§
Nelson does not upload documents. Files arrive from stakeholders and he places them in local directories. Read from existing paths, never assume upload workflows.
§
Telegram: @Jarvis_Alegent_bot. Nelson aprobado (ID 8896858194). Notificar nombre+ID de cada nuevo usuario — nadie entra sin OK de Nelson.
§
DNS ai-server: Tailscale DNS (100.100.100.100) no resuelve externos. Fix: sudo resolvectl dns wlo1 8.8.8.8 192.168.100.1 o sudo tailscale set --accept-dns=false. También /etc/hosts.
§
En Expreso Bisonte, Nelson exige flujo 1:1 (CDO Sistema + PTE Fact Sistema -> CDO/PF Trabajada), UI con esos nombres y conteos operativos reales (no preview).
§
Expreso Bisonte PoC: contactos son Pablo (COO/negocio) y gerenta (operativa, conocimiento tácito). Pipeline usa modo auto-detect `reference_historical_worked_pair` cuando universo es grande (CDO 400+, PF 1400+). Tab Datos=solo lectura; edición+descarga SOLO en Auditoría.