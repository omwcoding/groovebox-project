/**
 * GrooveBox — Helper HTTP centralizzato
 *
 * Tutte le chiamate API passano da qui: gestisce automaticamente
 * l'header Authorization con il token JWT salvato in localStorage.
 */

const API_BASE = '/api'

async function request(endpoint, options = {}) {
  const token = localStorage.getItem('groovebox_token')

  const isFormData = options.body instanceof FormData
  const headers = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...options.headers
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  })

  const data = await response.json()

  if (!response.ok) {
    const error = new Error(data.message || 'Errore di rete')
    error.status = response.status
    error.data = data
    throw error
  }

  return data
}

export const api = {
  get: (url) => request(url),
  post: (url, body) => request(url, {
    method: 'POST',
    body: body instanceof FormData ? body : JSON.stringify(body)
  }),
  put: (url, body) => request(url, { method: 'PUT', body: JSON.stringify(body) }),
  delete: (url) => request(url, { method: 'DELETE' })
}
