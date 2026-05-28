import axios from 'axios'

// IMPORTANTE: el fallback debe ser '' (URL relativa), nunca 'http://localhost:PORT'
// Si el build se hace con VITE_API_URL vacío, las requests van relativas al mismo dominio.
// Esto funciona tanto en local (con proxy de Vite) como vía tunnel/producción.
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default apiClient
