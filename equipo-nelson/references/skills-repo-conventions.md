# Skills repo — convención de limpieza

El repo https://github.com/aliagenttucuman-byte/nelson-hermes-skills.git
debe contener SOLO skills propias del equipo Nelson.

## Qué va en el repo

- nelson-* (todas)
- equipo-nelson/
- fastapi/
- spec-driven-development/
- nvidia-nim-free-api/
- debugging-hermes-tui-commands/ (Hermes-specific pero relevante)

## Qué NO va (skills genéricas de Hermes)

Todo lo demás: api-design-principles, apple, architecture-patterns, async-python-patterns,
autonomous-ai-agents, brainstorming, creative, curator_backups, data-science, defuddle,
devops, email, gaming, github, mcp, media, memories, mlops, node-inspect-debugger,
note-taking, obsidian-*, plan, productivity, python-*, red-teaming, requesting-code-review,
research, smart-home, social-media, software-development (carpeta paraguas), spike,
subagent-driven-development, systematic-debugging, test-driven-development, writing-plans,
yuanbao, .usage.json, sync-*.sh, .bundled_manifest, .curator_*, .hub/

## .gitignore actualizado el 2026-05-26

Se removieron >10.000 archivos en commit bc9c67b. El .gitignore ya bloquea la reentrada.

## Cómo remover una skill nueva si se coló

```bash
cd /home/server/.hermes/skills
git rm -r --cached <nombre-skill>/
echo "<nombre-skill>/" >> .gitignore
git add -A && git commit -m "chore: remover skill genérica de Hermes" && git push
```
