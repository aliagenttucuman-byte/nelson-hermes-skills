import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Document {
  key: string
  size: number
  last_modified: string
}

interface Source {
  document: string
  score: number
  text: string
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)
  
  // Ask state
  const [question, setQuestion] = useState('')
  const [asking, setAsking] = useState(false)
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState<Source[]>([])
  const [stats, setStats] = useState<any>(null)

  const fetchDocuments = useCallback(async () => {
    setLoading(true)
    try {
      const res = await axios.get(`${API_URL}/documents`)
      setDocuments(res.data.documents || [])
    } catch (err) {
      setMessage('Error al cargar documentos')
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchStats = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/stats`)
      setStats(res.data)
    } catch (err) {
      // Silencioso
    }
  }, [])

  useEffect(() => {
    fetchDocuments()
    fetchStats()
  }, [fetchDocuments, fetchStats])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return

    setUploading(true)
    setMessage('')

    const formData = new FormData()
    formData.append('file', file)

    try {
      await axios.post(`${API_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setMessage(`\u2705 "${file.name}" subido y procesado correctamente`)
      setFile(null)
      fetchDocuments()
      fetchStats()
    } catch (err: any) {
      setMessage(`\u274c Error: ${err.response?.data?.detail || err.message}`)
    } finally {
      setUploading(false)
    }
  }

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return

    setAsking(true)
    setAnswer('')
    setSources([])

    try {
      const res = await axios.post(`${API_URL}/ask`, { question })
      setAnswer(res.data.answer)
      setSources(res.data.sources || [])
    } catch (err: any) {
      setAnswer(`Error: ${err.response?.data?.detail || err.message}`)
    } finally {
      setAsking(false)
    }
  }

  return (
    <div className="min-h-screen p-6 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-2 text-blue-400">RAG PoC</h1>
      <p className="text-gray-400 mb-6">Subi un PDF y hace preguntas sobre el contenido. Etapa 2 — Equipo Nelson</p>

      {/* Stats */}
      {stats && (
        <div className="bg-slate-900 rounded-lg p-3 mb-6 border border-slate-700 flex gap-4 text-sm">
          <span className="text-gray-400">Chunks indexados: <span className="text-green-400 font-mono">{stats.points_count}</span></span>
          <span className="text-gray-400">Documentos: <span className="text-blue-400 font-mono">{documents.length}</span></span>
        </div>
      )}

      {/* Upload */}
      <div className="bg-slate-800 rounded-xl p-6 mb-6 border border-slate-700">
        <h2 className="text-lg font-semibold mb-4 text-white">Subir documento</h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-gray-300
              file:mr-4 file:py-2 file:px-4
              file:rounded-lg file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-600 file:text-white
              hover:file:bg-blue-500
              cursor-pointer"
          />
          {file && (
            <p className="text-sm text-gray-400">
              Seleccionado: <span className="text-white">{file.name}</span> ({formatBytes(file.size)})
            </p>
          )}
          <button
            type="submit"
            disabled={!file || uploading}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed
              text-white font-semibold py-2 px-4 rounded-lg transition-colors"
          >
            {uploading ? 'Procesando...' : 'Subir PDF'}
          </button>
        </form>
        {message && (
          <p className="mt-4 text-sm">{message}</p>
        )}
      </div>

      {/* Ask */}
      <div className="bg-slate-800 rounded-xl p-6 mb-6 border border-slate-700">
        <h2 className="text-lg font-semibold mb-4 text-white">Hacer una pregunta</h2>
        <form onSubmit={handleAsk} className="flex flex-col gap-4">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ej: Que frameworks de IA menciona el documento?"
            className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            disabled={!question.trim() || asking}
            className="bg-green-600 hover:bg-green-500 disabled:bg-slate-600 disabled:cursor-not-allowed
              text-white font-semibold py-2 px-4 rounded-lg transition-colors"
          >
            {asking ? 'Pensando...' : 'Preguntar'}
          </button>
        </form>

        {answer && (
          <div className="mt-4 space-y-4">
            <div className="bg-slate-900 rounded-lg p-4 border border-slate-600">
              <h3 className="text-sm font-semibold text-green-400 mb-2">Respuesta:</h3>
              <p className="text-gray-200 whitespace-pre-wrap">{answer}</p>
            </div>

            {sources.length > 0 && (
              <div className="bg-slate-900 rounded-lg p-4 border border-slate-600">
                <h3 className="text-sm font-semibold text-blue-400 mb-2">Fuentes encontradas:</h3>
                <ul className="space-y-2">
                  {sources.map((src, i) => (
                    <li key={i} className="text-xs text-gray-400 border-l-2 border-blue-500 pl-3">
                      <span className="text-white font-medium">{src.document}</span>
                      <span className="text-green-400 ml-2">(score: {src.score.toFixed(3)})</span>
                      <p className="mt-1 text-gray-500">{src.text}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Documents list */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Documentos ({documents.length})</h2>
          <button
            onClick={() => { fetchDocuments(); fetchStats(); }}
            disabled={loading}
            className="text-sm text-blue-400 hover:text-blue-300 disabled:text-gray-500"
          >
            {loading ? 'Cargando...' : '\u21bb Actualizar'}
          </button>
        </div>

        {documents.length === 0 ? (
          <p className="text-gray-500 text-sm">No hay documentos subidos todavia.</p>
        ) : (
          <ul className="divide-y divide-slate-700">
            {documents.map((doc) => (
              <li key={doc.key} className="py-3 flex items-center justify-between">
                <div>
                  <p className="text-white font-medium">{doc.key}</p>
                  <p className="text-xs text-gray-400">
                    {formatBytes(doc.size)} \u00b7 {new Date(doc.last_modified).toLocaleString()}
                  </p>
                </div>
                <span className="text-xs bg-green-900 text-green-300 px-2 py-1 rounded">PDF</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
