# WebSocket Colaboración — Cobranzas Contado

Estado: implementado jun 2026, funciona parcialmente. Pendiente de pulido.

## Archivos

- `backend/app/api/v1/endpoints/ws_contado.py` — endpoint FastAPI + room manager
- `frontend/src/hooks/useContadoWS.ts` — hook React
- `frontend/src/components/ContadoTable.tsx` — integración visual

## URL del WebSocket

Conecta directo al backend `:9000`, NO al spa_proxy `:9090`.
El spa_proxy es HTTP-puro (python `http.server`) — no soporta WebSocket upgrade.

```
ws://100.110.8.13:9000/api/v1/ws/contado
```

## Identificación de pestañas (sin login)

Cada pestaña genera un tabId único con `sessionStorage`:
- `sessionStorage` NO se comparte entre pestañas (a diferencia de `localStorage`)
- Formato: `tab_XXXXX` (5 chars aleatorios)
- Persiste mientras la pestaña esté abierta

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

## Protocolo de mensajes

### Cliente → Servidor
```json
{ "type": "join",    "user": "tab_X7K3P" }
{ "type": "editing", "user": "tab_X7K3P", "nro": "A.0053.00111316", "col": "REFERENTE" }
{ "type": "update",  "user": "tab_X7K3P", "nro": "...", "col": "...", "value": "CC" }
{ "type": "leave",   "user": "tab_X7K3P", "nro": "...", "col": "..." }
{ "type": "ping" }
```

### Servidor → Clientes
```json
{ "type": "presence",   "users": [{ "user", "color", "editing_nro", "editing_col" }] }
{ "type": "cell_lock",  "user": "...", "color": "#e53e3e", "nro": "...", "col": "..." }
{ "type": "cell_unlock","user": "...", "nro": "...", "col": "..." }
{ "type": "cell_update","user": "...", "nro": "...", "col": "...", "value": "..." }
```

## Diseño anti-blur (crítico)

### Problema
`cellLocks` como `useState(Map)` → cualquier lock remoto causaba re-render de la tabla
→ el input activo podía perder foco → disparaba `onBlur` → soltaba el lock del dueño.

### Solución implementada

```typescript
// Ref (no estado) — cambios NO causan re-render del input activo
const cellLocksRef = useRef<Map<string, CellLock>>(new Map())

// Contador de versión — sube cuando el Map cambia, triggerea re-render mínimo
const [cellLocksVer, setCellLocksVer] = useState(0)

// Qué celda tiene bloqueada ESTA pestaña
const myLockRef = useRef<{ nro: string; col: string } | null>(null)
```

`sendUpdate` y `sendLeave` verifican `myLockRef` antes de soltar — si la celda ya no es mía, no mando nada.

### Filtro en onmessage
```typescript
case 'cell_lock':
  // Solo guardar si es de OTRO — mi propio lock no me bloquea
  if (msg.user !== user) {
    cellLocksRef.current.set(key, { user: msg.user, color: msg.color })
    setCellLocksVer(v => v + 1)
  }
```

### Filtro en onFocus
```typescript
// No emitir editing si la celda ya la tiene otro
const handleCellFocus = (row, col, isLockedByOther) => {
  if (isLockedByOther) return
  sendEditing(nro, col)
}
```

## Issues pendientes conocidos

1. **Blur espurio** — en algunos casos de re-render el input pierde foco brevemente
2. **Sin login** — tabId aleatorio, no hay identidad real
3. **Cuando se agregue login** — pasar `currentUser` desde `HomePage` al `ContadoTable`
4. **nginx como proxy único** — cuando se agregue, el WS puede ir por `:9090` también

## Backend — ContadoRoom

Singleton `_room` en memoria. El endpoint gestiona el ciclo de vida:
1. `accept()` → esperar mensaje `join` → registrar en room → `broadcast_presence()`
2. Loop: `editing` → `handle_editing(ws_id, nro, col)` con lock exclusivo
3. `update` → broadcast a todos excepto emisor → unlock
4. `disconnect` → liberar todos los locks del usuario → `broadcast_presence()`

El lock es por `ws_id` (conexión), no por `user` string — dos pestañas del mismo usuario
físico tienen ws_id distintos y no se bloquean entre sí.
