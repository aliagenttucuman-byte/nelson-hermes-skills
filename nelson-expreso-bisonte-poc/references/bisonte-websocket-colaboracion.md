# Bisonte — Colaboración en tiempo real WebSocket (jun 2026)

## Arquitectura

- Backend: FastAPI WebSocket en `/api/v1/ws/contado` (puerto 9000)
- Frontend: hook `useContadoWS.ts` + componente `ContadoTable.tsx`
- El spa_proxy HTTP-puro en :9090 NO soporta WebSocket upgrade → WS conecta directo a :9000

```
Browser Tab A ──ws──→ :9000/api/v1/ws/contado
Browser Tab B ──ws──→ :9000/api/v1/ws/contado
```

## Identificación de pestañas sin login

Cada pestaña genera su propio ID usando `sessionStorage` (NO localStorage — localStorage se comparte entre pestañas del mismo origen):

```typescript
function getTabId(): string {
  const key = '__bisonte_tab_id__'
  let id = sessionStorage.getItem(key)
  if (!id) {
    id = 'tab_' + Math.random().toString(36).slice(2, 7).toUpperCase()
    sessionStorage.setItem(key, id)
  }
  return id
}
```

Formato: `tab_X7K3P` — corto, único por pestaña, muere cuando se cierra la pestaña.

## Protocolo de mensajes

### Cliente → Servidor
```json
{ "type": "join",    "user": "tab_X7K3P" }
{ "type": "editing", "user": "tab_X7K3P", "nro": "A.0053.00111316", "col": "REFERENTE" }
{ "type": "update",  "user": "tab_X7K3P", "nro": "A.0053.00111316", "col": "REFERENTE", "value": "CC" }
{ "type": "leave",   "user": "tab_X7K3P" }
{ "type": "ping" }
```

### Servidor → Cliente(s)
```json
{ "type": "presence",   "users": [{ "user", "color", "editing_nro", "editing_col" }] }
{ "type": "cell_lock",  "user": "tab_X7K3P", "color": "#e53e3e", "nro": "...", "col": "..." }
{ "type": "cell_unlock","user": "tab_X7K3P", "nro": "...", "col": "..." }
{ "type": "cell_update","user": "tab_X7K3P", "nro": "...", "col": "...", "value": "..." }
```

## PITFALL CRÍTICO — doble lock: pestaña 2 sobreescribe el lock de pestaña 1

### Síntoma
- Tab A hace foco en celda → manda `editing` → server broadcastea `cell_lock` a Tab B ✅
- Tab B recibe `cell_lock`, re-renderiza la celda como bloqueada (readOnly)
- **Tab B igual dispara `onFocus` del input** → manda su propio `editing` al server
- Server registra Tab B como nuevo dueño del lock → Tab A queda bloqueada

### Causa
React re-renderiza el input con `readOnly=true` pero el `onFocus` igual se dispara si el elemento recibe foco durante el render. El `onFocus` no tiene acceso al estado `lockedByOther` en el momento correcto.

### Fix — pasar `isLockedByOther` directamente al handler
```typescript
const handleCellFocus = useCallback((row: ContadoRow, col: string, isLockedByOther: boolean) => {
  if (isLockedByOther) return   // ← no emitir si la celda ya la tiene otro
  const nro = String(row[COL_NRO] ?? '')
  if (nro) sendEditing(nro, col)
}, [COL_NRO, sendEditing])

// En el JSX:
onFocus={() => handleCellFocus(row, col, lockedByOther)}
```

## PITFALL — self-lock: el dueño se bloquea a sí mismo

### Síntoma
La pestaña que tomó el lock también ve la celda como bloqueada (readOnly, cursor not-allowed).

### Causa 1 — cellLocks guarda locks propios
El hook almacena en `cellLocks` cualquier `cell_lock` que llega, incluyendo los propios.
El servidor excluye al emisor del broadcast (`exclude=ws_id`), pero si por algún motivo el mensaje
llegara, quedaría guardado.

### Fix en el hook (filtro en origen)
```typescript
case 'cell_lock':
  // Solo guardar si es de OTRO usuario
  if (msg.user !== user) {
    setCellLocks(prev => {
      const next = new Map(prev)
      next.set(`${msg.nro}::${msg.col}`, { user: msg.user, color: msg.color })
      return next
    })
  }
  break
```

### Causa 2 — comparación en el componente con variable incorrecta
El componente usaba `currentUser` (prop opcional) en lugar de `resolvedUser` (que incluye el fallback al tabId).

### Fix en el componente
```typescript
const resolvedUser = currentUser || getTabId()
// ...
const lockedByOther = !!lock && lock.user !== resolvedUser
```

Usar `lockedByOther` (no `!!lock`) en: `readOnly`, `cursor`, `color`, `border` del td, y `title`.

## Diagnóstico con logs del backend

Agregar temporalmente al `handle_editing` del room:
```python
print(f"[WS] LOCK: ws_id={ws_id[:8]} user={self.users[ws_id]['user']} nro={nro} col={col} → broadcast a {[v['user'] for k,v in self.users.items() if k != ws_id]}", flush=True)
```

Si ves el mismo `nro+col` apareciendo dos veces con users distintos, es el bug del doble-focus.
Si ves `broadcast a []` cuando debería haber otros conectados, verificar que los joins se registraron.

## Estado del room (backend)

```python
class ContadoRoom:
    connections: Dict[str, WebSocket]   # ws_id → ws
    users: Dict[str, dict]              # ws_id → { user, color, editing_nro, editing_col }
    locks: Dict[tuple, str]             # (nro, col) → ws_id
```

El `ws_id` es un UUID generado por conexión. El `user` es el tabId del cliente.
Los locks se limpian automáticamente al desconectarse (en `disconnect()`).

## UI de presencia

- Badge "Vos: tab_X7K3P" (fondo oscuro) — identifica la pestaña actual
- Indicador 🟢/🔴 — estado de conexión WS
- Avatares circulares con iniciales y color — una por usuario conectado
- "✏️ tab_X7K → col REFERENTE" — muestra qué columna edita cada otro usuario
- Borde de color en celda + mini-badge con iniciales — solo visible para los DEMÁS (no para el dueño)
