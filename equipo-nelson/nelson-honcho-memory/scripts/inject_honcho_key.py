#!/usr/bin/env python3
"""
Extrae la OPENAI_API_KEY real del .hermes/.env y la inyecta en el docker-compose de Honcho.
Necesario porque el shell redacta las keys con *** al hacer echo/grep.

Uso: python3 inject_honcho_key.py
"""
import re

# Leer el .env binario para evitar redacción del shell
raw = open('/home/server/.hermes/.env', 'rb').read().decode('utf-8', errors='replace')

match = re.search(r'OPENAI_API_KEY=(sk-\S+)', raw)
if not match:
    print("ERROR: OPENAI_API_KEY no encontrada en .hermes/.env")
    exit(1)

key = match.group(1).strip()
print(f"Key encontrada: len={len(key)} {key[:8]}...{key[-4:]}")

# Leer docker-compose
dc_path = '/home/server/proyectos/honcho/docker-compose.yml'
with open(dc_path) as f:
    content = f.read()

# Verificar si ya tiene la key correcta
if f'LLM_OPENAI_API_KEY={key}' in content:
    print("Key ya inyectada correctamente.")
    exit(0)

# Remover cualquier LLM_OPENAI_API_KEY existente (truncada o placeholder)
content = re.sub(r'\s*- LLM_OPENAI_API_KEY=.*\n', '\n', content)
content = re.sub(r'\s*- EMBEDDING_MODEL_CONFIG__TRANSPORT=.*\n', '\n', content)
content = re.sub(r'\s*- EMBEDDING_MODEL_CONFIG__MODEL=.*\n', '\n', content)
content = re.sub(r'\s*- DERIVER_ENABLED=.*\n', '\n', content)
content = re.sub(r'\s*- AUTH_USE_AUTH=.*\n', '\n', content)

# Agregar después de CACHE_ENABLED
inject = (
    f"\n      - LLM_OPENAI_API_KEY={key}"
    f"\n      - EMBEDDING_MODEL_CONFIG__TRANSPORT=openai"
    f"\n      - EMBEDDING_MODEL_CONFIG__MODEL=text-embedding-3-small"
    f"\n      - DERIVER_ENABLED=true"
    f"\n      - AUTH_USE_AUTH=false"
)
content = content.replace(
    '      - CACHE_ENABLED=true',
    '      - CACHE_ENABLED=true' + inject
)

with open(dc_path, 'w') as f:
    f.write(content)

print("docker-compose actualizado con key real.")
print("Ahora recrear el container: docker compose stop api && docker compose rm -f api && docker compose up -d api")
