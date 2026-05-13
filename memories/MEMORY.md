Nelson tiene GTX 1650 Mobile 4GB VRAM, 13GB RAM. Ollama con VRAM+RAM. Modelos probados: llama3.2:3b (~4s), qwen2.5:3b (~6s), gemma3:4b (~6s, 2.4GB VRAM), gemma4-e2b (~55s, 2.9GB). Gemma4-e4b no entra. nomic-embed-text para embeddings. Recomendación: llama3.2:3b velocidad, gemma3:4b capacidad, gemma4-e2b solo thinking mode.
§
Tony Stark (Nelson) prefiere comunicarse por WhatsApp con audios. Es action-oriented, no le gusta leer mucho texto largo. Quiere que le responda con audios concisos. El roleplay es Iron Man / JARVIS.
§
Sincronizar skills y memoria al repo nelson-hermes-skills solo cuando haya informacion valiosa o cambios importantes. No en cada modificacion menor. El usuario decide cuando es el momento de hacer backup. Las skills viven en ~/.hermes/skills/software-development/, la memoria en ~/.hermes/memories/, el repo en ~/repos/nelson-hermes-skills/ con scripts sync-to-repo.sh y sync-from-repo.sh. URL: github.com/aliagenttucuman-byte/nelson-hermes-skills
§
Al sincronizar skills al repo nelson-hermes-skills, verificar que TODAS las skills locales esten incluidas, no solo las del prefijo 'nelson-'. Ejemplo: spec-driven-development estaba local pero nunca en el repo. Antes de commitear, listar ~/.hermes/skills/software-development/ y comparar con el repo.
§
Gino (gestion proyectos, no tecnico) y Luigi (economia/empresas, cuentas, contactos, no tecnico) son asesores externos de la consultora. NO son socios. Socios fundadores: Tony (expertise IA + desarrollo) y Pablo. Equipo tecnico ejecutor: agentes IA (Beto, Ricky, Nico, Diego, Alma).
§
Convención brainstorming: Todo doc de proyecto/SDD/spec se guarda en ~/brainstorming/YYYY-MM-DD-nombre-proyecto/ con README.md obligatorio. Templates en ~/brainstorming/templates/. Skill: nelson-brainstorming.
§
Credenciales n8n local: email aliagenttucuman@gmail.com, password Aliagent1234.
§
Feeds RSS muertos detectados: Anthropic (anthropic.com/blog/rss.xml → 404), Google AI Blog antiguo (ai.googleblog.com → 404). Feed funcional de Google AI: blog.google/technology/ai/rss/. PyTorch blog no tiene feed RSS descubrible fácilmente.