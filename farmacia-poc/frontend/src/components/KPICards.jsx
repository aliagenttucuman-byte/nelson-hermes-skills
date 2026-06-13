export default function KPICards({ kpis }) {
  if (!kpis) return null

  const fmt = (n) => new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format(n)

  const cards = [
    {
      label: 'Ventas del Día',
      value: fmt(kpis.ventas_dia),
      sub: `${kpis.transacciones} transacciones · ticket $${(kpis.ticket_promedio).toFixed(0)}`,
      icon: '💰',
      color: 'green'
    },
    {
      label: 'Margen Bruto',
      value: fmt(kpis.margen_bruto),
      sub: `${kpis.margen_porcentaje}% sobre ventas`,
      icon: '📈',
      color: kpis.margen_porcentaje >= 30 ? 'green' : 'yellow'
    },
    {
      label: 'Alertas de Stock',
      value: kpis.productos_bajo_stock,
      sub: `${kpis.alertas_criticas} críticas`,
      icon: '📦',
      color: kpis.productos_bajo_stock > 0 ? 'red' : 'green'
    },
    {
      label: 'Por Vencer (30d)',
      value: kpis.productos_por_vencer,
      sub: 'productos en alerta',
      icon: '⏰',
      color: kpis.productos_por_vencer > 0 ? 'orange' : 'green'
    },
    {
      label: 'Rotación Promedio',
      value: `${kpis.rotacion_promedio}x`,
      sub: 'últimos 30 días',
      icon: '🔄',
      color: 'blue'
    },
    {
      label: 'Top Producto',
      value: '⭐',
      sub: kpis.top_producto_dia,
      icon: '🏆',
      color: 'purple'
    }
  ]

  const colorMap = {
    green: { border: '#10b981', glow: 'rgba(16,185,129,0.12)', text: '#6ee7b7' },
    red: { border: '#ef4444', glow: 'rgba(239,68,68,0.12)', text: '#fca5a5' },
    yellow: { border: '#f59e0b', glow: 'rgba(245,158,11,0.12)', text: '#fcd34d' },
    orange: { border: '#f97316', glow: 'rgba(249,115,22,0.12)', text: '#fdba74' },
    blue: { border: '#3b82f6', glow: 'rgba(59,130,246,0.12)', text: '#93c5fd' },
    purple: { border: '#8b5cf6', glow: 'rgba(139,92,246,0.12)', text: '#c4b5fd' }
  }

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '1rem',
      marginBottom: '0.5rem'
    }}>
      {cards.map((card, i) => {
        const c = colorMap[card.color]
        return (
          <div key={i} style={{
            background: 'var(--bg-card)',
            border: `1px solid ${c.border}`,
            borderRadius: '12px',
            padding: '1.1rem 1.25rem',
            background: c.glow,
            boxShadow: `0 0 0 1px ${c.border}30`,
            transition: 'transform 0.2s',
            cursor: 'default'
          }}
          onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
          onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', fontWeight: 600 }}>
                {card.label}
              </span>
              <span style={{ fontSize: '1.2rem' }}>{card.icon}</span>
            </div>
            <div style={{ fontSize: '1.6rem', fontWeight: 700, color: c.text, lineHeight: 1.2, marginBottom: '0.3rem' }}>
              {card.value}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              {card.sub}
            </div>
          </div>
        )
      })}
    </div>
  )
}
