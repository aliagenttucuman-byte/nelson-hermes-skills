# OpenWA / WAHA — WhatsApp API Gateway Open Source
## Investigación para PoC: Datos Energéticos Argentina → Reporte Imagen → WhatsApp

Fecha: 2026-05-19
Equipo: I+D+I Consultora de Software Argentina
Stack base: Python/FastAPI + React

---

## ÍNDICE

1. Qué es OpenWA / WAHA y por qué usarlo
2. Arquitectura del sistema (stack completo)
3. Guía de instalación rápida con Docker
4. Endpoints REST clave
5. Configuración de webhooks
6. Comparativa OpenWA/WAHA vs Baileys (directo)
7. Plan de implementación para la PoC
8. Checklist de tareas para ejecutar mañana

---

## 1. QUÉ ES OPENWA / WAHA Y POR QUÉ USARLO

### El ecosistema "OpenWA"

El término "OpenWA" engloba a una familia de proyectos open source que exponen WhatsApp
(versión Web/Multi-Device) como una API REST, sin depender de la API oficial de Meta
(que requiere aprobación comercial, cuesta dinero y tiene restricciones de plantilla).

El proyecto activo más relevante que cumple la descripción buscada es:

  WAHA — WhatsApp HTTP API
  Repositorio: https://github.com/devlikeapro/waha
  Stars: ~3.500 (mayo 2026)
  Creado: 2023, activo en 2024-2025-2026
  Stack: NestJS + TypeScript + React Dashboard + PostgreSQL/SQLite + Redis
  Licencia: MIT (core) / Commercial (Plus/Pro features)

Otros proyectos relacionados del ecosistema:
  - open-wa/wa-automate (deprecated, fue el "OpenWA" original, basado en Puppeteer)
  - WPPConnect/WPPConnect-Server (NestJS, similar propósito)
  - chrishubert/whatsapp-web-api (Express + whatsapp-web.js)

### Por qué WAHA para esta PoC

RAZONES TÉCNICAS:
  - API REST con Swagger UI integrado (documentación auto-generada)
  - Sin necesidad de código Node.js: se consume desde Python/FastAPI con requests
  - Docker-first: levanta en minutos con docker-compose
  - Soporte multi-sesión (múltiples cuentas WhatsApp simultáneas)
  - Webhooks para recibir mensajes entrantes
  - Envío de imágenes, documentos, audio, video, stickers, localización
  - QR code vía API o dashboard web para vincular el teléfono

RAZONES DE NEGOCIO:
  - Open source, sin costo de API oficial de Meta
  - No requiere número de teléfono empresarial ni aprobación
  - Ideal para PoCs, proyectos internos, demos
  - Comunidad activa con issues respondidos

CONSIDERACIÓN IMPORTANTE:
  Usar WhatsApp sin la API oficial viola los Términos de Servicio de Meta.
  Para una PoC/demo interna o proyecto de investigación el riesgo es bajo
  (posible ban del número de prueba, no hay consecuencias legales directas).
  Para producción a escala, evaluar la API oficial de WhatsApp Business.

---

## 2. ARQUITECTURA DEL SISTEMA (STACK COMPLETO)

### Stack de WAHA

  Capa             | Tecnología
  -----------------|------------------------------------------
  Backend API      | NestJS 10 + TypeScript
  Engine WA        | Baileys (WAHA Core) o whatsapp-web.js (WAHA Plus)
  Dashboard UI     | React + Material UI (puerto 3000)
  Base de datos    | SQLite (dev) / PostgreSQL (prod)
  Cache/Sessions   | Redis 7
  Containerización | Docker + Docker Compose
  Docs API         | Swagger UI (OpenAPI 3.0)
  Proxy opcional   | Nginx / Traefik

