export default function ProveedoresPanel({ data }) {
  const { proveedores = [], deuda_total = 0 } = data

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(239,68,68,0.08)',
        border: '1px solid rgba(239,68,68,0.3)',
        borderRadius: '10px',
        padding: '0.875rem 1.25rem'
      }}>
        <div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Deuda Total con Proveedores
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#fca5a5', marginTop: '0.25rem' }}>
            ${deuda_total.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
          </div>
        </div>
        <div style={{ fontSize: '3rem' }}>🚚</div>
      </div>

      {/* Tarjetas de proveedores */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '0.75rem' }}>
        {proveedores.map(p => {
          const urgente = p.dias_desde_pedido > 30
          return (
            <div
              key={p.id}
              className="card"
              style={{
                borderLeft: `3px solid ${urgente ? 'var(--accent-red)' : 'var(--accent-blue)'}`,
                transition: 'transform 0.2s'
              }}
              onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.3 }}>
                  {p.nombre}
                </h3>
                {urgente && <span className="tag tag-red">⚠️ Sin pedido +30d</span>}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Deuda</div>
                  <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fca5a5' }}>
                    ${p.deuda_pendiente.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Condición</div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--accent-blue)' }}>{p.condicion_pago}</div>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--border)', paddingTop: '0.6rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  📅 Último pedido: <span style={{ color: urgente ? 'var(--accent-red)' : 'var(--text-secondary)' }}>
                    {p.ultimo_pedido} (hace {p.dias_desde_pedido}d)
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  📦 Pedidos este mes: <span style={{ color: 'var(--text-secondary)' }}>{p.pedidos_mes}</span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  📧 {p.contacto}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
