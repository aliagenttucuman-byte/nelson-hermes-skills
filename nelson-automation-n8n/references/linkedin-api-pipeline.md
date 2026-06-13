# LinkedIn API — Notas de integración (equipo Nelson)

## App creada

- **Nombre**: Alegent AI investigations
- **Client ID**: 77djcvwzhlbcak
- **Cuenta**: aliagenttucuman@gmail.com
- **Creada**: 2026-05-31
- **Producto aprobado**: Share on LinkedIn (scope `w_member_social`)
- **Versión API**: 202401

## Endpoints disponibles con w_member_social

| Endpoint | Método | Uso |
|----------|--------|-----|
| `/rest/posts` | POST | Publicar post de texto o imagen |
| `/rest/documents` | POST + BATCH_GET | Subir y publicar documentos |
| `/rest/images` | POST | Subir imágenes |
| `/v2/ugcPosts` | POST | API legacy (aún funciona) |

## Flujo OAuth2 completo

```
1. GET https://www.linkedin.com/oauth/v2/authorization
   ?response_type=code
   &client_id={CLIENT_ID}
   &redirect_uri={REDIRECT_URI}
   &scope=w_member_social%20r_liteprofile%20r_emailaddress

2. Usuario autoriza → LinkedIn redirige a REDIRECT_URI?code=AUTH_CODE

3. POST https://www.linkedin.com/oauth/v2/accessToken
   client_id={CLIENT_ID}
   client_secret={CLIENT_SECRET}
   grant_type=authorization_code
   code={AUTH_CODE}
   redirect_uri={REDIRECT_URI}
   → Responde: { access_token, expires_in: 5183944 (~60 días) }

4. Usar access_token en header: Authorization: Bearer {TOKEN}
```

## Identificar el URN del usuario autenticado

```python
import requests

def get_person_urn(access_token: str) -> str:
    r = requests.get(
        "https://api.linkedin.com/v2/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return r.json()["id"]  # ej: "abc123XYZ" → urn:li:person:abc123XYZ
```

## Publicar post de texto (API v2 ugcPosts)

```python
def post_text(access_token: str, person_id: str, text: str) -> dict:
    r = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        },
        json={
            "author": f"urn:li:person:{person_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
    )
    return r.json()
```

## Pitfalls detectados en esta integración

### Token WPL_AP1 ≠ Client Secret
El formato `WPL_AP1.XXXX.YYYY==` es un access token de sesión generado por LinkedIn cuando el usuario está logueado en el browser. NO es el Client Secret de la Developer App. El Client Secret está en:
`developer.linkedin.com → Tu app → Auth → Primary Client Secret → icono ojo`

### Redirect URI debe coincidir exactamente
La Redirect URI registrada en la app debe ser IDÉNTICA (incluyendo trailing slash) a la usada en el flujo OAuth. Diferencias de un carácter dan error 400.

### Para n8n self-hosted
Redirect URI para n8n: `https://TU_DOMINIO/oauth2/callback`
Si usás la instancia local: `http://localhost:5678/oauth2/callback`

## Rate limits

- 100 req/día plan básico
- 500 req/día con verificación adicional  
- 1 post cada 10 segundos por usuario
- Token válido ~60 días (sin refresh automático en plan básico)

## Pipeline propuesto: contenido IA → LinkedIn

```
Fuente (RSS/manual/DB)
  → JARVIS genera el texto del post (LLM)
  → Revisión/aprobación (opcional, webhook a WhatsApp)
  → Python/n8n publica vía API
  → Registro en SQLite (fecha, texto, response_id)
```

## Estado actual (2026-05-31)

- App creada y producto aprobado ✅
- Client ID confirmado: 77djcvwzhlbcak ✅
- Client Secret: pendiente de obtener de pestaña Auth
- Access token: pendiente (completar flujo OAuth2)
- Pipeline n8n/Python: pendiente de implementar
