GitHub CLI (gh) instalado y autenticado con cuenta aliagenttucuman@gmail.com. Token guardado en keyring. Git configurado con user.name='aliagenttucuman' y user.email='aliagenttucuman@gmail.com'. gh CLI sirve para commits, push, PRs y para descargar skills sin rate limit.
§
Nelson tiene NVIDIA GeForce GTX 1650 Mobile/Max-Q con 4GB GDDR5 VRAM (no 6GB). RAM del sistema: 13GB total. Ollama puede correr modelos grandes usando VRAM+RAM automaticamente. Modelos probados y funcionando: llama3.2:3b (2GB, rapido en VRAM), qwen2.5:3b (1.9GB, rapido en VRAM), llama3.1:8b (4.9GB, usa 43% CPU + 57% GPU, respuesta <2 seg). nomic-embed-text (274MB) para embeddings.
§
Tony Stark (Nelson) prefiere comunicarse por WhatsApp con audios. Es action-oriented, no le gusta leer mucho texto largo. Quiere que le responda con audios concisos. El roleplay es Iron Man / JARVIS.
§
Cada vez que se crea o modifica una skill del equipo Nelson, o cuando se actualiza la memoria persistente (MEMORY.md o USER.md) con datos valiosos, se debe ejecutar sync-to-repo.sh + git push para actualizar el repo nelson-hermes-skills en GitHub. Es super importante para no perder ni skills ni memoria. Las skills viven en ~/.hermes/skills/software-development/, la memoria en ~/.hermes/memories/, el repo en ~/repos/nelson-hermes-skills/ con scripts sync-to-repo.sh y sync-from-repo.sh. URL: github.com/aliagenttucuman-byte/nelson-hermes-skills
§
Skill `nelson-rag-pipeline` actualizada con fix de Qdrant IDs (UUID requerido), seccion Testing y Validacion, y referencia `rag-query-tips.md` con lecciones de formulacion de preguntas.
§
Docker requiere sudo (usuario 'server' no está en grupo docker). Comando: 'docker compose' (V2). Puerto 3000 ocupado, frontend usa 8080. Google Cloud proyecto: latam-flight-delay, credenciales en ~/.gcp-service-account.json. GCP CLI en ~/google-cloud-sdk/.
§
Sudo password de usuario 'server': 'srv2026'. Docker requiere sudo.