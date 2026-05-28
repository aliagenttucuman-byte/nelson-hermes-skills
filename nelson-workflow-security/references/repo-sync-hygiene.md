# Higiene de Sync al Repo — Skills del equipo vs Built-in de Hermes

> **Lección aprendida (2026-05-26):** El script `sync-to-repo.sh` debe distinguir skills del equipo Nelson de skills built-in de Hermes. Commitear skills genéricos de Hermes ensucia el repo con código que no es nuestro y que el usuario no quiere mantener.

## Reglas del sync

### 1. SOLO sincronizar skills del equipo Nelson

**SÍ (equipo Nelson):**
- `nelson-*` (todas las skills que empiecen con nelson-)
- `equipo-nelson`

**NO (built-in de Hermes):**
- `api-design-principles`
- `architecture-patterns`
- `async-python-patterns`
- `debugging-hermes-tui-commands`
- `hermes-agent-skill-authoring`
- `node-inspect-debugger`
- `plan`
- `python-debugpy`
- `python-design-patterns`
- `python-project-structure`
- `python-testing-patterns`
- `requesting-code-review`
- `spike`
- `subagent-driven-development`
- `systematic-debugging`
- `test-driven-development`
- `writing-plans`

### 2. Preservar estructura de subdirectorios

Algunas skills tienen sub-skills anidadas. Ejemplo real:

```
nelson-ai-agents/
├── SKILL.md
├── agency-ai-engineer/
│   └── SKILL.md
├── agency-code-reviewer/
│   └── SKILL.md
├── agency-embedded-engineer/
│   └── SKILL.md
...
```

El sync debe copiar recursivamente, **NO aplanar** la estructura.

**Pitfall — sync que borra subdirectorios:**
```bash
# MAL: esto BORRA agency-* si el destino existe
rm -rf "$dst" && cp -r "$src" "$dst"

# Si el destino existe y tiene archivos que el source no tiene,
# el rm -rf los elimina. Verificar que no haya subdirectorios
# importantes antes de reemplazar.
```

**Fix:** Listar subdirectorios del source y destino antes del reemplazo:
```bash
echo "Subdirs en source:"
find "$src" -maxdepth 1 -type d | sort

echo "Subdirs en destino:"
find "$dst" -maxdepth 1 -type d | sort 2>/dev/null || true
```

### 3. .gitignore del repo debe excluir skills built-in

```gitignore
# Skills built-in de Hermes (no son del equipo Nelson)
api-design-principles/
architecture-patterns/
async-python-patterns/
debugging-hermes-tui-commands/
hermes-agent-skill-authoring/
node-inspect-debugger/
plan/
python-debugpy/
python-design-patterns/
python-project-structure/
python-testing-patterns/
requesting-code-review/
spike/
subagent-driven-development/
systematic-debugging/
test-driven-development/
writing-plans/
```

### 4. Verificación pre-commit

```bash
#!/bin/bash
# check-hermes-skills.sh — Pre-commit hook

BUILT_IN=(
  api-design-principles
  architecture-patterns
  async-python-patterns
  debugging-hermes-tui-commands
  hermes-agent-skill-authoring
  node-inspect-debugger
  plan
  python-debugpy
  python-design-patterns
  python-project-structure
  python-testing-patterns
  requesting-code-review
  spike
  subagent-driven-development
  systematic-debugging
  test-driven-development
  writing-plans
)

ERRORS=0
for skill in "${BUILT_IN[@]}"; do
  if git diff --cached --name-only | grep -q "^$skill/"; then
    echo "ERROR: Skill built-in '$skill' no debe commitearse."
    echo "  Agregar a .gitignore o remover del stage: git reset HEAD $skill/"
    ERRORS=$((ERRORS+1))
  fi
done

if [ $ERRORS -gt 0 ]; then
  echo "COMMIT BLOQUEADO: $ERRORS skill(s) built-in detectado(s)."
  exit 1
fi
```

## Caso real — 2026-05-26

El sync-to-repo.sh original tenía todos los skills en el array, incluyendo built-in de Hermes. Después de correr `./sync-to-repo.sh` y commitear, el usuario dijo:

> "los skills que son propios de hermes, no hace falta commitearlos"

Se removieron 17 skills built-in del tracking y se agregaron al .gitignore.

Luego, el sync borró accidentalmente los subdirectorios `agency-*` de `nelson-ai-agents`. El usuario dijo:

> "los agency tienen que estar, no los saques"

Se restauraron los 6 sub-skills agency-* desde `~/.hermes/skills/`.

## Checklist post-sync

- [ ] Array `SKILLS` de sync-to-repo.sh solo contiene `nelson-*` y `equipo-nelson`
- [ ] .gitignore excluye skills built-in de Hermes
- [ ] Subdirectorios dentro de skills (agency-*, templates/, scripts/) se preservan
- [ ] `git diff --stat` antes de commit para verificar que solo hay cambios esperados
- [ ] Si se borró algo accidentalmente, restaurar desde `~/.hermes/skills/software-development/`
