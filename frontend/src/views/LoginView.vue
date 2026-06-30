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
  <div class="min-h-screen flex items-center justify-center px-4">
    <div class="w-full max-w-md">
      <!-- Header -->
      <div class="text-center mb-8">
        <RouterLink to="/" class="inline-block mb-4">
          <h1 class="text-3xl font-bold">
            Groove<span class="text-violet-400">Box</span>
          </h1>
        </RouterLink>
        <p class="text-slate-400">Accedi al tuo account</p>
      </div>

      <!-- Card -->
      <form
        @submit.prevent="handleLogin"
        class="bg-slate-900/80 border border-slate-800 rounded-2xl p-8 space-y-5
               backdrop-blur-sm shadow-xl"
      >
        <!-- Errore -->
        <div
          v-if="error"
          class="bg-rose-500/10 border border-rose-500/30 text-rose-400
                 text-sm rounded-lg px-4 py-3"
        >
          {{ error }}
        </div>

        <!-- Username -->
        <div>
          <label for="login-username" class="block text-sm font-medium text-slate-300 mb-1.5">
            Username
          </label>
          <input
            id="login-username"
            v-model="username"
            type="text"
            required
            autocomplete="username"
            placeholder="Il tuo username"
            class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl
                   text-slate-100 placeholder-slate-500 focus:border-violet-500
                   focus:ring-1 focus:ring-violet-500 transition-colors outline-none"
          />
        </div>

        <!-- Password -->
        <div>
          <label for="login-password" class="block text-sm font-medium text-slate-300 mb-1.5">
            Password
          </label>
          <input
            id="login-password"
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
            placeholder="La tua password"
            class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl
                   text-slate-100 placeholder-slate-500 focus:border-violet-500
                   focus:ring-1 focus:ring-violet-500 transition-colors outline-none"
          />
        </div>

        <!-- Submit -->
        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3 bg-violet-600 hover:bg-violet-500 disabled:opacity-50
                 disabled:cursor-not-allowed text-white font-semibold rounded-xl
                 transition-all duration-200 hover:shadow-lg hover:shadow-violet-600/25"
        >
          {{ loading ? 'Accesso in corso...' : 'Accedi' }}
        </button>

        <!-- Link registrazione -->
        <p class="text-center text-sm text-slate-400">
          Non hai un account?
          <RouterLink to="/register" class="text-violet-400 hover:text-violet-300 font-medium">
            Registrati
          </RouterLink>
        </p>
      </form>
    </div>
  </div>
</template>
