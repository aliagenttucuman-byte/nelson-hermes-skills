# AI News Aggregator + WhatsApp Gateway 📰 📤

> Fecha: 2025-05-13  
> Propietario: Tony Stark (Nelson Acosta)  
> Objetivo: Mantener al equipo actualizado sobre novedades de IA 2 veces al día, y enviar mensajes de WhatsApp a múltiples números desde scripts Python.

## 🚀 Componentes

### 1. AI News Aggregator (`scripts/ai_news_collector.py`)

Escanea feeds RSS/Atom de las principales fuentes de inteligencia artificial, filtra por relevancia y genera un resumen.

**Fuentes monitoreadas:**

| Fuente | Tipo | Máx artículos |
|---|---|---|
| HuggingFace Blog | RSS | 5 |
| OpenAI Blog | RSS | 5 |
| Google AI Blog | RSS | 5 |
| LangChain Blog | RSS | 5 |
| Microsoft Research | RSS | 5 |
| arXiv cs.AI | RSS + keywords | 5 |
| arXiv cs.LG | RSS + keywords | 5 |
| arXiv cs.CL | RSS + keywords | 5 |

**Ejecución manual:**
```bash
python3 scripts/ai_news_collector.py
```

**Schedule automático:** Hermes cronjob corre **2 veces al día** (09:00 y 18:00).

---

### 2. WhatsApp Gateway (`whatsapp-gateway/`)

Servidor Node.js con Baileys que expone una API HTTP para enviar mensajes de WhatsApp a **cualquier número**.

**Características:**
- ✅ Envío a un número (`POST /send`)
- ✅ Envío batch a múltiples números (`POST /send-batch`)
- ✅ Delay configurable entre mensajes (evita bloqueos)
- ✅ Sesión persistente (no requiere re-escanear QR)

**Arrancar el gateway:**
El gateway se inicia automáticamente con el sistema gracias a systemd. Si necesita controlarlo manualmente:

```bash
# Ver estado
systemctl --user status whatsapp-gateway

# Reiniciar
systemctl --user restart whatsapp-gateway

# Parar
systemctl --user stop whatsapp-gateway

# Iniciar
systemctl --user start whatsapp-gateway
```

> Nota: El servicio usa `systemd --user`, por lo que el usuario `server` debe tener `linger` habilitado (ya está hecho).

**Endpoints:**

```bash
# Verificar estado
curl http://localhost:3001/health

# Enviar a un número
curl -X POST http://localhost:3001/send \
  -H "Content-Type: application/json" \
  -d '{"to": "5493816240691", "message": "Hola desde el gateway!"}'

# Enviar a múltiples números
curl -X POST http://localhost:3001/send-batch \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": [
      {"to": "5493816240691", "message": "Hola!"},
      {"to": "5493811234567", "message": "Hola!"}
    ],
    "delayMs": 2000
  }'
```

**Script Python helper:**
```bash
python3 whatsapp-gateway/send_whatsapp.py \
  --to 5493816240691 \
  --message "Hola desde Python!"

# Múltiples números
python3 whatsapp-gateway/send_whatsapp.py \
  --to 5493816240691,5493811234567 \
  --message "Broadcast desde Python!" \
  --batch
```

---

## 📁 Estructura

```
2025-05-13-ai-news-aggregator/
├── README.md
├── scripts/
│   └── ai_news_collector.py       # Agregador de noticias IA
└── whatsapp-gateway/
    ├── server.js                    # API HTTP con Baileys
    ├── connect.js                   # Script de conexión inicial
    ├── send_whatsapp.py             # Helper Python
    └── auth/                        # Sesión persistida
```

## ✅ Estado

- [x] AI News Aggregator funcionando
- [x] Cronjob programado 2 veces al día
- [x] WhatsApp Gateway conectado
- [x] API para envío a múltiples números
- [x] Script Python helper

## 🔧 Próximos pasos

- [ ] Agregar más fuentes de IA (Stability AI, Together AI, Cohere, Mistral)
- [ ] Clasificación automática por relevancia con LLM local
- [ ] Almacenar artículos útiles en base vectorial para RAG
- [ ] Integrar envío de resumen de noticias automático vía WhatsApp Gateway
