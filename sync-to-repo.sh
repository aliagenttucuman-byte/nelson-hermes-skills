#!/bin/bash
# sync-to-repo.sh — Exportar skills desde ~/.hermes/skills/ al repo
# Uso: ./sync-to-repo.sh

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
