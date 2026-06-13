# Rapid logo branding in React/Vite UI (Expreso Bisonte case)

## Trigger

Usuario manda imagen de marca por chat (WhatsApp/Telegram/etc.) y pide incorporarla ya en la UI del PoC.

## Patrón recomendado

1. Copiar la imagen al proyecto frontend en `public/`.
2. Usar nombre estable orientado negocio (ej. `expreso-bisonte-logo.jpg`).
3. Referenciar desde JSX con `src="/expreso-bisonte-logo.jpg"`.
4. Agregar logo en header con `display:flex`, `gap`, `alignItems:center`.
5. Ejecutar `npm run build`.
6. Validar asset directo en la URL pública (`/expreso-bisonte-logo.jpg`) devuelve 200.
7. Confirmar al usuario y pedir hard refresh del navegador.

## Por qué este patrón

- `public/` evita import paths frágiles y problemas de bundling para assets recibidos ad-hoc.
- Ruta absoluta (`/logo.jpg`) es simple de validar y funciona igual en local/túnel.
- Acelera cambios de branding en demos operativas sin tocar pipeline ni backend.

## Checklist rápido

- [ ] Archivo en `frontend/public/`
- [ ] Referencia JSX por `/archivo.ext`
- [ ] Build OK
- [ ] Asset URL 200
- [ ] Usuario ve logo tras hard refresh
