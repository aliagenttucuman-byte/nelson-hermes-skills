# LinkedIn OAuth2 Pipeline — AlegentAI

## Contexto

Pipeline para publicar posts en LinkedIn desde cuenta personal (aliagenttucuman@gmail.com)
usando la API oficial con el permiso `w_member_social`.

App LinkedIn: **Alegent AI investigations**
Client ID: `77djcvwzhlbcak`
Producto aprobado: Share on LinkedIn (v202401)

---

## Arquitectura

```
Fuente de contenido (RSS / brainstorming / novedades)
    ↓
JARVIS genera el post (tono profesional + hashtags)
    ↓
LinkedIn API v2 POST /v2/ugcPosts
    ↓
Confirmación WhatsApp a Nelson
```

---

## Flujo OAuth2 (una sola vez)

### Paso 1 — Redirect URI

**CRÍTICO:** La redirect URI registrada en LinkedIn Developer DEBE coincidir exactamente con la que usa el servidor.

- Si el servidor corre en localhost con túnel Cloudflare, registrar la URL del TÚNEL, no localhost.
- Ejemplo: `https://guru-snapshot-pike-strap.trycloudflare.com/callback`
- Error típico si no coincide: `"The redirect_uri does not match the registered value"`

### Paso 2 — Levantar servidor OAuth

```bash
cd ~/brainstorming/2026-05-31-linkedin-feed-pipeline
python3 server.py
```

El servidor corre en :8090 y expone:
- `GET /` — página con botón de autorización
- `GET /callback` — recibe el code de LinkedIn, intercambia por token, guarda en `auth/tokens.json`

### Paso 3 — Exponer con túnel Cloudflare

```bash
cloudflared tunnel --url http://localhost:8090 2>&1 | tee /tmp/cf_linkedin.log &
sleep 5 && grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cf_linkedin.log | tail -1
```

**Importante:** Actualizar el .env con la URL del túnel ANTES de reiniciar el servidor:

```bash
sed -i 's|LINKEDIN_REDIRECT_URI=.*|LINKEDIN_REDIRECT_URI=https://TU-TUNEL.trycloudflare.com/callback|' auth/.env
pkill -f "server.py" && python3 server.py &
```

### Paso 4 — Autorizar

1. Abrir la URL del túnel en el browser
2. Tocar "Autorizar en LinkedIn"
3. LinkedIn redirige al callback con el `code`
4. El servidor guarda `auth/tokens.json` con `access_token`, `refresh_token`, `person_id`

---

## Publicar un post

```python
from publisher import publish_post

text = """🚀 Texto del post aquí.

#AlegentAI #IA #ForestAI"""

result = publish_post(text)
# {"status": "ok", "post_id": "..."}
```

---

## Payload LinkedIn API v2

```json
{
  "author": "urn:li:person:{person_id}",
  "lifecycleState": "PUBLISHED",
  "specificContent": {
    "com.linkedin.ugc.ShareContent": {
      "shareCommentary": {"text": "Texto del post"},
      "shareMediaCategory": "NONE"
    }
  },
  "visibility": {
    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
  }
}
```

Headers requeridos:
```
Authorization: Bearer {access_token}
Content-Type: application/json
X-Restli-Protocol-Version: 2.0.0
```

---

## Tokens y expiración

- `access_token`: válido 60 días
- `refresh_token`: válido ~1 año
- Guardados en `auth/tokens.json` con `expires_at` calculado
- `person_id` (sub) también guardado — necesario para el campo `author`

---

## Pitfalls

1. **redirect_uri mismatch** — El error más común. La URI en el .env y la registrada en LinkedIn Developer deben ser IDÉNTICAS, incluyendo el scheme (https/http) y el path (/callback).

2. **Túnel Cloudflare cambia URL en cada reinicio** — Si el túnel cae y se reinicia, la URL cambia. Hay que actualizar LinkedIn Developer + el .env + reiniciar el servidor. Para URL estable, usar túnel nombrado con dominio propio.

3. **WPL_AP1.xxx NO es el Client Secret** — Es un token de sesión de LinkedIn. El Client Secret real está en la pestaña Auth de la app en LinkedIn Developer y tiene un formato alfanumérico largo sin prefijo.

4. **person_id es el `sub` del userinfo endpoint** — No confundir con el `id` de otros endpoints. Usar `https://api.linkedin.com/v2/userinfo` para obtenerlo.

5. **Scopes necesarios** — `openid profile email w_member_social`. Sin `w_member_social` no se puede publicar en cuenta personal.

---

## Archivos del proyecto

```
~/brainstorming/2026-05-31-linkedin-feed-pipeline/
├── auth/
│   ├── .env          # credenciales (gitignored)
│   └── tokens.json   # tokens OAuth (se genera al autenticar)
├── server.py         # servidor FastAPI para OAuth2 callback
├── publisher.py      # script de publicación
└── README.md
```

---

## Integración futura con n8n

n8n tiene nodo LinkedIn nativo que usa la misma app OAuth2.
Una vez que `tokens.json` existe, se puede configurar el nodo en n8n con las mismas credenciales
para pipelines automatizados RSS → JARVIS → LinkedIn.
