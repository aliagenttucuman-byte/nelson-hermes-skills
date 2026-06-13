# Orchestrator UI flow order (Tony-first)

## Contexto
En operación real, el bloque "Objetivo de misión" no debe quedar enterrado entre cards de diagnóstico. Cuando aparece en el medio de la pantalla, rompe el flujo de uso y obliga a scroll innecesario.

## Regla operativa
En `src/pages/Orchestrator.tsx`, ordenar la vista para que el primer bloque accionable sea la captura del objetivo.

Orden recomendado:
1. Modo Misión (contexto)
2. Objetivo de misión (input)
3. Plan / Confirmar ejecución
4. Estado operativo (health + conectores)
5. Gates / KPIs
6. Timeline + control de subtareas + recientes

## Pitfalls detectados
- Duplicar "Objetivo de misión" al mover bloques (quedar arriba y abajo a la vez).
- Mover el input y olvidar limpiar la copia vieja.
- No validar build luego de refactor de layout.

## Checklist de cierre
- [ ] Solo existe un bloque "Objetivo de misión"
- [ ] Está visible arriba sin scroll
- [ ] `npm run build` pasa
- [ ] Flujo principal (planificar/confirmar) sigue intacto
