Tony Stark (Nelson) prefiere comunicarse por WhatsApp con audios. Es action-oriented, no le gusta leer mucho texto largo. Quiere que le responda con audios concisos. El roleplay es Iron Man / JARVIS.
§
Equipo I+D+I: Tony + Julián (backend) + Mercedes (frontend). Stack mobile: Expo SDK 56, expo-dev-client (nunca Expo Go), EAS Build+OTA. ML en FastAPI :9000, Expo consume via Server Actions.
§
Puerto 3001 ai-server: WhatsApp Gateway (Node, NO Docker). FreeLLMAPI en 3101. n8n :5678 login: nelsongacosta@gmail.com/BuenosAires435!.
§
Tailscale: nelsondev=100.76.143.33 Win, ai-server=100.110.8.13 Linux. ai-server sudo: srv2026.
§
HU Nelson: "CREEMOS QUE [hipótesis], RESULTARÁ en [output], CRITERIOS DE ACEPTACION [verificable]".
§
AlegentAI propuestas comerciales: 3 caminos estándar (A=Sociedad 60% AlegentAI, B=Cliente paga 100% IP, C=Híbrido aporte valorizable). Equipo sweat equity 4 roles: Fede(Arquitecto)+Nelson(Líder Téc)+Gustavo(Analista Func)+Ana(QA), USD 30/h. Sin nombres propios de prospectos por defecto.
§
Nelson does not upload documents. Files arrive from stakeholders and he places them in local directories. Read from existing paths, never assume upload workflows.
§
Telegram: @Jarvis_Alegent_bot. Nelson aprobado (ID 8896858194). Avisar nombre+ID de nuevos usuarios — nadie sin OK Nelson.
§
Expreso Bisonte PoC: Pablo (COO). Infra: FastAPI :9000, spa_proxy :9090. CF→:9090. Repo: github.com/aliagenttucuman-byte/expreso-bisonte-excel-poc. NO venv. Pitfall: reiniciar spa_proxy tras build. WS: usar window.location.host, no hostname:9000.
§
LAN/LATAM: contractor Intermedia LLC 29/06-29/12/2026, $28/hr, 8h/día L-V 9-18 ARG. Rol: Data Scientist Sr - M365 Copilot governance. Pagos USDc via ARQ→Lead Bank Kansas City: ABA 101019644, Acc 219123167275, SWIFT LEADUS42, 1801 Main St KC MO 64108. Cláusula 7 exclusividad CHOCA con AlegentAI — pendiente carve-out con Cassola.
§
Hermes routing JARVIS: main=opus-4-7 (gateway custom Azure Anthropic). sonnet-4-6 para auxiliares: compression, session_search, title_generation, triage, curator. Config: ~/.hermes/config.yaml.