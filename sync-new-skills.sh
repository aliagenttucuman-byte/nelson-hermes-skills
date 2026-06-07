#!/bin/bash
# sync-new-skills.sh — Sync específico de las 4 skills nuevas al repo
# Las skills viven en ~/.hermes/skills/ (raíz), no en software-development/
# Después se puede integrar al sync-to-repo.sh general

set -e

REPO_DIR="/home/server/repos/nelson-hermes-skills"
HERMES_SKILLS_DIR="$HOME/.hermes/skills"

NEW_SKILLS=(
  nelson-incident-response
  nelson-multi-tenancy
  nelson-project-tracking
  nelson-backup-dr
)

echo "=== Sync de 4 skills nuevas al repo ==="
for skill in "${NEW_SKILLS[@]}"; do
  src="$HERMES_SKILLS_DIR/$skill"
  dst="$REPO_DIR/$skill"

  if [ -d "$src" ]; then
    echo "Copiando $skill..."
    rm -rf "$dst"
    cp -r "$src" "$dst"
    echo "  ✓ $skill → $dst"
  else
    echo "  ✗ $skill no existe en $HERMES_SKILLS_DIR"
  fi
done

# Sync memoria
echo ""
echo "=== Sync memoria ==="
[[ -f "$HOME/.hermes/memories/MEMORY.md" ]] && cp "$HOME/.hermes/memories/MEMORY.md" "$REPO_DIR/memories/" && echo "  ✓ MEMORY.md"
[[ -f "$HOME/.hermes/memories/USER.md" ]] && cp "$HOME/.hermes/memories/USER.md" "$REPO_DIR/memories/" && echo "  ✓ USER.md"

echo ""
echo "=== Listo. Siguiente paso: ==="
echo "  cd $REPO_DIR"
echo "  git add ."
echo "  git commit -m 'Add 4 new skills: incident-response, multi-tenancy, project-tracking, backup-dr'"
echo "  git push"
