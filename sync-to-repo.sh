#!/bin/bash
# sync-to-repo.sh — Exportar skills desde ~/.hermes/skills/ al repo
# Uso: ./sync-to-repo.sh

set -e

HERMES_SKILLS_DIR="$HOME/.hermes/skills/software-development"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

SKILLS=(
  api-design-principles
  architecture-patterns
  async-python-patterns
  debugging-hermes-tui-commands
  equipo-nelson
  hermes-agent-skill-authoring
  nelson-ai-agents
  nelson-ai-vision
  nelson-audio-processing
  nelson-automation-n8n
  nelson-background-jobs
  nelson-brainstorming
  nelson-ci-cd
  nelson-cloud-storage-comparison
  nelson-code-quality
  nelson-content-generation
  nelson-database
  nelson-data-science
  nelson-deploy-gcp
  nelson-documentation
  nelson-document-processing
  nelson-document-qa
  nelson-embeddings
  nelson-error-review
  nelson-external-communication
  nelson-external-integrations
  nvidia-nim-free-api
  nelson-frontend-agent
  nelson-frontend-stack
  nelson-frontend-testing
  nelson-llm-generation
  nelson-observability
  nelson-pricing-model
  nelson-os-security
  nelson-project-bootstrap
  nelson-project-constitution
  nelson-rag-pipeline
  nelson-react-doctor
  nelson-robotocore
  nelson-scheduled-jobs
  nelson-security
  nelson-senior-practices
  nelson-spec-analyzer
  nelson-spec-driven-workflow
  nelson-vector-databases
  nelson-whatsapp-gateway
  nelson-workflow-security
  node-inspect-debugger
  plan
  python-debugpy
  python-design-patterns
  python-project-structure
  python-testing-patterns
  requesting-code-review
  spec-driven-development
  spike
  subagent-driven-development
  systematic-debugging
  test-driven-development
  writing-plans
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
