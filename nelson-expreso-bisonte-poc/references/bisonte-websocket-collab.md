# Bisonte — Colaboración WebSocket en tiempo real (jun 2026)

## Arquitectura implementada

### Backend: `ws_contado.py`
- FastAPI WebSocket en `/api/v1/ws/contado`
- Room singleton `ContadoRoom` con:
  - `connections`: `Dict[ws_id, WebSocket]`
  - `users`: `Dict[ws_id, { user, color, editing_nro, editing_col }]`
  - `locks`: `Dict[(nro, col), ws_id]`
- El endpoint hace `await websocket.accept()` UNA sola vez — la clase `connect()` del room NO debe llamar `accept()` (genera doble accept si se usa)

### Frontend: `useContadoWS.ts` + `ContadoTable.tsx`
- `getTabId()` genera ID por pestaña usando `sessionStorage` — cada pestaña nueva tiene su propio ID
- El hook expone `getCellLocks()` (función, no estado) + `cellLocksVer` (contador)

---

## PITFALL CRÍTICO — cellLocks como useState causa blur espurio

**Síntoma:** escribís en una celda → la otra pestaña la ve bloqueada → al tocarla el original pierde el lock.

**Causa:** si `cellLocks` es `useState(Map)`, cada `cell_lock` remoto → re-render de toda la tabla → el input activo puede disparar `onBlur` → `sendUpdate`/`sendLeave` → el servidor suelta el lock.

**Fix:** usar `useRef` para el Map + contador de versión para el re-render mínimo:

```typescript
const cellLocksRef   = useRef<Map<string, CellLock>>(new Map())
const [cellLocksVer, setCellLocksVer] = useState(0)

// Al recibir cell_lock remoto:
cellLocksRef.current.set(key, { user, color })
setCellLocksVer(v => v + 1)   // re-render mínimo — NO destruye el foco activo

// El componente lee el Map directo (sin re-render por lectura):
const getCellLocks = useCallback(() => cellLocksRef.current, [])
```

El componente consume `cellLocksVer` con `void cellLocksVer` para que React sepa cuándo redibujar los bordes, pero el input activo no se toca.

---

## PITFALL — onFocus de la pestaña bloqueada emite editing

**Síntoma:** la pestaña 2 ve la celda bloqueada → pero igual al recibirla bloqueada manda su propio `editing` → doble lock en el servidor.

**Causa:** cuando llega `cell_lock` y React re-renderiza, si el foco del DOM estaba en esa celda, `onFocus` se dispara de nuevo.

**Fix:** `handleCellFocus` recibe `isLockedByOther` y retorna inmediatamente si es true:

```typescript
const handleCellFocus = useCallback((row, col, isLockedByOther: boolean) => {
  if (isLockedByOther) return
  const nro = String(row[COL_NRO] ?? '')
  if (nro) sendEditing(nro, col)
}, [COL_NRO, sendEditing])

// En el JSX:
onFocus={() => handleCellFocus(row, col, lockedByOther)}
```

---

## PITFALL — lock se aplica al propio dueño

**Síntoma:** hacés foco en una celda → queda bloqueada para vos mismo.

**Causa:** `readOnly={!!lock}` usa cualquier lock, incluyendo el propio.

**Fix en dos lugares:**

1. En el hook, al recibir `cell_lock`:
```typescript
if (msg.user !== user) {  // solo guardar locks de OTROS
  cellLocksRef.current.set(...)
}
```

2. En el componente al renderizar:
```typescript
const lockedByOther = !!lock && lock.user !== resolvedUser
// usar lockedByOther en readOnly, cursor, color, border — no !!lock
```

---

## PITFALL — sendUpdate/sendLeave se disparan aunque la celda ya no sea tuya

**Síntoma:** blur espurio (re-render) suelta el lock del dueño original.

**Fix:** `myLockRef` trackea qué celda tiene esta pestaña. Antes de soltar, verificar:

```typescript
const myLockRef = useRef<{ nro: string; col: string } | null>(null)

const sendUpdate = useCallback((nro, col, value) => {
  const mine = myLockRef.current
  if (!mine || mine.nro !== nro || mine.col !== col) return  // ya no es mi celda
  myLockRef.current = null
  ws.send(JSON.stringify({ type: 'update', user, nro, col, value }))
}, [user])
```

---

## PITFALL — double accept en el room

El método `ContadoRoom.connect()` llama `await ws.accept()` pero el endpoint WS de FastAPI ya hace `accept()`. Si se usa `connect()` del room → doble accept → error silencioso con doble `connection open` en logs.

**Fix:** el endpoint registra la conexión manualmente en el room sin llamar `connect()`:
```python
_room.connections[ws_id] = websocket
_room.users[ws_id] = { "user": user, "color": _room._next_color(), ... }
await _room.broadcast_presence()
```

---

## Diagnóstico con logs del servidor

Agregar prints en el backend para ver exactamente qué pasa:

```python
print(f"[WS] JOIN: ws_id={ws_id[:8]} user={user} — total={len(_room.connections)}", flush=True)
print(f"[WS] LOCK: ws_id={ws_id[:8]} user={...} nro={nro} col={col} → broadcast a {[v['user'] for k,v in self.users.items() if k != ws_id]}", flush=True)
```

Señal de bug: si aparece `LOCK: tab_X → broadcast a []` cuando hay 2 pestañas, significa que la pestaña que NO debería emitir está enviando `editing` igual.

---

## ID de pestaña con sessionStorage

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

`sessionStorage` es exclusivo por pestaña — no se comparte entre pestañas aunque sean del mismo origen. `localStorage` SÍ se comparte → no usar para tabId.

---

## Nota arquitectural

El `spa_proxy.py` (Python `http.server`) NO soporta WebSocket upgrade.
El WS conecta directo al backend FastAPI en `:9000`, no al proxy `:9090`.
Con nginx como reverse proxy se puede centralizar en un solo puerto.
