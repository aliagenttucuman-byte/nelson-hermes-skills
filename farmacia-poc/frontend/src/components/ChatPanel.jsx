import { useState, useRef, useEffect } from 'react'
import { api } from '../api.js'

const QUICK_QUESTIONS = [
  '¿Qué productos están por vencer?',
  '¿Cuál es el margen del día?',
  '¿Qué hay que reponer urgente?',
  '¿Cuánto debemos a proveedores?',
  '¿Qué productos se venden más?'
]

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: '0.75rem'
    }}>
      {!isUser && (
        <div style={{
          width: '28px', height: '28px', borderRadius: '50%',
          background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.85rem', flexShrink: 0, marginRight: '0.5rem', marginTop: '2px'
        }}>🤖</div>
      )}
      <div style={{
        maxWidth: '80%',
        background: isUser
          ? 'linear-gradient(135deg, #3b82f6, #2563eb)'
          : 'var(--bg-secondary)',
        border: isUser ? 'none' : '1px solid var(--border)',
        borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
        padding: '0.6rem 0.875rem',
        fontSize: '0.82rem',
        lineHeight: '1.5',
        color: 'var(--text-primary)',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word'
      }}>
        {msg.content}
        {msg.streaming && (
          <span style={{
            display: 'inline-block', width: '8px', height: '14px',
            background: 'var(--accent-blue)', marginLeft: '2px',
            animation: 'blink 1s step-end infinite', verticalAlign: 'middle',
            borderRadius: '2px'
          }} />
        )}
      </div>
    </div>
  )
}

export default function ChatPanel({ onClose, kpis }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `¡Hola! 👋 Soy tu asistente de farmacia. Tengo acceso al estado actual del negocio en tiempo real.\n\n${kpis ? `📊 **Resumen rápido:**\n• Ventas hoy: $${kpis.ventas_dia?.toLocaleString('es-AR', { maximumFractionDigits: 0 })}\n• Alertas de stock: ${kpis.productos_bajo_stock}\n• Por vencer: ${kpis.productos_por_vencer}\n\n` : ''}¿En qué puedo ayudarte?`
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (text) => {
    const msg = text || input.trim()
    if (!msg || loading) return
    setInput('')

    const history = messages.filter(m => !m.streaming).map(m => ({
      role: m.role,
      content: m.content
    }))

    setMessages(prev => [...prev, { role: 'user', content: msg }])
    setLoading(true)

    // Agregar mensaje vacío del asistente para streaming
    setMessages(prev => [...prev, { role: 'assistant', content: '', streaming: true }])

    try {
      await api.chat(msg, history, (token) => {
        setMessages(prev => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (last.role === 'assistant') {
            updated[updated.length - 1] = {
              ...last,
              content: last.content + token,
              streaming: true
            }
          }
          return updated
        })
      })
    } catch (e) {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: `Error al conectar con el asistente: ${e.message}`,
          streaming: false
        }
        return updated
      })
    } finally {
      // Quitar indicador de streaming
      setMessages(prev => {
        const updated = [...prev]
        if (updated[updated.length - 1].streaming) {
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            streaming: false
          }
        }
        return updated
      })
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <>
      {/* Overlay */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
          zIndex: 199, backdropFilter: 'blur(2px)'
        }}
      />

      {/* Panel */}
      <div style={{
        position: 'fixed',
        right: '1.5rem',
        bottom: '5rem',
        width: '420px',
        maxWidth: 'calc(100vw - 3rem)',
        height: '560px',
        maxHeight: 'calc(100vh - 8rem)',
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
        borderRadius: '16px',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 300,
        boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
        animation: 'slideUp 0.25s ease'
      }}>
        <style>{`
          @keyframes slideUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
          @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
        `}</style>

        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0.875rem 1rem',
          borderBottom: '1px solid var(--border)',
          borderRadius: '16px 16px 0 0',
          background: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(139,92,246,0.15))'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{
              width: '32px', height: '32px', borderRadius: '50%',
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem'
            }}>🤖</div>
            <div>
              <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>Asistente Farmacia</div>
              <div style={{ fontSize: '0.65rem', color: 'var(--accent-green)', display: 'flex', alignItems: 'center', gap: '3px' }}>
                <span style={{ width: '6px', height: '6px', background: 'currentColor', borderRadius: '50%', display: 'inline-block' }}></span>
                Con contexto en tiempo real
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none', border: 'none', color: 'var(--text-muted)',
              cursor: 'pointer', fontSize: '1.1rem', padding: '0.25rem', borderRadius: '6px',
              transition: 'color 0.2s'
            }}
          >✕</button>
        </div>

        {/* Messages */}
        <div style={{
          flex: 1, overflowY: 'auto', padding: '1rem',
          display: 'flex', flexDirection: 'column'
        }}>
          {messages.map((msg, i) => <Message key={i} msg={msg} />)}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick suggestions */}
        {messages.length <= 1 && (
          <div style={{ padding: '0 1rem 0.5rem', display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {QUICK_QUESTIONS.map((q, i) => (
              <button
                key={i}
                onClick={() => sendMessage(q)}
                disabled={loading}
                style={{
                  background: 'rgba(59,130,246,0.1)',
                  border: '1px solid rgba(59,130,246,0.3)',
                  color: '#93c5fd',
                  padding: '0.35rem 0.65rem',
                  borderRadius: '20px',
                  fontSize: '0.7rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  whiteSpace: 'nowrap'
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(59,130,246,0.2)'}
                onMouseLeave={e => e.currentTarget.style.background = 'rgba(59,130,246,0.1)'}
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div style={{
          padding: '0.75rem 1rem',
          borderTop: '1px solid var(--border)',
          display: 'flex',
          gap: '0.5rem',
          alignItems: 'flex-end'
        }}>
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Pregunta sobre inventario, ventas, alertas..."
            disabled={loading}
            rows={1}
            style={{
              flex: 1,
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
              borderRadius: '10px',
              color: 'var(--text-primary)',
              padding: '0.55rem 0.75rem',
              fontSize: '0.82rem',
              resize: 'none',
              outline: 'none',
              fontFamily: 'inherit',
              lineHeight: 1.5,
              maxHeight: '80px',
              overflowY: 'auto',
              transition: 'border-color 0.2s'
            }}
            onFocus={e => e.target.style.borderColor = 'var(--accent-blue)'}
            onBlur={e => e.target.style.borderColor = 'var(--border)'}
          />
          <button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            style={{
              background: loading || !input.trim()
                ? 'var(--bg-card)'
                : 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              border: '1px solid var(--border)',
              color: loading || !input.trim() ? 'var(--text-muted)' : 'white',
              width: '36px', height: '36px',
              borderRadius: '10px',
              cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              fontSize: '1rem',
              transition: 'all 0.2s',
              flexShrink: 0
            }}
          >
            {loading ? '⏳' : '➤'}
          </button>
        </div>
      </div>
    </>
  )
}
