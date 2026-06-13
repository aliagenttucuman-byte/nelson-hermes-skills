# Prompt-first Excel automation (usuarios no técnicos)

## Cuándo usar
- El usuario describe resultados esperados, no operaciones técnicas.
- Hay procesos manuales repetitivos con múltiples Excels.
- Se necesita confianza gradual antes de automatización total.

## Arquitectura mínima (PoC)

Frontend (wizard):
1) Objetivo
2) Plan sugerido
3) Resultado

Backend:
- `POST /excel/plan/suggest` → genera pasos sugeridos desde objetivo + archivos cargados.
- `POST /excel/merge` → ejecuta reglas + prompt de negocio.
- `GET /excel/files` + `DELETE /excel/files/{id}` + `POST /excel/files/clear`.
- `POST /excel/load-samples` para arrancar con data de prueba.
- Biblioteca de procedimientos:
  - `GET /excel/procedures`
  - `POST /excel/procedures`
  - `POST /excel/procedures/reorder`
  - `POST /excel/procedures/{id}/mark-used`

## Decisiones de UX clave
- Ocultar `join/concat` en UI principal.
- Mostrar explicaciones en español por paso.
- Guardar procedimiento automáticamente tras ejecución exitosa.
- Permitir reordenar biblioteca para priorizar procesos más usados.
- Pre-cargar archivos ejemplo para demo inmediata y permitir borrado/limpieza.

## Pitfalls observados
- En joins encadenados, evitar colisión de columnas `_right`: usar `suffix` único por paso o por file_id.
- No usar heurísticas NLP demasiado amplias para join type (ej: detectar "todo" como outer join genera falsos positivos).
- Mantener carga incremental: el usuario debe poder subir más archivos aunque ya tenga ejemplos cargados.

## Criterio de éxito para adopción
- Usuario no técnico logra correr flujo completo sin saber SQL/joins.
- Puede guardar y reutilizar lógica sin reconstruir pasos manualmente.
- Puede validar resultado con preview y descarga.
