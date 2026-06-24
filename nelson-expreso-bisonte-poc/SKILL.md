---
name: nelson-expreso-bisonte-poc
description: Levantar, verificar y mantener la PoC Expreso Bisonte en srv-ai. Backend FastAPI :9000, SPA proxy :9090, Next.js frontend :3000, túnel Cloudflare. Flujo Ejecutar CDO/PTE → Auditoría. Repo en GitHub aliagenttucuman-byte/expreso-bisonte-excel-poc.
category: nelson
---

# Expreso Bisonte PoC — Levantar y mantener

ESTADO VERIFICADO: 2026-06-17 — 376 guías activas, saldo pendiente $80.638.011,97.

> PITFALL WebSocket con CF: `references/websocket-cloudflare-fix.md` — usar `window.location.host` no `:9000` hardcodeado. Módulo 1 entregado y cotizado en $7.200 one-time + $300/mes suscripción.

## Estado del deploy (verificado 2026-06-17)

| Servicio | Puerto | Estado |
|---|---|---|
| Backend FastAPI | :9000 | ✅ sobrevive entre sesiones |
| SPA Proxy | :9090 | ✅ sobrevive entre sesiones |
| PostgreSQL | :5435 | ✅ sobrevive entre sesiones |
| Cloudflare Tunnel | — | levantar bajo demanda |

## Levantar túnel Cloudflare para demo remota

```bash
cloudflared tunnel --url http://localhost:9090 --no-autoupdate 2>&1 | tee /tmp/cf_bisonte.log
# En otra terminal, después de ~10s:
grep trycloudflare.com /tmp/cf_bisonte.log
```

Lanzar con `terminal(background=true)` y `watch_patterns=["trycloudflare.com"]`.
La URL aparece en `/tmp/cf_bisonte.log` cuando el proceso arranca.

**PITFALL DNS en ai-server:** Tailscale intercepta DNS — el server no resuelve dominios externos.
Para verificar el túnel desde el propio server:
```bash
IP=$(dig @8.8.8.8 <subdomain>.trycloudflare.com +short | head -1)
curl --resolve "<subdomain>.trycloudflare.com:443:$IP" https://<subdomain>.trycloudflare.com/
# HTTP 200 = túnel OK. Desde la PC del cliente funciona normal sin ese workaround.
```

> Esquema completo de BD y reglas de negocio: `references/bisonte-db-schema.md`

## Convención de colores en tabla (pitfall frecuente)

**NUNCA pintar filas completas.** Solo colorear la celda/columna específica afectada.
- La única columna con coloración automática es DIAS_ATRASO.
- Alertas de estado → marcar la celda de ESTADO de esa guía, no la fila entera.
- Si se propone row-highlight, Nelson lo va a rechazar.

ESTADO VERIFICADO ANTERIOR: 2026-06-08 funcionando end-to-end. Demo objetivo: mostrarle a la gerenta que el cruce CDO↔PF que ella hace a mano se puede ver lado a lado en la app (sistema vs trabajada).

## Script unificado ForestAI + Expreso Bisonte (demo con Gino)

Para reuniones donde se muestran ambas demos juntas:
```bash
bash /home/server/.hermes/scripts/demo_gino_up.sh
```
Levanta ForestAI (Docker Compose) + Bisonte (procesos directos) + regenera túnel CF si murió.
Entrega URLs listas en ~15 segundos.

## Servicios corriendo en /home/server (srv-ai) sin Docker

