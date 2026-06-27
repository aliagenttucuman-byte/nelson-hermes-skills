# Plantilla de mensaje de cierre (WhatsApp)

> ≤15 líneas. Nelson odia textos largos. La estructura es fija; el contenido cambia.

```
[NOMBRE-SKILL] creada en `~/.hermes/skills/<path>/` (X KB, N archivos)
- SKILL.md — [qué cubre, 1 línea]
- templates/<archivo> — [qué es, 1 línea]
- examples/<archivo> — [si aplica, qué muestra, 1 línea]

[Si hay decisión de diseño clave, incluir acá]
Decisión: [1 línea con la elección y por qué]. [Una oración de rationale si hace falta].

Roadmap actualizado: [skill-1, skill-2, skill-3] → 🟢 Hechas. Siguiente candidata: [nombre] (1 línea de por qué).

¿Seguimos con [próxima]?
```

## Variantes

### Cuando la skill es corta y no hay decisión de diseño

```
nelson-X creada (X KB).
- SKILL.md — [qué cubre]
- templates/<archivo> — [qué es]

Roadmap: [skills cerradas] → 🟢. Siguiente: [nombre].

¿Seguimos?
```

### Cuando se descubre algo que cambia el orden del roadmap

```
nelson-X creada (X KB). [Una línea de qué cubre]

Cambio en el roadmap: al inspeccionar [proyecto Y] descubrí que [problema Z] es más urgente que [skill planeada]. Reordeno: la próxima es [nombre nuevo] en lugar de [nombre viejo].

¿OK con el cambio o querés mantener el orden original?
```

### Cuando hay un error visible (la skill se hizo pero algo falló)

```
nelson-X creada (X KB) con caveat: [qué no funcionó, qué se puede hacer al respecto].

[Una oración de impacto en el roadmap si lo hay]

¿Lo dejamos así y avanzamos, o querés que arregle [X] antes de seguir?
```
