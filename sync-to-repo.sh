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

echo "=== Listo. Skills exportadas al repo. ==="
echo "Ahora haga: cd $REPO_DIR && git add . && git commit -m 'sync skills' && git push"
