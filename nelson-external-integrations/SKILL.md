---
name: nelson-external-integrations
description: "Patrones para integrar APIs y servicios externos en el equipo Nelson. Fallback strategy, rate limits, red Docker vs host, y spike obligatorio antes de integrar."
version: 1.0.0
author: Equipo Nelson (Tony + JARVIS)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [integrations, external-apis, fallback, docker, networking, nelson]
    related_skills: [nelson-project-constitution, spike, nelson-observability, nelson-senior-practices]
---

# Nelson External Integrations

Patrones para cuando el equipo integra servicios externos: buscadores, APIs de terceros, scraping, LLMs cloud, etc.

**Regla de oro:** Antes de integrar, hacer un spike de 15 minutos en el entorno real.

---

## 1. Spike obligatorio antes de integrar

Antes de que cualquier agente incorpore una librería externa al código base:

```
1. Identificar el entorno donde corre (host o Docker)
2. Instalar la lib en ese entorno
3. Hacer UNA llamada real con datos reales
4. Verificar que devuelve datos útiles (no solo "no crashea")
5. Si pasa → integrar. Si falla → reportar a Tony antes de continuar.
```

**Tiempo máximo del spike:** 15 minutos. Si tarda más, algo está mal.

---

## 2. Docker vs Host para llamadas externas

| Situación | Solución |
|-----------|----------|
| Backend llama a APIs externas (buscadores, scraping, etc.) | Correr en **host** con venv propio |
| Backend solo habla con DB/Redis/otros containers | Docker normal |
| Necesita ambos | `network_mode: host` en docker-compose |

**Por qué:** Las IPs de rangos Docker están bloqueadas por rate limits de muchos servicios (DuckDuckGo, Google Search, etc.). Desde el host con IP real no hay problema.

```yaml
# docker-compose.yml - Si el servicio hace llamadas externas
backend:
  network_mode: host  # ← Usar IP real del host
```

O mejor aún, correr el backend como proceso directo del host:

```bash
# Crear venv del host (fuera de Docker)
python3 -m venv ~/venvs/proyecto-backend
source ~/venvs/proyecto-backend/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --port 8004
```

---

## 3. Patrón de fallback para servicios de búsqueda

Cuando el proyecto necesita búsquedas web, definir proveedores en orden de prioridad:

```python
# app/services/search.py
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class SearchResult:
    title: str
    url: str
    snippet: str

async def search_web(query: str, max_results: int = 5) -> List[SearchResult]:
    """Búsqueda con fallback automático entre proveedores.
    
    Orden: DuckDuckGo → Brave Search → Wikipedia
    """
    providers = [
        _search_duckduckgo,
        _search_brave,
        _search_wikipedia,
    ]
    
    for provider in providers:
        try:
            results = await provider(query, max_results)
            if results:
                logger.info(f"Search OK via {provider.__name__}")
                return results
        except Exception as e:
            logger.warning(f"Search failed via {provider.__name__}: {e}")
            continue
    
    logger.error("All search providers failed")
    return []
```

**Proveedores disponibles (en orden de preferencia):**

| Proveedor | Lib | Costo | Rate Limit | Notas |
|-----------|-----|-------|------------|-------|
| DuckDuckGo | `duckduckgo-search` (ddgs) | Gratis | Bloquea si IP es de DC | Funciona bien desde host |
| Brave Search | API REST | 2000 req/mes gratis | Generoso | Requiere API key |
| Serper.dev | API REST | 2500 búsquedas gratis | Generoso | Requiere API key |
| SearXNG local | Docker | Gratis | Sin límite | Setup propio |
| Wikipedia | `wikipedia` lib | Gratis | Sin límite | Solo Wikipedia |

---

## 4. Logging de integraciones externas

Todo llamado a servicio externo DEBE loguearse:

