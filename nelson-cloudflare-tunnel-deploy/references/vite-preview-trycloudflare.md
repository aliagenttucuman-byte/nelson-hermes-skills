# Vite Preview + Cloudflare Quick Tunnel (2026-06)

Caso real validado en `excel-merger-poc` para demo mobile.

## Síntoma

La URL `https://<random>.trycloudflare.com` abre error:

`Blocked request. This host ("...trycloudflare.com") is not allowed.`

## Causa

`vite preview` bloquea hosts no permitidos (host check).

## Fix mínimo

1. `vite.config.ts`

```ts
preview: {
  host: '0.0.0.0',
  allowedHosts: ['.trycloudflare.com'],
  proxy: { '/api': 'http://localhost:9000' }
}
```

2. Mantener frontend con API relativa (`/api/v1`) para evitar hardcodear URLs efímeras.

3. Rebuild + restart preview:

```bash
npm run build
npx vite preview --port 5177 --host 0.0.0.0
```

4. Abrir tunnel al preview:

```bash
cloudflared tunnel --url http://localhost:5177
```

## Verificación rápida

```bash
curl -s -o /dev/null -w "%{http_code}" https://<tunnel>.trycloudflare.com
curl -s https://<tunnel>.trycloudflare.com/api/v1/excel/models
```

Esperado: `200` en ambos.
