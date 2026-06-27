# ROADMAP SKILLS — AlegentAI / Equipo Nelson
> Generado: 2026-06-20 | Total skills: 213 | Skills nelson-*: ~90

---

## 1. INFRAESTRUCTURA & DEVOPS
| Skill | Estado | Descripción |
|-------|--------|-------------|
| nelson-server-services | ✅ activa | Mapa servicios Docker ai-server |
| nelson-cloudflare-tunnel-deploy | ✅ activa | Deploy PoCs con CF tunnel + nginx |
| nelson-ci-cd | ✅ activa | GitHub Actions, Cloud Run, Artifact Registry |
| nelson-backup-dr | ✅ activa | Backups PostgreSQL/Qdrant/MinIO, RTO/RPO |
| nelson-incident-response | ✅ activa | Playbooks caídas, triage 5min, post-mortem |
| nelson-monitoring-observability | ✅ activa | Logging, health checks, Docker healthcheck |
| nelson-observability | ✅ activa | structlog JSON, Prometheus, middleware trazas |
| nelson-os-security | ✅ activa | Monitoreo seguridad Linux, intrusiones |
| nelson-workflow-security | ✅ activa | Sanitización output antes de publicar |
| docker-management | ✅ activa | Contenedores, imágenes, compose |
| nelson-deploy-gcp | ✅ activa | Cloud Run, Cloud SQL, Artifact Registry |
| nelson-gcp-terraform | ✅ activa | Terraform + Terraformer GCP real (LAN LATAM) |
| nelson-gcp-floci-terraform | ✅ activa | Spike floci-gcp + Terraform local |

---

## 2. BACKEND & APIs
| Skill | Estado | Descripción |
|-------|--------|-------------|
| nelson-database | ✅ activa | SQLAlchemy 2.0, Alembic, PostgreSQL |
| nelson-security | ✅ activa | JWT, OAuth2, CORS, rate limiting |
| nelson-background-jobs | ✅ activa | Celery + Redis, tareas async |
| nelson-external-integrations | ✅ activa | APIs externas, fallback, rate limits |
| nelson-api-gateway-pattern | ✅ activa | nginx reverse-proxy multi-servicio |
| nelson-scheduled-jobs | ✅ activa | Cron Hermes, scripts Python |
| nelson-multi-tenancy | ✅ activa | Aislamiento tenant FastAPI+SQLAlchemy |
| FastAPI / fastapi | ✅ activa | Best practices FastAPI + Pydantic |
| api-design-principles | ✅ activa | REST y GraphQL design |
| async-python-patterns | ✅ activa | asyncio, concurrent programming |

---

## 3. FRONTEND & UI
| Skill | Estado | Descripción |
|-------|--------|-------------|
| nelson-frontend-stack | ✅ activa | React 18, TypeScript, Vite, Tailwind |
| nelson-frontend-agent | ✅ activa | React 19, React Query 5, Router 7 |
| nelson-frontend-testing | ✅ activa | Vitest, RTL, Playwright |
| nelson-generative-ui | ✅ activa | Shell reutilizable OpenUI Lang + FastAPI |
| nelson-react-doctor | ✅ activa | Diagnóstico automático errores React |
| nelson-ui-frontend-design | ✅ activa | Diseño visual distintivo, tipografía |
| nelson-ui-theme-factory | ✅ activa | 10 temas predefinidos slides/docs/HTML |
| nelson-ui-webapp-testing | ✅ activa | Playwright, Reconnaissance-Then-Action |
| nelson-ui-xlsx | ✅ activa | Excel con pandas/openpyxl, estándares financieros |

---

