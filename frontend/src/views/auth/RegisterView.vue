<!--
GrooveBox - Pagina Registrazione
================================
Consente la registrazione sulla piattaforma di un nuovo utente con ruolo 'collector',
richiedendo i dati anagrafici e le credenziali di accesso.
-->

<script setup>
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const form = ref({
  username: '',
  name: '',
  surname: '',
  email: '',
  password: '',
  confirmPassword: ''
})
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''

  if (!form.value.username.trim()) {
    error.value = 'Lo username è obbligatorio'
    return
  }
  if (!form.value.name.trim() || !form.value.surname.trim()) {
    error.value = 'Nome e cognome sono obbligatori'
    return
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!form.value.email.trim() || !emailRegex.test(form.value.email)) {
    error.value = 'Inserisci un indirizzo email valido'
    return
  }

  if (form.value.password.length < 6) {
    error.value = 'La password deve contenere almeno 6 caratteri'
    return
  }

  if (form.value.password !== form.value.confirmPassword) {
    error.value = 'Le password non coincidono'
    return
  }

  loading.value = true

  try {
    await authStore.register({
      username: form.value.username,
      name: form.value.name,
      surname: form.value.surname,
      email: form.value.email,
      password: form.value.password
    })
    // Dopo la registrazione, login automatico
    await authStore.login(form.value.username, form.value.password)
    router.push('/dashboard')
  } catch (err) {
    error.value = err.message || 'Errore durante la registrazione'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4 py-16 relative overflow-hidden animate-fade-in">
    <!-- Background glow -->
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-brand-secondary/15 rounded-full blur-[130px] animate-pulse pointer-events-none"></div>

    <div class="w-full max-w-md z-10">
      <!-- Header -->
      <div class="text-center mb-8">
        <RouterLink to="/" class="inline-flex p-3 bg-white/5 rounded-2xl border border-white/10 mb-4 hover:scale-105 transition-transform">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="text-brand-secondary"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
        </RouterLink>
        <h1 class="text-3xl font-extrabold tracking-tight bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
          Crea il tuo profilo
        </h1>
        <p class="text-white/30 text-sm font-medium mt-1">Unisciti alla community di collezionisti di GrooveBox</p>
      </div>

      <!-- Card -->
      <form
        novalidate
        @submit.prevent="handleRegister"
        class="glass-panel p-8 rounded-apple-2xl space-y-5 shadow-2xl"
      >
        <!-- Errore -->
        <div
          v-if="error"
          class="bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold rounded-2xl px-4 py-3"
        >
          {{ error }}
        </div>

        <!-- Username -->
        <div class="space-y-1.5">
          <label for="reg-username" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">
            Username
          </label>
          <input
            id="reg-username"
            v-model="form.username"
            type="text"
            required
            placeholder="Scegli un username"
            class="apple-input"
          />
        </div>

        <!-- Nome e Cognome -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="space-y-1.5">
            <label for="reg-name" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">
              Nome
            </label>
            <input
              id="reg-name"
              v-model="form.name"
              type="text"
              required
              placeholder="Mario"
              class="apple-input"
            />
          </div>
          <div class="space-y-1.5">
            <label for="reg-surname" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">
              Cognome
            </label>
            <input
              id="reg-surname"
              v-model="form.surname"
              type="text"
              required
              placeholder="Rossi"
              class="apple-input"
            />
          </div>
        </div>

        <!-- Email -->
        <div class="space-y-1.5">
          <label for="reg-email" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">
            Email
          </label>
          <input
            id="reg-email"
            v-model="form.email"
            type="email"
            required
            placeholder="latua@email.com"
            class="apple-input"
          />
        </div>

        <!-- Password -->
        <div class="space-y-1.5">
          <label for="reg-password" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">
            Password
          </label>
          <input
            id="reg-password"
            v-model="form.password"
            type="password"
            required
            placeholder="Scegli una password"
            class="apple-input"
          />
        </div>

        <!-- Conferma Password -->
        <div class="space-y-1.5">
          <label for="reg-confirm" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">
            Conferma Password
          </label>
          <input
            id="reg-confirm"
            v-model="form.confirmPassword"
            type="password"
            required
            placeholder="Ripeti la password"
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
              Creazione...
            </span>
            <span v-else>Registrati</span>
          </button>
        </div>

        <!-- Link login -->
        <p class="text-center text-xs font-bold text-white/30 hover:text-white transition-colors uppercase tracking-widest pt-2">
          Hai già un account?
          <RouterLink to="/login" class="text-brand-secondary hover:underline">
            Accedi
          </RouterLink>
        </p>
      </form>
    </div>
  </div>
</template>
