<!--
Mint - Pagina Login
==================
Consente l'accesso alla piattaforma per gli utenti registrati tramite 
l'inserimento di username e password.
-->

<script setup>
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  
  if (!username.value.trim()) {
    error.value = 'L\'username è obbligatorio'
    return
  }
  if (!password.value) {
    error.value = 'La password è obbligatoria'
    return
  }

  loading.value = true
  try {
    await authStore.login(username.value, password.value)
    router.push('/dashboard')
  } catch (err) {
    error.value = err.message || 'Credenziali non valide'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4 relative overflow-hidden animate-fade-in">
    <!-- Background glow -->
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-brand-secondary/15 rounded-full blur-[130px] animate-pulse pointer-events-none"></div>

    <div class="w-full max-w-md z-10">
      <!-- Header -->
      <div class="text-center mb-10">
        <RouterLink to="/" class="inline-flex p-3 bg-white/5 rounded-2xl border border-white/10 mb-4 hover:scale-105 transition-transform">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="text-brand-secondary"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
        </RouterLink>
        <h1 class="text-3xl font-extrabold tracking-tight bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
          Bentornato su Mint
        </h1>
        <p class="text-white/30 text-sm font-medium mt-1">Accedi per gestire il tuo vault musicale</p>
      </div>

      <!-- Card -->
      <form
        novalidate
        @submit.prevent="handleLogin"
        class="glass-panel p-8 rounded-apple-2xl space-y-6 shadow-2xl"
      >
        <!-- Errore -->
        <div
          v-if="error"
          class="bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold rounded-2xl px-4 py-3"
        >
          {{ error }}
        </div>

        <!-- Username -->
        <div class="space-y-2">
          <label for="login-username" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">
            Username
          </label>
          <input
            id="login-username"
            v-model="username"
            type="text"
            required
            autocomplete="username"
            placeholder="Nome utente"
            class="apple-input"
          />
        </div>

        <!-- Password -->
        <div class="space-y-2">
          <label for="login-password" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">
            Password
          </label>
          <input
            id="login-password"
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
            placeholder="········"
            class="apple-input"
          />
        </div>

        <!-- Submit -->
        <div class="pt-2">
          <button
            type="submit"
            :disabled="loading"
            class="apple-button apple-button-primary w-full py-4 text-sm font-bold shadow-xl shadow-white/5"
          >
            <span v-if="loading" class="flex items-center justify-center gap-2">
              <div class="w-4 h-4 border-2 border-brand-background/30 border-t-brand-background rounded-full animate-spin"></div>
              Attendere...
            </span>
            <span v-else>Accedi</span>
          </button>
        </div>

        <!-- Link registrazione -->
        <p class="text-center text-xs font-bold text-white/30 hover:text-white transition-colors uppercase tracking-widest pt-2">
          Non hai un account?
          <RouterLink to="/register" class="text-brand-secondary hover:underline">
            Registrati
          </RouterLink>
        </p>
      </form>
    </div>
  </div>
</template>