### Diagrama de arquitectura

  ┌─────────────────────────────────────────────────────────┐
  │                    INTERNET                             │
  │                                                         │
  │   WhatsApp Servers ←──────────────────────────────┐    │
  └───────────────────────────────────────────────────│────┘
                                                       │
  ┌─────────────────────────────────────────────────────────┐
  │                    TU SERVIDOR / VPS                    │
  │                                                         │
  │  ┌──────────────┐    ┌──────────────┐                  │
  │  │  WAHA API    │    │  Dashboard   │                   │
  │  │  NestJS      │    │  React UI    │                   │
  │  │  :3000       │    │  :3001       │                   │
  │  └──────┬───────┘    └──────────────┘                  │
  │         │                                               │
  │  ┌──────▼───────┐    ┌──────────────┐                  │
  │  │  Baileys /   │    │  PostgreSQL  │                   │
  │  │  WA Engine   │    │  :5432       │                   │
  │  └──────────────┘    └──────────────┘                  │
  │                                                         │
  │  ┌──────────────┐                                       │
  │  │  Redis       │                                       │
  │  │  :6379       │                                       │
  │  └──────────────┘                                       │
  │                                                         │
  │  ┌──────────────────────────────────────────────┐      │
  │  │  TU APP (FastAPI/Python)                      │      │
  │  │  - Consume API energía datos.gob.ar           │      │
  │  │  - Procesa con LLM                            │      │
  │  │  - Genera imagen reporte (Pillow/matplotlib)  │      │
  │  │  - Llama WAHA REST API → envía imagen WA     │      │
  │  └──────────────────────────────────────────────┘      │
  └─────────────────────────────────────────────────────────┘

### Engines disponibles en WAHA

  Engine         | Proyecto base      | Multi-device | Estabilidad
  ---------------|--------------------|--------------|------------
  NOWEB (core)   | Baileys            | Sí           | Alta
  WEBJS (plus)   | whatsapp-web.js    | Sí           | Media-Alta
  VENOM (plus)   | venom-bot          | Parcial      | Media

Para la PoC: usar NOWEB (Baileys) — es el default en WAHA Core gratuito.

---

## 3. GUÍA DE INSTALACIÓN RÁPIDA CON DOCKER

### Prerequisitos

  - Docker >= 24.0
  - Docker Compose >= 2.20
  - Puerto 3000 libre (API) y 3001 libre (Dashboard)
  - Número de WhatsApp para vincular (puede ser el tuyo personal para la PoC)

### Instalación en 4 pasos

PASO 1: Clonar o crear el directorio del proyecto

  mkdir -p ~/waha-poc && cd ~/waha-poc

PASO 2: Crear el docker-compose.yml (ver archivo adjunto en este directorio)

PASO 3: Levantar los servicios

  docker compose up -d

PASO 4: Vincular WhatsApp (escanear QR)

  Opción A - vía API (curl):
    curl -X POST http://localhost:3000/api/sessions \
      -H "Content-Type: application/json" \
      -d '{"name": "default"}'

    # Obtener QR como imagen PNG
    curl http://localhost:3000/api/default/auth/qr.png --output qr.png
    # Abrir qr.png y escanearlo con tu WhatsApp

  Opción B - vía Dashboard:
    Abrir http://localhost:3001 en el navegador
    Ir a Sessions → Create → Scan QR

### Verificar que funciona

  # Enviar mensaje de prueba
  curl -X POST http://localhost:3000/api/sendText \
    -H "Content-Type: application/json" \
    -H "X-Api-Key: tu-api-key-aqui" \
    -d '{
      "chatId": "5491112345678@c.us",
      "text": "Hola desde WAHA PoC!"
    }'

  Formato del chatId: {código_país}{número}@c.us
  Argentina: 54 + 9 + área + número → "5491167890123@c.us"

### Variables de entorno importantes

  WHATSAPP_API_KEY        → API key para autenticar requests (requerida en prod)
  WHATSAPP_DEFAULT_ENGINE → NOWEB | WEBJS | VENOM (default: NOWEB)
  DATABASE_URL            → postgres://user:pass@host:5432/db
  REDIS_URL               → redis://localhost:6379
  WHATSAPP_FILES_FOLDER   → /tmp/whatsapp-files (almacenamiento de media)