```python
import time
import logging

logger = logging.getLogger(__name__)

async def call_external_service(url: str, payload: dict) -> dict:
    start = time.time()
    try:
        response = await client.post(url, json=payload)
        elapsed = time.time() - start
        logger.info(
            "external_call",
            extra={
                "url": url,
                "status": response.status_code,
                "elapsed_ms": round(elapsed * 1000),
            }
        )
        return response.json()
    except Exception as e:
        elapsed = time.time() - start
        logger.error(
            "external_call_failed",
            extra={
                "url": url,
                "error": str(e),
                "elapsed_ms": round(elapsed * 1000),
            }
        )
        raise
```

---

## 5. Demo rápida con Cloudflare Tunnel

Para mostrar un proyecto sin deploy real (I+D+I):

```bash
# Instalar cloudflared si no está
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Exponer frontend y backend
cloudflared tunnel --url http://localhost:3000  # Frontend
cloudflared tunnel --url http://localhost:8000  # Backend
```

Genera URLs públicas temporales (duran hasta que se cierra el proceso). Ideal para demos sin infraestructura.

**Regla:** Solo para demos. Nunca en producción.

---

## 6. Checklist de integración (antes de mergear)

- [ ] Spike validado en entorno real (host o Docker)
- [ ] Proveedor principal funciona desde el entorno target
- [ ] Fallback implementado si el servicio puede fallar
- [ ] Logging de cada llamada externa (éxito y error)
- [ ] Variables de entorno para API keys (nunca hardcodeadas)
- [ ] Timeout configurado (nunca esperar infinito)
- [ ] Rate limit documentado en CONSTITUTION o README

---

## 7. Datos abiertos de energía Argentina (para spikes tipo YPF)

Cuando se necesita un spike con datos reales de energía sin depender de credenciales corporativas, usar la API pública de datos.gob.ar. Tiene datasets oficiales de la Secretaría de Energía de Argentina con datos de producción de petróleo, gas, electricidad, y más.

**API base:** `https://www.datos.gob.ar/api/3/action/`

```python
import urllib.request, json

# Buscar datasets
resp = urllib.request.urlopen("https://www.datos.gob.ar/api/3/action/package_search?q=produccion+petroleo+gas&rows=5")
data = json.loads(resp.read())
for r in data["result"]["results"]:
    print(r["title"], "|", r["name"])

# Ver recursos de un dataset
resp = urllib.request.urlopen("https://www.datos.gob.ar/api/3/action/package_show?id=energia-produccion-petroleo-gas-sesco")
pkg = json.loads(resp.read())["result"]
for r in pkg["resources"]:
    if r.get("format") == "CSV":
        print(r["name"], "|", r["url"])
```

**Datasets clave para contexto YPF:**
- `energia-produccion-petroleo-gas-sesco` → producción petróleo/gas por empresa, yacimiento, cuenca, provincia. Incluye YPF. Series diarias, mensuales, históricas.
- `energia-generacion-electrica---centrales-generacion` → generación eléctrica por central
- `energia-reservas-petroleo-gas` → reservas certificadas por empresa

**CSV directo de producción de petróleo por empresa (el más útil para YPF):**
```
https://datos.energia.gob.ar/dataset/590d1284.../download/produccin-petrleo-sesco-tight-y-shale-captulo-iv-por-empresa.csv
```

**Flow completo PoC: datos abiertos → LLM → WhatsApp:**
1. Descargar CSV desde datos.gob.ar
2. Filtrar últimos N meses, calcular KPIs (producción YPF, market share, variación)
3. Pasar datos + contexto al LLM → interpretación en lenguaje natural
4. Generar imagen del reporte con matplotlib/reportlab
5. Enviar imagen + texto analítico por WhatsApp Gateway

Este es el patrón para la PoC antes de conectar al PowerBI real de YPF.

---

## 8. PowerBI → WhatsApp (integración corporativa YPF)

