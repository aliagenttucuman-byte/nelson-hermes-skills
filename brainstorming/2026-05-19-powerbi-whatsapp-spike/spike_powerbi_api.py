#!/usr/bin/env python3
"""
Spike: Power BI Public Embed → Datos → Reporte Visual
Técnica: API interna de Power BI para embeds públicos (sin Azure AD)

Flow:
1. Decodificar token del embed URL (base64 JSON)
2. Resolver cluster WABI via /public/routing/cluster/{tenantId}
3. Llamar /public/reports/{key}/modelsAndExploration para metadata
4. Llamar /public/reports/{key}/querydata para extraer datos DAX
5. Procesar → generar reporte matplotlib → WhatsApp
"""

import base64, json, ssl, re, os
import urllib.request, urllib.parse
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings
warnings.filterwarnings('ignore')

ctx = ssl._create_unverified_context()
OUTPUT_DIR = os.path.expanduser('~/brainstorming/2026-05-19-powerbi-whatsapp-spike/output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_APIM = 'https://wabi-brazil-south-b-redirect.analysis.windows.net'

def request_json(url, method='GET', data=None, headers=None):
    """Helper HTTP con manejo de errores."""
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
    }
    if headers:
        default_headers.update(headers)
    
    body = None
    if data:
        body = json.dumps(data).encode('utf-8')
        default_headers['Content-Type'] = 'application/json'
    
    req = urllib.request.Request(url, data=body, headers=default_headers, method=method)
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=20)
        content = resp.read().decode('utf-8', errors='replace')
        return json.loads(content), resp.status
    except urllib.error.HTTPError as e:
        body_err = e.read().decode('utf-8', errors='replace')
        print(f'  HTTP {e.code}: {body_err[:200]}')
        return None, e.code
    except Exception as e:
        print(f'  Error: {str(e)[:150]}')
        return None, 0


# ── PASO 1: Decodificar token del embed público ───────────────────────────────

def decode_embed_token(embed_url: str) -> dict:
    """Extrae y decodifica el token r=... de la URL de embed."""
    match = re.search(r'[?&]r=([^&]+)', embed_url)
    if not match:
        raise ValueError(f'No se encontró token r= en: {embed_url}')
    
    token_b64 = match.group(1)
    # Agregar padding
    token_b64 += '=' * (4 - len(token_b64) % 4)
    
    try:
        decoded = base64.b64decode(token_b64).decode('utf-8')
        data = json.loads(decoded)
        print(f'  Token decodificado:')
        print(f'    reportId: {data.get("reportId")}')
        print(f'    groupId:  {data.get("groupId")}')
        print(f'    type:     {data.get("type")}')
        return data
    except Exception as e:
        raise ValueError(f'Error decodificando token: {e}')


# ── PASO 2: Resolver cluster WABI ─────────────────────────────────────────────

def resolve_cluster(tenant_id: str, resource_key: str) -> str:
    """Encuentra el cluster WABI correcto para este tenant."""
    print(f'  Resolviendo cluster para tenantId={tenant_id[:8]}...')
    
    # La página de Power BI hace un GET a /public/routing/cluster/{tenantId}
    url = f'{BASE_APIM}/public/routing/cluster/{tenant_id}'
    data, status = request_json(url)
    
    if data and 'FixedClusterUri' in data:
        cluster = data['FixedClusterUri']
        print(f'  Cluster: {cluster}')
        return cluster
    
    # Si no hay routing, usar el default para Brasil Sur (común para Argentina)
    print(f'  Usando cluster default: {BASE_APIM}')
    return BASE_APIM


# ── PASO 3: Obtener metadata del reporte ─────────────────────────────────────

def get_report_models(cluster: str, resource_key: str) -> dict:
    """Obtiene el schema/modelo del reporte."""
    url = f'{cluster}/public/reports/{resource_key}/modelsAndExploration?preferReadOnlySession=True'
    print(f'  Obteniendo models: {url[:80]}...')
    
    data, status = request_json(url)
    return data


# ── PASO 4: Ejecutar query DAX ───────────────────────────────────────────────

