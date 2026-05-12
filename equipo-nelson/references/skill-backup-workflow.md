# Backup y Versionado de Skills Custom

Flujo para exportar las skills custom del equipo a un repo de GitHub, compartirlas con el equipo, e importarlas en una máquina nueva.

## Por qué

Las skills custom viven en `~/.hermes/skills/` y no se sincronizan automáticamente. Si cambias de máquina o se une un nuevo miembro al equipo (ej: Pablo Ruiz / Terian), hay que reinstalarlas manualmente. Este flujo las versiona con git y las hace portables.

## Repo de skills del equipo

URL: `https://github.com/aliagenttucuman-byte/nelson-hermes-skills`

Contiene 22 skills custom (~444 KB) más scripts de sincronización.

## Exportar skills desde Hermes al repo (backup)

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

## Notas

- Las skills del hub oficial no se incluyen en el backup; solo las custom del equipo.
- `hermes skills update` actualiza skills del hub, no las custom.
- Las skills custom se mantienen en `software-development/` porque todas las del equipo están categorizadas ahí.
- Si una skill tiene archivos vinculados (`references/`, `templates/`, `scripts/`), `sync-to-repo.sh` los copia recursivamente.
