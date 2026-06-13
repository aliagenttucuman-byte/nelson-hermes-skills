---
name: nelson-expreso-bisonte-poc
description: Levantar, verificar y mantener la PoC Expreso Bisonte en srv-ai. Backend FastAPI :9000, SPA proxy :9090, Next.js frontend :3000, túnel Cloudflare. Flujo Ejecutar CDO/PTE → Auditoría. Repo en GitHub aliagenttucuman-byte/expreso-bisonte-excel-poc.
category: nelson
---

# Expreso Bisonte PoC — Levantar y mantener

ESTADO VERIFICADO: 2026-06-08 funcionando end-to-end. Demo objetivo: mostrarle a la gerenta que el cruce CDO↔PF que ella hace a mano se puede ver lado a lado en la app (sistema vs trabajada).

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

## IMPORTANTE: comportamiento ante "levantame Expreso Bisonte"

- **TODO DE UNA SOLA VEZ** — sin preguntar, sin pasos intermedios, sin confirmaciones:
  1. Levantar backend :9000
  2. Levantar proxy SPA :9090
  3. Rearmar combinado (`rearmar_combinado.py`)
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

## PITFALL — document_cache path del combinado puede no existir

El script `rearmar_combinado.py` apunta a:
`/home/server/.hermes/document_cache/doc_59585daaffc8_CONTADO_PABLO_RUIZ.xlsx`
**Este archivo no siempre existe** — el document_cache se limpia entre sesiones.

Fallback verificado (jun 2026): el archivo con las 4 sheets está en:
`/home/server/brainstorming/2026-06-03-expreso-bisonte-diccionario-datos-pablo/entregables-xlsx/CONTADO_PABLO_RUIZ_origen.xlsx`

Sheets: `CDO SISTEMA`, `CDO TRABAJADA`, `PTE DE FACT SISTEMA`, `PF TRABAJADA` (en mayúsculas).
El script las renombra al mapeo correcto. Si rearmar_combinado.py falla por FileNotFoundError,
usar ese path directamente con el mapping:
```python
src = '/home/server/brainstorming/2026-06-03-expreso-bisonte-diccionario-datos-pablo/entregables-xlsx/CONTADO_PABLO_RUIZ_origen.xlsx'
mapping = {
    'CDO SISTEMA': 'CDO Sistema',
    'PTE DE FACT SISTEMA': 'PTE de Fact Sistema',
    'CDO TRABAJADA': 'CDO TRABAJADA',
    'PF TRABAJADA': 'PF TRABAJADA',
}
```

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

## PROHIBIDO

- Borrar `/tmp/excel-merger/expreso_bisonte_combinado.xlsx` — es el ÚNICO estado persistente
- Subir las 4 sheets como archivos individuales (rompe el flujo del frontend)
- Crear procedures (el front no los usa para "Ejecutar CDO/PTE")
- Llamar `/pipeline/static` o `/pipeline/compare-manual` desde curl antes que el usuario lo haga desde el frontend (los file_ids de salida se pierden del `_upload_registry`)
- Inventar tests, joins, plan/suggest — el flujo YA funciona como está
- Tocar el código del backend sin pedir permiso

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

## Contactos

- **Pablo**: COO AlegentAI + socio ForestAI, usa la app en reuniones con clientes
- **Gerenta Expreso Bisonte**: operativa, conocimiento tácito del cruce CDO↔PF
- **Mensaje demo**: "Mirá, este es el CDO crudo que te baja el sistema. Y este es el mismo CDO con la justificación que vos ponés a mano. La app te los muestra juntos para que vos toques solo lo que falta. Lo mismo con Pte Fact."