def query_report_data(cluster: str, resource_key: str, model_id: str, dax_query: str) -> dict:
    """Ejecuta una query DAX en el dataset embebido."""
    url = f'{cluster}/public/reports/{resource_key}/querydata?synchronous=true'
    
    payload = {
        "version": "1.0.0",
        "queries": [{
            "Query": {
                "Commands": [{
                    "SemanticQueryDataShapeCommand": {
                        "Query": {
                            "Version": 2,
                            "From": [],
                            "Select": []
                        }
                    }
                }]
            },
            "QueryId": "",
            "ApplicationContext": {
                "DatasetId": model_id,
                "Sources": []
            }
        }],
        "cancelQueries": [],
        "modelId": int(model_id) if model_id and model_id.isdigit() else 0
    }
    
    print(f'  Ejecutando query en: {url[:80]}...')
    data, status = request_json(url, method='POST', data=payload)
    return data


# ── PASO 5: Pipeline completo ─────────────────────────────────────────────────

def run_spike(embed_url: str):
    print('\n' + '='*55)
    print('🔍 Spike: Power BI Public Embed API')
    print('='*55)
    
    # 1. Decode token
    print('\n[1] Decodificando token...')
    token_data = decode_embed_token(embed_url)
    
    report_id = token_data.get('reportId') or token_data.get('k')
    group_id = token_data.get('groupId')
    resource_key = token_data.get('key') or token_data.get('k')
    tenant_id = token_data.get('t', group_id or '')
    
    if not resource_key:
        print('  ⚠️  No hay key en el token — este embed usa autenticación AAD')
        return None
    
    print(f'  resource_key: {resource_key[:30]}...')
    
    # 2. Resolver cluster
    print('\n[2] Resolviendo cluster WABI...')
    cluster = resolve_cluster(group_id or '', resource_key)
    
    # 3. Get models
    print('\n[3] Obteniendo metadata del reporte...')
    models = get_report_models(cluster, resource_key)
    
    if models:
        print(f'  Keys: {list(models.keys())[:5]}')
        # Guardar para inspección
        with open(f'{OUTPUT_DIR}/models_response.json', 'w') as f:
            json.dump(models, f, indent=2)
        print(f'  Guardado en {OUTPUT_DIR}/models_response.json')
        
        # Extraer model ID
        model_id = None
        if 'models' in models and models['models']:
            model_id = str(models['models'][0].get('id', ''))
            print(f'  modelId: {model_id}')
        elif 'modelId' in models:
            model_id = str(models['modelId'])
    else:
        print('  ❌ No se pudo obtener metadata')
        model_id = None
    
    # 4. Query data (si tenemos model_id)
    if model_id:
        print('\n[4] Ejecutando query de datos...')
        result = query_report_data(cluster, resource_key, model_id, '')
        if result:
            with open(f'{OUTPUT_DIR}/query_response.json', 'w') as f:
                json.dump(result, f, indent=2)
            print(f'  Respuesta guardada en {OUTPUT_DIR}/query_response.json')
    
    print('\n' + '='*55)
    print('✅ Spike completado — revisar JSONs en output/')
    return models


# ── URLs de embed público para testear ───────────────────────────────────────

EMBED_URLS_TEST = [
    # Demo de Microsoft (si existe público)
    'https://app.powerbi.com/view?r=eyJrIjoiMGJmZGVmNzUtOTMxOS00NTQxLWEzODQtMDFmYTRmMzhhZmExIiwidCI6IjcyZjk4OGJmLTg2ZjEtNDFhZi05MWFiLTJkN2NkMDExZGI0NyIsImMiOjV9',
]


if __name__ == '__main__':
    import sys
    
    url = sys.argv[1] if len(sys.argv) > 1 else EMBED_URLS_TEST[0]
    print(f'URL a testear: {url[:80]}...')
    
    result = run_spike(url)
    
    if result is None:
        print('\n⚠️  Este embed requiere AAD. Ver alternativas en el README.')
    else:
        print('\n📁 Archivos generados:')
        for f in os.listdir(OUTPUT_DIR):
            print(f'  {OUTPUT_DIR}/{f}')
