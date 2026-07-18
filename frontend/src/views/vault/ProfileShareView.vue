<!--
Mint - Pagina Condivisione Pubblica Vault (ProfileShareView)
============================================================
Visualizzazione in sola lettura del Vault di un utente specifico.
Raggiungibile pubblicamente alla route /share/:username.
-->

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import VaultShelf from '@/components/VaultShelf.vue'
import { useVault } from '@/composables/useVault'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/stores/api'

const route = useRoute()
const authStore = useAuthStore()
const username = route.params.username

const {
  copies,
  user,
  loading,
  error,
  search,
  filterFormat,
  filteredCopies,
  fetchCopies
} = useVault(username)

const viewMode = ref('shelf') // 'shelf' | 'grid'

// Gestione segnalazione profilo
const showReportModal = ref(false)
const reportCategory = ref('avatar')
const reportDetails = ref('')
const reportSuccess = ref('')
const reportError = ref('')
const reporting = ref(false)

const canReport = computed(() => {
  return authStore.isAuthenticated && 
         authStore.user && 
         user.value && 
         authStore.user.id_user !== user.value.id_user && 
         authStore.user.role === 'collector'
})

async function submitReport() {
  if (reporting.value) return
  
  if (reportCategory.value === 'other' && !reportDetails.value.trim()) {
    reportError.value = "La nota esplicativa è obbligatoria per la categoria 'Altro'"
    return
  }
  
  reporting.value = true
  reportError.value = ''
  reportSuccess.value = ''
  
  try {
    const res = await api.post('/users/reports', {
      reported_username: username,
      category: reportCategory.value,
      details: reportDetails.value
    })
    reportSuccess.value = res.message || "Segnalazione inviata con successo."
    reportDetails.value = ''
    setTimeout(() => {
      showReportModal.value = false
      reportSuccess.value = ''
    }, 2000)
  } catch (e) {
    reportError.value = e.message || "Impossibile inviare la segnalazione."
  } finally {
    reporting.value = false
  }
}

onMounted(() => {
  fetchCopies()
})
</script>