**Contexto:** Nelson lidera I+D+I en YPF. Los tableros PowerBI pueden exponerse como URLs públicas o autenticadas. La PoC consiste en acceder a esos tableros, extraer KPIs, y distribuir reportes por WhatsApp.

**Dos escenarios técnicos:**

### Escenario A: URL pública (sin login) — Técnica WABI Network Intercept ✅ VALIDADA

**Técnica correcta:** NO es screenshot del DOM. Power BI público usa la API interna WABI (Windows Azure BI) para transferir datos al JS. Playwright puede interceptar esas llamadas y capturar los datos reales en formato DSR (comprimido interno de PBI).

**Flow completo validado:**
1. Decodificar el token base64 de la URL `?r=BASE64` → obtener `reportId`, `groupId`, `key`, `tenantId`
2. Lanzar Playwright headless, interceptar respuestas de `analysis.windows.net`
3. Capturar `/public/reports/{key}/modelsAndExploration` → schema de entidades y columnas
4. Capturar `/public/reports/querydata` (múltiples POSTs) → datos en formato DSR
5. Parsear DSR con Python → DataFrames de pandas → procesar KPIs
6. Generar reporte matplotlib → enviar por WhatsApp

```python
import asyncio, json, os

async def capture_pbi_data(embed_url: str, output_dir: str):
    from playwright.async_api import async_playwright
    
    data_files = []
    query_count = [0]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120',
            locale='es-AR',
        )
        page = await context.new_page()
        
        async def on_response(response):
            if 'querydata' in response.url:
                try:
                    body = await response.body()
                    query_count[0] += 1
                    fpath = f'{output_dir}/qd_{query_count[0]}.json'
                    with open(fpath, 'wb') as f:
                        f.write(body)
                    data_files.append(fpath)
                except: pass
        
        page.on('response', on_response)
        
        try:
            await page.goto(embed_url, wait_until='networkidle', timeout=45000)
        except: pass
        
        await asyncio.sleep(8)  # esperar queries lazy
        await browser.close()
    
    return data_files
```

**Parser DSR (formato comprimido interno de Power BI):**
```python
def parse_dsr(dsr_data: dict, col_names: list) -> pd.DataFrame:
    """Convierte formato DSR comprimido → DataFrame."""
    ds = dsr_data.get('DS', [])
    if not ds: return pd.DataFrame()
    ph = ds[0].get('PH', [])
    if not ph: return pd.DataFrame()
    dm = ph[0].get('DM0', [])
    if not dm: return pd.DataFrame()
    
    rows, last_values = [], [None] * len(col_names)
    for item in dm:
        c = item.get('C', [])
        r = item.get('R', 0)  # bitmask: bit i=1 → repetir valor anterior de col i
        
        # PITFALL: algunos items tienen el valor en M0, M1... no en C
        if not c:
            c = [item[f'M{i}'] for i in range(len(col_names)) if f'M{i}' in item]
        
        current = list(last_values)
        ci = 0
        for i in range(len(col_names)):
            if r and (r >> i) & 1: pass  # repetir anterior
            elif ci < len(c):
                current[i] = c[ci]; ci += 1
        
        last_values = current
        rows.append(dict(zip(col_names, current)))
    
    return pd.DataFrame(rows)
```

**Cargar querydata capturado:**
```python
def load_query_files(data_files: list) -> list:
    datasets = []
    for fpath in sorted(data_files):
        with open(fpath) as f:
            d = json.load(f)
        results = d.get('results', [])
        if not results: continue
        result_data = results[0].get('result', {}).get('data', {})
        if not result_data: continue
        descriptor = result_data.get('descriptor', {})
        selects = descriptor.get('Select', [])
        col_names = [s.get('Name', f'col_{i}') for i, s in enumerate(selects)]
        dsr = result_data.get('dsr', {})
        df = parse_dsr(dsr, col_names)
        if not df.empty:
            datasets.append({'columns': col_names, 'df': df})
    return datasets
```