---

## 4. ENDPOINTS REST CLAVE

Base URL: http://localhost:3000/api
Autenticación: Header X-Api-Key: {tu-api-key}
Docs interactivos: http://localhost:3000/

### 4.1 Gestión de sesiones

  # Crear sesión
  POST /api/sessions
  Body: { "name": "mi-sesion", "config": { "webhooks": [...] } }

  # Listar sesiones
  GET /api/sessions
  Response: [{ "name": "default", "status": "WORKING", "me": {...} }]

  # Obtener QR para escanear
  GET /api/{session}/auth/qr
  Response: { "value": "data:image/png;base64,..." }

  # QR como imagen PNG directa
  GET /api/{session}/auth/qr.png

  # Estado de sesión
  GET /api/{session}/me
  Response: { "id": "5491167890123@c.us", "pushName": "Tu Nombre" }

  # Detener sesión
  DELETE /api/sessions/{session}

### 4.2 Enviar mensajes de texto

  POST /api/sendText
  Headers: Content-Type: application/json, X-Api-Key: {key}
  Body:
  {
    "chatId": "5491167890123@c.us",
    "text": "Hola mundo",
    "session": "default"
  }

  Response:
  {
    "id": "BAE5F0A0B9F0A0B9",
    "timestamp": 1716098400
  }

  Con formato (negrita, cursiva):
  {
    "chatId": "5491167890123@c.us",
    "text": "*Reporte Energético* 🔋\nGeneración: _1.234 MW_\nFecha: 2026-05-19",
    "session": "default"
  }

