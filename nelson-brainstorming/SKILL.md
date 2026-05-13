---
name: nelson-brainstorming
description: Archivado de brainstorming y documentos de proyecto para Nelson Acosta. Crea carpetas con fecha, README.md obligatorio, y templates reutilizables.
category: software-development
tags: [brainstorming, documentation, project-management, sdd, specs]
related_skills: [nelson-project-bootstrap, spec-driven-development, writing-plans]
---

# Brainstorming & Documentación de Proyectos

> **Trigger:** Cada vez que Tony (Nelson) propone una idea de negocio, proyecto nuevo, feature, o refinamiento de arquitectura. También cuando se genera un SDD, spec OpenAPI, análisis financiero o modelo de dominio.

## Convención de Carpetas

Todo brainstorming, SDD, spec o documento de proyecto se guarda en:

```
~/brainstorming/
├── YYYY-MM-DD-nombre-del-proyecto/
│   ├── README.md              # Resumen ejecutivo (obligatorio)
│   ├── SDD.md                 # Software Design Document (si aplica)
│   ├── openapi.yaml           # Spec API (si aplica)
│   ├── financiero.md          # Modelos VAN/TIR/costos (si aplica)
│   ├── diagramas/             # PNG/SVG/Excalidraw
│   ├── notas/                 # Ideas sueltas, links, referencias
│   └── decisiones.md          # Decisiones clave tomadas
│
└── templates/
    ├── sdd-template.md
    ├── brainstorming-README.md
    └── openapi-template.yaml
```

## Reglas de Oro

1. **UNA CARPETA POR SESIÓN/PROYECTO** — Nunca archivos sueltos en `~/`
2. **Fecha obligatoria** al inicio: `YYYY-MM-DD-`
3. **README.md siempre** — Resumen de 10-15 líneas para que cualquiera entienda de qué trata sin abrir otros archivos
4. **SDD separado del README** — El README es resumen; el SDD es el documento técnico completo
5. **Versionado** — Si hay cambios mayores, copiar a nueva carpeta con `_v2`

## Flujo de Trabajo Automático

Cuando Tony inicia un brainstorming:

```
1. Detectar tema/proyecto
2. Crear carpeta: mkdir -p ~/brainstorming/YYYY-MM-DD-{nombre}/
3. Generar documento(s) dentro de esa carpeta (SDD, specs, etc.)
4. Crear README.md usando template (ver templates/brainstorming-README.md)
5. Si es proyecto activo → considerar symlink a ~/proyectos/activos/
```

## Pitfalls

- **NO guardar specs en `~/` suelto** — Tony lo corrigió explícitamente: "vayamos generando mínimo una carpeta"
- **NO mezclar README con SDD** — El README debe caber en una pantalla; el SDD puede ser largo
- **NO olvidar la fecha** — Sin fecha no se sabe qué brainstorming es el más reciente
- **NO usar nombres genéricos** como `proyecto-nuevo`; ser específico: `fleet-optimizer`, `rag-documentos`

## Comandos Útiles

```bash
# Listar brainstormings recientes
ls -lt ~/brainstorming/ | head -20

# Buscar en todos los brainstormings
grep -r "VAN" ~/brainstorming/ --include="*.md"

# Último brainstorming
cd ~/brainstorming/$(ls -t ~/brainstorming/ | head -1)
```

## Archivos de Soporte

- `templates/brainstorming-README.md` — Template copiable para README de cada sesión
- `templates/sdd-template.md` — Template para Software Design Documents
- `references/fleet-optimizer-example.md` — Ejemplo concreto de SDD completo con VAN/TIR y OpenAPI
