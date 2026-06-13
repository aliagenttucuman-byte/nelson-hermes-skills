# LinkedIn OAuth2 — Pitfalls de la sesión 2026-05-31

## Error 1: invalid_scope_error

**Causa:** Usar scopes de OpenID Connect junto con w_member_social en una app con producto
"Share on LinkedIn" básico. LinkedIn rechaza la combinación.

**Síntoma:** Pantalla en blanco con texto `Error: invalid_scope_error`

**Fix:** Usar solo:
```
SCOPES = "w_member_social"
```

NO usar: `openid profile email w_member_social` ni `w_member_social r_liteprofile r_emailaddress`

---

## Error 2: redirect_uri does not match

**Causa:** La redirect_uri en el código no coincide exactamente con la registrada
en LinkedIn Developer → Auth → Authorized Redirect URLs.

**Síntoma:** Página de error LinkedIn: "Bummer, something went wrong. The redirect_uri
does not match the registered value"

**Fix:**
- Si se usa túnel Cloudflare para exponer el callback: registrar en LinkedIn la URL
  del túnel (https://xxx.trycloudflare.com/callback), NO localhost.
- Actualizar también el .env del servidor con la misma URL.
- Verificar con: `curl -s http://localhost:8090 | grep -o 'redirect_uri=[^&"]*'`

---

## Error 3: Proceso zombie con scopes viejos

**Causa:** Se corrige server.py y se relanza, pero el proceso viejo sigue vivo y el
túnel Cloudflare sigue apuntando al servidor con los scopes incorrectos.

**Fix:**
```bash
pkill -9 -f "server.py"
fuser -k 8090/tcp
# luego relanzar
python3 server.py &
```

---

## Error 4: Client Secret formato WPL_AP1

El Client Secret de LinkedIn puede tener formato:
```
WPL_AP1.XH51CrDe8lfF0Kc8.qnHTaQ==
```
Parece un token de sesión pero es el Client Secret real. Usarlo tal cual en el .env.

---

## Endpoint de perfil correcto según scopes

| Scopes usados | Endpoint de perfil | Campos |
|--------------|-------------------|--------|
| openid + profile | /v2/userinfo | name, sub |
| r_liteprofile | /v2/me | localizedFirstName, localizedLastName, id |

Con r_liteprofile (sin openid), usar /v2/me y extraer `id` como person_id.