- Pro: datos reales (no screenshot), parseable con pandas, sin Azure AD ni credenciales
- Con: depende de que el embed sea público y de la estructura interna de Power BI (puede cambiar)
- **Playwright ya instalado en el servidor:** `python3 -m playwright --version` → 1.59.0, chromium en `~/.cache/ms-playwright/`
- **Referencia técnica completa:** `references/powerbi-public-embed-wabi.md`

### Escenario B: URL con login corporativo (cuenta YPF + Azure AD)
- Registrar App en Azure AD del tenant de YPF con permisos: `Report.Read.All`, `Dataset.Read.All`
- Autenticar con `msal` (Microsoft Authentication Library)
- Usar Power BI REST API v2 para listar reportes, exportar páginas (PDF/PNG), leer datasets
- Pro: oficial, robusto, programático
- Con: requiere acceso al Azure Portal del tenant YPF + aprobación de permisos

```python
import msal, requests

# 1. Obtener token
app = msal.ConfidentialClientApplication(
    client_id=CLIENT_ID,
    client_credential=CLIENT_SECRET,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}"
)
token = app.acquire_token_for_client(scopes=["https://analysis.windows.net/powerbi/api/.default"])
access_token = token["access_token"]

# 2. Listar reportes
headers = {"Authorization": f"Bearer {access_token}"}
reports = requests.get("https://api.powerbi.com/v1.0/myorg/reports", headers=headers).json()

# 3. Exportar página como PNG
export_url = f"https://api.powerbi.com/v1.0/myorg/reports/{REPORT_ID}/ExportTo"
body = {"format": "PNG", "powerBIReportConfiguration": {"pages": [{"pageName": "ReportSection"}]}}
# Export es async — necesita polling en /exports/{exportId}
```

**Pregunta clave antes de arrancar el spike:** ¿Las URLs son públicas (no requieren login) o requieren cuenta corporativa YPF? Define qué escenario usar.

**Criterio de éxito de la PoC:**
- [ ] Acceder al tablero (público o autenticado)
- [ ] Extraer al menos 3 KPIs o una imagen del tablero
- [ ] Enviarlo por WhatsApp a un número de prueba

**References:** `references/powerbi-whatsapp-poc.md` — diseño inicial de la PoC

---

## Pitfalls

- **DuckDuckGo desde Docker:** Bloquea por IP de datacenter. Correr desde host.
- **ddgs vs duckduckgo_search:** La lib cambió de nombre. Usar `from duckduckgo_search import DDGS` y `ddgs.text()`. Los campos son `href` y `body`, no `url` y `snippet`.
- **SearXNG con bot detection:** Incluso con `pass_ip=true` puede devolver 403. Configurar `limiter.toml` para desactivarlo completamente.
- **Brave Search gratis:** 2000 req/mes. Suficiente para I+D+I, no para producción con tráfico real.
- **Timeouts:** Siempre setear `timeout=10` o similar. Sin timeout, una API lenta bloquea todo el worker.
- **Sync repo: agregar skill nueva a sync-to-repo.sh:** Cada vez que se crea una skill nueva (`skill_manage action=create`), agregarla manualmente al array `SKILLS=()` en `/home/server/repos/nelson-hermes-skills/sync-to-repo.sh` antes de hacer el sync. Si se olvida, la skill no se pushea al repo.
- **Token GitHub expira:** El token personal de GitHub (`ghp_...`) tiene vida limitada. Cuando `gh auth status` muestra "The token in default is invalid", re-autenticar con `gh auth login -h github.com -p https --with-token < ~/secrets/github_token.txt`. El token nuevo se genera en https://github.com/settings/tokens/new (scope: `repo` completo). Para push sin terminal interactiva: `git push "https://$(gh auth token)@github.com/USER/REPO.git" main`. Guardar siempre el token nuevo en `~/secrets/github_token.txt` (chmod 600).
