/**
 * GrooveBox — Pinia Store: Autenticazione
 *
 * Gestisce login, registrazione, logout e persistenza del token JWT
 * in localStorage. Espone computed reattivi per ruolo e stato di auth.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from './api'

export const useAuthStore = defineStore('auth', () => {
  // --- State ---
  const user = ref(null)
  const token = ref(null)

  // --- Getters ---
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'administrator')
  const isCollector = computed(() => user.value?.role === 'collector')

  // --- Actions ---

  /** Ripristina la sessione da localStorage (chiamato al mount dell'app). */
  function loadFromStorage() {
    const savedToken = localStorage.getItem('groovebox_token')
    const savedUser = localStorage.getItem('groovebox_user')
    if (savedToken && savedUser) {
      token.value = savedToken
      user.value = JSON.parse(savedUser)
    }
  }

  /** Effettua il login e salva token + utente. */
  async function login(username, password) {
    const response = await api.post('/auth/login', { username, password })
    token.value = response.data.token
    user.value = response.data.user
    localStorage.setItem('groovebox_token', token.value)
    localStorage.setItem('groovebox_user', JSON.stringify(user.value))
    return response
  }

  /** Registra un nuovo Collector. */
  async function register(userData) {
    const response = await api.post('/auth/register', userData)
    return response
  }

  /** Effettua il logout e pulisce lo storage. */
  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('groovebox_token')
    localStorage.removeItem('groovebox_user')
  }

  /** Aggiorna i dati utente nello store e nel localStorage. */
  function updateUser(updatedUser) {
    user.value = { ...user.value, ...updatedUser }
    localStorage.setItem('groovebox_user', JSON.stringify(user.value))
  }

  return {
    user,
    token,
    isAuthenticated,
    isAdmin,
    isCollector,
    loadFromStorage,
    login,
    register,
    logout,
    updateUser
  }
})
