# White screen triage (React + Vite + Cloudflare tunnel)

Use this when user reports "pantalla blanca" on a remote demo URL.

## Fast diagnosis

1) Verify URL is alive and serving built app HTML:
```bash
python3 - <<'PY'
import requests
u='https://<tunnel>.trycloudflare.com'
r=requests.get(u,timeout=20)
print(r.status_code)
print(r.text[:200])
PY
```

2) Validate runtime render + JS errors with Playwright (headless):
```bash
python3 - <<'PY'
from playwright.sync_api import sync_playwright
u='https://<tunnel>.trycloudflare.com'
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,args=['--no-sandbox'])
    page=b.new_page()
    errs=[]
    page.on('pageerror',lambda e: errs.append(str(e)))
    page.goto(u, wait_until='networkidle', timeout=60000)
    body=page.inner_text('body')
    print('body_len',len(body))
    print('has_content',len(body.strip())>0)
    print('errors',errs[:5])
    b.close()
PY
```

3) Validate API from the same domain (proxy path):
```bash
python3 - <<'PY'
import requests
u='https://<tunnel>.trycloudflare.com/api/v1/excel/procedures'
r=requests.get(u,timeout=20)
print(r.status_code, r.headers.get('content-type'))
print(r.text[:150])
PY
```

## Common root causes

- User is opening an old tunnel URL after a tunnel rotation.
- Frontend is updated but backend process is still old (route mismatch -> runtime break).
- Cached JS bundle in mobile browser.

## Recovery sequence (safe default)

1. Restart backend service/process used by the demo.
2. Rebuild frontend (`npm run build`).
3. Relaunch frontend preview (`npm run preview -- --host 0.0.0.0 --port <port>`).
4. Relaunch cloudflared and capture the new URL.
5. Re-run Playwright smoke check before sharing URL.
6. Ask user to close old tab and hard refresh on the new URL.

## UX hardening added in this class of app

For saved-procedure libraries, include explicit actions per row:
- `Usar`
- `Duplicar`
- `Eliminar`

This reduces recovery friction when users test many prompt variants and need quick cleanup.
