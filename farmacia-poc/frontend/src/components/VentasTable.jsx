const CAT_COLORS = {
  'antibióticos': 'tag-red',
  'analgésicos': 'tag-orange',
  'cardiología': 'tag-blue',
  'dermatología': 'tag-purple',
  'vitaminas': 'tag-green',
}

export default function VentasTable({ data }) {
  const { ventas = [], total_ventas = 0, cantidad_transacciones = 0 } = data

  // Agrupar por farmacéutico
  const porFarmaceutico = {}
  ventas.forEach(v => {
    porFarmaceutico[v.farmaceutico] = (porFarmaceutico[v.farmaceutico] || 0) + v.importe
  })
  const topFarm = Object.entries(porFarmaceutico).sort((a, b) => b[1] - a[1])[0]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.75rem' }}>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Total del Día</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-green)', marginTop: '0.3rem' }}>
            ${total_ventas.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
          </div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Transacciones</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-blue)', marginTop: '0.3rem' }}>
            {cantidad_transacciones}
          </div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Ticket Promedio</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-purple)', marginTop: '0.3rem' }}>
            ${cantidad_transacciones > 0 ? (total_ventas / cantidad_transacciones).toFixed(0) : '0'}
          </div>
        </div>
        {topFarm && (
          <div className="card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Mejor Vendedor</div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-yellow)', marginTop: '0.3rem' }}>
              🏆 {topFarm[0].split(' ')[0]}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>${topFarm[1].toFixed(0)}</div>
          </div>
        )}
      </div>

      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Hora</th>
                <th>Producto</th>
                <th>Categoría</th>
                <th style={{textAlign:'right'}}>Cant.</th>
                <th style={{textAlign:'right'}}>P. Unit.</th>
                <th style={{textAlign:'right'}}>Importe</th>
                <th>Farmacéutico</th>
              </tr>
            </thead>
            <tbody>
              {ventas.map(v => (
                <tr key={v.id}>
                  <td style={{ color: 'var(--text-muted)', width: '40px' }}>{v.id}</td>
                  <td style={{ fontFamily: 'monospace', color: 'var(--accent-blue)', fontWeight: 600 }}>{v.hora}</td>
                  <td style={{ fontWeight: 500, maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{v.producto}</td>
                  <td>
                    <span className={`tag ${CAT_COLORS[v.categoria] || 'tag-blue'}`}>
                      {v.categoria}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right', fontWeight: 700 }}>{v.cantidad}</td>
                  <td style={{ textAlign: 'right', color: 'var(--text-muted)' }}>${v.precio_unitario.toFixed(2)}</td>
                  <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--accent-green)' }}>
                    ${v.importe.toFixed(2)}
                  </td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{v.farmaceutico}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
