#!/usr/bin/env python3
"""
Spike: Power BI Public Embed - Extracción via Playwright
Intercepta las requests de red que hace el browser al cargar el embed
y captura los datos reales que Power BI devuelve al JS del reporte.
"""

import asyncio
import json
import os
import re
import base64

OUTPUT_DIR = os.path.expanduser('~/brainstorming/2026-05-19-powerbi-whatsapp-spike/output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

EMBED_URL = 'https://app.powerbi.com/view?r=eyJrIjoiM2Q4MjQ5ODctYzE5MS00MTAyLWI3YWEtMTUwYWMzNWVjZmQyIiwidCI6ImNiODg0ZGI1LTI0ODUtNGY5Yi05MzhlLTNlNjIxZjIyMjU3YiIsImMiOjR9'

async def capture_pbi_data():
    from playwright.async_api import async_playwright
    
    captured = {
        'requests': [],
        'responses': [],
        'models': None,
        'data_queries': [],
        'cluster': None,
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='es-AR',
        )
        
        page = await context.new_page()
        
        # Interceptar todas las requests
        async def on_request(request):
            url = request.url
            if any(x in url for x in ['analysis.windows.net', 'powerbi.com/public', 'querydata', 'modelsAndExploration', 'conceptualschema']):
                captured['requests'].append({
                    'url': url,
                    'method': request.method,
                    'headers': dict(request.headers),
                })
                # Detectar cluster
                match = re.search(r'https://([^/]+\.analysis\.windows\.net)', url)
                if match and not captured['cluster']:
                    captured['cluster'] = match.group(1)
                    print(f'  Cluster detectado: {captured["cluster"]}')
        
        # Interceptar responses
        async def on_response(response):
            url = response.url
            status = response.status
            
            if 'modelsAndExploration' in url or 'conceptualschema' in url:
                try:
                    body = await response.body()
                    data = json.loads(body)
                    captured['models'] = data
                    print(f'  ✅ Models capturado ({len(body)} bytes)')
                    with open(f'{OUTPUT_DIR}/models.json', 'wb') as f:
                        f.write(body)
                except Exception as e:
                    print(f'  Models error: {e}')
            
            elif 'querydata' in url:
                try:
                    body = await response.body()
                    data = json.loads(body)
                    captured['data_queries'].append({'url': url, 'data': data})
                    print(f'  ✅ QueryData capturado ({len(body)} bytes)')
                    idx = len(captured['data_queries'])
                    with open(f'{OUTPUT_DIR}/querydata_{idx}.json', 'wb') as f:
                        f.write(body)
                except Exception as e:
                    print(f'  QueryData error: {e}')
            
            elif 'analysis.windows.net' in url and status != 200:
                print(f'  ⚠️  {status} {url[:80]}')
        
        page.on('request', on_request)
        page.on('response', on_response)
        
        print(f'Cargando embed: {EMBED_URL[:80]}...')
        
        try:
            await page.goto(EMBED_URL, wait_until='networkidle', timeout=45000)
        except Exception as e:
            print(f'  Timeout/error en goto: {e}')
        
        # Esperar más tiempo para que carguen todos los datos de queries
        await asyncio.sleep(10)
        
        # Screenshot para ver qué renderizó
        screenshot_path = f'{OUTPUT_DIR}/pbi_screenshot.png'
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f'  Screenshot guardado: {screenshot_path}')
        
        # Capturar requests que hizo
        print(f'\nRequests a Power BI capturadas: {len(captured["requests"])}')
        for r in captured['requests']:
            print(f'  {r["method"]} {r["url"][:100]}')
        
        await browser.close()
    
    return captured


if __name__ == '__main__':
    print('=' * 55)
    print('🔍 Spike: Power BI via Playwright (Network Intercept)')
    print('=' * 55)
    
    result = asyncio.run(capture_pbi_data())
    
    print(f'\n📊 Resumen:')
    print(f'  Cluster: {result["cluster"]}')
    print(f'  Models capturado: {"✅" if result["models"] else "❌"}')
    print(f'  Data queries: {len(result["data_queries"])}')
    
    if result['models']:
        print('\n📋 Models keys:', list(result['models'].keys())[:5])
    
    if result['data_queries']:
        print('\n📋 Primer query data (preview):')
        first = result['data_queries'][0]['data']
        print(json.dumps(first, indent=2)[:500])
    
    print(f'\n📁 Archivos en {OUTPUT_DIR}:')
    for f in os.listdir(OUTPUT_DIR):
        size = os.path.getsize(f'{OUTPUT_DIR}/{f}')
        print(f'  {f} ({size} bytes)')
