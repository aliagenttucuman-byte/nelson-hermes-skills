#!/bin/bash
# sync-from-repo.sh — Importar skills desde el repo a ~/.hermes/skills/
# Uso: ./sync-from-repo.sh

set -e

HERMES_SKILLS_DIR="$HOME/.hermes/skills/software-development"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

SKILLS=(
  equipo-nelson
  nelson-ai-agents
  nelson-ai-vision
  nelson-background-jobs
  nelson-chat-with-documents
  nelson-ci-cd
  nelson-code-quality
  nelson-database
  nelson-data-science
  nelson-deploy-gcp
  nelson-documentation
  nelson-document-processing
  nelson-document-qa
  nelson-embeddings
  nelson-frontend-stack
  nelson-frontend-testing
  nelson-llm-generation
  nelson-observability
  nelson-project-bootstrap
  nelson-rag-pipeline
  nelson-security
  nelson-senior-practices
  nelson-vector-databases
)

echo "=== Sync FROM repo (import a Hermes) ==="
mkdir -p "$HERMES_SKILLS_DIR"

for skill in "${SKILLS[@]}"; do
  src="$REPO_DIR/$skill"
  dst="$HERMES_SKILLS_DIR/$skill"

  if [ -d "$src" ]; then
    echo "Instalando $skill..."
    rm -rf "$dst"
    cp -r "$src" "$dst"
  else
    echo "WARNING: $skill no existe en el repo"
  fi
done

# Sync memoria
echo "=== Sync memoria ==="
mkdir -p "$HOME/.hermes/memories"
cp "$REPO_DIR/memories/MEMORY.md" "$HOME/.hermes/memories/" 2>/dev/null || echo "MEMORY.md no existe en el repo"
cp "$REPO_DIR/memories/USER.md" "$HOME/.hermes/memories/" 2>/dev/null || echo "USER.md no existe en el repo"

echo "=== Listo. Skills y memoria importadas a Hermes. ==="
echo "Reiniciar Hermes o usar /reload-skills para que carguen."
