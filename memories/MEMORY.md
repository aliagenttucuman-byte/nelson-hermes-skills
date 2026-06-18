Tony Stark (Nelson) prefiere comunicarse por WhatsApp con audios. Es action-oriented, no le gusta leer mucho texto largo. Quiere que le responda con audios concisos. El roleplay es Iron Man / JARVIS.
§
Equipo I+D+I: Tony + Julián (backend) + Mercedes (frontend). Stack mobile: Expo SDK 56, expo-dev-client (nunca Expo Go), EAS Build+OTA. ML en FastAPI :9000, Expo consume via Server Actions.
§
Puerto 3001 ai-server: WhatsApp Gateway (Node, NO Docker). FreeLLMAPI en 3101. n8n :5678 login: nelsongacosta@gmail.com/BuenosAires435!.
§
Tailscale: nelsondev=100.76.143.33 Win, ai-server=100.110.8.13 Linux. ai-server sudo: srv2026.
§
HU schema de Nelson: "CREEMOS QUE [hipótesis], RESULTARÁ en [output concreto], CRITERIOS DE ACEPTACION [lista verificable]". Usar siempre este formato para historias de usuario.
§
ReForest Latam (Tucumán): prospecto AlegentAI, CEO Damián Rivadeneira, gap=YOLO drones. Propuesta jun 2026: Opción A sociedad 25% equity / Opción B inversión USD 20-57K.
§
Nelson does not upload documents. Files arrive from stakeholders and he places them in local directories. Read from existing paths, never assume upload workflows.
§
Telegram: @Jarvis_Alegent_bot. Nelson aprobado (ID 8896858194). Notificar nombre+ID de cada nuevo usuario — nadie entra sin OK de Nelson.
§
DNS ai-server: Tailscale DNS no resuelve externos. Fix: sudo resolvectl dns wlo1 8.8.8.8 o sudo tailscale set --accept-dns=false. /etc/hosts también sirve.
§
En Expreso Bisonte, Nelson exige flujo 1:1 (CDO Sistema + PTE Fact Sistema -> CDO/PF Trabajada), UI con esos nombres y conteos operativos reales (no preview).
§
Bisonte Contado: INICIAL+SISTEMA→FINAL. Sin filtro estado. Prefijos nro: A.B.R. EXISTENTES: ESTADO de SISTEMA, REFERENTE vacío→succobro. NUEVOS: idem+VER DIF. UPSERT en DB. CC=4d resto=7d. :5435. Sin prioridad UI. Solo celda DIAS_ATRASO coloreada.
§
Expreso Bisonte PoC: Pablo (COO). Infra: FastAPI :9000, spa_proxy :9090. CF→:9090. Repo: github.com/aliagenttucuman-byte/expreso-bisonte-excel-poc. NO venv. Pitfall: reiniciar spa_proxy tras build. WS: usar window.location.host, no hostname:9000.