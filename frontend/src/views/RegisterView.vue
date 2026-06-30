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
    // Dopo la registrazione, effettua il login automatico
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
  <div class="min-h-screen flex items-center justify-center px-4 py-12">
    <div class="w-full max-w-md">
      <!-- Header -->
      <div class="text-center mb-8">
        <RouterLink to="/" class="inline-block mb-4">
          <h1 class="text-3xl font-bold">
            Groove<span class="text-violet-400">Box</span>
          </h1>
        </RouterLink>
        <p class="text-slate-400">Crea il tuo account da collezionista</p>
      </div>

      <!-- Card -->
      <form
        @submit.prevent="handleRegister"
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
          <label for="reg-username" class="block text-sm font-medium text-slate-300 mb-1.5">
            Username
          </label>
          <input
            id="reg-username"
            v-model="form.username"
            type="text"
            required
            autocomplete="username"
            placeholder="Scegli un username"
            class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl
                   text-slate-100 placeholder-slate-500 focus:border-violet-500
                   focus:ring-1 focus:ring-violet-500 transition-colors outline-none"
          />
        </div>

        <!-- Nome e Cognome -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label for="reg-name" class="block text-sm font-medium text-slate-300 mb-1.5">
              Nome
            </label>
            <input
              id="reg-name"
              v-model="form.name"
              type="text"
              required
              autocomplete="given-name"
              placeholder="Mario"
              class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl
                     text-slate-100 placeholder-slate-500 focus:border-violet-500
                     focus:ring-1 focus:ring-violet-500 transition-colors outline-none"
            />
          </div>
          <div>
            <label for="reg-surname" class="block text-sm font-medium text-slate-300 mb-1.5">
              Cognome
            </label>
            <input
              id="reg-surname"
              v-model="form.surname"
              type="text"
              required
              autocomplete="family-name"
              placeholder="Rossi"
              class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl
                     text-slate-100 placeholder-slate-500 focus:border-violet-500
                     focus:ring-1 focus:ring-violet-500 transition-colors outline-none"
            />
          </div>
        </div>

        <!-- Email -->
        <div>
          <label for="reg-email" class="block text-sm font-medium text-slate-300 mb-1.5">
            Email
          </label>
          <input
            id="reg-email"
            v-model="form.email"
            type="email"
            required
            autocomplete="email"
            placeholder="la-tua@email.com"
            class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl
                   text-slate-100 placeholder-slate-500 focus:border-violet-500
                   focus:ring-1 focus:ring-violet-500 transition-colors outline-none"
          />
        </div>

        <!-- Password -->
        <div>
          <label for="reg-password" class="block text-sm font-medium text-slate-300 mb-1.5">
            Password
          </label>
          <input
            id="reg-password"
            v-model="form.password"
            type="password"
            required
            autocomplete="new-password"
            placeholder="Scegli una password"
            class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl
                   text-slate-100 placeholder-slate-500 focus:border-violet-500
                   focus:ring-1 focus:ring-violet-500 transition-colors outline-none"
          />
        </div>

        <!-- Conferma Password -->
        <div>
          <label for="reg-confirm" class="block text-sm font-medium text-slate-300 mb-1.5">
            Conferma Password
          </label>
          <input
            id="reg-confirm"
            v-model="form.confirmPassword"
            type="password"
            required
            autocomplete="new-password"
            placeholder="Ripeti la password"
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
          {{ loading ? 'Registrazione...' : 'Registrati' }}
        </button>

        <!-- Link login -->
        <p class="text-center text-sm text-slate-400">
          Hai gia' un account?
          <RouterLink to="/login" class="text-violet-400 hover:text-violet-300 font-medium">
            Accedi
          </RouterLink>
        </p>
      </form>
    </div>
  </div>
</template>
