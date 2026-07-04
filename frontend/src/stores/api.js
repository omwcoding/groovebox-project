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

  // Se il server risponde 401, il token JWT è scaduto o non valido.
  // Forza la pulizia del token e reindirizza alla pagina di login.
  if (response.status === 401) {
    localStorage.removeItem('groovebox_token')
    // Usiamo location.href per rinfrescare lo stato complessivo dell'applicazione
    window.location.href = '/login'
    return
  }

  // Gestione del parsing JSON sicuro
  let data = {}
  const contentType = response.headers.get('Content-Type')
  if (contentType && contentType.includes('application/json')) {
    try {
      data = await response.json()
    } catch (_) {
      // Ignora l'errore se il JSON è malformato
    }
  }

  if (!response.ok) {
    const error = new Error(data.message || `Errore del server (${response.status})`)
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
