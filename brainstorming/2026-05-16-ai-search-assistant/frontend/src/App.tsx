import { useState } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8004'

interface Source {
  title: string
  url: string
  snippet: string
}

interface SearchResponse {
  answer: string
  sources: Source[]
}

export default function App() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await fetch(`${API}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })
      const data = await res.json()
      setResult(data)
    } catch {
      setError('Error al conectar con el servidor')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', color: '#f1f5f9', fontFamily: 'sans-serif', padding: '2rem' }}>
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem', color: '#38bdf8' }}>🔍 AI Search Assistant</h1>
        <p style={{ color: '#94a3b8', marginBottom: '2rem' }}>Buscá en internet con inteligencia artificial</p>

        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.75rem', marginBottom: '2rem' }}>
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="¿Qué querés saber?"
            style={{
              flex: 1, padding: '0.75rem 1rem', borderRadius: '8px',
              border: '1px solid #334155', background: '#1e293b',
              color: '#f1f5f9', fontSize: '1rem', outline: 'none'
            }}
          />
          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '0.75rem 1.5rem', borderRadius: '8px',
              background: loading ? '#334155' : '#0284c7',
              color: 'white', border: 'none', fontSize: '1rem',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? '⏳ Buscando...' : 'Buscar'}
          </button>
        </form>

        {error && <p style={{ color: '#f87171', marginBottom: '1rem' }}>{error}</p>}

        {result && (
          <div>
            <div style={{ background: '#1e293b', borderRadius: '12px', padding: '1.5rem', marginBottom: '1.5rem', borderLeft: '4px solid #38bdf8' }}>
              <h2 style={{ fontSize: '1rem', color: '#94a3b8', marginBottom: '0.75rem' }}>Respuesta</h2>
              <p style={{ lineHeight: '1.7', whiteSpace: 'pre-wrap' }}>{result.answer}</p>
            </div>

            <h3 style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.75rem' }}>Fuentes</h3>
            {result.sources.map((s, i) => (
              <div key={i} style={{ background: '#1e293b', borderRadius: '8px', padding: '1rem', marginBottom: '0.5rem' }}>
                <a href={s.url} target="_blank" rel="noreferrer" style={{ color: '#38bdf8', fontWeight: 'bold', fontSize: '0.9rem' }}>{s.title}</a>
                <p style={{ color: '#94a3b8', fontSize: '0.8rem', marginTop: '0.25rem' }}>{s.snippet}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
