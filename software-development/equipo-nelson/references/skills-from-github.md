# Instalar Skills desde GitHub (Hub IDs truncados)

## Problema

`hermes skills search` muestra IDs truncados con `...` al final. Al intentar instalar con el ID truncado, falla con:
```
Error: Could not fetch 'skills-sh/wshob...' from any source.
```

## Solución 1: Agregar el repo como tap

```bash
# Ejemplo: skills de wshobson
hermes skills tap add https://github.com/wshobson/agents

# Luego buscar con el tap agregado
hermes skills search fastapi
```

## Solución 2: Instalar desde URL directa

```bash
hermes skills install https://raw.githubusercontent.com/USER/REPO/main/PATH/SKILL.md --name nombre-local
```

## Solución 3: Descargar manualmente y crear skill local

```python
import urllib.request

url = "https://raw.githubusercontent.com/USER/REPO/main/PATH/SKILL.md"
headers = {"Authorization": "token TU_TOKEN"}
req = urllib.request.Request(url, headers=headers)

with urllib.request.urlopen(req) as resp:
    content = resp.read().decode('utf-8')

with open(f"/tmp/nombre-skill.md", "w") as f:
    f.write(content)
```

Luego copiar a `~/.hermes/skills/software-development/nombre-skill/SKILL.md`.

## Estructura de repos comunes

### wshobson/agents
```
plugins/
  backend-development/skills/
    api-design-principles/
    architecture-patterns/
    microservices-patterns/
  python-development/skills/
    async-python-patterns/
    python-testing-patterns/
    python-project-structure/
    python-design-patterns/
```

## Repos útiles para descargar skills directamente

| Repo | Skills destacadas |
|------|-------------------|
| wshobson/agents | python-testing-patterns, async-python-patterns, api-design-principles |
| lobehub/lobe-chat-skills | software-architecture, api-docs-writer, tailwind-helper |

## Recomendación

Siempre preferir `hermes skills tap add` primero. Si falla por rate limit, autenticar gh CLI o usar token directo en curl.
