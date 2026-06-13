import { useState } from 'react'

const CAT_COLORS = {
  'antibióticos': 'tag-red',
  'analgésicos': 'tag-orange',
  'cardiología': 'tag-blue',
  'dermatología': 'tag-purple',
  'vitaminas': 'tag-green',
}

const CAT_ICONS = {
  'antibióticos': '🦠',
  'analgésicos': '💊',
  'cardiología': '❤️',
  'dermatología': '🧴',
  'vitaminas': '🌿',
}

export default function ProductosTable({ data, onFilter }) {
  const [filtroCategoria, setFiltroCategoria] = useState('')
  const [filtroAlerta, setFiltroAlerta] = useState('')
  const [buscar, setBuscar] = useState('')

  const handleFilter = (params) => {
    onFilter(params)
  }

  const applyFilters = (cat, alerta, search) => {
    const params = {}
    if (cat) params.categoria = cat
    if (alerta) params.alerta = alerta
    if (search) params.buscar = search
    handleFilter(params)
  }

  const { productos = [], total = 0 } = data

  const alertaLabel = (p) => {
    if (p.alerta === 'crítico') return <span className="tag tag-red">⚠️ Crítico</span>
    if (p.alerta === 'stock') return <span className="tag tag-yellow">📦 Bajo stock</span>
    if (p.alerta === 'vencimiento') return <span className="tag tag-orange">⏰ Vence pronto</span>
    return <span className="tag tag-green">✅ OK</span>
  }

  return (
    <div className="card">
      {/* Filtros */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          type="text"
          placeholder="🔍 Buscar producto..."
          value={buscar}
          onChange={e => {
            setBuscar(e.target.value)
            applyFilters(filtroCategoria, filtroAlerta, e.target.value)
          }}
          style={{
            background: 'var(--bg-secondary)', border: '1px solid var(--border)', color: 'var(--text-primary)',
            padding: '0.45rem 0.75rem', borderRadius: '8px', fontSize: '0.82rem', flex: '1', minWidth: '180px'
          }}
        />
        <select
          value={filtroCategoria}
          onChange={e => {
            setFiltroCategoria(e.target.value)
            applyFilters(e.target.value, filtroAlerta, buscar)
          }}
          style={{
            background: 'var(--bg-secondary)', border: '1px solid var(--border)', color: 'var(--text-secondary)',
            padding: '0.45rem 0.75rem', borderRadius: '8px', fontSize: '0.82rem', cursor: 'pointer'
          }}
        >
          <option value="">Todas las categorías</option>
          {(data.categorias || []).map(c => (
            <option key={c} value={c}>{CAT_ICONS[c]} {c.charAt(0).toUpperCase() + c.slice(1)}</option>
          ))}
        </select>
        <select
          value={filtroAlerta}
          onChange={e => {
            setFiltroAlerta(e.target.value)
            applyFilters(filtroCategoria, e.target.value, buscar)
          }}
          style={{
            background: 'var(--bg-secondary)', border: '1px solid var(--border)', color: 'var(--text-secondary)',
            padding: '0.45rem 0.75rem', borderRadius: '8px', fontSize: '0.82rem', cursor: 'pointer'
          }}
        >
          <option value="">Todas las alertas</option>
          <option value="crítico">⚠️ Crítico</option>
          <option value="stock">📦 Bajo stock</option>
          <option value="vencimiento">⏰ Por vencer</option>
        </select>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
          {total} productos
        </span>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Producto</th>
              <th>Categoría</th>
              <th>Laboratorio</th>
              <th style={{textAlign:'right'}}>Stock</th>
              <th style={{textAlign:'right'}}>Mín.</th>
              <th style={{textAlign:'right'}}>P. Compra</th>
              <th style={{textAlign:'right'}}>P. Venta</th>
              <th>Vencimiento</th>
              <th style={{textAlign:'right'}}>Ventas 30d</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {productos.map(p => (
              <tr key={p.id} className={p.alerta ? `alert-${p.alerta.replace('í','i')}` : 'alert-ok'}>
                <td style={{ fontWeight: 500, maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {p.nombre}
                </td>
                <td>
                  <span className={`tag ${CAT_COLORS[p.categoria] || 'tag-blue'}`}>
                    {CAT_ICONS[p.categoria]} {p.categoria}
                  </span>
                </td>
                <td style={{ color: 'var(--text-secondary)' }}>{p.laboratorio}</td>
                <td style={{
                  textAlign: 'right',
                  fontWeight: 700,
                  color: p.bajo_stock ? 'var(--accent-red)' : 'var(--accent-green)'
                }}>
                  {p.stock_actual}
                </td>
                <td style={{ textAlign: 'right', color: 'var(--text-muted)' }}>{p.stock_minimo}</td>
                <td style={{ textAlign: 'right', color: 'var(--text-muted)' }}>${p.precio_compra.toFixed(2)}</td>
                <td style={{ textAlign: 'right', color: 'var(--accent-green)', fontWeight: 600 }}>${p.precio_venta.toFixed(2)}</td>
                <td style={{
                  color: p.dias_para_vencer <= 7 ? 'var(--accent-red)'
                    : p.dias_para_vencer <= 30 ? 'var(--accent-orange)'
                    : 'var(--text-secondary)',
                  fontWeight: p.dias_para_vencer <= 30 ? 600 : 400
                }}>
                  {p.vencimiento}
                  {p.dias_para_vencer <= 30 && (
                    <span style={{ fontSize: '0.68rem', display: 'block', color: 'var(--accent-red)' }}>
                      en {p.dias_para_vencer}d
                    </span>
                  )}
                </td>
                <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>{p.ventas_30d}</td>
                <td>{alertaLabel(p)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
