# Bisonte DB — Schema v1 (jun 2026)

PostgreSQL 16 en bisonte-db :5435. Creds: bisonte/bisonte2026, db=bisonte.
Script completo: `bisonte_schema_v1.sql` en la raíz del repo.

## Diagrama de relaciones

```
cat_sucursal        cat_estado_guia     cat_referente
     │                    │                   │
     └──────────────┬─────┘                   │
                    ▼                         │
                  guia  ◄── (nro = PK) ───────┘
                    │
          ┌─────────┼──────────┬──────────────┐
          ▼         ▼          ▼              ▼
  contado_anotacion  cdo_guia  pte_fact_guia  (futuros)
       │                │           │
       ▼                └─────┬─────┘
  contado_run              cdo_run

Vista: v_guia_cruce — JOIN de guia + contado_anotacion + cdo_guia + pte_fact_guia
```

## Tablas

### cat_sucursal
| campo | tipo | notas |
|---|---|---|
| codigo | TEXT PK | CC, BA, JU, RO, SA |
| nombre | TEXT | Casa Central (Tucumán), etc. |
| tipo | TEXT | propia / agencia |
| activa | BOOLEAN | default TRUE |

### cat_estado_guia
| codigo | descripcion | proceso |
|---|---|---|
| ED | Entregada pendiente de cobro | contado |
| DT | Despachada en tránsito | transito |
| TT | En tránsito | transito |
| RL | Recibida en depósito local | deposito |
| RT | Retornada | devolucion |
| DO | Devuelta al origen | devolucion |
| DI | Documentación incompleta | problema |
| OB | Observada | problema |
| NR | No retirada | problema |

### cat_referente
| codigo | nombre | tipo |
|---|---|---|
| BA | Buenos Aires | sucursal |
| CC | Casa Central | sucursal |
| JU | Jujuy | sucursal |
| RO | Rosario | sucursal |
| SA | Salta | sucursal |
| HM / HMS | Héctor M. | comercial |
| MRA | Comercial MRA | comercial |
| FN | Federico Nacif | comercial |
| NDS / NDE | Sin asignar | sin_asignar |
| POSVENTA | Área Posventa | interno |

### guia (eje central)
Universo completo de guías de Transoft. PK = `nro`.

Campos: nro, guiafec, razsocc, clase, fechaedit (TIMESTAMPTZ), sucori, sucdest,
importe, saldo, succobro, tiporec, sucursal, nrogen_a, estado_actual,
primera_vez_visto, ultima_vez_visto, fuente ('transoft' default).

Índices: estado_actual, succobro, sucdest, fechaedit.

### contado_run
Auditoría de cada ejecución del merge INICIAL+SISTEMA=FINAL.
Campos: id SERIAL PK, fecha_run, usuario, total_inicial, total_sistema, total_final,
nuevos, eliminados, existentes, estado_cambio, archivo_inicial, archivo_sistema.

### contado_anotacion
Campos manuales de Edith sobre cada guía. UNIQUE(nro) → una anotación por guía.
Campos: id, nro FK→guia, justificacion, referente, estado_gestion, observacion,
dias_atraso, updated_at, updated_by, run_id FK→contado_run.

### cdo_run
Auditoría de cada ejecución CDO/PTE.
Campos: id, fecha_run, usuario, total_cdo, total_pte_fact, diff_cdo, diff_pte, archivo_combinado.

### cdo_guia
Comparación sistema vs trabajado para CDO. UNIQUE(nro).
Campos: importe_sistema, importe_trabajado, diff_importe, diff_saldo, tiene_diferencia,
run_id FK→cdo_run, updated_at, updated_by.

### pte_fact_guia
Ídem para PTE de Facturación. Misma estructura que cdo_guia.

## Vista v_guia_cruce

```sql
SELECT g.nro, g.razsocc, g.importe, g.saldo, g.succobro, g.estado_actual,
       ca.referente AS contado_referente, ca.estado_gestion AS contado_estado,
       ca.observacion AS contado_obs, ca.dias_atraso AS contado_dias,
       cdo.importe_sistema AS cdo_importe_sis, cdo.importe_trabajado AS cdo_importe_trab,
       cdo.diff_importe AS cdo_diff, cdo.tiene_diferencia AS cdo_tiene_diff,
       pte.importe_sistema AS pte_importe_sis, pte.importe_trabajado AS pte_importe_trab,
       pte.diff_importe AS pte_diff, pte.tiene_diferencia AS pte_tiene_diff
FROM guia g
LEFT JOIN contado_anotacion ca ON ca.nro = g.nro
LEFT JOIN cdo_guia cdo         ON cdo.nro = g.nro
LEFT JOIN pte_fact_guia pte    ON pte.nro = g.nro;
```

Ejemplo de consulta cruzada:
```sql
-- Guías que tienen problema en CONTADO y también diferencia en CDO
SELECT nro, razsocc, contado_obs, cdo_diff
FROM v_guia_cruce
WHERE contado_obs LIKE '%VER DIF%' AND cdo_tiene_diff = true;
```

## Migración desde contado_guias (legacy)

La tabla `contado_guias` sigue existiendo para compatibilidad. El endpoint `/contado/save`
hace UPSERT en las 3 tablas simultáneamente: guia + contado_anotacion + contado_guias.

Migración inicial ejecutada jun 2026: 374 filas migradas.

## Levantar las BDs

```bash
cd /home/server/proyectos/excel-merger-poc
docker compose -f docker-compose.db.yml up -d
docker exec bisonte-db pg_isready -U bisonte -d bisonte
```

## PITFALL — heredoc bash no llega a docker exec

`docker exec bisonte-db psql -U bisonte -d bisonte << 'SQL' ... SQL` no funciona —
el heredoc lo interpreta la shell local, no se pasa al container. El output es vacío.

Fix correcto: escribir el SQL a un archivo temporal, copiarlo al container y ejecutar con -f:
```bash
cat > /tmp/mi_script.sql << 'EOF'
-- SQL aquí
EOF
docker cp /tmp/mi_script.sql bisonte-db:/tmp/mi_script.sql
docker exec bisonte-db psql -U bisonte -d bisonte -f /tmp/mi_script.sql
```

## Convención para nuevos procesos

Cada proceso nuevo que se agregue debe tener:
1. Una tabla `<proceso>_run` — auditoría de cada ejecución
2. Una tabla `<proceso>_<entidad>` con FK → guia(nro) — datos del proceso
3. Columnas: updated_at TIMESTAMPTZ, updated_by TEXT en todas las tablas editables
4. La vista `v_guia_cruce` se actualiza con LEFT JOIN al nuevo proceso
5. El endpoint de save hace UPSERT atómico (todo en una transacción)
