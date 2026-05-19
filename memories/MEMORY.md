Tony Stark (Nelson) prefiere comunicarse por WhatsApp con audios. Es action-oriented, no le gusta leer mucho texto largo. Quiere que le responda con audios concisos. El roleplay es Iron Man / JARVIS.
§
Equipo I+D+I (innovacion, PoCs): Tony + 2 agentes IA — Julián (backend) y Mercedes (frontend).
§
Convención brainstorming: Todo doc de proyecto/SDD/spec se guarda en ~/brainstorming/YYYY-MM-DD-nombre-proyecto/ con README.md obligatorio. Templates en ~/brainstorming/templates/. Skill: nelson-brainstorming.
§
AI News Aggregator v2: script en ~/brainstorming/2025-05-13-ai-news-aggregator/scripts/ai_news_collector_v2.py. Delivery: Nelson + Gabi (5491132438887) + Pablo (5493816240691) + Faku (5493813022552). Cronjob ID 04bdd6e154a3, 11:30 y 20:30 UTC. Fuentes: RSS pasivo + DDG News + Google News + Reddit + Dev.to + Referentes.
§
Applio: /home/server/Applio, venv propio, torch 2.6+cu124, extras: torchfcpe+torchcrepe, rmvpe.pt bajar manual HF IAHispano/Applio, cut_preprocess='Simple', batch=2+checkpointing=True, matar Whisper antes de entrenar (libera 550MB VRAM). RVC necesita min 100-200 épocas. Whisper daemon: whisper_daemon.py puerto 5001 CUDA. Modelo messi: best epoch en /home/server/Applio/logs/messi/. run_infer_script() NO tiene filter_radius ni hop_length — verificar con inspect.signature().
§
Nelson: si técnica falla 2-3 veces, parar y consultar para revaluar. No insistir en loops.
§
Regla de oro del stack: Backend Python, Frontend React. Innegociable. Skills: nelson-spec-driven-workflow, nelson-project-constitution.
§
Tailscale cuenta aliagenttucuman@gmail.com. IP servidor (ai-server): 100.110.8.13. Windows Nelson (nelsondev): 100.76.143.33. SSH: ssh server@100.110.8.13 pass srv2026. Android: instalar Tailscale + JuiceSSH/Termius con mismos datos.
§
PoC datos energéticos→WhatsApp: API datos.gob.ar (petróleo/gas por empresa, YPF) + LLM → imagen reporte → WhatsApp. Docs: ~/brainstorming/2026-05-19-powerbi-whatsapp-poc/ y ~/brainstorming/2026-05-19-openwa-whatsapp-gateway/. Spike pendiente. PoC PowerBI→WhatsApp (YPF, Azure AD): URLs tableros publicados → LLM → reporte visual. Pendiente post-spike energético.