| Servicio | Puerto | Comando |
|---|---|---|
| Backend FastAPI | `localhost:9000` | `uvicorn app.main:app --host 0.0.0.0 --port 9000` desde `/home/server/proyectos/excel-merger-poc/backend` |
| Frontend Next.js | `localhost:3000` | `npm run start` desde `/home/server/proyectos/excel-merger-poc/frontend` |
| Proxy SPA | `localhost:9090` | `python3 /home/server/proyectos/excel-merger-poc/spa_proxy.py` (sirve dist + /api/* → :9000) |
| Túnel Cloudflare | **URL cambia en cada reinicio** — leer de `/tmp/cf_expreso.log` | `cloudflared tunnel --url http://localhost:9090 > /tmp/cf_expreso.log 2>&1 &` |

`UPLOAD_DIR` del backend: `/tmp/excel-merger` (config en `app/core/config.py:6`).

## Estado limpio que tiene que quedar

`/tmp/excel-merger/` debe contener **UN SOLO archivo**:

```
expreso_bisonte_combinado.xlsx
  ├── "CDO Sistema"          (409 filas, sistema real)
  ├── "PTE de Fact Sistema"  (1413 filas, sistema real)
  ├── "CDO TRABAJADA"        (409 filas, validación gerenta — Pablo Ruiz)
  └── "PF TRABAJADA"         (1507 filas, validación gerenta — Pablo Ruiz)
```

Nombres de sheets **EXACTOS** (case-sensitive para el lookup interno).

## Flujo end-to-end (NO TOCAR, ya anduvo)

1. Frontend muestra el combinado con 4 sheets
2. Click **"Ejecutar CDO/PTE"** → `POST /api/v1/excel/split-system-sheets/{file_id}` → separa CDO y PF en 2 archivos
3. Frontend → `POST /api/v1/excel/pipeline/static` con cdo_file_id + pf_file_id → motor busca baseline en `/tmp/excel-merger/*.xlsx` (encuentra el combinado con sheets "cdo trabajada" + "pf trabajada" ≥380 + ≥1400 filas) → genera `cdo_trabajada_{uuid}.xlsx` + `pf_trabajada_{uuid}.xlsx`
4. Frontend → `POST /api/v1/excel/pipeline/compare-manual` con manual_file_id (combinado) + cdo_output_file_id + pf_output_file_id → compara fila por fila

## Tailscale vs Cloudflare

Cuando Nelson diga "levantame bisonte para tailscale" o "quiero entrar por tailscale":
- URL directa: http://100.110.8.13:9090
- NO levantar túnel Cloudflare (es para acceso externo, no interno)
- Verificar solo que :9000 y :9090 estén arriba + rearmar combinado

Cuando pida acceso externo (demo con cliente, Pablo, Gino fuera de la red): SÍ levantar cloudflared y dar la URL nueva.

## IMPORTANTE: comportamiento ante "levantame Expreso Bisonte"

Nelson pide acceso por Tailscale — la URL siempre es http://100.110.8.13:9090 (no túnel Cloudflare).

- **TODO DE UNA SOLA VEZ** — sin preguntar, sin pasos intermedios, sin confirmaciones:
  1. Verificar puertos con `ss -tlnp | grep -E ':(3000|9000|9090)'`
  2. Levantar lo que falte: backend :9000, proxy SPA :9090
  3. Rearmar combinado (`rearmar_combinado.py`) — SIEMPRE, no verificar si ya hay archivos
  4. Subir combinado al backend (`/api/v1/excel/upload`)
  5. Dar la URL de Tailscale lista para usar: http://100.110.8.13:9090
- **NUNCA hacer `pip install` ni buscar venvs** — el backend NO tiene venv. `python3 -m uvicorn` directo del sistema.
- **NO reinventar** el proyecto — ya existe en `/home/server/proyectos/excel-merger-poc`
- **NO preguntar nada** — ejecutar todo y reportar resultado final con la URL
- El objetivo es dar la URL en menos de 2 minutos desde que Nelson lo pide

## IMPORTANTE — el proyecto YA EXISTE

Cuando Nelson diga "levantá Expreso Bisonte" o "dame la URL", NO arrancar a instalar
dependencias, NO buscar venvs, NO hacer pip install. El proyecto está en
`/home/server/proyectos/excel-merger-poc/`. Solo verificar procesos y levantar lo que falte.

## PITFALL — rearmar_combinado.py ya no existe + colisión openpyxl

Verificado jun 2026: `rearmar_combinado.py` fue removido del repo. Ir directo al fallback.

Fuente: `/home/server/brainstorming/2026-06-03-expreso-bisonte-diccionario-datos-pablo/entregables-xlsx/CONTADO_PABLO_RUIZ_origen.xlsx`

NO renombrar sheets in-place con `wb[sheet].title = ...` y borrar las que sobran — colisiona con sheets ya presentes y deja solo 2 de 4. Patrón correcto (Workbook nuevo + copy por filas) y upload al backend en `references/rearmar-combinado-fallback.md`.

El backend se levanta con:
```bash
cd /home/server/proyectos/excel-merger-poc/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 9000 > /tmp/excel_backend.log 2>&1 &
```
El proxy SPA:
```bash
python3 /home/server/proyectos/excel-merger-poc/spa_proxy.py > /tmp/expreso_proxy.log 2>&1 &
```
El túnel (URL nueva cada vez que muere):
```bash
cloudflared tunnel --url http://localhost:9090 > /tmp/cf_expreso.log 2>&1 &
sleep 8 && grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cf_expreso.log | tail -1
```

El frontend Next.js en `:3000` **sobrevive reinicios** (pid 3350 estable, verificado 2026-06-09). Verificar antes de intentar levantarlo — casi nunca hace falta.

⚠️ El spa_proxy en :9090 y el backend en :9000 SÍ caen con cada reinicio del server. Siempre verificar con `ss -tlnp | grep -E ':(3000|9000|9090)'` antes de dar la URL.

El spa_proxy y backend NO sobreviven reinicios — siempre hay que levantarlos.

## Script unificado — Demo Gino (ForestAI + Expreso Bisonte)

Cuando Nelson diga "levantá las demos para Gino" o similar:

```bash
bash /home/server/.hermes/scripts/demo_gino_up.sh
```

Levanta ForestAI (Docker Compose) + Expreso Bisonte (procesos directos) y entrega ambas URLs en un solo comando. Incluye túnel Cloudflare nuevo si el anterior cayó.

## Procedimiento de levantamiento

Cuando Nelson pida "levantar Expreso Bisonte": ejecutar TODO de una sola vez sin diagnósticos previos ni confirmaciones intermedias.

### Secuencia completa (siempre ejecutar todo, sin preguntar, sin pasos intermedios)

**REGLA EXPLÍCITA DE NELSON (2026-06-13):** al decir "levantame bisonte" ejecutar TODO de una sola vez:
backend + proxy + rearmar combinado + subir sheets. Solo dar la URL al final. Sin preguntas intermedias.

**IMPORTANTE (2026-06-15):** usar `terminal(background=True)` para levantar uvicorn. El `&` inline en terminal falla con error. Luego verificar con curl en llamada separada.

**VARIANTE TAILSCALE (2026-06-15):** "levantame bisonte para tailscale" o "quiero entrar por tailscale" → misma secuencia, URL = http://100.110.8.13:9090. NO levantar Cloudflare.



```bash
# 1. Backend
cd /home/server/proyectos/excel-merger-poc/backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 9000 > /tmp/excel_backend.log 2>&1 &
# 2. Proxy SPA
python3 /home/server/proyectos/excel-merger-poc/spa_proxy.py > /tmp/expreso_proxy.log 2>&1 &
# Esperar 4s
sleep 4
# 3. Rearmar combinado y subirlo
python3 /home/server/.hermes/skills/nelson-expreso-bisonte-poc/scripts/rearmar_combinado.py
curl -s -X POST http://localhost:9000/api/v1/excel/upload -F file=@/tmp/expreso_ref/expreso_bisonte_combinado.xlsx
```

El paso 3 (rearmar + subir combinado) es OBLIGATORIO siempre — no verificar si ya hay archivos en /tmp/excel-merger, no saltear. Puede haber archivos viejos de sesiones previas pero sin el combinado con las 4 sheets que el backend necesita para el flujo CDO/PTE. Rearmar siempre.

Reportar solo: qué quedó levantado + URL de Tailscale http://100.110.8.13:9090

### Si el túnel Cloudflare murió (acceso externo)

⚠️ **La URL del túnel cambia cada vez que cloudflared se reinicia.** No hardcodear la URL anterior.

⚠️ **cloudflared escribe a stderr. Sin `tee` la URL nunca aparece en el log de Hermes.**
Comando correcto — SIEMPRE con `tee`:
```bash
cloudflared tunnel --url http://localhost:9090 --no-autoupdate 2>&1 | tee /tmp/cf_bisonte.log
```
Leer la URL después de ~5 segundos:
```bash
grep trycloudflare.com /tmp/cf_bisonte.log
```
Si se lanza con `background=true` sin `tee`, el log queda vacío → matar y relanzar con `tee`.

```bash
cloudflared tunnel --url http://localhost:9090 > /tmp/cf_expreso.log 2>&1 &
sleep 8
# Leer la URL nueva del log:
grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cf_expreso.log | tail -1
```

Pasarle la URL nueva a Nelson directamente.

## Repo GitHub

https://github.com/aliagenttucuman-byte/expreso-bisonte-excel-poc

Lo que NO va al repo: `uploads_temp/` con Excels reales (datos del cliente).
Para commitear: `git add spa_proxy.py samples/ .gitignore && git commit -m "..." && git push origin main`

## PITFALL — spa_proxy.py cae con cada reinicio del server

El spa_proxy no es un servicio systemd — muere si el server se reinicia o el proceso se mata.
Síntoma: `http://100.110.8.13:9090/` no responde.

Verificar y levantar:
```bash
ss -tlnp | grep 9090 || python3 /home/server/proyectos/excel-merger-poc/spa_proxy.py > /tmp/expreso_proxy.log 2>&1 &
```

## PITFALL — Archivo combinado: fuente correcta en junio 2026

El path original en `rearmar_combinado.py` apuntaba a:
`/home/server/.hermes/document_cache/doc_59585daaffc8_CONTADO_PABLO_RUIZ.xlsx`
que ya NO existe. La fuente correcta con las 4 sheets es:
`/home/server/brainstorming/2026-06-03-expreso-bisonte-diccionario-datos-pablo/entregables-xlsx/CONTADO_PABLO_RUIZ_origen.xlsx`

Sheets disponibles en esa fuente: `CDO SISTEMA`, `CDO TRABAJADA`, `PTE DE FACT SISTEMA`, `PF TRABAJADA`.
Actualizar el script `rearmar_combinado.py` si el path vuelve a romper.

**Script seguro** (incluye fix de openpyxl rename-in-place): `scripts/rearmar_combinado_safe.py`
Ejecutar: `python3 scripts/rearmar_combinado_safe.py --upload`
NO hacer rename in-place + del — openpyxl descarta silenciosamente una sheet si el nuevo nombre colisiona con otra existente, dejando 2 sheets en vez de 4 sin error.

## PITFALL — pg_isready da falso negativo con Docker

`pg_isready` busca el postgres del sistema — si la DB corre en Docker, reporta DOWN
aunque el contenedor esté perfectamente healthy. Verificar siempre con:

```bash
docker exec bisonte-db psql -U bisonte -d bisonte -c "SELECT count(*) FROM guia;"
```

La tabla es `guia` (sin 's') — `guias` no existe.

## PITFALL — Backend no se mata con pkill

`pkill -f 'uvicorn app.main'` a veces no funciona. Usar siempre:
```bash
fuser -k 9000/tcp
```
El proceso viejo queda en memoria con el módulo Python cacheado — si no se mata correctamente, el nuevo proceso no arranca (EADDRINUSE) o el viejo sigue sirviendo código viejo.

## Bisonte Contado — DIAS_ATRASO

Campo fuente: `fechaedit` (datetime, en CDO Sistema / SISTEMA sheet del IA_CONTADO).
Cálculo: `hoy(AR, UTC-3) - fechaedit.date()`.
NO usar `guiafec` (es string `'DD/MM/YYYY'`, fecha de emisión, no de gestión).
Bug histórico fixeado: `extra_cols` estaba indefinido → merge reventaba silenciosamente.

## Bisonte Frontend — localStorage

- `contado_last_run`: timestamp del último procesamiento (string, ej: `'15/6/2026, 03:00'`)
- `contado_last_table`: JSON de `{ columns, rows }` del último FINAL generado
- Botón "👁 Ver último FINAL" solo aparece si `contado_last_table` existe
- Al apretar: setea `contadoTableData` + scrollIntoView al `contadoTableRef`

## PITFALL — Redis URL corrupta en .env

### Síntoma
Celery no conecta. Logs muestran `gmail.com:6379` como host:
```
consumer: Cannot connect to redis://redis:***@gmail.com:6379//
```
Causa: la URL tenía una password con `@` (ej: email como password). Celery interpreta todo antes del último `@` como `user:pass` y lo que sigue como host.

### Fix
```python
import re
with open('/home/server/proyectos/forestai-poc/.env', 'r') as f:
    content = f.read()
new_content = re.sub(r'REDIS_URL=.*\n', 'REDIS_URL=redis://redis:6379/0\n', content)
with open('/home/server/proyectos/forestai-poc/.env', 'w') as f:
    f.write(new_content)
```
Luego `docker compose up -d --force-recreate celery_worker backend` (restart NO toma el .env nuevo).

## BUG RESUELTO — ESTADO siempre desde SISTEMA (jun 2026)

El merger preservaba el ESTADO del INICIAL de Edith para registros EXISTENTES.
Pero el ESTADO lo pone Transoft — no Edith. Si una guía cambiaba de TT/RL a ED en Transoft,
el FINAL la seguía mostrando con el estado viejo y NO aparecía al filtrar por ED.

Fix aplicado en `contado_merger.py` (bloque EXISTENTES):
```python
# ESTADO siempre desde SISTEMA (lo pone Transoft, no Edith)
row_data["ESTADO"] = estado_sis
```
Esta línea va DESPUÉS del loop que copia MANUAL_COLS, sobreescribiendo el ESTADO que trajo del INICIAL.

Las columnas que SÍ preservamos de Edith (MANUAL_COLS):
- JUSTIFICACIÓN — la pone Edith
- REFERENTE — la pone Edith (si está vacía, se auto-sugiere desde succobro)
- OBSERVACIÓN — la pone Edith

El ESTADO es de Transoft → siempre desde SISTEMA.

## BUG RESUELTO — REFERENTE vacío en EXISTENTES se auto-sugiere desde succobro (jun 2026)

Guías EXISTENTES que en INICIAL tenían REFERENTE=#N/A (nunca asignado) NO recibían
el auto-sugerido desde succobro — esa lógica solo corría para NUEVOS.

Síntoma: ED + REFERENTE=CC daba 8 filas en la app vs 12 en el Excel de Edith.
Las 4 faltantes eran existentes con REFERENTE=#N/A en INICIAL que habían cambiado a ED.

Fix aplicado en el bloque EXISTENTES, después de copiar MANUAL_COLS y setear ESTADO:
```python
# REFERENTE: si viene vacío del INICIAL → auto-sugerir desde succobro
if not str(row_data.get("REFERENTE", "") or "").strip():
    succobro_ref = str(r_sis.get("succobro", "") or "").strip().upper()
    if succobro_ref:
        row_data["REFERENTE"] = succobro_ref
        stats["referente_auto"] = stats.get("referente_auto", 0) + 1
```

Regla general: REFERENTE vacío (sea registro NUEVO o EXISTENTE sin asignar) → auto-sugerir desde succobro.
Si Edith ya puso un REFERENTE, se preserva. Solo se sugiere cuando está vacío.

## IMPORTANT — reiniciar backend después de editar código Python

El backend corre sin `--reload`. Cualquier cambio en `app/services/contado_merger.py` o endpoints requiere reinicio manual:

```bash
pkill -f 'uvicorn app.main:app'
sleep 1
cd /home/server/proyectos/excel-merger-poc/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 9000 > /tmp/excel_backend.log 2>&1 &
sleep 3
curl -s http://localhost:9000/health
```

Verificar que devuelva `{"status":"ok",...}` antes de dar la URL a Nelson.

## Colaboración WebSocket — Pitfalls críticos (jun 2026)

Ver `references/bisonte-websocket-collab.md` para el detalle completo. Resumen de bugs resueltos:

### cellLocks como useState → blur espurio → lock se suelta solo
`useState(Map)` → re-render → input pierde foco → `onBlur` → `sendUpdate` → lock suelto.
Fix: `useRef` para el Map + contador de versión `cellLocksVer` para re-render mínimo.

### onFocus de celda bloqueada emite editing
La pestaña 2 recibe el lock → re-render → onFocus se dispara igual → manda su propio `editing`.
Fix: `handleCellFocus(row, col, isLockedByOther)` — retornar inmediatamente si `isLockedByOther`.

### Lock bloquea al propio dueño
`readOnly={!!lock}` incluye al dueño. Fix: `const lockedByOther = !!lock && lock.user !== resolvedUser`.
También en el hook: `if (msg.user !== user)` antes de guardar en cellLocksRef.

### sendUpdate/sendLeave se disparan aunque la celda ya no sea tuya
Fix: `myLockRef` trackea la celda activa de esta pestaña. Verificar antes de soltar:
```typescript
if (!mine || mine.nro !== nro || mine.col !== col) return
```

### ID de pestaña: usar sessionStorage, no localStorage
`localStorage` se comparte entre pestañas → todos tendrían el mismo ID.
`sessionStorage` es exclusivo por pestaña → cada una genera su propio `tab_XXXXX`.

## PROHIBIDO

- Borrar `/tmp/excel-merger/expreso_bisonte_combinado.xlsx` — es el ÚNICO estado persistente
- Subir las 4 sheets como archivos individuales (rompe el flujo del frontend)
- Crear procedures (el front no los usa para "Ejecutar CDO/PTE")
- Llamar `/pipeline/static` o `/pipeline/compare-manual` desde curl antes que el usuario lo haga desde el frontend (los file_ids de salida se pierden del `_upload_registry`)
- Inventar tests, joins, plan/suggest — el flujo YA funciona como está
- Tocar el código del backend sin pedir permiso

## Referencias técnicas

- `references/casos-de-uso-contado.md` — catálogo completo de 13 CU del módulo cobranzas contado (relevados jun 2026): reglas de merge, columnas FINAL, endpoints, DB schema resumido
- `references/bisonte-contado-merger-fixes-jun2026.md` — fixes críticos: prefijos R., ESTADO desde SISTEMA, REFERENTE auto-sugerido en existentes, colores por columna, diagnóstico de diferencias de conteo
- `references/bisonte-contado-columnas-tecnicas.md` — columnas del IA_CONTADO, cálculo DIAS_ATRASO, tolerancias, estados, y pitfalls del merger
- `references/bisonte-ia-contado-edith-reglas.md` — análisis completo del video de Edith
- `references/bisonte-ia-contado-edith-reglas.md` — análisis completo del video de Edith
- `references/bisonte-empresa-perfil.md` — perfil de Expreso Bisonte
- `references/bisonte-propuesta-roi-patron.md` — estructura de propuesta comercial
- `references/bisonte-db-schema-v1.md` — schema PostgreSQL v1: tablas, relaciones, vista cruce, convención para nuevos procesos
- `references/bisonte-websocket-collab.md` — colaboración en tiempo real WebSocket: arquitectura, todos los pitfalls de lock/blur/doble-accept diagnosticados en jun 2026
- `references/bisonte-websocket-colaboracion.md` — arquitectura WS en tiempo real, pitfalls de self-lock y doble-lock, protocolo de mensajes, diagnóstico

## Repositorio GitHub

https://github.com/aliagenttucuman-byte/expreso-bisonte-excel-poc

Rama: `main`. Commits actualizados con `spa_proxy.py` + demo sample + gitignore.
NO va al repo: `uploads_temp/` con Excels reales del cliente.

## PITFALL — spa_proxy timeout

El `spa_proxy.py` tiene `timeout=600s` por defecto. Si el backend tarda más de 10 min, el proxy
corta y el frontend recibe texto plano `"timed out"` en lugar de JSON, crasheando con:
```
Unexpected token 'i', "timed out" is not valid JSON
```

Fix: subir el timeout en `spa_proxy.py` línea ~37:
```python
with urllib.request.urlopen(req, timeout=3600) as resp:
```
Luego reiniciar el proxy (`pkill -f spa_proxy.py` + relanzar).

## Watchdog ForestAI (referencia cruzada)

El cron `forestai-deteccion-watchdog` (cada 2 min) monitorea tiles activos en el backend.
Si la detección supera 5 min sin terminar → alerta WhatsApp automático.
Script: `/home/server/.hermes/scripts/forestai_watchdog.sh`

## PITFALL — Columnas extra ESTADO_SISTEMA y ORIGEN en el FINAL

El merger incluía dos columnas extra (`ESTADO_SISTEMA`, `ORIGEN`) al final del Excel generado.
Nelson pidió sacarlas — el FINAL solo tiene las `FINAL_COLS` operativas.

Fix aplicado en `contado_merger.py`:
- Eliminar el bloque que escribe el encabezado de `extra_cols`
- Eliminar las líneas que escriben `__estado_sis__` y `__origen__` en cada fila
- Reemplazar ambos bloques con comentario `# (sin columnas extra)`

Si vuelven a aparecer columnas extra, buscar en `contado_merger.py`:
```python
extra_cols = ["ESTADO_SISTEMA", "ORIGEN"]
```
y eliminar ese bloque + el bloque `write_row` que las escribe.

## PITFALL — Columnas con tilde en headers Excel rompen `.includes()` en JavaScript

El backend devuelve la columna como `'OBSERVACIÓN'` (con tilde). En el frontend,
`'OBSERVACIÓN'.toLowerCase()` puede producir `'observaciÓn'` (Ó no baja a minúscula en algunos engines V8).
Resultado: `colLower[i].includes('observ')` devuelve `true` hasta la `'o'` de `'observ'` pero
el `COL_OBSERV` puede resolverse a `''` si el normalize falla — dejando el filtro "sin observación" roto.

**Fix — normalizar antes de buscar (quita tildes vía NFD):**
```typescript
const COL_OBSERV = columns.find((_, i) => {
  const c = colLower[i].normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  return c.includes('observ')
}) ?? ''
```
Aplicar el mismo patrón a cualquier columna con nombre que tenga tilde (JUSTIFICACIÓN, etc.).
Versión inline para usos únicos:
```typescript
columns.find(c => c.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().includes('observ')) ?? ''
```

## PITFALL — Filtro días de atraso no filtra filas sin fecha

Síntoma: el usuario pone un mínimo de días (ej: 7) y el filtro parece no ejecutarse — aparecen filas sin datos de días igual.

Causa: `DIAS_ATRASO` viene como `""` cuando la guía no tiene `guiafec`. El código original hacía:
```js
const dias = parseFloat(String(row[COL_DIAS] ?? '0'))
if (dias < parseFloat(filterDiasMin)) return false
```
`parseFloat("") = NaN`, y `NaN < 7 = false` → la fila pasa el filtro aunque no debería.

Fix correcto en `ContadoTable.tsx`:
```typescript
if (filterDiasMin !== '') {
  const minVal = parseFloat(filterDiasMin)
  const raw = row[COL_DIAS]
  const dias = (raw !== '' && raw !== null && raw !== undefined) ? parseFloat(String(raw)) : NaN
  // Si no tiene dato de días, o es menor al mínimo → filtrar
  if (isNaN(dias) || dias < minVal) return false
}
```
Regla: filas sin fecha de entrega (`DIAS_ATRASO = ""`) se EXCLUYEN cuando hay filtro por días activo.

## PITFALL — Columnas debug en el FINAL Excel (ESTADO_SISTEMA, ORIGEN)

El merger `contado_merger.py` tenía columnas extra de diagnóstico (`ESTADO_SISTEMA`, `ORIGEN`) que aparecían en el Excel descargado por Edith. No son columnas operativas — son residuos de desarrollo.

Las columnas se generan en dos lugares de `write_row()`:
1. El bloque `extra_cols = ["ESTADO_SISTEMA", "ORIGEN"]` en el encabezado (línea ~220)
2. Las dos líneas `ws_out.cell(row_out, len(FINAL_COLS) + 1, ...)` dentro de `write_row()`

Ambos lugares deben eliminarse juntos. Si se saca uno solo, el Excel queda con encabezado sin datos o datos sin encabezado.

Fix aplicado: reemplazar ambos bloques por comentarios `# (sin columnas extra)`.

## PITFALL — Filtro días de atraso con NaN (ContadoTable.tsx)

`DIAS_ATRASO` puede ser `""` para guías sin fecha de entrega. El filtro original hacía:
```js
const dias = parseFloat(String(row[COL_DIAS] ?? '0'))
if (dias < parseFloat(filterDiasMin)) return false
```
`parseFloat("") = NaN` → `NaN < 7` es `false` → las filas sin fecha **pasaban el filtro** aunque no debían.

Fix correcto — excluir filas sin dato:
```js
const minVal = parseFloat(filterDiasMin)
const raw = row[COL_DIAS]
const dias = (raw !== '' && raw !== null && raw !== undefined) ? parseFloat(String(raw)) : NaN
if (isNaN(dias) || dias < minVal) return false
```
Así las guías sin fecha de entrega NO aparecen cuando Edith filtra por días mínimos.

## PATRÓN — Timestamp de último procesamiento con localStorage

Para que Edith sepa cuándo se procesó por última vez sin depender del servidor:

```tsx
// Estado inicializado desde localStorage (sobrevive recargas)
const [contadoLastRun, setContadoLastRun] = useState<string>(
  () => localStorage.getItem('contado_last_run') || ''
)

// Al completar el merge exitosamente:
const ts = new Date().toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' })
localStorage.setItem('contado_last_run', ts)
setContadoLastRun(ts)

// Badge verde en el JSX (mostrar solo si existe):
{contadoLastRun && (
  <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
    background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '8px',
    padding: '0.35rem 0.75rem', fontSize: '0.82rem', color: '#15803d', marginBottom: '0.75rem' }}>
    ✅ Último procesamiento: <strong>{contadoLastRun}</strong>
  </div>
)}
```

Ventajas: persiste entre sesiones del browser, no requiere backend, Edith lo ve al abrir la app sin necesidad de re-procesar.

## PITFALL — columnas extra (ESTADO_SISTEMA, ORIGEN) en el FINAL

El merger `contado_merger.py` tenía columnas extra `ESTADO_SISTEMA` y `ORIGEN` que aparecían en el Excel descargado. Nelson no las quiere — solo las columnas del negocio. Si vuelven a aparecer, eliminarlas de `extra_cols` en el merger y del `write_row` helper.

## PITFALL — filtro DIAS_ATRASO con NaN pasa filas sin dato

En el frontend, `parseFloat("") = NaN` y `NaN < 7 = false` — las filas sin fecha de entrega pasan el filtro de días mínimos aunque no deberían.

Fix correcto en `ContadoTable.tsx`:
```typescript
if (filterDiasMin !== '') {
  const minVal = parseFloat(filterDiasMin)
  const raw = row[COL_DIAS]
  const dias = (raw !== '' && raw !== null && raw !== undefined) ? parseFloat(String(raw)) : NaN
  if (isNaN(dias) || dias < minVal) return false
}
```
Filas sin dato de días se excluyen cuando hay filtro activo.

## Feature: persistencia del último FINAL (localStorage)

Patron implementado jun 2026 para que Edith pueda ver el último FINAL sin re-subir archivos:

1. `loadContadoTable()` guarda la tabla en `localStorage.setItem('contado_last_table', JSON.stringify(tableData))`
2. Al generar FINAL se guarda timestamp: `localStorage.setItem('contado_last_run', ts)`
3. Al montar el componente se restaura: `const saved = localStorage.getItem('contado_last_table')` → `setContadoTableData(JSON.parse(saved))`
4. UI: badge verde "✅ Último procesamiento: DD/MM/AAAA HH:MM" + botón negro "👁 Ver último FINAL" que llama al mismo restore

El botón aparece solo si `contadoLastRun` tiene valor (es decir, hubo al menos un procesamiento en ese browser).

## PITFALL — ESTADO en EXISTENTES debe venir de SISTEMA, no de INICIAL

El merger preservaba las MANUAL_COLS del INICIAL — incluyendo ESTADO. Pero ESTADO lo pone Transoft, no Edith. Si una guía cambia de estado entre el INICIAL y el SISTEMA (ej: DT→ED, RL→ED), el merger la ponía en el FINAL con el estado viejo → Edith filtraba por ED y no la veía.

Fix aplicado en `contado_merger.py` (jun 2026): después de copiar MANUAL_COLS, sobreescribir siempre ESTADO con el valor del SISTEMA:

```python
# Anotaciones manuales de INICIAL (preservar)
for col in MANUAL_COLS:
    v = r_ini.get(col, "")
    if str(v) in ("#N/A", "#NA", "nan", "None"):
        v = ""
    row_data[col] = v

# ESTADO siempre desde SISTEMA (lo pone Transoft, no Edith)
row_data["ESTADO"] = estado_sis
```

Regla: las únicas columnas que Edith "posee" son JUSTIFICACIÓN, REFERENTE y OBSERVACIÓN. ESTADO siempre es de Transoft.

### Diagnóstico de diferencias INICIAL vs SISTEMA vs FINAL

Cuando el conteo de ED no coincide entre Excel de Edith y la app, pasos en orden:

**1. Confirmar el filtro exacto** — REFERENTE, succobro y sucdest son distintos. En la imagen
el dropdown "CC" puede ser cualquiera de los tres — verificar qué columna está activa.

**2. Cruzar los 3 archivos** con script: `scripts/diagnostico_merger_contado.py`
Pide: INICIAL.xlsx, SISTEMA.xlsx, FINAL_edith.xlsx (opcional).
Reporta: total/ED por sheet, existentes/nuevos/eliminados, cambios de estado, duplicados.

**3. Causas comunes verificadas (jun 2026):**

| Causa | Síntoma | Fix |
|-------|---------|-----|
| ESTADO preservado del INICIAL | guías que cambiaron a ED no aparecen | ESTADO siempre de SISTEMA ✅ FIXEADO |
| REFERENTE vacío en existentes | filas ED sin REFERENTE asignado | auto-sugerir desde succobro si vacío ✅ FIXEADO |
| Duplicados en SISTEMA | merger descarta la segunda ocurrencia | verificar con Counter — si ambas son ED no hay pérdida |
| INICIAL incorrecto | base distinta a la que usa Edith | verificar que sea el FINAL de la sesión anterior |

**Script inline rápido:**
```python
# Ver guías que cambiaron estado entre INICIAL y SISTEMA
for nro, r_sis in dict_sis.items():
    estado_sis = str(r_sis.get('estado') or '').strip().upper()
    r_ini = dict_ini.get(nro)
    if not r_ini: continue
    estado_ini = str(r_ini.get('ESTADO') or r_ini.get('estado') or '').strip().upper()
    if estado_ini != estado_sis:
        print(f"nro={nro}  INICIAL={estado_ini}  SISTEMA={estado_sis}")
```

Script reutilizable: `scripts/diagnostico_merger_contado.py INICIAL.xlsx SISTEMA.xlsx [FINAL.xlsx]`

## PITFALL — Prefijos de nro válidos en _sheet_to_dicts

El merger original solo aceptaba nros con prefijo `A.` o `B.`. Transoft también genera guías con prefijo `R.` (ej: `R.0009.00107766`). Si no se incluye `R.` en la validación, esas guías se descartan silenciosamente.

Fix en `contado_merger.py` función `_sheet_to_dicts`:
```python
# Correcto — incluir R.
if nro and str(nro).strip()[:2] in ("A.", "B.", "R."):
```

El footer del informe de Transoft genera filas con prefijos `Fi`, `Fe`, `Pe`, `Or`, `In` (ej: "Filtros adicionales seleccionados", "Fecha...") — esos NO son guías y quedan correctamente excluidos.

## PITFALL — ESTADO en EXISTENTES debe venir siempre de SISTEMA

El merger copiaba el campo ESTADO del INICIAL (anotación de Edith). Pero ESTADO es dato de Transoft, no de Edith. Si una guía cambió de TT/RL/DT a ED entre el INICIAL y el SISTEMA, el merger la ponía en el FINAL con estado viejo → desaparecía del filtro ED.

Fix: después de copiar MANUAL_COLS, sobreescribir ESTADO con el valor de SISTEMA:
```python
# Anotaciones manuales de INICIAL (preservar)
for col in MANUAL_COLS:
    v = r_ini.get(col, "")
    if str(v) in ("#N/A", "#NA", "nan", "None"):
        v = ""
    row_data[col] = v

# ESTADO siempre desde SISTEMA (lo pone Transoft, no Edith)
row_data["ESTADO"] = estado_sis
```

Las columnas que SÍ son anotaciones de Edith (preservar del INICIAL): JUSTIFICACIÓN, REFERENTE, OBSERVACIÓN.
El ESTADO es de Transoft → siempre del SISTEMA.

## PITFALL — REFERENTE vacío en EXISTENTES no se auto-sugiere

El merger auto-sugería REFERENTE desde `succobro` solo para registros NUEVOS. Para EXISTENTES donde REFERENTE venía como `#N/A` (limpiado a vacío), no se sugería nada → la guía quedaba sin REFERENTE aunque succobro tuviera valor.

Fix: para EXISTENTES, si REFERENTE queda vacío después de copiar del INICIAL → auto-sugerir desde succobro (igual que los nuevos):
```python
# REFERENTE: si viene vacío del INICIAL → auto-sugerir desde succobro
if not str(row_data.get("REFERENTE", "") or "").strip():
    succobro_ref = str(r_sis.get("succobro", "") or "").strip().upper()
    if succobro_ref:
        row_data["REFERENTE"] = succobro_ref
        stats["referente_auto"] = stats.get("referente_auto", 0) + 1
```

## PITFALL — Filtro de REFERENTE ≠ filtro de succobro ≠ filtro de sucdest

En la app hay tres dropdowns distintos con valores parecidos:
- **REFERENTE** — columna manual de Edith (BA, CC, JU, etc.) → filtro operativo principal
- **Suc. cobro (succobro)** — columna de Transoft
- **Todas las sucdest** — sucursal de destino de Transoft

Cuando Nelson dice "filtro CC da 8 filas", preguntar cuál dropdown está activo — son tres columnas distintas con valores similares pero significados diferentes.

## Flujo IA CONTADO — Cobranzas Contado (estado jun 2026)

### Columnas del Excel Transoft (sheet SISTEMA / INICIAL)
CDO Sistema headers: `nro, guiafec, razsocc, clase, fechaedit, sucori, sucdest, importe, saldo, succobro, estado, tiporec, sucursal, nrogen_a`

- `guiafec` — string `'27/05/2026'` (fecha de emisión de la guía, formato %d/%m/%Y)
- `fechaedit` — datetime nativo de openpyxl `datetime(2026, 6, 11, 10:56)` (última edición en Transoft = fecha de entrega)

**DIAS_ATRASO se calcula desde `fechaedit`, NO desde `guiafec`.** Confirmado con Edith — es la columna que ella señala como "fecha de entrega" en el video.

### Filtros aplicados al SISTEMA antes del merge

### DECISIÓN jun 2026 (Nelson): el merger NO filtra por estado ED. Trae TODOS los estados del SISTEMA.
El foco operativo sigue siendo ED, pero Edith necesita ver el panorama completo.
El filtro de ED sigue disponible en el dropdown del frontend si lo necesita.

Solo se aplica deduplicación por `nro`:
```python
# Sin filtro de estado — traer todos los registros del SISTEMA
rows_sis: list[dict] = []
seen_nros: set[str] = set()
for r in rows_sis_raw:   # ← rows_sis_raw, NO rows_sis_ed
    if r["nro"] not in seen_nros:
        seen_nros.add(r["nro"])
        rows_sis.append(r)
```

**Pitfall:** si se revierte este cambio y se vuelve a filtrar por ED, verificar que la variable
se llame `rows_sis_ed` en el loop — no dejar referencia a `rows_sis_raw` o a una variable indefinida.

### REGLA — ESTADO pre-poblado en registros NUEVOS (jun 2026)

Los registros NUEVOS (que no estaban en INICIAL) llegan con los campos manuales vacíos
para que Edith los complete. PERO el campo ESTADO se pre-puebla con el estado de Transoft
(`estado` del SISTEMA) — así Edith no arranca de cero:

```python
# En el loop de NUEVOS, después de vaciar MANUAL_COLS:
estado_transoft = _normalize_estado(r_sis.get("estado"))
if estado_transoft:
    row_data["ESTADO"] = estado_transoft
    stats["estado_auto"] = stats.get("estado_auto", 0) + 1
```

Edith confirma o corrige. REFERENTE sigue auto-sugiriéndose desde `succobro`.

### PITFALL — importe/saldo con decimales excesivos

Los valores de importe y saldo de Transoft pueden traer muchos decimales (ej: 1234.5600001).
Siempre redondear a 2 decimales en `write_row` y aplicar `number_format`:

```python
if col_name in ("importe", "saldo") and v not in (None, ""):
    try:
        v = round(float(v), 2)
    except (TypeError, ValueError):
        pass
# ...
if col_name in ("importe", "saldo") and isinstance(v, float):
    cell.number_format = '#,##0.00'
```

Hacerlo dentro del loop de columnas de `write_row`, ANTES de asignar el valor a la celda.

### PITFALL — extra_cols indefinido rompe el merge silenciosamente

Si se elimina la sección de columnas extra del encabezado pero queda una referencia a `extra_cols` más abajo (ej: `all_cols = FINAL_COLS + extra_cols`), el merge revienta con `NameError` y FastAPI devuelve 500. El Excel no se genera y el frontend no muestra nada.

Fix: cuando no hay columnas extra, cambiar a `all_cols = FINAL_COLS`.

### PITFALL — servidor en UTC, cálculo de días debe usar zona AR

El servidor corre en UTC. `date.today()` devuelve la fecha UTC (puede ser un día adelante respecto a Argentina). El cálculo correcto:

```python
from datetime import datetime, timezone, timedelta
ar_tz = timezone(timedelta(hours=-3))
hoy = datetime.now(ar_tz).date()
return (hoy - fecha).days
```

### PITFALL — backend Python cachea módulos en memoria

Si se edita `contado_merger.py` y el uvicorn sigue corriendo, el módulo viejo queda cacheado. **El backend debe reiniciarse con kill -9 por pid** (pkill -f no siempre mata el proceso correcto si hay múltiples). Verificar siempre con `ss -tlnp | grep 9000` antes y después.

Secuencia correcta:
```bash
fuser -k 9000/tcp 2>/dev/null   # mata lo que tenga el puerto
sleep 1
# verificar que quedó libre
ss -tlnp | grep 9000 || echo "LIBRE"
# levantar con background=true (no usar & en terminal inline)
```

Usar `terminal(background=True)` para el proceso uvicorn, luego verificar con `curl -s http://localhost:9000/health` en llamada separada.

### Tabla editable CONTADO — localStorage

- `contado_last_run` — timestamp string del último procesamiento
- `contado_last_table` — JSON de `{ columns, rows }` del último FINAL
- `contadoHasSaved` — flag booleano inicializado desde `!!localStorage.getItem('contado_last_table')`
- Botón "👁 Ver último FINAL" solo se renderiza si `contadoHasSaved === true`
- Al apretar: `setContadoTableData(JSON.parse(saved))` + scroll via `contadoTableRef.current?.scrollIntoView({ behavior: 'smooth' })`

### PITFALL — filtro DIAS_ATRASO con NaN

`DIAS_ATRASO` llega como string desde `excel_to_table` (todo se convierte a str). Filas sin fecha tienen `DIAS_ATRASO = ""`. El filtro debe excluir esas filas cuando hay mínimo definido:

```typescript
const raw = row[COL_DIAS]
const dias = (raw !== '' && raw !== null && raw !== undefined) ? parseFloat(String(raw)) : NaN
if (isNaN(dias) || dias < minVal) return false
```

NO usar `parseFloat(String(row[COL_DIAS] ?? '0'))` — el `?? '0'` hace que filas sin dato cuenten como 0 días y siempre pasen el filtro.

## Filtros disponibles en ContadoTable (jun 2026)

Filtros implementados y sus COL_ correspondientes:

| Filtro | Estado variable | COL_ | Detección |
|--------|----------------|------|-----------|
| Texto libre | filterText | — | razsocc + nro |
| Estado | filterEstado | COL_ESTADO | includes('estado') |
| Referente | filterRef | COL_REF | includes('referente') o 'refer' |
| Suc. cobro | filterSucCobro | COL_SUCCOBRO | includes('succobro') |
| Suc. destino | filterSucDest | COL_SUCDEST | includes('sucdest') |
| Suc. origen | filterSucOri | COL_SUCORI | === 'sucori' (exacto) |
| Clase | filterClase | COL_CLASE | === 'clase' (exacto) |
| Justificación | filterJustif | COL_JUSTIF | includes('justif') |
| Observación | filterObserv | COL_OBSERV | includes('observ') |
| Sin asignar | filterSinAsignar | — | ref === NDS/NDE/'') |
| Días mínimo | filterDiasMin | COL_DIAS | includes('dias') o 'atraso' |
| Origen badge | filterOrigen | COL_ORIGEN | === '__ORIGEN__' |

**Patrón para agregar un nuevo filtro:**
1. `useState<string>('all')` para el estado
2. `columns.find((_, i) => colLower[i] === 'nombre_exacto') ?? ''` para la COL_
3. `useMemo` con `new Set(data.map(...)).sort()` para los valores únicos
4. `if (filter !== 'all' && String(row[COL] ?? '') !== filter) return false` en el useMemo de filtrado
5. Agregar a deps del useMemo de filtrado
6. `setFilterX('all')` en `resetFilters()`
7. Select en JSX con opción `all` + valores dinámicos

**NOTA:** `sucori` y `clase` usan match EXACTO (`=== 'sucori'`) porque `includes` podría matchear otras columnas. Usar exacto siempre que el nombre de columna sea corto y ambiguo.

## PITFALL — discrepancia de filas entre Excel manual y app

**Síntoma:** el Excel de Edith muestra N filas con filtro ED (o ED+REFERENTE=X), la app muestra N-X.

**IMPORTANTE:** antes de diagnosticar, confirmar qué filtro exacto está activo en la app.
El dropdown "CC" puede ser REFERENTE, succobro o sucdest — son columnas distintas con conteos distintos.

**Diagnóstico rápido:**
```bash
python3 ~/.hermes/skills/nelson-expreso-bisonte-poc/scripts/diagnostico_merger_contado.py \
  INICIAL.xlsx SISTEMA.xlsx FINAL_edith.xlsx
```
Reporta automáticamente: totales, cambios de estado, faltantes por REFERENTE.

**Causas verificadas (jun 2026) — ya fixeadas:**
- ESTADO se preservaba del INICIAL → guías que cambiaron a ED no aparecían. Fix: ESTADO siempre de SISTEMA.
- REFERENTE vacío (#N/A) en existentes no se auto-sugería → fix: si vacío, sugerir desde succobro.

**Otras causas posibles:**
- Deduplicación por `nro` en SISTEMA descarta duplicados (verificar si ambas ocurrencias son ED)
- `_find_header_row` detecta fila de título en lugar de header (Excel con título en fila 1)
- El INICIAL subido no es el correcto

Ver `references/bisonte-contado-merger-pitfalls.md` para detalle completo.

## PITFALL — patch en TSX puede borrar líneas y desbalancear el componente

Síntoma: esbuild/tsc reportan error en la ÚLTIMA línea del archivo (`Unexpected "}"`  o `'return' outside of function`) pero el verdadero problema está mucho antes.

Causa: un patch que matchea texto ambiguo puede borrar parte de una línea contigua. En esta sesión se borró la línea `if (!data) {` de `renderPreviewTable`, dejando el `}` de cierre flotando y desbalanceando todo el componente.

Diagnóstico rápido:
```bash
node -e "
const {parse} = require('@babel/parser');
const fs = require('fs');
const code = fs.readFileSync('src/pages/HomePage.tsx', 'utf8');
try { parse(code, {sourceType:'module', plugins:['typescript','jsx']}); console.log('OK'); }
catch(e) { console.log('ERROR:', e.message.split('\n')[0], 'loc:', JSON.stringify(e.loc)); }
"
```
Babel reporta el error en la línea REAL (ej: `'return' outside of function. (1142:2)`), no en la última.

Verificar el diff:
```bash
git diff HEAD src/pages/HomePage.tsx | head -40
```

Fix: restaurar la línea faltante con patch exacto incluyendo suficiente contexto antes y después.

## PITFALL — colaboración multiusuario: usar sessionStorage, no localStorage

Cuando se necesita identificar pestañas distintas sin sistema de login, usar `sessionStorage`:
- `localStorage` es compartido entre pestañas del mismo dominio → todas serían el mismo usuario
- `sessionStorage` es exclusivo de cada pestaña → cada una genera su propio ID único
- El ID persiste mientras la pestaña esté abierta, se regenera al cerrarla/abrirla

## PITFALL — spa_proxy filtra headers custom del backend

El `spa_proxy.py` usa `http.server` de Python que puede silenciar headers con guión en el nombre.
Aunque `expose_headers` en CORS del backend es necesario, también verificar que el proxy los reenvíe:

```python
# En _proxy_request, la línea de filtrado:
if header.lower() not in ("transfer-encoding", "content-encoding", "connection"):
    self.send_header(header, value)
```
Los headers `X-Stats-*` deben pasar por este filtro. Si axios sigue sin verlos, agregar log temporal en el proxy para confirmar que llegan del backend.

## BD Bisonte — Schema v1 (jun 2026)

Ver `references/bisonte-db-schema-v1.md` para el schema completo con todas las tablas,
relaciones, vista de cruce y convención para nuevos procesos.

**Resumen del eje de datos:**
- `guia` — PK nro, universo completo Transoft
- `contado_anotacion` — campos manuales Edith, FK→guia
- `cdo_guia` / `pte_fact_guia` — datos CDO/PTE sistema vs trabajado
- `v_guia_cruce` — JOIN de todos los procesos por nro
- Tablas `contado_guias` (legacy) — mantener para compatibilidad

**Convención:** todo proceso nuevo = tabla `<proceso>_run` (auditoría) + `<proceso>_<entidad>` (datos), FK→guia.

### PITFALL — heredoc bash NO llega a docker exec

`docker exec bisonte-db psql ... << 'SQL' ... SQL` → output vacío, el SQL no se ejecuta.
Fix: escribir a archivo temporal + docker cp + psql -f:
```bash
cat > /tmp/schema.sql << 'EOF'
-- SQL aquí
EOF
docker cp /tmp/schema.sql bisonte-db:/tmp/schema.sql
docker exec bisonte-db psql -U bisonte -d bisonte -f /tmp/schema.sql
```

### PITFALL — rows como dicts en /contado/save

El frontend manda rows como **lista de objetos** `[{ nro: "...", REFERENTE: "...", _row_idx: 0, _color: "none" }]`,
NO como arrays. Acceder con `row[0]` sobre un dict da `KeyError: 0` → HTTP 500.

Detección antes de iterar:
```python
is_dict_rows = len(rows) > 0 and isinstance(rows[0], dict)
# ...
val = row.get(col_frontend) if is_dict_rows else row[columns.index(col_frontend)]
```

El check `columns.index("nro")` solo es necesario cuando las rows son arrays, no cuando son dicts.

### Levantar BDs (bisonte-db + bisonte-qdrant)

```bash
cd /home/server/proyectos/excel-merger-poc
docker compose -f docker-compose.db.yml up -d
docker exec bisonte-db pg_isready -U bisonte -d bisonte   # bisonte-db :5435
curl -s http://localhost:6335/healthz                      # bisonte-qdrant :6335
```

### Tabla `contado_guias` (legacy — mantener para compatibilidad)

Tabla original antes del schema v1. El endpoint /contado/save sigue escribiendo en ella
además de guia + contado_anotacion. NO eliminar — código anterior depende de ella.

Schema original de `contado_guias`:

```sql
CREATE TABLE IF NOT EXISTS contado_guias (
    nro             TEXT PRIMARY KEY,
    justificacion   TEXT,
    referente       TEXT,
    estado          TEXT,
    observacion     TEXT,
    dias_atraso     INTEGER,
    guiafec         TEXT,
    razsocc         TEXT,
    clase           TEXT,
    fechaedit       TEXT,
    sucori          TEXT,
    sucdest         TEXT,
    importe         NUMERIC(18,2),
    saldo           NUMERIC(18,2),
    succobro        TEXT,
    tiporec         TEXT,
    sucursal        TEXT,
    nrogen_a        TEXT,
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_by      TEXT DEFAULT 'sistema'
);
```

### Endpoints implementados

- `POST /api/v1/excel/contado/save` — UPSERT por `nro`. Recibe `{ columns, rows, updated_by }`. Devuelve `{ saved: N, updated_at: "DD/MM HH:MM" }`.
- `GET  /api/v1/excel/contado/save` — Recupera todas las guías guardadas. Devuelve `{ columns, rows, total, updated_at }`.

### PITFALL — rows como dicts vs arrays en /contado/save

El frontend (ContadoTable.tsx) manda las rows como **lista de objetos** `[{ nro: "...", REFERENTE: "...", _row_idx: 0, _color: "none", ... }]`, NO como lista de arrays `[[val1, val2, ...]]`.

El backend debe detectar el tipo antes de acceder:
```python
is_dict_rows = len(rows) > 0 and isinstance(rows[0], dict)

for row in rows:
    for col_frontend, col_db in _COL_MAP.items():
        if is_dict_rows:
            val = row.get(col_frontend)   # dict: acceso por clave
        else:
            idx = columns.index(col_frontend)
            val = row[idx] if idx < len(row) else None  # array: acceso por índice
```

Si se usa `row[0]` directamente sobre un dict → `KeyError: 0`. Síntoma: HTTP 500 al apretar Guardar.

### Flujo del botón Guardar (jun 2026)

El botón "Guardar y descargar FINAL" hace DOS cosas en orden:
1. `POST /contado/save` → UPSERT en PostgreSQL → badge se actualiza con "BD ✅ N guías · DD/MM HH:MM"
2. `POST /contado/export` → descarga Excel editado

El `btoa()` para archivos grandes usa loop explícito (no spread operator — revienta el stack):
```typescript
const bytes = new Uint8Array(buf)
let binary = ''
for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i])
const b64 = btoa(binary)
```

## Arquitectura futura — BD + IA (decisión jun 2026)

Nelson definió la dirección arquitectural para la siguiente fase:

## BD PostgreSQL — Schema y endpoints (implementado jun 2026)

### Levantar las BDs de Bisonte

```bash
cd /home/server/proyectos/excel-merger-poc
docker compose -f docker-compose.db.yml up -d
# Verificar
docker exec bisonte-db pg_isready -U bisonte -d bisonte
curl -s http://localhost:6335/healthz
```

Containers:
- `bisonte-db` postgres:16-alpine → :5435, creds: bisonte/bisonte2026, db=bisonte
- `bisonte-qdrant` qdrant:latest → :6335 (HTTP), :6336 (gRPC)

### Schema contado_guias (ya creado — NO recrear)

```sql
-- Verificar que existe:
docker exec bisonte-db psql -U bisonte -d bisonte -c "\dt"

-- Si está vacío, crear:
docker exec bisonte-db psql -U bisonte -d bisonte -c "
CREATE TABLE IF NOT EXISTS contado_guias (
    nro             TEXT PRIMARY KEY,
    justificacion   TEXT,
    referente       TEXT,
    estado          TEXT,
    observacion     TEXT,
    dias_atraso     INTEGER,
    guiafec         TEXT,
    razsocc         TEXT,
    clase           TEXT,
    fechaedit       TEXT,
    sucori          TEXT,
    sucdest         TEXT,
    importe         NUMERIC(18,2),
    saldo           NUMERIC(18,2),
    succobro        TEXT,
    tiporec         TEXT,
    sucursal        TEXT,
    nrogen_a        TEXT,
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_by      TEXT DEFAULT 'sistema'
);
CREATE INDEX IF NOT EXISTS idx_contado_estado    ON contado_guias(estado);
CREATE INDEX IF NOT EXISTS idx_contado_referente ON contado_guias(referente);
CREATE INDEX IF NOT EXISTS idx_contado_succobro  ON contado_guias(succobro);
CREATE INDEX IF NOT EXISTS idx_contado_updated   ON contado_guias(updated_at);
"
```

### Endpoints de BD implementados

| Método | Path | Descripción |
|--------|------|-------------|
| POST | `/api/v1/excel/contado/save` | UPSERT de todas las filas por `nro`. Recibe `{columns, rows, updated_by}`. Devuelve `{saved: N, updated_at}` |
| GET  | `/api/v1/excel/contado/save` | Recupera todas las guías guardadas. Devuelve `{columns, rows, total, updated_at}` |

El endpoint POST usa `psycopg2.extras.execute_batch` con `page_size=200` para UPSERT en bloque eficiente.

### Flujo del botón Guardar (implementado jun 2026)

El botón "💾 Guardar y descargar FINAL" hace DOS cosas en orden:
1. `POST /excel/contado/save` → UPSERT en PostgreSQL → badge se actualiza con "BD ✅ N guías · DD/MM HH:MM"
2. `POST /excel/contado/export` → descarga el Excel editado

El `updated_by` se fija como `'edith'` en el frontend (hardcodeado por ahora).

### PITFALL — psycopg2 ya está instalado en el sistema

`python3 -c "import psycopg2"` debe funcionar sin pip install. Si falla, instalarlo a nivel sistema:
```bash
sudo apt install python3-psycopg2
```
No usar pip ni venv para esto — el backend corre sin venv.

### Arquitectura futura pendiente

- **INICIAL en BD** — una vez corroborado, el INICIAL se persiste en BD. Los días siguientes solo se sube el SISTEMA nuevo. El merge corre contra BD, no contra un Excel.
- **FINAL en BD** — el equipo lo ve sin re-ejecutar. Las ediciones se guardan en tiempo real. Edith aprueba → ese FINAL pasa a ser el nuevo INICIAL.
- **Qdrant** — por ahora no se usa. Solo PostgreSQL para datos operativos.
- **Fuente futura**: scraping automático de Transoft.

## PITFALL — "Ver último FINAL" no funciona en primera sesión

El botón `👁 Ver último FINAL` lee `contado_last_table` de localStorage.
Si el usuario nunca procesó en ese browser, localStorage está vacío → el botón no hace nada visible.

Fix aplicado: el botón solo se renderiza si `contadoHasSaved` es true (hay datos reales en localStorage).
Al guardar la tabla en `loadContadoTable` se setea `setContadoHasSaved(true)`.
El botón también hace `scrollIntoView` con un delay de 100ms para que el usuario vea la tabla aparecer.

```tsx
// Estado inicial desde localStorage
const [contadoHasSaved, setContadoHasSaved] = useState<boolean>(
  () => !!localStorage.getItem('contado_last_table')
)
// Al guardar:
localStorage.setItem('contado_last_table', JSON.stringify(tableData))
setContadoHasSaved(true)
// Al apretar el botón:
setContadoTableData(JSON.parse(saved))
setTimeout(() => contadoTableRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
```

## PITFALL — Columnas extra ESTADO_SISTEMA / ORIGEN en el FINAL

El merger agregaba dos columnas al final del Excel: `ESTADO_SISTEMA` y `ORIGEN`.
Edith no las necesita — confunden el documento. Sacarlas del merger:

```python
# En write_row: NO agregar columnas extra
# En el header: NO extra_cols = ["ESTADO_SISTEMA", "ORIGEN"]
```

Solo escribir `FINAL_COLS`, sin columnas de diagnóstico interno.

## PITFALL — Filtro días de atraso: NaN bug

Cuando `DIAS_ATRASO` es `""` (sin fecha de entrega), `parseFloat("") = NaN`.
`NaN < 7` es `false` → la fila pasaba el filtro aunque no tuviera datos.

Fix correcto en ContadoTable.tsx:
```tsx
if (filterDiasMin !== '') {
  const minVal = parseFloat(filterDiasMin)
  const raw = row[COL_DIAS]
  const dias = (raw !== '' && raw !== null && raw !== undefined) ? parseFloat(String(raw)) : NaN
  // Sin dato de días → excluir del resultado
  if (isNaN(dias) || dias < minVal) return false
}
```

## Tabla editable — Flujo Cobranzas Contado (jun 2026)

### Persistencia de la tabla en localStorage

Al generar el FINAL, la tabla se persiste en `localStorage` del browser:
- `contado_last_run` → timestamp string legible ("14/6/2026, 23:57")
- `contado_last_table` → JSON del `{ columns, rows }` devuelto por `/contado/preview`

Al montar el componente, se restauran automáticamente. El botón "👁 Ver último FINAL" (negro,
arriba del botón Generar) solo aparece si `contado_last_table` existe en localStorage.
Al presionarlo: `setContadoTableData(parsed)` + `scrollIntoView` hacia el `ref` de la tabla.

Estado booleano `contadoHasSaved` se inicializa con `!!localStorage.getItem('contado_last_table')`.

### PITFALL — filtro DIAS_ATRASO con NaN

`parseFloat("") = NaN`, y `NaN < 7` es `false` → las filas sin dato de días **pasan** el filtro.
Fix: excluir explícitamente NaN:
```typescript
const raw = row[COL_DIAS]
const dias = (raw !== '' && raw !== null && raw !== undefined) ? parseFloat(String(raw)) : NaN
if (isNaN(dias) || dias < minVal) return false
```

### PITFALL — scroll invisible al restaurar tabla

`setContadoTableData(parsed)` es asíncrono — el DOM aún no tiene el div de la tabla cuando
se llama `scrollIntoView`. Solución: `setTimeout(..., 100)`.



Después del merge, el frontend carga automáticamente la tabla editable:

1. `POST /api/v1/excel/contado/preview` — recibe Excel blob, devuelve `{ columns, rows }` (sin `_color` — los colores se eliminaron del output)
2. `POST /api/v1/excel/contado/export` — recibe `{ columns, rows, original_bytes_b64 }`, devuelve Excel editado

### COLUMNAS EXTRA ELIMINADAS del FINAL

Las columnas `ESTADO_SISTEMA` y `ORIGEN` fueron removidas del Excel de salida (jun 2026).
El merger interno sigue usando `__estado_sis__` y `__origen__` como campos internos para detectar cambios,
pero NO se escriben al Excel final. El `write_row` en `contado_merger.py` no emite columnas extra.

### COLUMNAS INTERNAS vs COLUMNA OCULTA `__ORIGEN__` (jun 2026)

El merger calcula `__origen__` internamente (valores: `NUEVO`, `EXISTENTE`, `CAMBIO_ESTADO`) pero NO
la escribe en el Excel. Sin embargo, el endpoint `/contado/preview` puede incluir `__ORIGEN__` como
columna en la tabla para que el frontend pueda mostrar badges sin exponer la columna como editable.

Patrón en ContadoTable.tsx:
```typescript
const HIDDEN_COLS = ['__ORIGEN__', '_row_idx', '_color']  // no renderizar como columnas
// Badges en la primera celda de cada fila:
const origen = row['__ORIGEN__'] ?? ''
if (origen === 'NUEVO')         badge = <span style={{background:'#fef9c3'}}>NUEVO</span>
if (origen === 'CAMBIO_ESTADO') badge = <span style={{background:'#fee2e2'}}>CAMBIO</span>
// Filtro de origen:
const filterOrigen = useState<string>('all')  // 'all' | 'NUEVO' | 'CAMBIO_ESTADO' | 'EXISTENTE'
```

**NO agregar `__ORIGEN__` como columna visible en el Excel descargado.** Solo vive en el preview JSON.

### Colores en el frontend — solo por columna, nunca por fila

**REGLA EXPLÍCITA DE NELSON (junio 2026):** 
- NO pintar filas enteras — solo la celda de la columna que corresponde a la regla
- Colores se agregan gradualmente — NO agregarlos antes de que Nelson lo pida
- En el frontend: colorear solo la celda específica (COL_DIAS, COL_FECHAEDIT) con `cellStyle(col)`
- En el backend (openpyxl): `ws_out.cell(row_out, IDX).fill = FILL_ROJO` para la columna exacta

Eliminar cualquier lógica de `_color` o `rowStyle` que pinte toda la fila.

### Feature: Colaboración en tiempo real — WebSocket (implementado jun 2026)

### Arquitectura

- Backend: `app/api/v1/endpoints/ws_contado.py` — FastAPI WebSocket en `/api/v1/ws/contado`
- Frontend hook: `src/hooks/useContadoWS.ts`
- ContadoTable.tsx integrado con presencia, locks y updates remotos

### Protocolo de mensajes

Cliente → servidor:
- `{ type: "join", user: "edith" }` — registrar con color asignado
- `{ type: "editing", user, nro, col }` — bloquear celda
- `{ type: "update", user, nro, col, value }` — confirmar cambio (onBlur)
- `{ type: "leave", user, nro, col }` — soltar celda sin confirmar
- `{ type: "ping" }` — keepalive

Servidor → clientes:
- `{ type: "presence", users: [{user, color, editing_nro, editing_col}] }` — broadcast presencia
- `{ type: "cell_lock", user, color, nro, col }` — celda bloqueada por otro
- `{ type: "cell_unlock", user, nro, col }` — celda liberada
- `{ type: "cell_update", user, color, nro, col, value }` — valor nuevo de otro usuario
- `{ type: "cell_locked_by_other", user, color, nro, col }` — rechazo de lock (ya lo tiene otro)

### PITFALL — spa_proxy Python NO soporta WebSocket upgrade

El `spa_proxy.py` usa `http.server` de Python puro — no maneja el handshake HTTP→WS.
El frontend conecta el WS **directo al backend :9000**, no al proxy :9090:

```typescript
const WS_URL = (() => {
  const proto    = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const hostname = window.location.hostname   // 100.110.8.13
  return `${proto}://${hostname}:9000/api/v1/ws/contado`
})()
```

Si en el futuro se agrega nginx como proxy único, el WS puede centralizarse en :9090 con:
```nginx
location /api/v1/ws/ {
    proxy_pass http://localhost:9000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### Room singleton — modelo de estado

```python
class ContadoRoom:
    connections: Dict[str, WebSocket]   # ws_id → ws
    users: Dict[str, dict]              # ws_id → {user, color, editing_nro, editing_col}
    locks: Dict[tuple, str]             # (nro, col) → ws_id
```

Un solo room para toda la sesión del server. Si el backend se reinicia, todos los clientes reconectan solos (el hook tiene retry de 3s).

### Hook useContadoWS — patrón de uso

```typescript
const { connected, presence, cellLocks, sendEditing, sendUpdate, sendLeave, wsRef } =
  useContadoWS(currentUser)

// En celda input:
onFocus={() => sendEditing(nro, col)}
onBlur={e => { sendUpdate(nro, col, e.target.value); handleCellChange(...) }}

// Lock visual:
const lock = cellLocks.get(`${nro}::${col}`)
// → border colorido + readOnly + badge con iniciales
```

### Updates remotos via CustomEvent

El hook despacha eventos custom en el WS object para que el componente los escuche:
```typescript
ws.dispatchEvent(new CustomEvent('remote_update', { detail: msg }))
// En ContadoTable:
ws.addEventListener('remote_update', handler)
// handler: setData(prev => prev.map(r => r[COL_NRO] === msg.nro ? {...r, [msg.col]: msg.value} : r))
```

### Colaboración en tiempo real — WebSocket (implementado jun 2026)

Backend: `app/api/v1/endpoints/ws_contado.py` — room singleton con locks por (nro, col).
Frontend: `hooks/useContadoWS.ts` + integrado en `ContadoTable.tsx`.
WS conecta directo a `:9000` (el spa_proxy HTTP no soporta upgrade).

Identificación de pestañas sin login: `sessionStorage` genera un `tab_XXXXX` único por pestaña.
NO usar `localStorage` — se comparte entre pestañas del mismo origen.

Ver `references/bisonte-websocket-colaboracion.md` para protocolo completo, pitfalls de
self-lock y doble-lock, y snippet de diagnóstico con logs del backend.

### PITFALL — doble lock (pestaña 2 sobreescribe el lock de pestaña 1)
La pestaña que recibe un `cell_lock` y re-renderiza el input como `readOnly` igual puede
disparar `onFocus` → manda su propio `editing` → sobreescribe el lock.
Fix: pasar `isLockedByOther` al handler y salir si es true:
```typescript
const handleCellFocus = (row, col, isLockedByOther) => {
  if (isLockedByOther) return
  sendEditing(String(row[COL_NRO]), col)
}
// JSX:
onFocus={() => handleCellFocus(row, col, lockedByOther)}
```

### PITFALL — self-lock (el dueño se bloquea a sí mismo)
Filtrar en el hook antes de guardar en cellLocks:
```typescript
case 'cell_lock':
  if (msg.user !== user) { setCellLocks(...) }
```
Y en el componente: `const lockedByOther = !!lock && lock.user !== resolvedUser`
Usar `lockedByOther` (no `!!lock`) en readOnly, cursor, color, border, y title.

## PITFALL — Color por columna en openpyxl (no por fila)

Para pintar solo una celda de una columna específica (no toda la fila):

```python
# Precalcular índice 1-based UNA sola vez fuera del loop
_FECHAEDIT_COL_IDX = FINAL_COLS.index("fechaedit") + 1 if "fechaedit" in FINAL_COLS else None

# Dentro de write_row, DESPUÉS de escribir todos los valores:
dias    = row_data.get("DIAS_ATRASO", "")
sucdest = str(row_data.get("sucdest", "") or "").strip().upper()
if isinstance(dias, int) and _FECHAEDIT_COL_IDX:
    tolerancia = 2 if sucdest == "CC" else 7
    if dias > tolerancia:
        ws_out.cell(row_out, _FECHAEDIT_COL_IDX).fill = FILL_ROJO
```

Regla Bisonte: `sucdest == "CC"` → tolerancia 2 días, resto → 7 días.
Aplica solo a la celda `fechaedit`, no a la fila entera.

## Colores por columna — implementado jun 2026

Regla activa en `contado_merger.py`:
- Columna `fechaedit` → celda roja si `DIAS_ATRASO > 2` cuando `sucdest == "CC"`, o `> 7` para el resto
- Constante precalculada: `_FECHAEDIT_COL_IDX = FINAL_COLS.index("fechaedit") + 1`
- Se aplica en `write_row()` DESPUÉS de escribir la fila — sobreescribe el fill de esa celda puntual
- NO pintar filas enteras — solo la celda de la columna correspondiente a la regla

Patrón para agregar color a otras columnas en el futuro:
```python
_MICOL_IDX = FINAL_COLS.index("micol") + 1 if "micol" in FINAL_COLS else None
# dentro de write_row():
if condicion and _MICOL_IDX:
    ws_out.cell(row_out, _MICOL_IDX).fill = FILL_ROJO
```

## DIAS_ATRASO — no editable en frontend

En `ContadoTable.tsx`, la columna `COL_DIAS` tiene `readOnly` y cursor `default`:
```tsx
readOnly={lockedByOther || col === COL_DIAS}
cursor: (lockedByOther || col === COL_DIAS) ? 'default' : 'text'
```
También se pasa `col === COL_DIAS` al `handleCellFocus` para que no emita WS editing.

## Filtros — opción "vacío" en selects con valores dinámicos

Patrón para agregar "Sin X" a cualquier filtro dinámico:
```tsx
<option value="__empty__">⬜ Sin justificación</option>
{values.map(j => <option key={j} value={j}>{j}</option>)}
```
Lógica del filtro:
```tsx
if (filter !== 'all') {
  const val = String(row[COL] ?? '').trim()
  if (filter === '__empty__') { if (val !== '') return false }
  else { if (val !== filter) return false }
}
```
Mostrar el select aunque `values.length === 0` — la opción "vacío" siempre tiene sentido.

## WebSocket colaboración — estado jun 2026 (funciona parcialmente)

## Auto-persistencia en DB al ejecutar "Generar FINAL" (implementado jun 2026)

### PITFALL — no bloquear la descarga si la DB falla

El UPSERT en DB corre DESPUÉS del merge. Si falla (DB caída, schema desactualizado, etc.),
`db_saved` queda en `-1` y el error va a `stats["db_error"]`, pero el Excel **igual se descarga**.
Nunca levantar HTTPException desde el bloque de persistencia — el usuario siempre recibe su archivo.

```python
try:
    table = excel_to_table(final_bytes)
    _upsert_rows(table["columns"], table["rows"], updated_by="merge_auto")
    db_saved = len(table["rows"])
except Exception as e:
    db_saved = -1
    stats["db_error"] = str(e)  # log para diagnóstico, no bloquear
```

Cada vez que Edith presiona "Generar FINAL", el endpoint `POST /merge-contado` ahora:
1. Ejecuta el merge (INICIAL + SISTEMA → FINAL)
2. Parsea el Excel resultante con `excel_to_table()`
3. Llama a `_upsert_rows()` automáticamente — pisa toda la BD con el nuevo procesamiento
4. Retorna el Excel descargable + header `X-Stats-DbSaved: N`

Si la DB falla, el Excel igual se descarga — no bloquea al usuario. El error queda en `stats["db_error"]`.

### Función `_upsert_rows()` — lógica centralizada

La lógica de UPSERT está en una función compartida que usan tanto `merge-contado` (automático)
como `/contado/save` (manual):

```python
def _upsert_rows(columns: list, rows: list, updated_by: str = "sistema") -> int:
    # Acepta rows como lista de dicts (frontend) o lista de arrays
    # UPSERT en las 3 tablas: guia, contado_anotacion, contado_guias (legacy)
    # Devuelve cantidad de registros guardados
    # Levanta Exception si falla la DB (no HTTPException — el caller decide cómo manejarla)
```

Usar esta función para cualquier nuevo endpoint que necesite persistir guías — no duplicar el SQL.

### PITFALL — auto-persistencia puede fallar silenciosamente

Si `excel_to_table()` no puede parsear el Excel del merge (sheet no encontrado, columnas faltantes),
el UPSERT no corre y `db_saved` queda en `-1`. El usuario descarga el Excel igual.

Para diagnosticar: revisar `/tmp/excel_backend.log` — el error de la DB aparece loguado.

## IA Contado — Automáticos del merger (implementados jun 2026)

### Auto-sugerir REFERENTE desde succobro (registros NUEVOS)

Regla de Edith: 90% de las guías nuevas tienen correlación directa `succobro → REFERENTE`.
El merger auto-rellena REFERENTE en los nuevos con el valor de `succobro` (en mayúsculas):

```python
succobro = str(r_sis.get("succobro", "") or "").strip().upper()
if succobro:
    row_data["REFERENTE"] = succobro
    stats["referente_auto"] = stats.get("referente_auto", 0) + 1
```

Solo aplica a registros NUEVOS (no en INICIAL). En EXISTENTES se preserva el REFERENTE que puso Edith.

### Auto-detectar VER DIF (importe != saldo)

Detecta automáticamente diferencias entre importe y saldo. Aplica a NUEVOS y EXISTENTES.
Solo sugiere si la OBSERVACIÓN está vacía (no sobreescribe lo que Edith ya puso):

```python
def _hay_diferencia(importe: Any, saldo: Any) -> bool:
    try:
        imp = float(importe) if importe not in (None, "", "nan") else None
        sal = float(saldo)   if saldo   not in (None, "", "nan") else None
        if imp is None or sal is None:
            return False
        return abs(imp - sal) > 0.01  # tolerancia 1 centavo
    except (TypeError, ValueError):
        return False

# En EXISTENTES: si OBSERVACIÓN vacía Y hay diferencia → "VER DIF"
obs_actual = str(row_data.get("OBSERVACIÓN", "") or "").strip()
if _hay_diferencia(importe, saldo) and not obs_actual:
    row_data["OBSERVACIÓN"] = "VER DIF"

# En NUEVOS: siempre si hay diferencia (no hay anotación previa)
if _hay_diferencia(importe, saldo):
    row_data["OBSERVACIÓN"] = "VER DIF"
```

Stats devueltas: `stats["ver_dif_auto"]`, `stats["referente_auto"]`.

### Frontend — Coloreado de DIAS_ATRASO por celda (ContadoTable.tsx)

La celda de DIAS_ATRASO se colorea con tolerancia adaptada según `succobro` de esa fila:
- CC (Casa Central): tolerancia = 4 días
- Resto de sucursales: tolerancia = 7 días

Colores:
- Verde (`#dcfce7`): dentro de tolerancia
- Amarillo (`#fef9c3`): entre 70% y 100% de la tolerancia
- Rojo (`#fee2e2`): supera la tolerancia

Implementado en `cellStyle()` en `ContadoTable.tsx`:
```typescript
if (col === COL_DIAS) {
  const dias = parseInt(String(row[col] ?? ''), 10)
  const succobro = String(row[COL_SUCCOBRO] ?? '').trim().toUpperCase()
  const tolerancia = succobro === 'CC' ? 4 : 7
  if (!isNaN(dias)) {
    if (dias > tolerancia) diasBg = '#fee2e2'
    else if (dias > Math.floor(tolerancia * 0.7)) diasBg = '#fef9c3'
    else if (dias >= 0) diasBg = '#dcfce7'
  }
}
```

### Frontend — Filtros dinámicos implementados (jun 2026)

Filtros disponibles en ContadoTable (todos con valores únicos del dataset):
- **ESTADO** — dropdown con estados Transoft (ED, DT, TT, RL, etc.)
- **REFERENTE** — columna manual de Edith + opción `__empty__` para sin asignar
- **Suc. cobro (succobro)** — sucursal de cobro de Transoft
- **Todas las sucdest** — sucursal de destino
- **Suc. origen (sucori)** — sucursal origen ← NUEVO jun 2026
- **Clase** — clase de guía (CONTADO, SUCURSAL, etc.) ← NUEVO jun 2026
- **JUSTIFICACIÓN** — con opción `__empty__`
- **OBSERVACIÓN** — con opción `__empty__`
- **Atraso mín. días** — input numérico
- **Sin asignar (NDS / NDE)** — checkbox

Los botones de PRIORIDAD (1️⃣2️⃣3️⃣4️⃣) fueron ELIMINADOS — causaban confusión operativa. NO volver a agregar sin que Nelson lo pida.
Los badges de Rojos/Amarillos/Sin asignar también fueron eliminados. Solo quedan Total y Visibles.

### Frontend — Filtro por succobro (sucursal de cobro)

Select dinámico con valores únicos del dataset. Detectado como `COL_SUCCOBRO`:
```typescript
const COL_SUCCOBRO = columns.find((_, i) => colLower[i].includes('succobro')) ?? ''
const sucCobroValues = useMemo(() =>
  [...new Set(data.map(r => String(r[COL_SUCCOBRO] ?? '').trim()).filter(Boolean))].sort()
, [data, COL_SUCCOBRO])
```

### Frontend — Botones de prioridad rápida

Fila de botones arriba de los filtros que configuran un filtro con un click:

| Botón | Filtro que activa |
|---|---|
| 1️⃣ Sin asignar | `filterSinAsignar = true` |
| 2️⃣ Rojos (atrasados) | `filterColor = 'red'` |
| 3️⃣ Ver diferencia | `filterObserv = 'VER DIF'` |
| 4️⃣ Retenciones | `filterObserv = 'RETENCION'` |

Cada botón llama a `resetFilters()` antes de setear su filtro — limpia todo para no combinar inadvertidamente.

## Coloreado por columna — reglas de negocio (jun 2026)

Columna `fechaedit` se pinta roja en el Excel FINAL según sucdest:
- `sucdest = CC` → rojo si `DIAS_ATRASO >= 1` (tolerancia = 0, `dias > 0`)
- cualquier otra sucdest → rojo si `DIAS_ATRASO > 7`

Implementado en `contado_merger.py` con constante `_FECHAEDIT_COL_IDX` (1-based, calculada al importar).
El `write_row` aplica el fill DESPUÉS de escribir la fila completa, solo a la celda de fechaedit.
NO pintar filas enteras. Solo la celda de la columna que corresponde a la regla.

```python
_FECHAEDIT_COL_IDX = FINAL_COLS.index("fechaedit") + 1 if "fechaedit" in FINAL_COLS else None

# dentro de write_row — al final, después del loop de columnas:
dias    = row_data.get("DIAS_ATRASO", "")
sucdest = str(row_data.get("sucdest", "") or "").strip().upper()
if isinstance(dias, int) and _FECHAEDIT_COL_IDX:
    tolerancia = 0 if sucdest == "CC" else 7   # CC: pinta desde dia=1; resto: desde dia=8
    if dias > tolerancia:
        ws_out.cell(row_out, _FECHAEDIT_COL_IDX).fill = FILL_ROJO
```

## Agregar filtro nuevo por columna del SISTEMA — patrón completo (jun 2026)

Cuando Edith necesita filtrar por una columna nueva del sistema (ej: sucori, clase, razsocc),
aplicar este patrón de 5 toques en `ContadoTable.tsx`:

### 1. Estado
```typescript
const [filterSucOri, setFilterSucOri] = useState<string>('all')
```

### 2. COL_ resolver
```typescript
const COL_SUCORI = columns.find((_, i) => colLower[i] === 'sucori') ?? ''
```
Usar `===` para columnas con nombre exacto. Usar `.includes('x')` solo si el nombre varía.

### 3. Lógica de filtrado en useMemo
```typescript
if (filterSucOri !== 'all' && String(row[COL_SUCORI] ?? '') !== filterSucOri) return false
```

### 4. Dep array del useMemo
Agregar `filterSucOri` y `COL_SUCORI` al array de dependencias.

### 5. Valores únicos + select en JSX
```typescript
const sucOriValues = useMemo(() =>
  [...new Set(data.map(r => String(r[COL_SUCORI] ?? '').trim()).filter(Boolean))].sort()
, [data, COL_SUCORI])

// JSX:
{COL_SUCORI && sucOriValues.length > 0 && (
  <select value={filterSucOri} onChange={e => setFilterSucOri(e.target.value)}
    style={{ padding: '0.35rem 0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.82rem' }}>
    <option value="all">📍 Suc. origen (todas)</option>
    {sucOriValues.map(s => <option key={s} value={s}>{s}</option>)}
  </select>
)}
```

### Agregar al resetFilters()
```typescript
setFilterSucOri('all'); setFilterClase('all')
```

### Filtros de columnas del SISTEMA agregados hasta jun 2026
| Filtro | COL_ | Emoji |
|--------|------|-------|
| succobro | COL_SUCCOBRO | 🏦 Suc. cobro |
| sucdest | COL_SUCDEST | 🏢 Sucdest |
| sucori | COL_SUCORI | 📍 Suc. origen |
| clase | COL_CLASE | 📦 Clase |

## Filtros con opción "vacío" — patrón ContadoTable (jun 2026)

Para cualquier columna que necesite filtrar filas sin valor:

1. Siempre mostrar el select aunque no haya valores cargados (`justifValues.length > 0` → sacar esa condición)
2. Agregar `<option value="__empty__">⬜ Sin X</option>` como primera opción fija antes de los dinámicos
3. Cambiar la comparación directa a:

```typescript
if (filterX !== 'all') {
  const val = String(row[COL_X] ?? '').trim()
  if (filterX === '__empty__') { if (val !== '') return false }
  else { if (val !== filterX) return false }
}
```

Aplicado a JUSTIFICACIÓN y REFERENTE (jun 2026). Mismo patrón para cualquier columna nueva.

## Columnas no editables en ContadoTable — patrón (jun 2026)

Columnas calculadas por el sistema (ej: DIAS_ATRASO) no deben ser editables:

```tsx
readOnly={lockedByOther || col === COL_DIAS}
cursor: (lockedByOther || col === COL_DIAS) ? 'default' : 'text'
onFocus={() => handleCellFocus(row, col, lockedByOther || col === COL_DIAS)}
```

Para más columnas no editables: extender la condición con `|| col === COL_X`.

## WebSocket colaboración — estado jun 2026 (funciona parcialmente)

Implementado pero con issues pendientes. No tocar hasta que Nelson lo pida.

Archivos:
- `frontend/src/hooks/useContadoWS.ts` — hook WS, tabId por sessionStorage, cellLocksRef (ref, no state)
- `frontend/src/components/ContadoTable.tsx` — presencia, lock visual, readOnly condicional
- `backend/app/api/v1/endpoints/ws_contado.py` — room singleton, broadcast con exclude

### PITFALL — cellLocks como useState causa blur espurio en el dueño

Si `cellLocks` es `useState(Map)`, cada lock remoto causa re-render de toda la tabla.
El input activo puede perder foco → `onBlur` dispara → `sendUpdate` suelta el lock del dueño.

Fix: usar `useRef` para el Map + contador de versión para re-renders controlados:
```typescript
const cellLocksRef = useRef<Map<string, CellLock>>(new Map())
const [cellLocksVer, setCellLocksVer] = useState(0)
// Al recibir cell_lock:
cellLocksRef.current.set(key, lock)
setCellLocksVer(v => v + 1)  // solo sube el contador
// En el componente: void cellLocksVer  para que React re-renderice bordes sin tocar inputs
```

### PITFALL — pestaña receptora del lock dispara su propio editing

Cuando la pestaña 2 recibe `cell_lock` y React re-renderiza, el `onFocus` del input bloqueado
puede dispararse → manda `editing` al server → el server lo registra como lock de pestaña 2.

Fix: `handleCellFocus` recibe `isLockedByOther` y sale sin enviar si es true:
```typescript
const handleCellFocus = (row, col, isLockedByOther: boolean) => {
  if (isLockedByOther) return
  sendEditing(nro, col)
}
```

### PITFALL — filtrar locks propios en el hook, no en el componente

Filtrar `msg.user !== user` dentro del `onmessage` del hook garantiza que el Map nunca
contenga locks propios. Si se filtra en el componente con `lock.user !== resolvedUser`
puede haber desincronía si `resolvedUser` no coincide exactamente con el `user` del hook.

### TabId por pestaña (sin login)
`sessionStorage` (NO localStorage) genera un ID único por pestaña:
```ts
function getTabId(): string {
  const key = '__bisonte_tab_id__'
  let id = sessionStorage.getItem(key)
  if (!id) {
    id = 'tab_' + Math.random().toString(36).slice(2, 7).toUpperCase()
    sessionStorage.setItem(key, id)
  }
  return id
}
```
Cada nueva pestaña = nuevo ID. Misma pestaña recargada = mismo ID.

### PITFALL — cellLocks como useState causa blur espurio

Si `cellLocks` es `useState(Map)`, cada lock remoto trigerea re-render de toda la tabla → el input activo puede perder foco → `onBlur` dispara → se manda `update`+`unlock` → la celda queda libre para el otro.

Fix: usar `useRef` para el Map + contador de versión para re-renders mínimos:
```ts
const cellLocksRef   = useRef<Map<string, CellLock>>(new Map())
const [cellLocksVer, setCellLocksVer] = useState(0)
// Al cambiar el map:
cellLocksRef.current.set(key, lock)
setCellLocksVer(v => v + 1)  // triggerea re-render solo para bordes
```
En el componente: `void cellLocksVer` para consumirlo sin asignar.

### PITFALL — pestaña bloqueada por su propio lock

El server hace broadcast con `exclude=ws_id` pero el frontend igual puede procesar su propio `cell_lock` si llega por otra vía. Fix en el hook:
```ts
case 'cell_lock':
  if (msg.user !== user) {  // solo guardar si es de OTRO
    cellLocksRef.current.set(...)
  }
```

### PITFALL — onFocus en celda readOnly dispara editing al server

Cuando la pestaña 2 ve una celda bloqueada (`readOnly=true`) y hace foco, igual dispara `onFocus` → manda `editing` al server → doble lock. Fix:
```tsx
onFocus={() => handleCellFocus(row, col, lockedByOther)}
// dentro del handler:
if (isLockedByOther) return
```

### PITFALL — blur espurio cuando readOnly cambia durante re-render

El browser puede disparar `blur` cuando un input cambia de `readOnly=false` a `readOnly=true` durante un re-render. Fix con `myLockRef`:
```ts
const myLockRef = useRef<{ nro: string; col: string } | null>(null)
// en sendUpdate/sendLeave: verificar antes de soltar
const mine = myLockRef.current
if (!mine || mine.nro !== nro || mine.col !== col) return
```

### WS conecta directo a :9000

El `spa_proxy.py` HTTP-puro no soporta WebSocket upgrade.
```ts
const WS_URL = `${proto}://${hostname}:9000/api/v1/ws/contado`
```
Con nginx como reverse proxy esto sería transparente en :9090.

### Debugging: logs en el backend

Para diagnosticar problemas de lock, agregar prints en `handle_editing`:
```python
print(f"[WS] LOCK: ws_id={ws_id[:8]} user={...} → broadcast a {[...]}", flush=True)
```
Luego `grep "\[WS\]" /tmp/excel_backend.log` para ver el flujo.

Pendientes conocidos:
- Blur espurio todavía ocurre en algunos casos
- Sin login — tabId aleatorio por sessionStorage
## Referencias de fixes y pitfalls del merger

Ver `references/bisonte-merger-fixes-jun2026.md` — prefijo R. en nros, ESTADO desde SISTEMA, REFERENTE auto en existentes, colores por celda (VER DIF + fechaedit), diagnóstico de diferencias de conteo, filtros sucori/clase.

## COLORES — regla de diseño (jun 2026)

**REGLA EXPLÍCITA DE NELSON:** 
- Pintar solo la celda de la columna correspondiente, NUNCA filas enteras
- Cuando Nelson diga "saquemos los colores" o "no pintemos nada" → eliminar TODO el código de color (fill, cellStyle, rowStyle) sin dejar residuos. Continuar con las otras features sin preguntar — no bloquear el avance.
- Cuando Nelson diga "agreguemos color para X" → implementar solo esa columna específica
- Los colores se agregan gradualmente — NUNCA agregar colores sin que Nelson lo pida explícitamente, ni siquiera como "preview" o "mejora visual"

### Activo (jun 2026)
- Columna `fechaedit` → rojo si `DIAS_ATRASO >= 1` (sucdest=CC) o `> 7` (resto) — tolerancia CC = 0 en código (`dias > 0`)
- Frontend: `cellStyle(col)` devuelve background solo para `COL_FECHAEDIT` / `COL_DIAS` — nunca para toda la fila

### Pendientes — agregar solo cuando Nelson lo pida
- Columna `ESTADO` → celda naranja si el estado cambió entre INICIAL y SISTEMA
- Columna `REFERENTE` → celda amarilla si es NDS/NDE (sin asignar)

NO agregar colores sin que Nelson lo pida explícitamente.

### PITFALL — sacar colores sin dejar residuos

Cuando Nelson dice "saquemos los colores" hay que eliminar:
1. Backend (`contado_merger.py`): bloque `if isinstance(dias, int) and _FECHAEDIT_COL_IDX: ... cell.fill = FILL_ROJO`
2. Frontend (`ContadoTable.tsx`): la función `cellStyle(col)` y el `style={cellStyle(col)}` de cada `<td>`
3. No dejar `_color` ni `__color__` en el JSON del preview — el endpoint `/contado/preview` no debe emitir esa columna

Si Nelson dice "no pintemos nada" a mitad de sesión → sacar TODO el código de color de ambos lados antes de continuar con otras features.

## Pintar celda por columna en openpyxl (write_row)

Para pintar UNA SOLA celda (no toda la fila) en `write_row`, hacerlo DESPUÉS del loop:

```python
# Precalcular índice 1-based fuera del merger (constante, no recalcular por fila)
_FECHAEDIT_COL_IDX = FINAL_COLS.index("fechaedit") + 1 if "fechaedit" in FINAL_COLS else None

# Dentro de write_row, después del loop de columnas:
dias    = row_data.get("DIAS_ATRASO", "")
sucdest = str(row_data.get("sucdest", "") or "").strip().upper()
if isinstance(dias, int) and _FECHAEDIT_COL_IDX:
    tolerancia = 0 if sucdest == "CC" else 7   # CC: pinta desde dia=1; resto: desde dia=8   # CC: pinta desde dia=1; resto: desde dia=8
    if dias > tolerancia:
        ws_out.cell(row_out, _FECHAEDIT_COL_IDX).fill = FILL_ROJO
```

## Filtros con opción "vacío" — patrón ContadoTable

Centinela `__empty__` para cualquier columna. Siempre mostrar el select aunque no haya valores:

```tsx
// Select — siempre visible (no condicionar a values.length > 0)
{COL_X && (
  <select value={filterX} onChange={e => setFilterX(e.target.value)} ...>
    <option value="all">... Todos ...</option>
    <option value="__empty__">⬜ Sin X</option>
    {xValues.map(v => <option key={v} value={v}>{v}</option>)}
  </select>
)}

// Filtrado
if (filterX !== 'all') {
  const val = String(row[COL_X] ?? '').trim()
  if (filterX === '__empty__') { if (val !== '') return false }
  else { if (val !== filterX) return false }
}
```

Columnas con filtro vacío implementadas: REFERENTE, JUSTIFICACIÓN, OBSERVACIÓN.

## Columnas de solo lectura en ContadoTable

Columnas calculadas por el sistema (ej: DIAS_ATRASO) no deben ser editables:

```tsx
readOnly={lockedByOther || col === COL_DIAS}
cursor: (lockedByOther || col === COL_DIAS) ? 'default' : 'text'
onFocus={() => handleCellFocus(row, col, lockedByOther || col === COL_DIAS)}
```

Usar `cursor: 'default'` (no `'not-allowed'`) — indica solo lectura sin implicar error.

## Colaboración en tiempo real — WebSocket (implementado jun 2026)

### Arquitectura

- Backend: `app/api/v1/endpoints/ws_contado.py` — WebSocket en `/api/v1/ws/contado`
- Hook: `frontend/src/hooks/useContadoWS.ts`
- Componente: `ContadoTable.tsx` integra presencia + locks

El WS conecta directo al backend `:9000` (NO a través del spa_proxy :9090 — el proxy HTTP puro de Python no soporta WebSocket upgrade).

### Identificación de pestañas sin login

Cada pestaña genera su propio ID usando `sessionStorage` (NO localStorage — localStorage es compartido entre pestañas, sessionStorage no):

```typescript
function getTabId(): string {
  const key = '__bisonte_tab_id__'
  let id = sessionStorage.getItem(key)
  if (!id) {
    id = 'tab_' + Math.random().toString(36).slice(2, 7).toUpperCase()
    sessionStorage.setItem(key, id)
  }
  return id
}
```

Resultado: pestaña 1 = "tab_X7K3P", pestaña 2 = "tab_M2QW8". Cada una opera como usuario independiente.

### Protocolo WS (cliente → server)

| Tipo | Payload | Acción |
|------|---------|--------|
| join | `{ user }` | Registrar en room, broadcastear presencia |
| editing | `{ nro, col }` | Lock de celda — otros la ven bloqueada |
| update | `{ nro, col, value }` | Confirmar cambio + release lock |
| leave | `{ nro, col }` | Release lock sin confirmar cambio |
| ping | — | Keepalive |

### Protocolo WS (server → clientes)

| Tipo | Payload | Significado |
|------|---------|-------------|
| presence | `{ users[] }` | Lista actualizada de usuarios conectados |
| cell_lock | `{ user, color, nro, col }` | Alguien tomó una celda |
| cell_unlock | `{ user, nro, col }` | Celda liberada |
| cell_update | `{ user, color, nro, col, value }` | Valor nuevo de otra persona |
| cell_locked_by_other | `{ user, color, nro, col }` | Celda ya tomada — rechazado |

### UX visual

- Barra de avatares de color (iniciales del usuario) — se actualiza en tiempo real
- Badge "Vos: tab_XXXXX" para identificar la pestaña actual
- Celdas bloqueadas por otro: borde de color + mini badge con iniciales en la esquina
- Celdas de otro usuario: `readOnly=true` + cursor `not-allowed`
- Updates remotos: se aplican al state local sin recargar

### PITFALL — spa_proxy no soporta WS

El `spa_proxy.py` usa `http.server` de Python — no hace WebSocket upgrade. El WS debe ir directo al backend:

```typescript
const WS_URL = `${proto}://${hostname}:9000/api/v1/ws/contado`
// NO: `${proto}://${host}/api/v1/ws/contado`  (ese sería :9090 y falla)
```

Si en el futuro se migra a nginx como proxy único, nginx sí soporta WS con `proxy_pass` + headers `Upgrade` y `Connection`.

### Regla de colores del FINAL — lógica completa

Rojo se aplica por DOS motivos (OR):
1. Estado cambió en Transoft entre INICIAL y SISTEMA
2. Días de atraso supera tolerancia según succobro:
   - CC (Casa Central): > 4 días → rojo
   - Resto de sucursales: > 7 días → rojo

Los registros NUEVOS (amarillo base) también se pintan rojo si ya superaron la tolerancia.

```python
def _es_rojo_por_atraso(dias_atraso, succobro):
    if not isinstance(dias_atraso, int): return False
    suc = str(succobro or '').strip().upper()
    tolerancia = 4 if suc == 'CC' else 7
    return dias_atraso > tolerancia
```

    ### Filtros dinámicos disponibles en ContadoTable (jun 2026)

| Filtro | Columna fuente | Select label |
|--------|---------------|--------------|
| Estado | ESTADO | estados fijos |
| Referente | REFERENTE | dinámico |
| Suc. cobro | succobro | 🏦 Suc. cobro |
| Suc. destino | sucdest | 🏢 Todas las sucdest |
| Suc. origen | sucori | 📍 Suc. origen |
| Clase | clase | 📦 Clase |
| Justificación | JUSTIFICACIÓN | dinámico + vacío |
| Observación | OBSERVACIÓN | dinámico + vacío |
| Sin asignar | REFERENTE=NDS/NDE | checkbox |
| Días mínimos | DIAS_ATRASO | input numérico |
| Origen | __ORIGEN__ | NUEVO/EXISTENTE |
| Texto libre | todos | buscador |

Para agregar un nuevo filtro dinámico, el patrón es:
1. `useState<string>('all')` para el state
2. `columns.find((_, i) => colLower[i] === 'nombre_col')` para detectar la columna
3. `useMemo` con `[...new Set(data.map(...))]` para valores únicos
4. Agregar al `if (filterX !== 'all') return false` en el useMemo de filtrado
5. Agregar a `resetFilters()`
6. Agregar al JSX con `<select>` y `<option value="all">`

### Filtros dinámicos — todos usan valores únicos del dataset

No usar listas hardcodeadas para referente, sucdest, o justificación. Siempre derivar de los datos reales:

```typescript
const refValues = useMemo(() =>
  [...new Set(data.map(r => String(r[COL_REF] ?? '').trim()).filter(Boolean))].sort()
, [data, COL_REF])

const sucDestValues = useMemo(() =>
  [...new Set(data.map(r => String(r[COL_SUCDEST] ?? '').trim()).filter(Boolean))].sort()
, [data, COL_SUCDEST])

const justifValues = useMemo(() =>
  [...new Set(data.map(r => String(r[COL_JUSTIF] ?? '').trim()).filter(Boolean))].sort()
, [data, COL_JUSTIF])
```

Así cuando aparece una nueva sucursal o código en Transoft, aparece automáticamente en el filtro.

### PITFALL — excel_to_table: primera fila ≠ encabezado

Si el Excel tiene un título en la fila 1 (ej: "Informe: GF Pendientes de Cobro..."), openpyxl lo toma como encabezado y genera columnas COL_2, COL_3, etc.

Fix: buscar la primera fila con **al menos 5 celdas con valor** (no solo "any"):
```python
for row in ws.iter_rows():
    vals = [c.value for c in row if c.value is not None]
    if len(vals) >= 5:
        header_row = row
        break
```

### PITFALL — btoa() falla con blobs grandes (>few MB)

`btoa(String.fromCharCode(...new Uint8Array(buf)))` lanza `Maximum call stack size exceeded` con archivos Excel grandes.

Fix robusto:
```typescript
const buf = await blob.arrayBuffer()
const bytes = new Uint8Array(buf)
let binary = ''
for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i])
const b64 = btoa(binary)
```

### PITFALL — color detection en openpyxl

El fill RGB en openpyxl puede venir como `"FFFF0000"` (ARGB) o `"00000000"` (sin fill). Verificar siempre:
```python
if fill and fill.fgColor and fill.fgColor.type == "rgb":
    rgb = fill.fgColor.rgb
    if rgb.upper().endswith("FF0000"): color = "red"
    elif rgb.upper().endswith("FFFF00"): color = "yellow"
```
El prefijo `FF` es el canal alpha (opaco). No comparar el string completo.

## Persistencia de tabla — localStorage pattern (jun 2026)

La tabla del último FINAL se persiste en localStorage del browser con dos keys:
- `contado_last_run` — timestamp string "dd/mm/yy, HH:mm"
- `contado_last_table` — JSON con `{ columns, rows }` del preview

Al montar el componente se restaura automáticamente la tabla si existe.
El botón "👁 Ver último FINAL" solo aparece si `contadoHasSaved` es true.
Usar `useRef` + `scrollIntoView` con 100ms de delay para llevar al usuario hasta la tabla.

⚠️ localStorage tiene límite ~5MB. Si el FINAL es muy grande el `JSON.stringify` puede fallar.
El `try/catch` alrededor del guardado previene crash, pero la tabla no queda persistida.
Señal: el botón no aparece aunque se procesó. Workaround futuro: IndexedDB o compresión.

## Known issues (no son bugs a arreglar)

- `plan/suggest` devuelve un plan con join keys malas (`__UNNAMED__1`) → es la heurística del motor, no se usa en el flujo real
- `/pipeline/static` exige baseline histórico si el universo es grande (CDO ≥400 + PF ≥1400) → por eso el combinado DEBE tener las 4 sheets con TRABAJADA adentro
- `_upload_registry` es en memoria → se borra si reiniciás el backend
- El frontend puede mostrar `plan/suggest` con claves malas; el botón correcto es "Ejecutar CDO/PTE" (que NO usa suggest, usa split + static + compare-manual)

## Repo GitHub

https://github.com/aliagenttucuman-byte/expreso-bisonte-excel-poc

Commits:
- `bc55bb0` — inicial (backend + frontend completo)
- `0b993fe` — spa_proxy.py + demo sample + gitignore actualizado

Lo que NO va al repo: `uploads_temp/` con Excels reales de Expreso Bisonte (datos del cliente).

---

## Propuesta Comercial Bisonte — Patrón de pricing (jun 2026)

Cuando se genere propuesta para Bisonte o clientes similares (empresa que contrata
desarrollo a medida, no equity):

**Sweat equity acumulado:** ~560 hs x USD 30/h = USD 16.800 (no se vuelve a cobrar, es antecedente de validación).
**10 procesos de automatización** — ver `/home/server/brainstorming/2026-06-11-expreso-bisonte-propuesta-comercial/PROPUESTA-COMERCIAL-BISONTE.md`

Bloques:
- Bloque 1 (base PoC): Gestión cobranzas + Facturación pendiente + Auditoría diaria (Procesos 0-3)
- Bloque 2: Dashboard gerencial + Reporte semanal automático (Procesos 4-5)
- Bloque 3: Seguimiento envíos centralizado + Control discrepancias bultos (Procesos 6-7)
- Bloque 4: Análisis clientes por rentabilidad + Cotizador inteligente + Motor genérico (Procesos 8-10)

**Pricing validado:**
- Opción A (fee mensual): Starter USD 800/mes, Operativo USD 1.400/mes, Completo USD 2.000/mes — contrato mínimo 12 meses
- Opción B (inversión): 30% adelantado (USD 7.200) + 12 cuotas USD 1.400/mes — cliente dueño del código
- Mantenimiento post-proyecto: Básico USD 400/mes, Evolutivo USD 800/mes, Full USD 1.200/mes
- A 3 años la Opción B sale ~50% menos que el fee mensual acumulado

**Desarrollo adicional:** 800 hs x USD 30/h = USD 24.000 (5 meses, 4 fases).

## PITFALL — extra_cols indefinido rompe el merge silenciosamente

Si se eliminan las columnas extra (ESTADO_SISTEMA, ORIGEN) del encabezado pero no se actualiza
`all_cols = FINAL_COLS + extra_cols`, el merge lanza `NameError: extra_cols is not defined`
y el endpoint devuelve HTTP 500. El frontend no muestra error visible si no loguea bien.

Fix: reemplazar `all_cols = FINAL_COLS + extra_cols` por `all_cols = FINAL_COLS` cuando no hay columnas extra.

## PITFALL — DIAS_ATRASO: usar `fechaedit`, no `guiafec`

- `guiafec` = fecha de emisión de la guía (string `'DD/MM/YYYY'` en CDO, diferente a CONTADO)
- `fechaedit` = última edición en Transoft (datetime con hora, es el dato correcto)

En el IA_CONTADO (sheet SISTEMA): `fechaedit` viene como `datetime.datetime(2026, 6, 11, 10, 56, 37)`.
Siempre pasar `r_sis.get("fechaedit")` a `_calc_dias_atraso`.

## PITFALL — DIAS_ATRASO: el servidor corre en UTC, Edith está en UTC-3

`date.today()` devuelve fecha UTC. A las 23:57 AR el servidor ya está en el día siguiente.
Siempre calcular "hoy" en zona Argentina:

```python
from datetime import datetime, timezone, timedelta
ar_tz = timezone(timedelta(hours=-3))
hoy = datetime.now(ar_tz).date()
return (hoy - fecha).days
```

## PITFALL — `fechaedit` del Excel viene como datetime naive (con hora)

openpyxl lo lee como `datetime.datetime(2026, 6, 11, 10, 56, 37, 999000)` — no como `date`.
El cast correcto: `isinstance(fechaedit, datetime)` primero, luego `.date()`. No usar `isinstance(v, (datetime, date))` porque `datetime` es subclase de `date` y el orden importa.

## Excel IA_CONTADO — Reglas de Negocio Completas (jun 2026)

`IA_CONTADO.xlsx` — planilla GF Pendientes de Cobro CONTADO. 3 hojas: INICIAL (369 filas), SISTEMA (377 filas), FINAL (374 filas).

### Regla del merge: INICIAL + SISTEMA = FINAL

| Caso | Acción |
|---|---|
| Registro en AMBOS (281) | Va a FINAL preservando JUSTIFICACIÓN, REFERENTE, ESTADO, OBSERVACIÓN de INICIAL |
| Solo en SISTEMA (93 nuevos) | Se agrega a FINAL con campos manuales en BLANCO (no #N/A) — Edith y su equipo los completan |
| Solo en INICIAL (88 eliminados) | Se descarta — ya fueron cobrados o cerrados en Transoft |
| Estado cambió entre INICIAL y SISTEMA (18) | Va a FINAL pintado en **ROJO** — alerta para revisar |

FINAL es **documento colaborativo** — varias personas de distintas sucursales cargan los 4 campos manuales. Edith supervisa desde Dropbox.

### Estados de guía (campo ESTADO)

| Código | Significado |
|---|---|
| ED | Entregada pendiente de cobro — el ÚNICO que trabaja en esta matriz |
| DT | Despachada en tránsito |
| TT | En tránsito |
| RL | Recibida en depósito local |
| RT | Retornada |
| DO | Devuelta al origen |
| DI | Documentación incompleta |
| OB | Observada |
| NR | No retirada |

Solo se trabaja el estado ED en esta planilla. Los demás estados van a otras matrices.

### REFERENTE — sucursal/persona responsable del cobro

| Código | Significado |
|---|---|
| BA | Buenos Aires |
| CC | Casa Central (Tucumán) |
| JU | Jujuy |
| RO | Rosario |
| SA | Salta |
| HM / HMS | Héctor M. (comercial) |
| MRA | Comercial MRA |
| FN | Federico Nacif (comercial) |
| POSVENTA | Área de posventa |
| NDS / NDE | Sin asignar (filtro para encontrar nuevas) |

Regla: REFERENTE = succobro (columna N del sistema). 90% de los casos hay correlación directa. Excepción: si la negociación la hizo un comercial de Tucumán aunque el cobro figure en otra sucursal.

### OBSERVACIÓN — valores usados

| Valor | Significado |
|---|---|
| VER DIF | Saldo ≠ importe, diferencia sin explicar — urgente |
| RETENCION | Diferencia es retención impositiva, la sucursal la gestiona |
| SI + número | Solicitud de Indemnización (ligada a posventa) |
| SGCP + número | Número de gestión de cobro asignada |
| PAGA DD/MM | Ya fue pagada en esa fecha |
| SALDO PENDIENTE | Saldo con causa justificada (mudanza, espera, etc.) |

### JUSTIFICACIÓN — formato libre, ej: "SGCP 6560", "SGCP 6562"

### Tolerancias de cobro (días antes de pintar rojo)

- **Casa Central (Tucumán)**: tolerancia 0 — la documentación se procesa el mismo día
- **Sucursales (BA, JU, RO, SA)**: 5-7 días — tiempo para que la caja mande documentación

### Columna nueva requerida: "Días de atraso en cobranza"

```
dias_atraso = fecha_hoy - guiafec (fecha de entrega)
```

Visible para todos. Se actualiza automáticamente cada vez que se genera el FINAL. Edith lo usa como indicador de gestión.

### Flujo diario de Edith (mínimo 4x/semana, objetivo: todos los días al mediodía)

1. Descarga de Transoft: Operativos → Informes Generales → Detalle Guías por Sucursal → "Contado con Estado de Guía"
2. Pega en hoja nueva del día en su Excel acumulado
3. Vincula con BUSCARV desde hoja anterior (trae JUSTIFICACIÓN, REFERENTE, OBSERVACIÓN)
4. Elimina duplicados (pagos a cuenta + nota de crédito sobre misma guía)
5. Filtra solo estado ED
6. Asigna REFERENTE a las NDS (nuevas sin asignar)
7. Pinta en rojo las urgentes según tolerancia
8. Agrega observaciones manuales
9. Sube al Dropbox → equipo de cuentas corrientes trabaja encima

### Merger backend — endpoint y CORS

- Endpoint: `POST /api/v1/excel/merge-contado` — recibe `inicial` + `sistema` como UploadFile, devuelve FINAL como blob xlsx
- Stats se devuelven en headers: `X-Stats-Existentes`, `X-Stats-Nuevos`, `X-Stats-Eliminados`, `X-Stats-EstadoCambio`
- **CRÍTICO**: el `CORSMiddleware` debe incluir `expose_headers` explícito, si no axios no puede leer esos headers custom:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Stats-Existentes", "X-Stats-Nuevos", "X-Stats-Eliminados", "X-Stats-EstadoCambio", "Content-Disposition"],
)
```

### Resultado verificado con IA_CONTADO.xlsx (jun 2026)

Con el mismo archivo como INICIAL y SISTEMA (control):
- 281 existentes preservados con anotaciones
- 93 nuevos en amarillo (carga manual)
- 88 eliminados (cobrados/cerrados)
- 114 en rojo (estado cambió en Transoft)

Nota: el conteo de "rojo" (114) difiere del análisis visual previo (18) — el merger detecta cualquier cambio de estado, no solo los pintados en el Excel de ejemplo.

### Video de Edith

Descargado con gdown: file_id `1sw6PahPF1EA51TjokD5qDnXB2IEDxgYK`, 454MB, 57 min.
Transcripción: `/tmp/bisonte/transcripcion.txt` (44KB, Whisper `small` CPU ~30 min).
Ver `references/bisonte-ia-contado-edith-reglas.md` para análisis completo.

## Referencias de columnas técnicas

Ver `references/bisonte-contado-columnas-tecnicas.md` — tipos de dato verificados con openpyxl, regla DIAS_ATRASO, tolerancias, estados, y pitfalls del merger.

## Acceso por Tailscale (sin túnel CF)

Cuando el túnel Cloudflare tiene problemas de conectividad externa (QUIC timeout, sin acceso a internet desde ai-server), los servicios siguen 100% accesibles por Tailscale:

- SPA completa (frontend + API proxiada): http://100.110.8.13:9090
- Backend FastAPI directo: http://100.110.8.13:9000
- Health check: `curl http://100.110.8.13:9000/health`

Desde nelsondev (100.76.143.33) funciona sin necesitar el túnel. El túnel CF es solo para demos con externos (Pablo, clientes) que no tienen Tailscale.

Si cloudflared falla con `failed to dial to edge with quic: timeout: no recent network activity`:
1. Verificar conectividad: `curl -s --max-time 5 https://cloudflare.com` — si falla, es DNS/red externa
2. Fix DNS Tailscale: `sudo tailscale set --accept-dns=false`
3. Reintentar: `pkill -f cloudflared; nohup cloudflared tunnel --url http://localhost:9090 > /tmp/cf_expreso.log 2>&1 &`
4. Si sigue fallando → usar Tailscale directo y avisar a Nelson

## Contactos

- **Pablo**: COO AlegentAI + socio ForestAI, usa la app en reuniones con clientes

## Perfil completo de Bisonte

Ver `references/bisonte-empresa-perfil.md` — 6 líneas de servicio, 5 sucursales, sistemas Transoft + Sitrack, gerenta general como stakeholder principal (3-5 hs diarias lunes a lunes haciendo procesos Excel manuales).

Ver `references/bisonte-propuesta-roi-patron.md` — estructura validada de propuesta comercial, fórmula ROI con costo de oportunidad, reglas de alcance (no comprometer procesos no relevados, no mencionar dashboards no pedidos), impacto multi-sucursal en presupuesto, y patrón de scraping del sitio del cliente.
- **Gerenta Expreso Bisonte**: operativa, conocimiento tácito del cruce CDO↔PF
- **Mensaje demo**: "Mirá, este es el CDO crudo que te baja el sistema. Y este es el mismo CDO con la justificación que vos ponés a mano. La app te los muestra juntos para que vos toques solo lo que falta. Lo mismo con Pte Fact."
