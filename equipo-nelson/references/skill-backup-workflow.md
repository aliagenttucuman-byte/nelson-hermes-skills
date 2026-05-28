# Backup y Versionado de Skills Custom

Flujo para exportar las skills custom del equipo a un repo de GitHub, compartirlas con el equipo, e importarlas en una máquina nueva.

## Por qué

Las skills custom viven en `~/.hermes/skills/` y no se sincronizan automáticamente. Si cambias de máquina o se une un nuevo miembro al equipo (ej: Pablo Ruiz / Terian), hay que reinstalarlas manualmente. Este flujo las versiona con git y las hace portables.

## Repo de skills del equipo

URL: `https://github.com/aliagenttucuman-byte/nelson-hermes-skills`

Contiene 22 skills custom (~444 KB) más scripts de sincronización.

## Exportar skills desde Hermes al repo (backup)

> **⚠️ REGLA DEL EQUIPO:** No sincronizar automáticamente después de cada cambio menor. El usuario decide cuándo la información es valiosa. Esperar indicación explícita como "guardá esto", "hacé backup", "sync al repo", o similar.

```bash
cd ~/repos/nelson-hermes-skills
./sync-to-repo.sh
git add . && git commit -m "sync skills" && git push
```

El script `sync-to-repo.sh` copia las skills desde `~/.hermes/skills/software-development/` al repo, manteniendo la estructura de directorios.

Skills cubiertas:
- `equipo-nelson` (skill maestra)
- `nelson-*` (21 skills especializadas: ai-agents, ai-vision, backend, frontend, database, security, deploy, etc.)

## Importar skills desde el repo a Hermes (nueva máquina)

```bash
git clone https://github.com/aliagenttucuman-byte/nelson-hermes-skills.git
cd nelson-hermes-skills
./sync-from-repo.sh
```

El script `sync-from-repo.sh` copia las skills al directorio `~/.hermes/skills/software-development/` donde Hermes las descubre automáticamente.

Después del sync, reiniciar la sesión de Hermes (`/reset` en chat o nueva sesión CLI) para que recargue las skills.

## Instalar una skill individual desde archivo local

```bash
hermes skills install ./nelson-security/SKILL.md --name nelson-security
```

O usar ruta absoluta:

```bash
hermes skills install /home/server/repos/nelson-hermes-skills/nelson-security/SKILL.md
```

## Registrar el repo como fuente de skills (tap)

Hermes puede instalar skills directamente desde un repo de GitHub sin clonar:

```bash
hermes skills tap add https://github.com/aliagenttucuman-byte/nelson-hermes-skills
```

Luego instalar individualmente:

```bash
hermes skills install equipo-nelson
hermes skills install nelson-deploy-gcp
```

## Listar skills custom actuales

```bash
find ~/.hermes/skills/software-development -maxdepth 1 -type d | sort
# o
hermes skills list | grep nelson
```

## Verificar espacio

```bash
du -sh ~/.hermes/skills/software-development/nelson-* ~/.hermes/skills/software-development/equipo-nelson
```

## Estructura del repo de skills

```
nelson-hermes-skills/
├── README.md
├── sync-to-repo.sh       # export desde Hermes
├── sync-from-repo.sh     # import a Hermes
├── equipo-nelson/
│   ├── SKILL.md
│   ├── references/
│   └── templates/
├── nelson-ai-agents/
│   └── SKILL.md
├── nelson-ai-vision/
│   └── SKILL.md
├── nelson-backend/
│   └── SKILL.md
├── ... (21 skills)
```

## Chequeo post-import

Después de correr `sync-from-repo.sh`, verificar que Hermes las ve:

```bash
hermes skills list | grep -E "equipo-nelson|nelson-"
```

Si no aparecen, revisar que el directorio destino sea exactamente `~/.hermes/skills/software-development/` y que cada skill tenga su `SKILL.md` en la raíz del directorio.

## Actualizar skills en el repo

Cuando se crea una skill nueva o se modifica una existente:

