# LinkedIn API OAuth2 — AlegentAI

## App registrada

- **Nombre:** Alegent AI investigations
- **Client ID:** 77djcvwzhlbcak
- **Cuenta:** aliagenttucuman@gmail.com
- **Producto aprobado:** Share on LinkedIn (w_member_social) ✅
- **Creada:** 2026-05-31
- **Credenciales guardadas en:** `~/brainstorming/2026-05-31-linkedin-feed-pipeline/auth/.env`

## Quirk importante: formato del Client Secret

LinkedIn Developer muestra el Client Secret con el prefijo `WPL_AP1.`:
```
WPL_AP1.XH51CrDe8lfF0Kc8.qnHTaQ==
```
Esto es correcto y válido — NO es un token de acceso ni una sesión. Es el Client Secret real de la app, simplemente tiene un formato diferente al esperado (no es una cadena hexadecimal estándar).

## Flujo OAuth2

1. Crear app en https://developer.linkedin.com
2. Solicitar producto "Share on LinkedIn" → obtiene scope `w_member_social`
3. En pestaña Auth → Authorized Redirect URLs → agregar `http://localhost:8090/callback`
4. Correr `server.py` (FastAPI en :8090)
5. Abrir URL de autorización en browser → LinkedIn redirige con `code`
6. El server intercambia `code` por `access_token` + guarda `person_id` en `tokens.json`
7. A partir de ahí usar `publisher.py` para publicar

## Scopes necesarios

```
openid profile email w_member_social
```

## Endpoint de publicación

```
POST https://api.linkedin.com/v2/ugcPosts
Authorization: Bearer {access_token}
X-Restli-Protocol-Version: 2.0.0
```

Payload mínimo para post de texto:
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

## Archivos del pipeline

```
~/brainstorming/2026-05-31-linkedin-feed-pipeline/
├── auth/
│   ├── .env          ← CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
│   └── tokens.json   ← access_token, person_id (se genera al autenticar)
├── server.py         ← FastAPI OAuth2 callback, genera tokens.json
├── publisher.py      ← publica post usando tokens.json
├── generator.py      ← (pendiente) genera contenido con IA
└── README.md
```

## Rate limits

- Máx ~100 posts/día (plan básico)
- En la práctica: 1-3 posts/día es lo óptimo
- access_token válido: 60 días
- refresh_token válido: 1 año

## Integración con n8n

n8n tiene nodo nativo de LinkedIn (operación "Create Post").
Requiere la misma OAuth2 app con `w_member_social`.
n8n maneja el refresh de tokens automáticamente — ventaja vs implementación manual.

Pipeline típico:
```
RSS/fuente → Code Node (formatear) → LinkedIn (Create Post) → WhatsApp notificación
```

## Evitar

- `linkedin-api` library (usa cookies de sesión, alto riesgo de ban)
- Selenium/Playwright para publicar (LinkedIn detecta automatización)
- Email/password directo sin OAuth
