<!--
Mint - Pagina Gestione Profilo
================================
Mostra le informazioni anagrafiche dell'utente. Consente la modifica
delle credenziali, dei dati personali, della bio e del toggle profilo
pubblico. Gestisce lo svuotamento della collezione e la cancellazione dell'account.
-->

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/stores/api'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const editing = ref(false)
const loading = ref(false)
const message = ref('')
const error = ref('')

// Impostazioni del profilo pubblico
const isPublic = ref(false)
const bio = ref('')

const avatarInput = ref(null)

const form = ref({
  name: '',
  surname: '',
  currentPassword: '',
  password: '',
  confirmPassword: ''
})

onMounted(async () => {
  if (authStore.isAuthenticated) {
    await authStore.fetchCurrentUser()
  }
  resetForm()
  if (route.query.edit === 'true') {
    editing.value = true
  }
})

watch(() => route.query.edit, (newVal) => {
  if (newVal === 'true') {
    editing.value = true
  } else {
    editing.value = false
  }
})

function resetForm() {
  form.value = {
    name: authStore.user?.name || '',
    surname: authStore.user?.surname || '',
    currentPassword: '',
    password: '',
    confirmPassword: ''
  }
  isPublic.value = !!authStore.user?.is_public
  bio.value = authStore.user?.bio || ''
  editing.value = false
  message.value = ''
  error.value = ''
  if (route.query.edit) {
    router.replace('/profile')
  }
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
    // 1. Salva dati anagrafici
    const payload = {
      name: form.value.name,
      surname: form.value.surname
    }
    if (form.value.password) {
      payload.password = form.value.password
      payload.current_password = form.value.currentPassword
    }

    const res = await api.put('/users/me', payload)
    authStore.updateUser(res.data)

    // 2. Salva impostazioni profilo pubblico (is_public e bio)
    const resPublic = await api.put('/users/me/public-profile', {
      is_public: isPublic.value,
      bio: bio.value
    })
    authStore.updateUser(resPublic.data)

    message.value = 'Profilo aggiornato con successo'
    editing.value = false
    form.value.currentPassword = ''
    form.value.password = ''
    form.value.confirmPassword = ''
    if (route.query.edit) {
      router.replace('/profile')
    }
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
    await authStore.logout()
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

// ── Profilo Pubblico ──────────────────────────────────────────────────────────

const copied = ref(false)

const shareUrl = computed(() => {
  const base = window.location.origin
  return `${base}/share/${authStore.user?.username}`
})

async function copyShareUrl() {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch (_) {}
}

// ── Gestione Avatar ───────────────────────────────────────────────────────────

function triggerAvatarSelect() {
  avatarInput.value.click()
}

async function handleAvatarChange(e) {
  const file = e.target.files[0]
  if (!file) return

  error.value = ''
  message.value = ''
  loading.value = true

  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await api.post('/users/me/avatar', formData)
    authStore.updateUser(res.data)
    message.value = 'Foto profilo aggiornata con successo'
  } catch (err) {
    error.value = err.message || 'Errore durante il caricamento della foto profilo'
  } finally {
    loading.value = false
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

      <!-- Vista lettura (Sola Lettura) -->
      <div v-if="!editing" class="space-y-8">
        <div class="flex items-center gap-4 pb-6 border-b border-white/5">
          <!-- Avatar Statico in sola lettura -->
          <div class="w-16 h-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center overflow-hidden relative shadow-inner">
            <img v-if="authStore.user?.avatar_path" :src="`/api/users/${authStore.user?.id_user}/avatar`" class="w-full h-full object-cover" />
            <span v-else class="text-xl font-bold text-brand-secondary">
              {{ authStore.user?.name?.charAt(0) }}{{ authStore.user?.surname?.charAt(0) }}
            </span>
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
          <!-- Bio in sola lettura se esistente -->
          <div v-if="authStore.user?.bio" class="space-y-1 sm:col-span-2">
            <span class="text-[10px] font-bold uppercase tracking-widest text-white/30 block">Bio</span>
            <p class="text-white/70 text-sm leading-relaxed italic bg-white/[0.01] border border-white/5 p-4 rounded-2xl">
              "{{ authStore.user.bio }}"
            </p>
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

        <!-- ── Link di condivisione pubblico (solo se abilitato) ── -->
        <transition name="fade">
          <div v-if="authStore.isCollector && authStore.user?.is_public" class="mt-8 pt-6 border-t border-white/5 space-y-3">
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
                {{ copied ? '✓ Copiato!' : 'Copia Link' }}
              </button>
            </div>
          </div>
        </transition>
      </div>

      <!-- Vista modifica (solo Collector) -->
      <form v-else @submit.prevent="handleSave" class="space-y-6">
        <!-- Sezione Foto Profilo Interattiva (solo in Modifica) -->
        <div class="flex items-center gap-4 pb-6 border-b border-white/5">
          <div 
            class="w-16 h-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center overflow-hidden relative shadow-inner group cursor-pointer"
            @click="triggerAvatarSelect"
            title="Cambia foto profilo"
          >
            <img v-if="authStore.user?.avatar_path" :src="`/api/users/${authStore.user?.id_user}/avatar`" class="w-full h-full object-cover" />
            <span v-else class="text-xl font-bold text-brand-secondary">
              {{ authStore.user?.name?.charAt(0) }}{{ authStore.user?.surname?.charAt(0) }}
            </span>
            <!-- Hover overlay di modifica -->
            <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity duration-300">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-white"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
            </div>
            <input 
              ref="avatarInput" 
              type="file" 
              accept="image/*" 
              class="hidden" 
              @change="handleAvatarChange" 
            />
          </div>
          <div>
            <h3 class="text-sm font-bold">Foto Profilo</h3>
            <p class="text-xs text-white/30">Clicca sul cerchio per aggiornare l'immagine.</p>
          </div>
        </div>

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

        <!-- Email Non Modificabile -->
        <div class="space-y-2">
          <label for="profile-email" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Email (Non modificabile)</label>
          <input 
            id="profile-email" 
            disabled 
            :value="authStore.user?.email" 
            type="email" 
            class="apple-input !bg-white/[0.01] opacity-40 cursor-not-allowed border-white/5" 
          />
        </div>

        <!-- ── Sezione Impostazioni Pubbliche in Modifica ── -->
        <div class="border-t border-white/5 pt-6 space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <span class="text-[10px] font-bold uppercase tracking-widest text-white/30 block mb-1">Profilo Pubblico</span>
              <p class="text-xs text-white/50">Rendi il tuo Vault visibile a chiunque abbia il link.</p>
            </div>
            <!-- Toggle Switch -->
            <button
              id="public-profile-toggle"
              type="button"
              @click="isPublic = !isPublic"
              :class="isPublic
                ? 'bg-brand-secondary border-brand-secondary/60'
                : 'bg-white/10 border-white/10'"
              class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border transition-colors duration-200 ease-in-out focus:outline-none"
              :aria-checked="isPublic"
              role="switch"
            >
              <span
                :class="isPublic ? 'translate-x-5' : 'translate-x-0.5'"
                class="inline-block h-5 w-5 transform rounded-full bg-white shadow-lg transition duration-200 ease-in-out mt-px"
              />
            </button>
          </div>

          <!-- Bio -->
          <div class="space-y-2">
            <label for="profile-bio" class="text-[10px] font-bold uppercase tracking-widest text-white/30 block">Bio</label>
            <textarea
              id="profile-bio"
              v-model="bio"
              rows="3"
              maxlength="500"
              placeholder="Racconta qualcosa di te e della tua collezione..."
              class="apple-input resize-none text-sm leading-relaxed"
            />
            <p class="text-[10px] text-white/20 text-right">{{ bio.length }}/500</p>
          </div>
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

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
