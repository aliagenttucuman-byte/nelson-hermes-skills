Tony Stark (Nelson) prefiere comunicarse por WhatsApp con audios. Es action-oriented, no le gusta leer mucho texto largo. Quiere que le responda con audios concisos. El roleplay es Iron Man / JARVIS.
§
Al sincronizar skills al repo nelson-hermes-skills, verificar que TODAS las skills locales esten incluidas, no solo las del prefijo 'nelson-'. Ejemplo: spec-driven-development estaba local pero nunca en el repo. Antes de commitear, listar ~/.hermes/skills/software-development/ y comparar con el repo.
§
Gino (gestion proyectos, no tecnico) y Luigi (economia/empresas, cuentas, contactos, no tecnico) son asesores externos de la consultora. NO son socios. Socios fundadores: Tony (expertise IA + desarrollo) y Pablo. Equipo tecnico ejecutor: agentes IA (Beto, Ricky, Nico, Diego, Alma).
§
Convención brainstorming: Todo doc de proyecto/SDD/spec se guarda en ~/brainstorming/YYYY-MM-DD-nombre-proyecto/ con README.md obligatorio. Templates en ~/brainstorming/templates/. Skill: nelson-brainstorming.
§
Credenciales n8n local: email aliagenttucuman@gmail.com, password Aliagent1234.
§
Nelson prefiere probar cosas solo primero antes de compartir con Pablo/equipo ("envíamelo a mí nomás"). Es proactive con recursos del sistema (avisó sobre limpieza de disco). Interesado en consumir tech news via audio/podcast (runner, manos libres).
§
Nelson usa PC con Windows + servidor Linux con Gnome/Epiphany como navegador. GTX 1650 Mobile 4GB VRAM, 13GB RAM. Ollama con VRAM+RAM. Modelos: llama3.2:3b (~4s), qwen2.5:3b (~6s), gemma3:4b (~6s), gemma4-e2b (~55s). nomic-embed-text para embeddings.
§
Nelson: si técnica falla 2-3 veces, parar y consultar para revaluar. No insistir en loops.
§
RAG PoC con 3 backends en paralelo desplegados 2026-05-14: FLoCI-AWS (memoria, S3 emulado), MinIO (disco, S3 real), FLoCI-Azure (hybrid, Azure Blob emulado). Demo Package para Pablo en ~/brainstorming/2026-05-14-rag-floci-azure/README.md. URLs publicas via Cloudflare. MinIO es la opcion mas estable para produccion on-premise. FLoCI-Azure tiene startup ~100ms ideal para demos. Flujo end-to-end documentado en skill nelson-cloud-storage-comparison.