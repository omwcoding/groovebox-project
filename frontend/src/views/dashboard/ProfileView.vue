<!--
GrooveBox - Pagina Gestione Profilo
===================================
Mostra le informazioni anagrafiche dell'utente registrato. Consente la modifica
delle credenziali e dei dati personali, nonchè lo svuotamento della collezione e la cancellazione dell'account.
-->

<script setup>
import { ref, onMounted, computed } from 'vue'
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
  currentPassword: '',
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
    currentPassword: '',
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

  if (form.value.password) {
    if (!form.value.currentPassword) {
      error.value = 'La password attuale è obbligatoria per poter inserire una nuova password'
      return
    }
    if (form.value.password.length < 6) {
      error.value = 'La nuova password deve contenere almeno 6 caratteri'
      return
    }
    if (form.value.password !== form.value.confirmPassword) {
      error.value = 'Le password non coincidono'
      return
    }
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
      payload.current_password = form.value.currentPassword
    }

    const res = await api.put('/users/me', payload)
    authStore.updateUser(res.data)
    message.value = 'Profilo aggiornato con successo'
    editing.value = false
    form.value.currentPassword = ''
    form.value.password = ''
    form.value.confirmPassword = ''
  } catch (err) {
    error.value = err.message || 'Errore durante l\'aggiornamento'
  } finally {
    loading.value = false
  }
}