1. Desarrollar la skill en Hermes (`skill_manage` o edición directa)
2. Correr `sync-to-repo.sh` para exportar
3. `git add . && git commit -m "feat: descripción del cambio" && git push`
4. El equipo hace `git pull && ./sync-from-repo.sh` para actualizar

## Pitfall: Conflictos de rebase al hacer push

Si el remote tiene commits que no tenemos localmente, `git pull --rebase` puede generar conflictos. Estrategia correcta — **el servidor es siempre la fuente de verdad**:

```bash
cd /home/server/repos/nelson-hermes-skills

# 1. Pull con rebase
git pull --rebase origin main

# 2. Si hay conflictos (suele ser en SKILL.md y memories/):
#    "theirs" = nuestra versión local (ya que hacemos rebase encima del remote)
git checkout --theirs equipo-nelson/SKILL.md
git checkout --theirs nelson-brainstorming/SKILL.md
# ... repetir para cada archivo en conflicto que muestre el rebase ...
git checkout --theirs memories/MEMORY.md
git checkout --theirs memories/USER.md
git checkout --theirs sync-to-repo.sh

# 3. Marcar como resueltos
git add .

# 4. Continuar rebase (sin abrir editor)
GIT_EDITOR=true git rebase --continue

# 5. Push
git push
```

Los conflictos más comunes son en:
- `equipo-nelson/SKILL.md` (la skill más activa)
- `memories/MEMORY.md` y `memories/USER.md` (el remote los eliminó en algún commit)
- Skills recién creadas que el remote también tiene (add/add conflict)
- `sync-to-repo.sh` (si se actualizó la lista de skills)

## Pitfall: Skills en paths distintos a software-development/

Algunas skills no están en `~/.hermes/skills/software-development/` sino en subdirectorios propios:
- `fastapi` → `~/.hermes/skills/fastapi/` (no en software-development)
- `nelson-server-services` → `~/.hermes/skills/devops/nelson-server-services/`

El `sync-to-repo.sh` busca en `software-development/` por defecto. Para estas skills, copiar manualmente:

```bash
cp -r ~/.hermes/skills/fastapi /home/server/repos/nelson-hermes-skills/fastapi
cp -r ~/.hermes/skills/devops/nelson-server-services /home/server/repos/nelson-hermes-skills/nelson-server-services
```

## Skills nuevas agregadas en sync 2026-05-28

Las siguientes 20 skills faltaban en el repo y fueron agregadas:
`nelson-agent-routing`, `nelson-browser-agent`, `nelson-business-plan`, `nelson-cloudflare-tunnel-deploy`,
`nelson-codegraph`, `nelson-context-handoff`, `nelson-demo-script`, `nelson-eval-harness`,
`nelson-floci-gcp`, `nelson-forest-inventory`, `nelson-generative-ui`, `nelson-lean-ctx`,
`nelson-meta-orchestrator`, `nelson-monitoring-observability`, `nelson-optillm`, `nelson-poc-dashboard-ai-chat`,
`nelson-server-services`, `nelson-startup-benchmarking`, `nelson-task-memory`, `understand-anything`.

El `sync-to-repo.sh` fue actualizado con la lista completa.

## Cómo detectar skills faltantes

```bash
# Ver qué está en Hermes pero no en el repo
ls ~/.hermes/skills/software-development/ | sort > /tmp/hermes_skills.txt
ls /home/server/repos/nelson-hermes-skills/ | grep -E '^(nelson-|equipo-|nvidia-|spec-|fastapi|understand)' | sort > /tmp/repo_skills.txt
diff /tmp/hermes_skills.txt /tmp/repo_skills.txt
```

## Notas

- Las skills del hub oficial no se incluyen en el backup; solo las custom del equipo.
- `hermes skills update` actualiza skills del hub, no las custom.
- Las skills custom se mantienen en `software-development/` porque todas las del equipo están categorizadas ahí.
- Si una skill tiene archivos vinculados (`references/`, `templates/`, `scripts/`), `sync-to-repo.sh` los copia recursivamente.
