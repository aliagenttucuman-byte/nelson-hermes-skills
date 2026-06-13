// API base URL — nunca localhost hardcodeado
const BASE_URL = `http://${window.location.hostname}:8030`

export const api = {
  kpis: () => fetch(`${BASE_URL}/api/kpis`).then(r => r.json()),
  productos: (params = {}) => {
    const q = new URLSearchParams(params).toString()
    return fetch(`${BASE_URL}/api/productos${q ? '?' + q : ''}`).then(r => r.json())
  },
  ventas: () => fetch(`${BASE_URL}/api/ventas`).then(r => r.json()),
  proveedores: () => fetch(`${BASE_URL}/api/proveedores`).then(r => r.json()),
  chat: async function*(message, history, onToken) {
    const res = await fetch(`${BASE_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history })
    })
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()
          if (data === '[DONE]') return
          try {
            const parsed = JSON.parse(data)
            if (parsed.token) onToken(parsed.token)
            if (parsed.error) onToken(`\n[Error: ${parsed.error}]`)
          } catch {}
        }
      }
    }
  }
}
