# Pre-flight check antes de declarar la skill "lista"

> Correr mentalmente (o en una checklist) antes del mensaje de cierre al usuario. Si falla algún punto, fixear antes de mandar el recap.

## Frontmatter

- [ ] `name` en lowercase, hyphens, ≤64 chars
- [ ] `description` ≤1024 chars, empieza con trigger class (no "esta skill es para...")
- [ ] `version: 1.0.0` (o bumped si era patch)
- [ ] `author: JARVIS`
- [ ] `license: MIT`
- [ ] `platforms: [linux]` (o la lista correcta)
- [ ] `metadata.hermes.tags` con 3-6 tags, primero el dominio
- [ ] `metadata.hermes.related_skills` con skills que se cargan junto (no todo el equipo)
- [ ] El primer byte es `---` (sin blank line leading)
- [ ] Cierra con `\n---\n` antes del body

## Tamaño y estructura

- [ ] SKILL.md <30 KB (si está >30, mover secciones a `references/`)
- [ ] Templates separados en `templates/`
- [ ] Si la skill es abstracta, 1-2 ejemplos en `examples/`
- [ ] Estructura sigue el orden: trigger quote → principio rector → § § por capa → pitfalls
- [ ] Tablas no truncadas (no `|...|` con columnas cortadas)

## Contenido

- [ ] Pitfalls son específicos y accionables (no "tener cuidado con X")
- [ ] Si la skill implica decisión de arquitectura, está al frente (§ 2 o § 3), no al final
- [ ] Comandos verificados de correr mentalmente (sintaxis, paths absolutos)
- [ ] Code blocks con el stack real del equipo (Postgres 16, no 14; FastAPI con python 3.12)
- [ ] Cross-refs a otras skills usan `nelson-*` (las que sí están en este equipo)

## Cierre de sesión

- [ ] Carpeta de brainstorming creada: `~/brainstorming/YYYY-MM-DD-nombre-skill/`
- [ ] README de brainstorming 50-100 líneas con: qué se hizo, decisiones, qué NO se hizo, próximos pasos
- [ ] ROADMAP actualizado: skill marcada como 🟢, línea en Histórico
- [ ] `sync-to-repo.sh` del repo `nelson-hermes-skills` actualizado con la skill nueva en el array (si la skill quedó en `~/.hermes/skills/` raíz, no en `software-development/`)
- [ ] Recap al usuario <15 líneas, WhatsApp-friendly
- [ ] Próxima candidata mencionada con pregunta ("¿Seguimos con X?")

## Anti-checks (lo que la skill NO debe tener)

- ❌ "Investigar más adelante" — si falta info, ir a buscarla ahora
- ❌ "TODO: completar X" — los TODOs se pagan solos, resolver antes de cerrar
- ❌ Cross-refs a skills que no existen (ej: `nelson-arquitecto` que no se creó)
- ❌ Información del session ID o fecha hardcodeada en el body (es info efímera)
- ❌ Decisión de arquitectura escondida en el medio (siempre al frente)
