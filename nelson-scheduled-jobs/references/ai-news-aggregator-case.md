# Caso Real: AI News Aggregator + WhatsApp Gateway

**Fecha:** 2025-05-13
**Proyecto:** Área I+D+i de la consultora
**Schedule:** 2 veces por día (9:00 y 18:00)

---

## Qué hace

1. Lee 8+ fuentes RSS de IA (HuggingFace, OpenAI, Google AI, LangChain, Microsoft Research, arXiv)
2. Filtra por keywords relevantes (llm, model, open source, framework, benchmark)
3. Evita duplicados entre corridas (state JSON persistente)
4. Genera resumen compacto para WhatsApp
5. Envía automáticamente a destinatarios configurados vía WhatsApp Gateway

## Estructura de archivos

```
~/brainstorming/2025-05-13-ai-news-aggregator/
├── scripts/
│   └── ai_news_collector.py      # Script principal Python
├── whatsapp-gateway/
│   ├── server.js                  # API Baileys (Express)
│   ├── send_whatsapp.py           # Helper CLI Python
│   └── auth/                      # Sesión persistente
└── README.md
```

## WhatsApp Gateway: setup rápido

```bash
cd whatsapp-gateway
npm install @whiskeysockets/baileys qrcode express
node connect.js   # Genera QR o pairing code, escanear con celular
node server.js    # API en localhost:3001
```

**systemd auto-arranque:**
```bash
systemctl --user enable whatsapp-gateway
systemctl --user start whatsapp-gateway
```

## Integración desde el script de cron

```python
# Al final del aggregator, enviar resumen
WHATSAPP_RECIPIENTS = ["5493816240691"]  # Pablo, Nelson, etc.

def send_whatsapp(to: str, message: str):
    data = json.dumps({"to": to, "message": message}).encode()
    req = request.Request(
        "http://localhost:3001/send",
        data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    request.urlopen(req, timeout=10)

# Formato resumen para WhatsApp (compacto, sin markdown pesado)
whatsapp_summary = f"""🧠 *Novedades IA* ({datetime.now().strftime('%d/%m %H:%M')})

🔹 Llama 4: multimodal + reasoning
🔹 Nuevo framework de agentes de Google
🔹 Benchmark actualizado en HuggingFace

Total: 5 artículos. Ver más: {notebook_url}
"""

for recipient in WHATSAPP_RECIPIENTS:
    send_whatsapp(recipient, whatsapp_summary)
```

## Cron job (Hermes)

```yaml
schedule: "0 9,18 * * *"
command: "ai-news-collector.sh"
deliver: "origin"
no_agent: true
```

Wrapper en `~/.hermes/scripts/ai-news-collector.sh`:
```bash
#!/bin/bash
cd /home/server/brainstorming/2025-05-13-ai-news-aggregator
python3 scripts/ai_news_collector.py
```

## Lecciones aprendidas

- **Formato WhatsApp:** evitar markdown complejo (negritas con asteriscos sí, bloques de código no). WhatsApp no renderiza markdown.
- **Health check del gateway:** antes de enviar, verificar `GET /health`. Si no está disponible, loguear error y continuar — no crashear el job.
- **Mensajes cortos:** WhatsApp corta líneas largas. Resumen máximo 20-30 líneas.
- **Deduplicación robusta:** usar `title + source` como ID, no solo URL (algunos feeds no tienen URL estable).
- **Feeds RSS muertos:** verificar periódicamente que los feeds respondan. Anthropic y Google AI Blog antiguos dieron 404.

## Variaciones posibles

| Variación | Cambio |
|-----------|--------|
| **Más frecuencia** | `0 */4 * * *` (cada 4 horas) |
| **Fuentes técnicas específicas** | Agregar feeds de PyTorch, JAX, CUDA |
| **Clasificación automática** | LLM local clasifica cada noticia en Adoptar/Probar/Evaluar/Descartar |
| **Podcast en vez de texto** | Integrar notebooklm-py para generar Audio Overview |
| **Solo novedades relevantes** | LLM local filtra relevancia antes de enviar |

---

*Referencia generada 2025-05-13. Revisar feeds RSS cada 3 meses.*
