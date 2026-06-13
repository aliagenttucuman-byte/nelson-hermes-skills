# Prompt-first workflow pattern (usuarios no técnicos)

Cuándo usar:
- Herramientas de automatización de procesos manuales (Excel, reportes, conciliaciones) donde el usuario final NO domina términos técnicos (`join`, `concat`, `group by`).

Objetivo UX:
- Reemplazar configuración técnica por intención en lenguaje natural.

Patrón recomendado:
1. **Objetivo**: textarea libre (`Qué querés obtener`).
2. **Plan sugerido**: backend interpreta intención y propone pasos legibles.
3. **Ejecución**: botón único (`Ejecutar plan`).
4. **Resultado**: preview + descarga.
5. **Reuso**: guardar automáticamente procedimiento cuando ejecución fue exitosa.

Buenas prácticas de UI:
- No mostrar `join_type/how` al usuario final.
- Mostrar frases humanas: `Cruzar archivo 2 por DNI`, `Combinar archivo 3`.
- Mantener modo avanzado oculto (solo para soporte/debug).
- En mobile: CTA full-width, cards apiladas, tabla con scroll horizontal.

Persistencia de procedimientos (PoC pragmático):
- Guardar: `name`, `objective`, `expected_result`, `model`, `run_count`, `sort_order`.
- Operaciones mínimas:
  - listar
  - crear/actualizar por nombre
  - marcar uso exitoso
  - reordenar (drag/drop o flechas)

Contrato backend sugerido:
- `POST /plan/suggest`  -> plan en lenguaje natural (pasos)
- `POST /merge`         -> ejecuta
- `GET /procedures`     -> biblioteca
- `POST /procedures`    -> upsert
- `POST /procedures/reorder`
- `POST /procedures/{id}/mark-used`

Pitfall clave:
- Si se hace multi-join encadenado, usar sufijos por paso/archivo para evitar colisiones de columnas duplicadas (`_s2`, `_ab12cd`).
