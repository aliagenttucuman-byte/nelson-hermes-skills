# ui-skills.com — Integración al stack Nelson

## Origen
ui-skills.com es un registry de skills curadas para agentes IA, basado en el repo público:
https://github.com/anthropics/skills/tree/main/skills

## Skills integradas al equipo Nelson (19/06/2026)

| Skill Nelson | Skill Original | Descripción |
|---|---|---|
| nelson-ui-frontend-design | frontend-design | Diseño visual distintivo, tipografía, layout |
| nelson-ui-webapp-testing | webapp-testing | Testing Playwright — Reconnaissance-Then-Action |
| nelson-ui-theme-factory | theme-factory | 10 temas predefinidos para slides/docs/landing |
| nelson-ui-xlsx | xlsx | Excel con pandas/openpyxl, estándares financieros |

## Cómo agregar más skills del registry

```bash
# Ver skills disponibles
curl -sL 'https://api.github.com/repos/anthropics/skills/contents/skills' | python3 -c "
import sys, json
for item in json.load(sys.stdin):
    print(item['name'])
"

# Descargar una skill específica
curl -sL 'https://raw.githubusercontent.com/anthropics/skills/main/skills/{nombre}/SKILL.md'
```

## Convención de nombres
Todas las skills de ui-skills integradas al equipo Nelson usan el prefijo `nelson-ui-`.
Se crean en la categoría `nelson-frontend-stack`.

## Cuándo usar
- Antes de tocar cualquier componente UI — cargar nelson-ui-frontend-design
- Para testing de UI — cargar nelson-ui-webapp-testing  
- Para demos/presentaciones — cargar nelson-ui-theme-factory
- Para cualquier Excel — cargar nelson-ui-xlsx (ya usado en Bisonte)
