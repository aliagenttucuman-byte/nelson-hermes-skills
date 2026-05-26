# Patrón: Evaluar e integrar una herramienta nueva al stack

> **Referencia:** Cómo investigar, comparar e integrar una herramienta de terceros descubierta durante una sesión.

## Contexto

Durante el desarrollo, Tony (o cualquier miembro del equipo) puede compartir el URL de una herramienta nueva y preguntar "¿qué opinas?". Esta referencia documenta el patrón probado en las integraciones de **robotocore** (2026-05-26) y **Docling** (2026-05-26).

## Patrón de 7 pasos

```
Paso 1: INVESTIGAR (2-3 min)
    ├── curl GitHub API para metadata (stars, descripción, license)
    ├── Leer README.md (quickstart, features, formatos soportados)
    ├── Identificar si es drop-in replacement, complemento, o alternativa
    └── Buscar LOCALSTACK.md, AGENTS.md, MCP docs si existen

Paso 2: COMPARAR con stack actual (2 min)
    ├── Tabla lado-a-lado: feature vs feature
    ├── Identificar gaps que la herramienta nueva cubre
    ├── Identificar regressions (qué perdemos si reemplazamos)
    └── Veredicto: ¿reemplaza, complementa, o coexiste?

Paso 3: DECIDIR con el usuario (30 seg)
    ├── "¿Querés que lo agregue al stack?"
    ├── "¿Reemplazamos el actual o mantenemos ambos?"
    └── Si el usuario dice "hacelo" sin más detalle → proceder

Paso 4: INTEGRAR en skills existentes (5-10 min)
    ├── Buscar skills que referencien la herramienta anterior
    ├── Actualizar skill maestra (ej. nelson-document-processing)
    ├── Crear skill específica nueva (ej. nelson-docling)
    ├── Actualizar skills relacionadas (ej. nelson-rag-pipeline)
    ├── Mantener legacy como opción alternativa
    └── Documentar connection strings, Docker, pitfalls

Paso 5: ACTUALIZAR sync-to-repo.sh (30 seg)
    ├── Agregar nueva skill al array SKILLS
    └── Verificar que no hay duplicados ni skills built-in de Hermes

Paso 6: COMMIT y PUSH (2 min)
    ├── cd ~/repos/nelson-hermes-skills
    ├── ./sync-to-repo.sh (o cp manual si hay problemas)
    ├── git add -A && git commit -m "feat: integrar X al stack"
    └── git push origin main

Paso 7: VERIFICAR con usuario (30 seg)
    ├── "Commit hecho, push exitoso, hash: abc1234"
    ├── "¿Necesitás que prepare un demo package en ~/brainstorming/?"
    └── Si el usuario dice "no probemos nada" → parar aquí
```

## Ejemplos reales de la sesión

### robotocore (emulador AWS)

| | robotocore | FLoCI-AWS |
|---|---|---|
| Servicios | 147 | ~25 |
| License | MIT | Apache 2.0 |
| Persistencia | Snapshots API | ❌ |
| Drop-in | Sí (puerto 4566) | Sí |

**Veredicto:** Coexistencia. robotocore como opción #1 recomendada, FLoCI-AWS como legacy #4.

**Skills tocadas:**
- `nelson-cloud-storage-comparison` — agregada opción 1 (robotocore), FLoCI-AWS movido a 4
- `nelson-rag-pipeline` — agregada Opción C en docker-compose
- `nelson-robotocore` — skill nueva creada
- `templates/ai-search-assistant-poc.md` — robotocore como default

### Docling (parser de documentos)

| | Docling | pdfplumber |
|---|---|---|
| PDF layout | ✅ | ❌ |
| OCR | ✅ Built-in | ❌ |
| PPTX/XLSX | ✅ | ❌ |
| Peso Docker | ~1.5GB | ~100MB |

**Veredicto:** Docling como estrategia premium, pdfplumber como fallback ligero. Selector inteligente según mime_type y tamaño.

**Skills tocadas:**
- `nelson-document-processing` — reescrita con Docling como #1 + selector
- `nelson-docling` — skill nueva
- `nelson-rag-pipeline` — checklist actualizado

## Decision tree: ¿Cuándo crear skill nueva vs. actualizar existente?

```
¿La herramienta reemplaza una existente?
  ├── NO → ¿Es un nuevo dominio?
  │       ├── SÍ → Crear skill nueva (ej. nelson-docling)
  │       └── NO → Agregar sección en skill existente
  └── SÍ → ¿Es un reemplazo total o coexistencia?
          ├── Total → Actualizar skill existente, documentar migración
          └── Coexistencia → Actualizar skill existente + crear skill específica nueva
```

## Pitfalls

1. **No probar sin permiso:** Si el usuario dice "no probemos nada", no levantar containers ni instalar paquetes. Solo documentar.
2. **Mantener legacy:** No eliminar la opción anterior sin consultar. Alguien puede depender de ella.
3. **Actualizar todas las skills relacionadas:** Un cambio en `nelson-document-processing` requiere revisar `nelson-rag-pipeline`, templates, y scripts de monitoreo.
4. **No commitear built-in de Hermes:** sync-to-repo.sh solo debe tener skills del equipo. Ver referencia `nelson-workflow-security/references/repo-sync-hygiene.md`.
5. **Preservar sub-skills:** Algunas skills tienen subdirectorios (agency-ai-engineer, etc.). El sync debe mantener la estructura.
