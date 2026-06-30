<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/stores/api'

const authStore = useAuthStore()
const router = useRouter()

const editing = ref(false)
const loading = ref(false)
const message = ref('')
const error = ref('')

const form = ref({
  name: '',
  surname: '',
  email: '',
  password: '',
  confirmPassword: ''
})

onMounted(() => {
  resetForm()
})

function resetForm() {
  form.value = {
    name: authStore.user?.name || '',
    surname: authStore.user?.surname || '',
    email: authStore.user?.email || '',
    password: '',
    confirmPassword: ''
  }
  editing.value = false
  message.value = ''
  error.value = ''
}

async function handleSave() {
  error.value = ''
  message.value = ''

  if (form.value.password && form.value.password !== form.value.confirmPassword) {
    error.value = 'Le password non coincidono'
    return
  }

  loading.value = true
  try {
    const payload = {
      name: form.value.name,
      surname: form.value.surname,
      email: form.value.email
    }
    if (form.value.password) {
      payload.password = form.value.password
    }

    const res = await api.put('/users/me', payload)
    authStore.updateUser(res.data)
    message.value = 'Profilo aggiornato con successo'
    editing.value = false
    form.value.password = ''
    form.value.confirmPassword = ''
  } catch (err) {
    error.value = err.message || 'Errore durante l\'aggiornamento'
  } finally {
    loading.value = false
  }
}

async function handleDeleteAccount() {
  if (!confirm('Sei sicuro di voler eliminare il tuo account? Questa azione e\' irreversibile.')) {
    return
  }
  try {
    await api.delete('/users/me')
    authStore.logout()
    router.push('/')
  } catch (err) {
    error.value = err.message || 'Errore durante l\'eliminazione'
  }
}
</script>

<template>
  <div class="p-6 md:p-8 max-w-2xl mx-auto">
    <h1 class="text-3xl font-bold mb-6">Il Mio Profilo</h1>

    <!-- Messaggi -->
    <div v-if="message" class="mb-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm rounded-lg px-4 py-3">
      {{ message }}
    </div>
    <div v-if="error" class="mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm rounded-lg px-4 py-3">
      {{ error }}
    </div>

    <!-- Card Profilo -->
    <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8">

      <!-- Vista lettura -->
      <div v-if="!editing" class="space-y-4">
        <div class="flex items-center gap-4 mb-6">
          <div class="w-16 h-16 rounded-full bg-violet-600 flex items-center justify-center text-2xl font-bold text-white">
            {{ authStore.user?.name?.charAt(0) }}{{ authStore.user?.surname?.charAt(0) }}
          </div>
          <div>
            <h2 class="text-xl font-semibold">{{ authStore.user?.name }} {{ authStore.user?.surname }}</h2>
            <p class="text-slate-400 text-sm">@{{ authStore.user?.username }}</p>
          </div>
          <span class="ml-auto px-3 py-1 rounded-full text-xs font-medium"
                :class="authStore.isAdmin
                  ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                  : 'bg-violet-500/10 text-violet-400 border border-violet-500/30'">
            {{ authStore.isAdmin ? 'Administrator' : 'Collector' }}
          </span>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <span class="text-slate-500 block mb-1">Email</span>
            <span>{{ authStore.user?.email }}</span>
          </div>
          <div>
            <span class="text-slate-500 block mb-1">Username</span>
            <span>{{ authStore.user?.username }}</span>
          </div>
        </div>

        <div class="flex gap-3 pt-4 border-t border-slate-800 mt-6" v-if="authStore.isCollector">
          <button
            @click="editing = true"
            class="px-5 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium
                   rounded-xl transition-colors"
          >
            Modifica profilo
          </button>
          <button
            @click="handleDeleteAccount"
            class="px-5 py-2 border border-rose-500/30 text-rose-400 hover:bg-rose-500/10
                   text-sm font-medium rounded-xl transition-colors"
          >
            Elimina account
          </button>
        </div>
      </div>

      <!-- Vista modifica (solo Collector) -->
      <form v-else @submit.prevent="handleSave" class="space-y-5">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label for="profile-name" class="block text-sm font-medium text-slate-300 mb-1.5">Nome</label>
            <input id="profile-name" v-model="form.name" type="text" required
              class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                     focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none" />
          </div>
          <div>
            <label for="profile-surname" class="block text-sm font-medium text-slate-300 mb-1.5">Cognome</label>
            <input id="profile-surname" v-model="form.surname" type="text" required
              class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                     focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none" />
          </div>
        </div>

        <div>
          <label for="profile-email" class="block text-sm font-medium text-slate-300 mb-1.5">Email</label>
          <input id="profile-email" v-model="form.email" type="email" required
            class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                   focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none" />
        </div>

        <hr class="border-slate-800" />
        <p class="text-xs text-slate-500">Lascia vuoti i campi password per non modificarla.</p>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label for="profile-password" class="block text-sm font-medium text-slate-300 mb-1.5">Nuova password</label>
            <input id="profile-password" v-model="form.password" type="password" autocomplete="new-password"
              class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                     focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none" />
          </div>
          <div>
            <label for="profile-confirm" class="block text-sm font-medium text-slate-300 mb-1.5">Conferma password</label>
            <input id="profile-confirm" v-model="form.confirmPassword" type="password" autocomplete="new-password"
              class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                     focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none" />
          </div>
        </div>

        <div class="flex gap-3 pt-2">
          <button type="submit" :disabled="loading"
            class="px-5 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white text-sm
                   font-medium rounded-xl transition-colors">
            {{ loading ? 'Salvataggio...' : 'Salva modifiche' }}
          </button>
          <button type="button" @click="resetForm"
            class="px-5 py-2 border border-slate-700 text-slate-300 hover:text-white text-sm
                   font-medium rounded-xl transition-colors">
            Annulla
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
