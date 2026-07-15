/**
 * GrooveBox - Gestione Stato Autenticazione (Pinia)
 * =================================================
 * Store centralizzato per la memorizzazione dell'utente e del token di sessione,
 * la persistenza dello stato nel localStorage e l'esposizione delle azioni
 * per login, registrazione, logout e modifica profilo.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from './api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'administrator')
  const isCollector = computed(() => user.value?.role === 'collector')

  // Ripristina la sessione utente precedentemente salvata nel browser.
  function loadFromStorage() {
    const savedToken = localStorage.getItem('mint_token')
    const savedUser = localStorage.getItem('mint_user')
    if (savedToken && savedUser) {
      try {
        token.value = savedToken
        user.value = JSON.parse(savedUser)
      } catch (_) {
        localStorage.removeItem('mint_token')
        localStorage.removeItem('mint_user')
      }
    }
  }

  // Invia le credenziali per ottenere un token ed inizializzare la sessione.
  async function login(username, password) {
    const response = await api.post('/auth/login', { username, password })
    token.value = response.data.token
    user.value = response.data.user
    localStorage.setItem('mint_token', token.value)
    localStorage.setItem('mint_user', JSON.stringify(user.value))
    return response
  }

  // Invia la richiesta per registrare un nuovo account collector.
  async function register(userData) {
    const response = await api.post('/auth/register', userData)
    return response
  }

  // Termina la sessione utente eliminando i token locali.
  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('mint_token')
    localStorage.removeItem('mint_user')
  }

  // Sincronizza le informazioni utente aggiornate nello store e nello storage locale.
  function updateUser(updatedUser) {
    user.value = { ...user.value, ...updatedUser }
    localStorage.setItem('mint_user', JSON.stringify(user.value))
  }

  loadFromStorage()

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