<template>
  <div class="space-y-8 animate-fade-in pb-20">
    <LoadingSpinner v-if="loading" />

    <div v-else-if="error" class="py-20 text-center space-y-4">
      <div class="inline-block bg-white/5 p-6 rounded-full text-rose-400">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
      </div>
      <p class="text-xl font-bold text-white/80">{{ error }}</p>
      <p class="text-white/40 text-sm">Controlla l'URL o chiedi al proprietario del Vault.</p>
    </div>

    <template v-else-if="user">
      <!-- Header Profilo Condiviso -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-6 p-6 border border-white/10 rounded-apple-3xl bg-white/[0.02]">
        <div class="flex flex-col sm:flex-row sm:items-center gap-6">
          <img v-if="user.avatar_path" :src="`/api/users/${user.id_user}/avatar`" class="w-16 h-16 rounded-full object-cover border border-brand-secondary/40 shrink-0" />
          <div v-else class="w-16 h-16 rounded-full bg-brand-secondary/20 border border-brand-secondary/40 flex items-center justify-center text-xl font-extrabold text-brand-secondary shrink-0">
            {{ user.name?.charAt(0) }}{{ user.surname?.charAt(0) }}
          </div>
          <div class="space-y-1">
            <h1 class="text-3xl font-extrabold tracking-tight text-white/90">
              Il Vault di {{ user.username }}
            </h1>
            <p class="text-sm text-white/40 font-medium">
              Profilo pubblico (@{{ user.username }}) &middot; {{ copies.length }} dischi custoditi.
            </p>
            <p v-if="user.bio" class="text-sm text-white/60 italic pt-1 max-w-lg leading-relaxed">
              "{{ user.bio }}"
            </p>
          </div>
        </div>

        <button
          v-if="canReport"
          @click="showReportModal = true"
          class="px-4 py-2 border border-rose-500/30 hover:bg-rose-500/10 text-rose-400 rounded-full text-xs font-bold transition-all shrink-0 self-start md:self-center flex items-center gap-1.5 cursor-pointer shadow-md"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" x2="4" y1="22" y2="15"/></svg>
          Segnala Profilo
        </button>
      </div>


      <!-- Filtri e Toggle -->
      <div class="flex flex-col md:flex-row items-center gap-4 py-4 border-y border-white/5 justify-between">
        <div class="flex flex-col sm:flex-row items-center gap-4 w-full md:max-w-xl">
          <div class="relative w-full">
            <input 
              v-model="search" 
              type="text" 
              placeholder="Cerca nel Vault..." 
              class="apple-input !pl-10 !py-2.5 text-sm" 
            />
            <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/20">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            </span>
          </div>

          <div class="relative w-full sm:w-48 shrink-0">
            <select v-model="filterFormat" class="apple-input !py-2.5 !pr-10 text-sm appearance-none cursor-pointer">
              <option value="">Tutti i formati</option>
              <option value="Vinile">Vinile</option>
              <option value="CD">CD</option>
              <option value="Cassetta">Cassetta</option>
            </select>
            <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>
            </div>
          </div>
        </div>

        <div class="flex items-center p-1 bg-white/5 border border-white/5 rounded-2xl shrink-0 self-end md:self-auto">
          <button 
            @click="viewMode = 'shelf'"
            :class="viewMode === 'shelf' ? 'bg-white/10 text-white shadow-lg' : 'text-white/40 hover:text-white/60'"
            class="px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5"
          >
            Scaffale
          </button>
          <button 
            @click="viewMode = 'grid'"
            :class="viewMode === 'grid' ? 'bg-white/10 text-white shadow-lg' : 'text-white/40 hover:text-white/60'"
            class="px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5"
          >
            Griglia
          </button>
        </div>
      </div>

      <!-- Visualizzazioni -->
      <div v-if="viewMode === 'shelf'" class="animate-fade-in">
        <VaultShelf :copies="filteredCopies" readOnly />
      </div>

      <div v-else class="animate-fade-in">
        <div v-if="filteredCopies.length === 0" class="text-center py-20 text-white/30 italic">
          Nessun disco corrisponde ai criteri di ricerca.
        </div>
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          <RouterLink
            v-for="copy in filteredCopies" 
            :key="copy.id_copy"
            :to="`/albums/${copy.id_album}`"
            class="group glass-card p-4 flex gap-4 hover:scale-[1.02] hover:shadow-2xl transition-all duration-300 border border-white/5"
          >
            <div class="w-20 h-20 bg-white/5 rounded-xl overflow-hidden shrink-0 flex items-center justify-center relative">
              <img v-if="copy.cover_path" :src="`/api/albums/${copy.id_album}/cover`" class="w-full h-full object-cover" />
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="opacity-15"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
            </div>
            <div class="min-w-0 flex flex-col justify-between py-1 flex-grow">
              <div>
                <p class="font-bold text-white/90 group-hover:text-brand-secondary transition-colors truncate">{{ copy.album_title }}</p>
                <p class="text-xs text-white/50 truncate">{{ copy.artists?.map(a => a.name).join(', ') || 'Artista' }}</p>
              </div>
              <div class="flex gap-2 text-[10px] font-bold uppercase tracking-wider">
                <span class="px-2 py-0.5 bg-brand-secondary/15 border border-brand-secondary/20 text-brand-secondary rounded">
                  {{ copy.format }}
                </span>
                <span class="px-2 py-0.5 bg-white/5 border border-white/10 text-white/60 rounded">
                  {{ copy.condition }}
                </span>
              </div>
            </div>
          </RouterLink>
        </div>
      </div>
    </template>

    <!-- Modale Segnalazione -->
    <transition name="fade">
      <div v-if="showReportModal" class="fixed inset-0 bg-black/60 backdrop-blur-md z-[10000] flex items-center justify-center p-4">
        <div class="glass-panel max-w-md w-full p-6 space-y-6 border border-white/10 rounded-3xl relative animate-fade-in shadow-2xl">
          <button 
            @click="showReportModal = false; reportSuccess = ''; reportError = ''" 
            class="absolute top-4 right-4 text-white/40 hover:text-white cursor-pointer"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" x2="6" y1="6" y2="18"/><line x1="6" x2="18" y1="6" y2="18"/></svg>
          </button>
          
          <div class="space-y-1">
            <h3 class="text-xl font-bold text-white/90">Segnala Profilo</h3>
            <p class="text-xs text-white/40">Segnala il profilo di @{{ user.username }} all'amministratore.</p>
          </div>

          <div v-if="reportSuccess" class="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm rounded-2xl text-center">
            {{ reportSuccess }}
          </div>
          
          <div v-else class="space-y-4">
            <div v-if="reportError" class="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl">
              {{ reportError }}
            </div>

            <div class="space-y-2">
              <label class="text-xs font-semibold text-white/50 uppercase tracking-wider">Motivo della segnalazione</label>
              <select v-model="reportCategory" class="apple-input text-sm cursor-pointer appearance-none">
                <option value="avatar">Avatar inappropriato</option>
                <option value="bio">Biografia offensiva</option>
                <option value="username">Username non idoneo</option>
                <option value="spam">Spam / Account falso</option>
                <option value="other">Altro</option>
              </select>
            </div>

            <div class="space-y-2">
              <label class="text-xs font-semibold text-white/50 uppercase tracking-wider">Dettagli aggiuntivi</label>
              <textarea 
                v-model="reportDetails" 
                rows="4" 
                placeholder="Spiega brevemente il motivo per aiutare l'amministrazione..." 
                class="apple-input text-sm resize-none"
              ></textarea>
            </div>

            <div class="flex gap-3 pt-2">
              <button 
                @click="showReportModal = false"
                class="flex-1 py-3 border border-white/5 bg-white/5 text-white/70 hover:bg-white/10 rounded-2xl text-xs font-bold transition-all cursor-pointer"
              >
                Annulla
              </button>
              <button 
                @click="submitReport"
                :disabled="reporting"
                class="flex-1 py-3 bg-rose-500 hover:bg-rose-600 text-white rounded-2xl text-xs font-bold transition-all cursor-pointer flex items-center justify-center gap-2 shadow-lg"
              >
                <span v-if="reporting" class="border-2 border-white/20 border-t-white w-4 h-4 rounded-full animate-spin"></span>
                Invia
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>
