#!/bin/bash
# sync-to-repo.sh — Exportar skills desde ~/.hermes/skills/ al repo
# Uso: ./sync-to-repo.sh

set -e

HERMES_SKILLS_DIR="$HOME/.hermes/skills/software-development"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

SKILLS=(
  equipo-nelson
  fastapi
  nelson-agent-routing
  nelson-ai-agents
  nelson-ai-vision
  nelson-audio-processing
  nelson-automation-n8n
  nelson-background-jobs
  nelson-brainstorming
  nelson-browser-agent
  nelson-business-plan
  nelson-ci-cd
  nelson-cloud-storage-comparison
  nelson-cloudflare-tunnel-deploy
  nelson-code-quality
  nelson-codegraph
  nelson-content-generation
  nelson-context-handoff
  nelson-database
  nelson-data-science
  nelson-demo-script
  nelson-deploy-gcp
  nelson-docling
  nelson-documentation
  nelson-document-processing
  nelson-document-qa
  nelson-embeddings
  nelson-error-review
  nelson-eval-harness
  nelson-external-communication
  nelson-external-integrations
  nelson-floci-gcp
  nelson-forest-inventory
  nelson-frontend-agent
  nelson-frontend-stack
  nelson-frontend-testing
  nelson-generative-ui
  nelson-lean-ctx
  nelson-llm-generation
  nelson-meta-orchestrator
  nelson-monitoring-observability
  nelson-observability
  nelson-optillm
  nelson-os-security
  nelson-poc-dashboard-ai-chat
  nelson-pricing-model
  nelson-project-bootstrap
  nelson-project-constitution
  nelson-rag-pipeline
  nelson-react-doctor
  nelson-robotocore
  nelson-scheduled-jobs
  nelson-security
  nelson-senior-practices
  nelson-server-services
  nelson-spec-analyzer
  nelson-spec-driven-workflow
  nelson-startup-benchmarking
  nelson-task-memory
  nelson-vector-databases
  nelson-whatsapp-gateway
  nelson-workflow-security
  nvidia-nim-free-api
  spec-driven-development
  understand-anything
)

echo "=== Sync TO repo (export desde Hermes) ==="
for skill in "${SKILLS[@]}"; do
  src="$HERMES_SKILLS_DIR/$skill"
  dst="$REPO_DIR/$skill"

  if [ -d "$src" ]; then
    echo "Copiando $skill..."
    rm -rf "$dst"
    cp -r "$src" "$dst"
  else
    echo "WARNING: $skill no existe en $HERMES_SKILLS_DIR"
  fi
done

# Sync memoria
echo "=== Sync memoria ==="
cp "$HOME/.hermes/memories/MEMORY.md" "$REPO_DIR/memories/" 2>/dev/null || echo "MEMORY.md no encontrado"
cp "$HOME/.hermes/memories/USER.md" "$REPO_DIR/memories/" 2>/dev/null || echo "USER.md no encontrado"

echo "=== Listo. Skills y memoria exportadas al repo. ==="
echo "Ahora haga: cd $REPO_DIR && git add . && git commit -m 'sync skills + memoria' && git push"