## 4. IA / LLMs / AGENTES
| Skill | Estado | Descripción |
|-------|--------|-------------|
| nelson-llm-generation | ✅ activa | OpenRouter, Anthropic, Groq, FreeLLMAPI |
| nelson-ai-agents | ✅ activa | ReAct, function calling, multi-agent |
| nelson-meta-orchestrator | ✅ activa | Loop maestro: descomponer, asignar, verificar |
| nelson-agent-routing | ✅ activa | Routing declarativo con scoring de confianza |
| nelson-poc-ai-quickstart | ✅ activa | Quickstart PoC con IA/LLM |
| nelson-eval-harness | ✅ activa | Métricas, scoring 0-100, gates |
| nelson-context-handoff | ✅ activa | HandoffPacket entre subagentes |
| nelson-task-memory | ✅ activa | SQLite persistente entre sesiones |
| nelson-headroom | ✅ activa | Proxy compresión contexto :8787 |
| nelson-lean-ctx | ✅ activa | lean-ctx ahorro tokens lecturas/shell |
| nelson-honcho | ✅ activa | Memoria multi-usuario :8008 |
| nelson-optillm | ✅ activa | Proxy inferencia optimizado |
| nelson-opik-eval | ✅ activa | Opik eval LLMs, tracing, LLM-as-Judge |
| nelson-codegraph | ✅ activa | CodeGraph pre-indexado reduce tokens |
| nelson-harness-creator | ✅ activa | AGENTS.md, feature_list, init.sh |
| nelson-multi-agent-orchestrator | ✅ activa | Julian+Mercedes paralelo con checkpoints |
| ponytail | ✅ activa | Modo lazy senior dev, YAGNI |
| nelson-browser-agent | ✅ activa | Playwright headless Firefox |
| claude-code / codex / opencode | ✅ activas | Delegación coding a agentes CLI |

---

## 5. DATA SCIENCE & ML
| Skill | Estado | Descripción |
|-------|--------|-------------|
| nelson-data-science | ✅ activa | XGBoost/LightGBM, Optuna, MLflow |
| nelson-data-viz | ✅ activa | matplotlib, seaborn, plotly |
| nelson-embeddings | ✅ activa | OpenAI, sentence-transformers, Ollama |
| nelson-vector-databases | ✅ activa | Qdrant, Chroma, Weaviate |
| nelson-rag-pipeline | ✅ activa | Chunking, retrieval, re-ranking |
| nelson-document-qa | ✅ activa | RAG sobre PDFs con FastAPI+Qdrant |
| nelson-document-processing | ✅ activa | MarkItDown, Surya, pdfplumber |
| nelson-docling | ✅ activa | Docling IBM, tablas, OCR, PPTX |
| nelson-ai-vision | ✅ activa | OCR, EasyOCR, OpenCV, multimodal |
| nelson-audio-processing | ✅ activa | Whisper local, TTS edge |
| nelson-local-llm-stack | ✅ activa | Ollama vs vLLM vs llama.cpp |
| nelson-vllm-deploy | ✅ activa | vLLM Docker/bare metal |
| nelson-gemini-live | ✅ activa | Gemini Live voz+video tiempo real |
| nelson-finance-ml | ✅ activa | Forecasting, clasificación riesgo, SHAP |
| nelson-finance-anomaly | ✅ activa | Isolation Forest, Autoencoders, LOF |
| nelson-finance-reporting | ✅ activa | CASK, RASK, Load Factor, Plotly/Dash |

---

## 6. AEROLINEAS / LAN LATAM
| Skill | Estado | Descripción |
|-------|--------|-------------|
| nelson-airline-booking-prediction | ✅ activa | Conversión reservas XGBoost+SHAP |
| nelson-airline-bts-dataset | ✅ activa | BTS 70M+ vuelos, Polars |
| nelson-airline-clustering | ✅ activa | Flash-KMeans GPU, segmentación pasajeros |
| nelson-airline-delay-prediction | ✅ activa | Delays/cancelaciones AUC>0.85 |
| nelson-airline-openflights | ✅ activa | Red rutas globales NetworkX |
| nelson-airline-passenger-satisfaction | ✅ activa | Satisfacción 120K registros XGBoost |
| nelson-airline-sentiment | ✅ activa | Sentiment español pysentimiento |

---

## 7. FORESTAI / REFOREST LATAM
| Skill | Estado | Descripción |
|-------|--------|-------------|
| nelson-forest-inventory | ✅ activa | PoC inventario forestal drones |
| nelson-forestai-demo | ✅ activa | Demo para Gino/ReforestLatam |
| nelson-forestai-roadmap | ✅ activa | Hoja de ruta MRV forestal |
| nelson-mrv-reports | ✅ activa | Reportes MRV PDF ejecutivo |
| nelson-multispectral-indices | ✅ activa | NDVI, NDRE, GNDVI sobre GeoTIFF |
| nelson-netflora | ✅ activa | NetFlora Embrapa/JBS 72 especies |
| nelson-yolov-finetuning | ✅ activa | Fine-tuning YOLO v8/v9/v11 árboles |

---