async function handleDeleteAccount() {
  if (!confirm('Sei sicuro di voler eliminare il tuo account? Questa azione è irreversibile.')) {
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

async function handleClearCollection() {
  if (!confirm('Sei sicuro di voler svuotare interamente la tua collezione? Verranno rimosse tutte le tue copie fisiche. Questa azione è irreversibile.')) {
    return
  }
  loading.value = true
  message.value = ''
  error.value = ''
  try {
    await api.delete('/copies/clear')
    message.value = 'La tua collezione è stata svuotata con successo!'
  } catch (err) {
    error.value = err.message || 'Errore durante lo svuotamento della collezione'
  } finally {
    loading.value = false
  }
}

const copied = ref(false)

const shareUrl = computed(() => {
  const base = window.location.origin
  return `${base}/share/${authStore.user?.username}`
})

async function copyShareUrl() {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (_) {
  }
}
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-8 animate-fade-in">
    <div class="space-y-1">
      <h1 class="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
        Il Mio Profilo
      </h1>
      <p class="text-white/40 text-lg font-medium">Gestisci le informazioni personali del tuo account.</p>
    </div>

    <!-- Messaggi -->
    <div v-if="message" class="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold rounded-2xl px-4 py-3">
      {{ message }}
    </div>
    <div v-if="error" class="bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold rounded-2xl px-4 py-3">
      {{ error }}
    </div>

    <!-- Card Profilo -->
    <div class="glass-panel p-8 rounded-apple-2xl shadow-2xl">

      <!-- Vista lettura -->
      <div v-if="!editing" class="space-y-8">
        <div class="flex items-center gap-4 pb-6 border-b border-white/5">
          <div class="w-16 h-16 rounded-full bg-brand-secondary/20 flex items-center justify-center text-xl font-bold text-brand-secondary">
            {{ authStore.user?.name?.charAt(0) }}{{ authStore.user?.surname?.charAt(0) }}
          </div>
          <div>
            <h2 class="text-xl font-bold">{{ authStore.user?.name }} {{ authStore.user?.surname }}</h2>
            <p class="text-white/30 text-sm font-medium">@{{ authStore.user?.username }}</p>
          </div>
          <span class="ml-auto px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider border"
                :class="authStore.isAdmin
                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                  : 'bg-brand-secondary/10 text-brand-secondary border-brand-secondary/20'">
            {{ authStore.isAdmin ? 'Admin' : 'Collector' }}
          </span>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 text-sm">
          <div class="space-y-1">
            <span class="text-[10px] font-bold uppercase tracking-widest text-white/30 block">Nome</span>
            <span class="font-semibold text-white/90 text-base">{{ authStore.user?.name }}</span>
          </div>
          <div class="space-y-1">
            <span class="text-[10px] font-bold uppercase tracking-widest text-white/30 block">Cognome</span>
            <span class="font-semibold text-white/90 text-base">{{ authStore.user?.surname }}</span>
          </div>
          <div class="space-y-1 sm:col-span-2">
            <span class="text-[10px] font-bold uppercase tracking-widest text-white/30 block">Indirizzo Email</span>
            <span class="font-semibold text-white/90 text-base">{{ authStore.user?.email }}</span>
          </div>
        </div>

        <div class="flex flex-col sm:flex-row gap-3 pt-6 border-t border-white/5" v-if="authStore.isCollector">
          <button
            @click="editing = true"
            class="apple-button apple-button-primary text-sm shadow-xl shadow-white/5"
          >
            Modifica profilo
          </button>
          <button
            @click="handleClearCollection"
            :disabled="loading"
            class="apple-button apple-button-secondary text-sm !text-amber-500 hover:!bg-amber-500/10 hover:!border-amber-500/20"
          >
            Svuota collezione
          </button>
          <button
            @click="handleDeleteAccount"
            class="apple-button apple-button-secondary text-sm !text-brand-accent hover:!bg-brand-accent/10 hover:!border-brand-accent/20"
          >
            Elimina account
          </button>
        </div>

        <!-- Sezione Condivisione Vault per Collector -->
        <div v-if="authStore.isCollector" class="mt-8 pt-6 border-t border-white/5 space-y-3">
          <span class="text-[10px] font-bold uppercase tracking-widest text-white/30 block">Condividi il tuo Vault</span>
          <p class="text-xs text-white/50">Consenti ad altri utenti di esplorare la tua collezione in sola lettura con questo link pubblico:</p>
          <div class="flex items-center gap-2">
            <input 
              type="text" 
              readonly 
              :value="shareUrl" 
              class="apple-input !py-2 text-xs !bg-white/[0.02] flex-grow select-all font-mono" 
            />
            <button 
              @click="copyShareUrl" 
              class="apple-button apple-button-primary !py-2.5 px-4 text-xs font-bold whitespace-nowrap"
            >
              {{ copied ? 'Copiato!' : 'Copia Link' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Vista modifica (solo Collector) -->
      <form v-else @submit.prevent="handleSave" class="space-y-6">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="space-y-2">
            <label for="profile-name" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Nome</label>
            <input id="profile-name" v-model="form.name" type="text" required class="apple-input" />
          </div>
          <div class="space-y-2">
            <label for="profile-surname" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Cognome</label>
            <input id="profile-surname" v-model="form.surname" type="text" required class="apple-input" />
          </div>
        </div>

        <div class="space-y-2">
          <label for="profile-email" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Email</label>
          <input id="profile-email" v-model="form.email" type="email" required class="apple-input" />
        </div>

        <div class="border-t border-white/5 pt-6 space-y-4">
          <div class="space-y-1">
            <h3 class="text-sm font-bold">Cambio Password</h3>
            <p class="text-xs text-white/30">Lascia vuoti i campi password per non modificarla.</p>
          </div>

          <div class="space-y-2">
            <label for="profile-current-password" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Password attuale</label>
            <input id="profile-current-password" v-model="form.currentPassword" type="password" autocomplete="current-password" placeholder="Inserisci la password attuale" class="apple-input" />
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="space-y-2">
              <label for="profile-password" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Nuova password</label>
              <input id="profile-password" v-model="form.password" type="password" autocomplete="new-password" placeholder="········" class="apple-input" />
            </div>
            <div class="space-y-2">
              <label for="profile-confirm" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Conferma password</label>
              <input id="profile-confirm" v-model="form.confirmPassword" type="password" autocomplete="new-password" placeholder="········" class="apple-input" />
            </div>
          </div>
        </div>

        <div class="flex gap-3 pt-4">
          <button type="submit" :disabled="loading" class="apple-button apple-button-primary text-sm shadow-xl shadow-white/5">
            {{ loading ? 'Salvataggio...' : 'Salva modifiche' }}
          </button>
          <button type="button" @click="resetForm" class="apple-button apple-button-secondary text-sm">
            Annulla
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
