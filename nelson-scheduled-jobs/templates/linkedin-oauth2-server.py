"""
Servidor OAuth2 para LinkedIn — AlegentAI
Obtiene access_token y lo guarda en auth/tokens.json

SCOPES CORRECTOS para app "Alegent AI investigations":
  SOLO: w_member_social
  NO usar: r_liteprofile, r_emailaddress, openid, profile, email
  → Cualquier scope extra produce invalid_scope_error

Sin r_liteprofile no se puede llamar /v2/me para obtener person_id.
Solución: hardcodear person_id en tokens.json (sacarlo de URL del perfil LinkedIn).

Client Secret LinkedIn puede tener formato WPL_AP1.xxx.xxx== — es válido, usarlo tal cual.

Pitfall túnel Cloudflare: la URL cambia en cada restart.
Orden correcto:
  1. python3 server.py
  2. cloudflared tunnel --url http://localhost:8090
  3. Capturar URL nueva
  4. Actualizar .env LINKEDIN_REDIRECT_URI
  5. Actualizar LinkedIn Developer → Auth → Authorized Redirect URLs
  6. Reiniciar server.py
  7. Verificar: curl -s http://localhost:8090 | grep 'scope='
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / "auth" / ".env")

CLIENT_ID     = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI  = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8090/callback")
TOKENS_FILE   = BASE_DIR / "auth" / "tokens.json"

# CRÍTICO: SOLO w_member_social. Nada más.
SCOPES = "w_member_social"

AUTH_URL = (
    f"https://www.linkedin.com/oauth/v2/authorization"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope={SCOPES.replace(' ', '%20')}"
    f"&state=alegentai2026"
)

app = FastAPI(title="LinkedIn OAuth2 — AlegentAI")


@app.get("/")
def index():
    return HTMLResponse(f"""
    <html><body style="font-family:sans-serif;padding:40px;background:#0f1729;color:white">
    <h2>LinkedIn OAuth2 — AlegentAI</h2>
    <p>Redirect URI: <code>{REDIRECT_URI}</code></p>
    <p>Scopes: <code>{SCOPES}</code></p>
    <a href="{AUTH_URL}" style="background:#0077B5;color:white;padding:12px 24px;
       border-radius:6px;text-decoration:none;font-weight:bold">
      🔗 Autorizar en LinkedIn
    </a>
    </body></html>
    """)


@app.get("/callback")
async def callback(request: Request):
    code  = request.query_params.get("code")
    error = request.query_params.get("error")

    if error:
        desc = request.query_params.get("error_description", "")
        return HTMLResponse(f"<h2 style='color:red'>Error: {error}</h2><p>{desc}</p>")
    if not code:
        return HTMLResponse("<h2>No se recibió código de autorización</h2>")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type":    "authorization_code",
                "code":          code,
                "redirect_uri":  REDIRECT_URI,
                "client_id":     CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if resp.status_code != 200:
        return HTMLResponse(f"<h2>Error al obtener token: {resp.status_code}</h2><pre>{resp.text}</pre>")

    tokens = resp.json()
    tokens["obtained_at"] = datetime.utcnow().isoformat()
    tokens["expires_at"]  = (
        datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 5184000))
    ).isoformat()

    # Sin r_liteprofile no podemos llamar /v2/me.
    # person_id se debe hardcodear manualmente en tokens.json después.
    tokens["person_id"]   = ""  # completar manualmente con ID del perfil LinkedIn
    tokens["person_name"] = "Nelson"
    TOKENS_FILE.parent.mkdir(exist_ok=True)
    TOKENS_FILE.write_text(json.dumps(tokens, indent=2))

    return HTMLResponse(f"""
    <html><body style="font-family:sans-serif;padding:40px;background:#0f1729;color:white">
    <h2>✅ Token obtenido</h2>
    <p>access_token guardado en <code>auth/tokens.json</code></p>
    <p>Expira: {tokens['expires_at']}</p>
    <p><strong>Paso siguiente:</strong> agregar <code>person_id</code> manualmente en tokens.json
    (sacarlo de la URL de tu perfil LinkedIn).</p>
    </body></html>
    """)


if __name__ == "__main__":
    print(f"\n🔗 URL de autorización:\n{AUTH_URL}\n")
    uvicorn.run(app, host="0.0.0.0", port=8090)