## 8. PROYECTOS CLIENTES
| Skill | Estado | Descripción |
|-------|--------|-------------|
| nelson-expreso-bisonte-poc | ✅ activa | PoC Bisonte :9000/:9090, CF tunnel |
| nelson-excel-pipeline-ops | ✅ activa | Pipeline Excel CDO/PF determinístico |
| nelson-sitrack-scraper | ✅ activa | Scraping Sitrack para Fleet Optimizer |
| nelson-firestore-api-poc | ✅ activa | CRUD FastAPI + Firestore floci-gcp |
| nelson-gcp-fullstack-poc | ✅ activa | E2E GCP local floci-gcp |
| nelson-gcp-pubsub-poc | ✅ activa | Event-driven Pub/Sub + React |
| nelson-gcs-rag-poc | ✅ activa | RAG sobre GCS emulado |
| nelson-iot-arduino-spike | ✅ activa | Arduino/ESP32 + MQTT + FastAPI |
| nelson-poc-dashboard-ai-chat | ✅ activa | Dashboard + chat IA NVIDIA NIM |

---

## 9. WORKFLOW / METODOLOGÍA
| Skill | Estado | Descripción |
|-------|--------|-------------|
| nelson-spec-driven-workflow | ✅ activa | SDD 8 fases completo |
| nelson-project-constitution | ✅ activa | CONSTITUTION.md fase 1 |
| nelson-pricing-model | ✅ activa | ESTIMACION.md costos reales |
| nelson-spec-analyzer | ✅ activa | Coherencia spec vs plan fase 5 |
| nelson-project-bootstrap | ✅ activa | Scaffold completo backend+frontend |
| nelson-project-tracking | ✅ activa | T-shirt, velocity, burndown SQLite |
| nelson-documentation | ✅ activa | README, docstrings, MkDocs |
| nelson-code-quality | ✅ activa | Ruff, mypy, pre-commit |
| nelson-senior-practices | ✅ activa | Type hints, SOLID, clean code |
| nelson-skill-authoring | ✅ activa | Workflow crear skills nelson-* |
| nelson-brainstorming | ✅ activa | Carpetas fecha + README templates |
| nelson-context-handoff | ✅ activa | HandoffPacket comprimido |
| nelson-error-review | ✅ activa | Revisión anomalías en flujos |
| nelson-demo-script | ✅ activa | Guía conversación demos Pablo/clientes |
| nelson-external-communication | ✅ activa | JARVIS interacción externa, audios |
| nelson-business-plan | ✅ activa | Business Plan Veigele 10 secciones |
| nelson-startup-benchmarking | ✅ activa | Benchmarking, valuación, equity |

---

## 10. COMUNICACIÓN & AUTOMATIZACIÓN
| Skill | Estado | Descripción |
|-------|--------|-------------|
| nelson-whatsapp-gateway | ✅ activa | Baileys :3001, envío desde Python |
| nelson-whatsapp-bot-template | ✅ activa | Template Baileys + FastAPI |
| nelson-telegram-bot-template | ✅ activa | Template Telegram webhook + FastAPI |
| nelson-automation-n8n | ✅ activa | n8n :5678 workflows, webhooks |
| nelson-content-generation | ✅ activa | Podcasts, audio, slides, quizzes |

---

## 🔴 GAPS DETECTADOS — Skills por crear

| Gap | Trigger | Prioridad |
|-----|---------|-----------|
| nelson-bisonte-colores-excel | Reglas de color por celda en Excel descargado — sucdest+tolerancia+OBSERVACIÓN | ALTA |
| nelson-cloudflare-dns-fix | DNS Pablo no resuelve *.trycloudflare.com — workaround probado | MEDIA |
| nelson-reporting-bisonte | Generación reporte PDF/Excel semanal automático para Pablo | MEDIA |
| nelson-flota-optimizador | Fleet Optimizer con Sitrack real + MapLibre + LLM | MEDIA |
| nelson-lan-latam-pipeline | Pipeline BTS + KPIs financieros + dashboard LAN Chile | ALTA |
| nelson-ypf-automation | Automatización procesos YPF (cuando Nelson confirme scope) | BAJA |

---

## 📊 RESUMEN
- Total skills: 213
- Skills nelson-*: ~90 activas
- Gaps identificados: 6
- Dominios cubiertos: 10
- Última actualización: 2026-06-20