### 4.3 Enviar imagen

  POST /api/sendImage
  Headers: Content-Type: application/json, X-Api-Key: {key}
  Body:
  {
    "chatId": "5491167890123@c.us",
    "caption": "Reporte Energético Argentina - Mayo 2026",
    "file": {
      "mimetype": "image/png",
      "filename": "reporte-energia.png",
      "data": "BASE64_STRING_AQUI"
    },
    "session": "default"
  }

  Alternativa con URL pública:
  {
    "chatId": "5491167890123@c.us",
    "caption": "Reporte Energético",
    "file": {
      "url": "https://tu-servidor.com/reportes/reporte-2026-05-19.png"
    },
    "session": "default"
  }

  Cómo generar el base64 en Python:
    import base64
    with open("reporte.png", "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    # usar encoded como valor de "data"

### 4.4 Enviar documento/PDF

  POST /api/sendFile
  Headers: Content-Type: application/json, X-Api-Key: {key}
  Body:
  {
    "chatId": "5491167890123@c.us",
    "caption": "Reporte completo en PDF",
    "file": {
      "mimetype": "application/pdf",
      "filename": "reporte-energia-mayo2026.pdf",
      "data": "BASE64_DEL_PDF"
    },
    "session": "default"
  }

### 4.5 Enviar a múltiples contactos (broadcast)

  No hay endpoint nativo de broadcast. Implementar loop en Python:

    import httpx
    import asyncio

    WAHA_URL = "http://localhost:3000/api"
    API_KEY = "tu-key"
    CONTACTS = [
      "5491167890123@c.us",
      "5491198765432@c.us",
      "5491145678901@c.us"
    ]

    async def send_report_to_all(image_base64: str, caption: str):
        async with httpx.AsyncClient() as client:
            for contact in CONTACTS:
                response = await client.post(
                    f"{WAHA_URL}/sendImage",
                    headers={"X-Api-Key": API_KEY},
                    json={
                        "chatId": contact,
                        "caption": caption,
                        "file": {
                            "mimetype": "image/png",
                            "filename": "reporte.png",
                            "data": image_base64
                        },
                        "session": "default"
                    }
                )
                print(f"Enviado a {contact}: {response.status_code}")
                await asyncio.sleep(2)  # respetar rate limiting

### 4.6 Enviar mensaje de voz (audio)

  POST /api/sendVoice
  Body:
  {
    "chatId": "5491167890123@c.us",
    "file": {
      "mimetype": "audio/ogg; codecs=opus",
      "data": "BASE64_AUDIO_OGG"
    },
    "session": "default"
  }

### 4.7 Obtener chats y contactos

  GET /api/{session}/chats
  GET /api/{session}/contacts
  GET /api/{session}/contacts/{contactId}
  GET /api/{session}/messages?chatId=XXXX@c.us&limit=20

---

## 5. CONFIGURACIÓN DE WEBHOOKS

Los webhooks permiten que WAHA notifique a tu app cuando llegan mensajes,
cambios de estado, etc. Esencial para chatbots o flujos bidireccionales.

### 5.1 Configurar webhook al crear sesión

  POST /api/sessions
  Body:
  {
    "name": "default",
    "config": {
      "webhooks": [
        {
          "url": "https://tu-app.com/webhook/whatsapp",
          "events": ["message", "message.reaction", "session.status"],
          "hmac": {
            "key": "tu-clave-secreta-hmac"
          }
        }
      ]
    }
  }

### 5.2 Agregar webhook a sesión existente

  POST /api/{session}/webhooks
  Body:
  {
    "url": "https://tu-app.com/webhook/whatsapp",
    "events": ["message", "message.ack", "session.status"]
  }

  Listar webhooks configurados:
  GET /api/{session}/webhooks

### 5.3 Eventos disponibles

  Evento              | Descripción
  --------------------|------------------------------------------
  message             | Mensaje entrante recibido
  message.any         | Cualquier mensaje (enviado o recibido)
  message.reaction    | Reacción a un mensaje
  message.ack         | Confirmación de entrega/lectura
  session.status      | Cambio de estado de sesión (QR, conectado, etc.)
  call                | Llamada entrante
  group.join          | Alguien se unió a un grupo
  group.leave         | Alguien salió de un grupo
  presence.update     | Estado de presencia (escribiendo...)

### 5.4 Estructura del payload de webhook (mensaje entrante)

  {
    "event": "message",
    "session": "default",
    "payload": {
      "id": "BAE5F0A0B9",
      "timestamp": 1716098400,
      "from": "5491167890123@c.us",
      "fromMe": false,
      "body": "Hola! Quiero el reporte de hoy",
      "hasMedia": false,
      "ack": 1,
      "_data": { ... }
    }
  }

### 5.5 Endpoint FastAPI para recibir webhooks

  from fastapi import FastAPI, Request, HTTPException
  import hmac, hashlib

  app = FastAPI()
  WEBHOOK_SECRET = "tu-clave-secreta-hmac"

  @app.post("/webhook/whatsapp")
  async def whatsapp_webhook(request: Request):
      # Verificar firma HMAC
      body = await request.body()
      signature = request.headers.get("X-Webhook-Hmac-Sha512", "")
      expected = hmac.new(
          WEBHOOK_SECRET.encode(),
          body,
          hashlib.sha512
      ).hexdigest()

      if not hmac.compare_digest(signature, expected):
          raise HTTPException(status_code=401, detail="Invalid signature")

      data = await request.json()
      event = data.get("event")

      if event == "message" and not data["payload"]["fromMe"]:
          sender = data["payload"]["from"]
          text = data["payload"]["body"]
          # Procesar mensaje y responder
          await process_incoming_message(sender, text)

      return {"status": "ok"}

---

## 6. COMPARATIVA WAHA/OpenWA vs BAILEYS (DIRECTO)

### ¿Qué es Baileys?
Baileys es la librería Node.js de bajo nivel que implementa el protocolo
WhatsApp Multi-Device. WAHA usa Baileys internamente en su engine NOWEB.

  Característica          | WAHA (sobre Baileys)     | Baileys directo
  ------------------------|--------------------------|---------------------------
  Lenguaje               | Any (REST API)           | Node.js / TypeScript
  Curva de aprendizaje   | Baja                     | Alta
  Integración Python     | Trivial (httpx/requests) | Imposible directo
  Setup inicial          | docker-compose up -d     | npm install + código TS
  Dashboard web          | Incluido                 | No existe
  Multi-sesión           | Nativo en API            | Manual (código propio)
  Webhooks               | Configuración JSON       | Código Node.js
  Documentación API      | Swagger UI auto          | Leer el código fuente
  Persistencia sesiones  | PostgreSQL/SQLite/Redis  | Manual (archivos locales)
  Mantenimiento          | Comunidad activa         | Comunidad activa (base)
  Control bajo nivel     | Limitado                 | Total
  Rate limiting          | Manejado internamente    | Manual
  Reconexión automática  | Sí                       | Manual (evento de reconexión)
  Envío de media         | POST multipart/base64    | Buffer + método JS
  Costo                  | Gratis (core)            | Gratis (librería)
  Ideal para            | PoC, microservicio REST  | Chatbot full Node.js

### Veredicto para este proyecto

  Para una consultora con stack Python/FastAPI → WAHA es la elección correcta.
  
  No tiene sentido escribir un microservicio Node.js/TypeScript solo para
  interactuar con Baileys cuando WAHA ya expone todo como REST y el equipo
  puede consumirlo desde Python con 5 líneas de código.

  Baileys directo tiene sentido si:
  - Tu stack YA ES Node.js/TypeScript
  - Necesitás control muy fino del protocolo WA
  - Querés customizar profundamente el comportamiento

---

## 7. PLAN DE IMPLEMENTACIÓN PARA LA PoC

### Descripción del flujo completo

  [CRON/Trigger] → [FastAPI: consume datos.gob.ar] → [LLM: genera análisis]
       → [Python: genera imagen reporte] → [WAHA REST: envía imagen WA]
       → [Lista de contactos WhatsApp]

### Componentes a desarrollar

COMPONENTE 1: Data Fetcher (Python)
  - Endpoint: https://datos.gob.ar/api/3/action/datastore_search
  - Dataset objetivo: generación eléctrica por fuente (CAMMESA)
    Resource ID: a consultar en datos.gob.ar/dataset/cammesa
  - Frecuencia: diaria (cron a las 08:00 AM)
  - Output: DataFrame pandas con los datos del día

  Ejemplo de llamada:
    import httpx

    async def fetch_energy_data():
        url = "https://datos.gob.ar/api/3/action/datastore_search"
        params = {
            "resource_id": "RESOURCE_ID_CAMMESA",
            "limit": 30,
            "sort": "fecha desc"
        }
        response = await httpx.get(url, params=params)
        records = response.json()["result"]["records"]
        return records

COMPONENTE 2: LLM Analyzer (Python)
  - Input: datos energéticos del día
  - Prompt: análisis de tendencias, anomalías, % por fuente renovable
  - Output: texto de análisis (3-4 párrafos)
  - Recomendado: OpenAI GPT-4o / Anthropic Claude / Ollama local
  
  Prompt template:
    """Sos un analista de energía argentina. Analizá estos datos de generación
    eléctrica del día {fecha} y generá un resumen ejecutivo de 3 puntos clave,
    destacando la participación de fuentes renovables y tendencias respecto
    al mes anterior. Datos: {json_datos}"""

COMPONENTE 3: Report Image Generator (Python)
  - Librería principal: matplotlib + PIL/Pillow
  - Alternativa moderna: plotly + kaleido (export a PNG)
  - Diseño: gráfico de torta (% por fuente) + barra temporal + texto LLM
  
  Template visual:
    ┌────────────────────────────────────┐
    │  ⚡ REPORTE ENERGÉTICO ARGENTINA  │
    │  19 de mayo de 2026               │
    │                                    │
    │  [Gráfico torta - Mix energético] │
    │                                    │
    │  🌱 Renovables: 35.2%             │
    │  ⛽ Gas Natural: 48.1%            │
    │  💧 Hidráulica: 12.3%             │
    │  🏭 Nuclear: 4.4%                 │
    │                                    │
    │  📊 Análisis LLM:                 │
    │  "La generación renovable superó  │
    │  el promedio mensual..."          │
    │                                    │
    │  Fuente: CAMMESA / datos.gob.ar   │
    └────────────────────────────────────┘
  
  Dimensiones recomendadas: 1080x1080px (cuadrado, óptimo para WA)

COMPONENTE 4: WhatsApp Sender (Python)
  - Usa WAHA REST API
  - Envía imagen PNG con caption
  - Loop sobre lista de contactos con delay entre envíos

COMPONENTE 5: Scheduler (Python)
  - APScheduler o Celery + Beat
  - Alternativa simple: cron del sistema operativo

### Estructura de directorios del proyecto

  energy-wa-poc/
  ├── docker-compose.yml          ← WAHA + PostgreSQL + Redis
  ├── app/
  │   ├── main.py                 ← FastAPI app principal
  │   ├── fetcher.py              ← Consume datos.gob.ar
  │   ├── analyzer.py             ← LLM analyzer
  │   ├── report_generator.py     ← Genera imagen PNG
  │   ├── whatsapp_sender.py      ← Cliente WAHA REST
  │   ├── scheduler.py            ← APScheduler / cron
  │   └── config.py               ← Variables de entorno
  ├── templates/
  │   └── report_template.png     ← Fondo/template visual
  ├── contacts.json               ← Lista de números de contacto
  ├── requirements.txt
  └── .env

### requirements.txt para la PoC

  fastapi==0.111.0
  uvicorn==0.30.0
  httpx==0.27.0
  pandas==2.2.0
  matplotlib==3.8.0
  Pillow==10.3.0
  plotly==5.22.0
  kaleido==0.2.1
  openai==1.30.0          # o anthropic==0.28.0
  apscheduler==3.10.4
  python-dotenv==1.0.1
  pydantic-settings==2.3.0

### Variables de entorno (.env)

  # WAHA
  WAHA_BASE_URL=http://localhost:3000/api
  WAHA_API_KEY=tu-api-key-secreta
  WAHA_SESSION=default

  # LLM
  OPENAI_API_KEY=sk-...
  # o
  ANTHROPIC_API_KEY=sk-ant-...

  # Datos Argentina
  DATOS_GOB_AR_BASE_URL=https://datos.gob.ar/api/3/action
  ENERGY_RESOURCE_ID=RESOURCE_ID_A_CONFIRMAR

  # Contactos WhatsApp
  WA_CONTACTS=5491167890123,5491198765432,5491145678901

---

## 8. CHECKLIST DE TAREAS PARA MAÑANA

### BLOQUE 1: Setup infraestructura (1-2 hs)

  [ ] Copiar el docker-compose.yml de este directorio al servidor/máquina
  [ ] Ejecutar: docker compose up -d
  [ ] Verificar que los 3 contenedores están UP:
      docker compose ps → waha, postgres, redis todos en Running
  [ ] Abrir http://localhost:3000/ → ver Swagger UI
  [ ] Abrir http://localhost:3001/ → ver Dashboard (si está habilitado)
  [ ] Crear sesión de WhatsApp vía curl o Dashboard
  [ ] Escanear QR con el teléfono de prueba
  [ ] Verificar status: GET /api/sessions → status: WORKING
  [ ] Enviar mensaje de texto de prueba a propio número
  [ ] Confirmar recepción → WAHA funcionando correctamente

### BLOQUE 2: Explorar API de datos energéticos (1 hs)

  [ ] Ir a https://datos.gob.ar/dataset
  [ ] Buscar datasets de CAMMESA / generación eléctrica
  [ ] Identificar Resource IDs de los datasets relevantes
  [ ] Probar llamada API directa:
      curl "https://datos.gob.ar/api/3/action/datastore_search?resource_id=XXX&limit=5"
  [ ] Entender la estructura de los datos (columnas, tipos, fechas)
  [ ] Documentar los 2-3 endpoints/datasets más útiles para la PoC

### BLOQUE 3: Prototipo Python básico (2-3 hs)

  [ ] Crear directorio: mkdir energy-wa-poc && cd energy-wa-poc
  [ ] Crear virtualenv: python -m venv venv && source venv/bin/activate
  [ ] Instalar dependencias: pip install httpx pandas matplotlib Pillow python-dotenv
  [ ] Crear .env con las variables de WAHA
  [ ] Escribir fetcher.py → función que retorna datos energéticos del día
  [ ] Escribir report_generator.py → función que toma datos y genera PNG
  [ ] Verificar imagen generada: python report_generator.py → abrir output.png
  [ ] Escribir whatsapp_sender.py → función que envía imagen via WAHA
  [ ] Test end-to-end: python -c "from whatsapp_sender import send_report; send_report()"
  [ ] Confirmar recepción de imagen en WhatsApp con formato correcto

### BLOQUE 4: Integración LLM (1 hs)

  [ ] Elegir LLM: OpenAI GPT-4o / Claude / Ollama local (recomendado: GPT-4o mini por costo)
  [ ] Configurar API key en .env
  [ ] Escribir analyzer.py → función que recibe datos y retorna análisis texto
  [ ] Integrar texto del LLM en la imagen del reporte
  [ ] Test: generar imagen con análisis LLM real

### BLOQUE 5: Lista de contactos y broadcast (30 min)

  [ ] Definir lista de contactos de prueba (mínimo 3-5 personas del equipo)
  [ ] Crear contacts.json con números en formato 54911XXXXXXXX
  [ ] Implementar loop de envío con delay de 2-3 segundos entre mensajes
  [ ] Test: enviar a todos los contactos de prueba
  [ ] Verificar que todos lo recibieron

### BLOQUE 6: Polish y automatización (1 hs)

  [ ] Mejorar diseño visual de la imagen (colores, tipografía, logo consultora)
  [ ] Agregar manejo de errores (retry si WAHA falla, logging)
  [ ] Configurar APScheduler para correr el flujo diariamente a las 08:00
  [ ] Documentar el proceso en un README del proyecto
  [ ] Demo interna al equipo: mostrar el flujo completo end-to-end

### BONUS: Si hay tiempo

  [ ] Configurar webhook en WAHA para responder mensajes entrantes
  [ ] Implementar comando "!reporte" → responde con el último reporte generado
  [ ] Evaluar HTTPS con Nginx reverse proxy para producción
  [ ] Evaluar múltiples sesiones (una por cliente)

---

## RECURSOS Y LINKS ÚTILES

  WAHA:
  - GitHub: https://github.com/devlikeapro/waha
  - Docs oficiales: https://waha.devlike.pro/docs/
  - Swagger UI local: http://localhost:3000/
  - Docker Hub: https://hub.docker.com/r/devlikeapro/waha

  Datos Argentina:
  - Portal datos.gob.ar: https://datos.gob.ar
  - API CKAN: https://datos.gob.ar/api/3/action/
  - Dataset CAMMESA búsqueda: https://datos.gob.ar/dataset?q=cammesa+energia
  - Dataset generación eléctrica: https://datos.gob.ar/dataset/energia-generacion-electrica-del-sistema-argentino-interconectado

  Python libs para reportes visuales:
  - matplotlib: https://matplotlib.org/
  - plotly: https://plotly.com/python/
  - Pillow: https://pillow.readthedocs.io/

  LLMs recomendados (costo/calidad):
  - OpenAI GPT-4o mini: ~$0.15/1M tokens input (muy barato para PoC)
  - Anthropic Claude Haiku: similar costo
  - Ollama local (llama3, mistral): gratis, requiere GPU

---

Nota: Este documento fue preparado el 2026-05-19 para el equipo I+D+I.
Actualizar con los Resource IDs reales de datos.gob.ar una vez identificados.
