Tony Stark (Nelson) prefiere comunicarse por WhatsApp con audios. Es action-oriented, no le gusta leer mucho texto largo. Quiere que le responda con audios concisos. El roleplay es Iron Man / JARVIS.
§
Consultora: 2 equipos bajo liderazgo de Tony (Nelson).
Equipo Desarrollo Central (produccion): Beto, Ricky, Nico, Diego, Alma (5 agentes IA).
Equipo I+D+I (innovacion, PoCs): Tony + 2 agentes IA.
Asesores externos: Gino (gestion) y Luigi (economia/cuentas).
Socio: Pablo (negocios).

Monitoreo activo: cronjob cada 5 min revisa salud de los 3 RAGs (FLoCI-AWS, MinIO, FLoCI-Azure). Auto-reinicio + alerta si no responden. Script: nelson-rag-pipeline/scripts/rag-health-monitor.sh.
§
Convención brainstorming: Todo doc de proyecto/SDD/spec se guarda en ~/brainstorming/YYYY-MM-DD-nombre-proyecto/ con README.md obligatorio. Templates en ~/brainstorming/templates/. Skill: nelson-brainstorming.
§
Credenciales n8n local: email aliagenttucuman@gmail.com, password Aliagent1234.
§
Nelson prefiere probar cosas solo primero antes de compartir con Pablo/equipo ("envíamelo a mí nomás"). Es proactive con recursos del sistema (avisó sobre limpieza de disco). Interesado en consumir tech news via audio/podcast (runner, manos libres).
§
Nelson usa PC con Windows + servidor Linux. GTX 1650 4GB VRAM, 13GB RAM. Ollama local con nomic-embed-text.
§
Nelson: si técnica falla 2-3 veces, parar y consultar para revaluar. No insistir en loops.
§
Nelson quiere la consultora como 'maquina de automatizacion': todo sincronizado (skills, memoria, workflows, deploys), procesos repetitivos automaticos, equipo humano en decisiones estrategicas. Si algo se repite 2+ veces por semana, automatizarse. 3 RAGs deployados. Interes en MCP para futura adopcion via I+D+I.
§
Regla de oro del stack: Backend SIEMPRE Python, Frontend SIEMPRE React. Aplica a todos los equipos (Central e I+D+I). Pueden variar librerias/frameworks dentro de ese stack (FastAPI vs Flask, Vite vs Next.js), pero el lenguaje y framework base son innegociables. Documentado en skills nelson-spec-driven-workflow y nelson-project-constitution.