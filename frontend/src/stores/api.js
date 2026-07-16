/**
 * GrooveBox - Client API Centralizzato
 * ===================================
 * Configura le chiamate HTTP verso il backend, iniettando automaticamente il
 * token JWT di autorizzazione e gestendo centralitamente i fallimenti di sessione (HTTP 401).
 */

const API_BASE = '/api'

async function request(endpoint, options = {}) {
  const isFormData = options.body instanceof FormData
  const headers = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...options.headers
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    credentials: 'include',
    headers
  })

  // Gestione centralizzata dei token non validi o scaduti (HTTP 401)
  if (response.status === 401 && !endpoint.includes('/auth/login')) {
    try {
      const { useAuthStore } = await import('@/stores/auth')
      const authStore = useAuthStore()
      await authStore.logout()
    } catch (_) {
      localStorage.removeItem('mint_user')
    }
    window.location.href = '/login'
    return
  }

  let data = {}
  const contentType = response.headers.get('Content-Type')
  if (contentType && contentType.includes('application/json')) {
    try {
      data = await response.json()
    } catch (_) {
      // Ignora l'errore in caso di risposta vuota o non formattata JSON
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
