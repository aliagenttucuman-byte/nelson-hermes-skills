import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from './api.js'
import KPICards from './components/KPICards.jsx'
import ProductosTable from './components/ProductosTable.jsx'
import VentasTable from './components/VentasTable.jsx'
import ProveedoresPanel from './components/ProveedoresPanel.jsx'
import ChatPanel from './components/ChatPanel.jsx'
import './App.css'

export default function App() {
  const [kpis, setKpis] = useState(null)
  const [productos, setProductos] = useState({ productos: [], total: 0, categorias: [] })
  const [ventas, setVentas] = useState({ ventas: [], total_ventas: 0 })
  const [proveedores, setProveedores] = useState({ proveedores: [], deuda_total: 0 })
  const [activeTab, setActiveTab] = useState('productos')
  const [chatOpen, setChatOpen] = useState(false)
  const [loading, setLoading] = useState(true)

  const loadData = useCallback(async () => {
    try {
      const [k, p, v, pr] = await Promise.all([
        api.kpis(),
        api.productos(),
        api.ventas(),
        api.proveedores()
      ])
      setKpis(k)
      setProductos(p)
      setVentas(v)
      setProveedores(pr)
    } catch (e) {
      console.error('Error loading data:', e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 60000) // refresh cada minuto
    return () => clearInterval(interval)
  }, [loadData])

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <div className="logo">💊</div>
          <div>
            <h1 className="header-title">Farmacia Dashboard</h1>
            <p className="header-sub">Sistema de Gestión · {kpis?.fecha || '...'}</p>
          </div>
        </div>
        <div className="header-right">
          {kpis && (
            <div className="header-status">
              <span className="status-dot"></span>
              <span>Actualizado {kpis.hora_actualizacion}</span>
            </div>
          )}
          <button className="btn-refresh" onClick={loadData} title="Actualizar datos">
            ↻
          </button>
        </div>
      </header>

      <main className="main">
        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Cargando datos...</p>
          </div>
        ) : (
          <>
            <KPICards kpis={kpis} />

            <div className="tabs">
              <button
                className={`tab ${activeTab === 'productos' ? 'active' : ''}`}
                onClick={() => setActiveTab('productos')}
              >
                📦 Productos
                {kpis?.productos_bajo_stock > 0 && (
                  <span className="badge badge-red">{kpis.productos_bajo_stock}</span>
                )}
              </button>
              <button
                className={`tab ${activeTab === 'ventas' ? 'active' : ''}`}
                onClick={() => setActiveTab('ventas')}
              >
                💰 Ventas del día
                <span className="badge badge-blue">{ventas.cantidad_transacciones}</span>
              </button>
              <button
                className={`tab ${activeTab === 'proveedores' ? 'active' : ''}`}
                onClick={() => setActiveTab('proveedores')}
              >
                🚚 Proveedores
              </button>
            </div>

            <div className="tab-content">
              {activeTab === 'productos' && (
                <ProductosTable
                  data={productos}
                  onFilter={(params) => api.productos(params).then(setProductos)}
                />
              )}
              {activeTab === 'ventas' && <VentasTable data={ventas} />}
              {activeTab === 'proveedores' && <ProveedoresPanel data={proveedores} />}
            </div>
          </>
        )}
      </main>

      {/* FAB Chat */}
      <button
        className={`fab ${chatOpen ? 'fab-active' : ''}`}
        onClick={() => setChatOpen(!chatOpen)}
        title="Asistente IA"
      >
        {chatOpen ? '✕' : '🤖'}
      </button>

      {chatOpen && (
        <ChatPanel onClose={() => setChatOpen(false)} kpis={kpis} />
      )}
    </div>
  )
}
