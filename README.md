# Skills del Equipo Nelson para Hermes Agent

Repositorio de backup y versionado de las skills custom y la memoria persistente creadas para el equipo de desarrollo de Nelson Acosta (Tony Stark).

## Skills incluidas

| Skill | Descripcion |
|-------|-------------|
| equipo-nelson | Skill maestra del equipo. Stack general y convenciones |
| nelson-ai-agents | Agentes de IA autonomos. ReAct, function calling, multi-agent |
| nelson-ai-vision | Vision por computadora. OCR, object detection, documentos |
| nelson-backup-dr | Politica de backups y disaster recovery. RTO/RPO, scripts, runbooks |
| nelson-background-jobs | Procesamiento async con Celery + Redis |
| nelson-ci-cd | Pipeline CI/CD con GitHub Actions + GCP |
| nelson-code-quality | Ruff, mypy, pre-commit hooks |
| nelson-database | SQLAlchemy 2.0, Alembic, PostgreSQL |
| nelson-data-science | XGBoost, LightGBM, scikit-learn, Optuna |
| nelson-deploy-gcp | Cloud Run, Cloud SQL, Artifact Registry |
| nelson-documentation | README, docstrings, MkDocs |
| nelson-document-processing | Extraccion de texto de PDFs, Word, TXT |
| nelson-embeddings | OpenAI, sentence-transformers, Ollama local |
| nelson-frontend-stack | React 18, TypeScript, Vite, Tailwind |
| nelson-frontend-testing | Vitest, React Testing Library, Playwright |
| nelson-incident-response | Runbooks y escalamiento para caidas en produccion |
| nelson-llm-generation | Integracion LLMs. Streaming, retry, cost tracking |
| nelson-multi-tenancy | Aislamiento multi-tenant. DB separada, schema, row-level + RLS |
| nelson-observability | structlog, Prometheus, health checks |
| nelson-project-bootstrap | Scaffold completo backend+frontend+devops |
| nelson-project-tracking | Estimacion T-shirt, velocity, burndown, time tracking |
| nelson-rag-pipeline | Chunking, embeddings, retrieval, re-ranking |
| nelson-security | JWT, OAuth2, CORS, rate limiting, bcrypt |
| nelson-senior-practices | Type hints estrictos, SOLID, clean code |
| nelson-vector-databases | Qdrant, Chroma, Weaviate |

## Instalacion rapida

Desde una maquina nueva con Hermes Agent instalado:

```bash
# Clonar
git clone https://github.com/aliagenttucuman-byte/nelson-hermes-skills.git

# Instalar todas las skills
./sync-from-repo.sh

# O instalar una sola
hermes skills install ./nelson-security/SKILL.md
```

## Memoria persistente

Tambien se backupea la memoria de JARVIS:

| Archivo | Que guarda |
|---------|-----------|
| `memories/MEMORY.md` | Notas del entorno, preferencias, lecciones aprendidas |
| `memories/USER.md` | Perfil de Nelson (Tony Stark), stack, familia, socios |

Esto permite que si cambiamos de maquina, JARVIS recuerde todo desde el primer momento.

## Flujo de trabajo

### Exportar skills y memoria desde Hermes al repo (backup)

```bash
./sync-to-repo.sh
```

Esto copia las skills desde `~/.hermes/skills/software-development/` y la memoria desde `~/.hermes/memories/` al repo.

### Importar skills y memoria desde el repo a Hermes

```bash
./sync-from-repo.sh
```

Esto copia todo al directorio de Hermes y lo hace disponible inmediatamente.

### Usar como fuente de skills (tap)

Hermes puede leer skills directamente desde un repo de GitHub:

```bash
hermes skills tap add https://github.com/aliagenttucuman-byte/nelson-hermes-skills
```

Luego se instalan individualmente con:

```bash
hermes skills install equipo-nelson
```

## Contribuciones

- Pablo Ruiz (Terian)
- Nelson Acosta

---

*JARVIS approved.*
