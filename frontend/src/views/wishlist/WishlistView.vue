<!--
Mint - Pagina Wishlist Utente
=============================
Consente di salvare i dischi desiderati cercando nel catalogo locale o su Discogs.
Permette la promozione rapida a copia fisica ("Ho comprato questo disco").
-->

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/stores/api'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import { FORMAT_OPTIONS as formatOptions, CONDITION_OPTIONS as conditionOptions } from '@/constants/music'

const wishlist = ref([])
const loading = ref(true)
const error = ref('')

// Stati Ricerca per Aggiunta
const showSearchModal = ref(false)
const searchInput = ref('')
const searchLoading = ref(false)
const searchResults = ref([])
const hasSearched = ref(false)

// Stati Promozione a Vault
const showPromoteModal = ref(false)
const selectedItem = ref(null)
const format = ref('Vinile')
const condition = ref('Nuovo')
const personalNotes = ref('')
const promoteLoading = ref(false)

async function fetchWishlist() {
  try {
    const res = await api.get('/wishlist')
    wishlist.value = res.data
  } catch (err) {
    error.value = err.message || 'Errore nel caricamento della wishlist'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchWishlist()
})

// Ricerca unificata
async function handleSearch() {
  const query = searchInput.value.trim()
  if (!query) return
  searchLoading.value = true
  hasSearched.value = true
  try {
    const res = await api.get(`/discogs/search/unified?q=${encodeURIComponent(query)}`)
    searchResults.value = res.data
  } catch (err) {
    error.value = err.message || 'Errore durante la ricerca'
  } finally {
    searchLoading.value = false
  }
}

// Aggiunta a wishlist
async function handleAddToWishlist(album) {
  try {
    const payload = {
      id_album: album.id_album || null,
      discogs_id: album.discogs_id || null,
      title: album.title,
      artist_name: album.artist_name || album.artists?.map(a => a.name).join(', '),
      cover_url: album.coverPath ? `/api/albums/${album.id_album}/cover` : album.thumb
    }
    await api.post('/wishlist', payload)
    
    // Reset e ricarica
    showSearchModal.value = false
    searchInput.value = ''
    searchResults.value = []
    hasSearched.value = false
    loading.value = true
    await fetchWishlist()
  } catch (err) {
    error.value = err.message || 'Errore durante l\'aggiunta alla wishlist'
  }
}

// Rimozione da wishlist
async function handleRemove(id) {
  if (!confirm('Rimuovere questo album dalla wishlist?')) return
  try {
    await api.delete(`/wishlist/${id}`)
    wishlist.value = wishlist.value.filter(item => item.id_wishlist !== id)
  } catch (err) {
    error.value = err.message || 'Errore durante la rimozione'
  }
}

// Apre modale di promozione
function openPromoteModal(item) {
  selectedItem.value = item
  format.value = 'Vinile'
  condition.value = 'Nuovo'
  personalNotes.value = ''
  showPromoteModal.value = true
}

// Esegue promozione a copia fisica
async function handlePromote() {
  if (!selectedItem.value) return
  promoteLoading.value = true
  error.value = ''
  try {
    await api.post(`/wishlist/${selectedItem.value.id_wishlist}/promote`, {
      format: format.value,
      condition: condition.value,
      personalNotes: personalNotes.value.trim() || null
    })
    
    // Chiudi modale e ricarica
    showPromoteModal.value = false
    selectedItem.value = null
    loading.value = true
    await fetchWishlist()
  } catch (err) {
    error.value = err.message || 'Errore durante l\'acquisto del disco'
  } finally {
    promoteLoading.value = false
  }
}
</script>

<template>
  <div class="space-y-8 animate-fade-in pb-20">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6">
      <div class="space-y-1">
        <h1 class="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
          La mia Wishlist
        </h1>
        <p class="text-white/40 text-lg font-medium">I dischi che vuoi aggiungere alla tua collezione fisica.</p>
      </div>

      <button 
        @click="showSearchModal = true"
        class="apple-button apple-button-primary shadow-xl shadow-brand-secondary/5 self-start sm:self-auto flex items-center justify-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
        Cerca e Aggiungi
      </button>
    </div>

    <ErrorMessage v-if="error" :message="error" />

    <LoadingSpinner v-if="loading" />

    <!-- Lista Wishlist -->
    <template v-else>
      <div v-if="wishlist.length === 0" class="text-center py-20 text-white/30 italic">
        La tua wishlist è vuota. Clicca su "Cerca e Aggiungi" per pianificare i tuoi prossimi acquisti.
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div 
          v-for="item in wishlist" 
          :key="item.id_wishlist"
          class="glass-panel p-5 flex gap-5 border border-white/5 rounded-apple-2xl shadow-xl hover:shadow-2xl transition-all duration-300 relative overflow-hidden"
        >
          <!-- Thumbnail -->
          <div class="w-24 h-24 bg-white/5 border border-white/5 rounded-xl overflow-hidden shrink-0 flex items-center justify-center relative">
            <img v-if="item.local_cover_path || item.cover_url" :src="item.local_cover_path ? `/api/albums/${item.id_album}/cover` : item.cover_url" class="w-full h-full object-cover" />
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="opacity-15"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
          </div>

          <!-- Dettagli -->
          <div class="min-w-0 flex-grow flex flex-col justify-between py-1">
            <div>
              <h3 class="font-extrabold text-white text-lg truncate">{{ item.local_title || item.title }}</h3>
              <p class="text-sm text-white/50 truncate mt-1">
                di {{ item.artists?.map(a => a.name).join(', ') || item.artist_name }}
              </p>
              <p class="text-[10px] text-white/30 mt-2">
                Aggiunto il {{ item.addedDate }}
              </p>
            </div>

            <!-- Azioni -->
            <div class="flex gap-3 mt-4">
              <button 
                @click="openPromoteModal(item)"
                class="apple-button apple-button-primary !py-1.5 !px-3.5 text-xs shadow-md font-bold whitespace-nowrap"
              >
                Comprato!
              </button>
              <button 
                @click="handleRemove(item.id_wishlist)"
                class="apple-button apple-button-secondary !py-1.5 !px-3.5 text-xs font-semibold whitespace-nowrap !text-brand-accent hover:!bg-brand-accent/10"
              >
                Rimuovi
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- MODALE RICERCA UNIFICATA -->
    <div v-if="showSearchModal" class="fixed inset-0 z-[150] flex items-center justify-center p-4">
      <div @click="showSearchModal = false" class="absolute inset-0 bg-black/60 backdrop-blur-md"></div>
      <div class="relative glass-panel w-full max-w-lg rounded-apple-3xl shadow-2xl border border-white/10 overflow-hidden z-10 flex flex-col max-h-[85vh]">
        <div class="p-6 border-b border-white/5 flex items-center justify-between">
          <h3 class="text-xl font-bold">Cerca per Wishlist</h3>
          <button @click="showSearchModal = false" class="text-white/40 hover:text-white rounded-full w-8 h-8 flex items-center justify-center bg-white/5">✕</button>
        </div>
        
        <div class="p-6 overflow-y-auto space-y-4">
          <form @submit.prevent="handleSearch" class="flex gap-2">
            <input v-model="searchInput" type="text" placeholder="Cerca album da aggiungere..." required class="apple-input flex-grow" />
            <button type="submit" class="apple-button apple-button-primary !py-2.5 px-5">Cerca</button>
          </form>

          <div v-if="searchLoading" class="py-12 flex justify-center"><LoadingSpinner /></div>

          <div v-else-if="hasSearched" class="space-y-2">
            <div v-if="searchResults.length > 0" class="space-y-2 max-h-72 overflow-y-auto border border-white/5 rounded-2xl bg-white/[0.01] divide-y divide-white/5">
              <div 
                v-for="album in searchResults" 
                :key="album.discogs_id || album.id_album"
                @click="handleAddToWishlist(album)"
                class="flex items-center gap-4 p-3 hover:bg-white/5 cursor-pointer transition-colors"
              >
                <div class="w-10 h-10 bg-white/5 rounded-lg overflow-hidden shrink-0 flex items-center justify-center">
                  <img v-if="album.thumb || album.coverPath" :src="album.coverPath ? `/api/albums/${album.id_album}/cover` : album.thumb" class="w-full h-full object-cover" />
                  <span v-else class="text-sm">&#127925;</span>
                </div>
                <div class="min-w-0 flex-grow">
                  <span class="font-bold text-sm block truncate text-white/95">{{ album.title }}</span>
                  <span class="text-xs text-white/40 block truncate mt-0.5">
                    {{ album.artist_name || album.artists?.map(a => a.name).join(', ') }}
                  </span>
                </div>
                <span class="text-[9px] font-bold uppercase tracking-wider text-brand-secondary bg-brand-secondary/10 px-2.5 py-1 border border-brand-secondary/20 rounded-full shrink-0">
                  + Aggiungi
                </span>
              </div>
            </div>
            <div v-else class="text-center py-10 text-white/30 italic text-sm">Nessun album trovato.</div>
          </div>
        </div>
      </div>
    </div>

    <!-- MODALE PROMOZIONE A VAULT -->
    <div v-if="showPromoteModal" class="fixed inset-0 z-[150] flex items-center justify-center p-4">
      <div @click="showPromoteModal = false" class="absolute inset-0 bg-black/60 backdrop-blur-md"></div>
      <div class="relative glass-panel w-full max-w-md rounded-apple-3xl shadow-2xl border border-white/10 overflow-hidden z-10 flex flex-col">
        <div class="p-6 border-b border-white/5 flex items-center justify-between">
          <h3 class="text-xl font-bold">Aggiungi al Vault</h3>
          <button @click="showPromoteModal = false" class="text-white/40 hover:text-white rounded-full w-8 h-8 flex items-center justify-center bg-white/5">✕</button>
        </div>

        <div v-if="promoteLoading" class="p-12 flex flex-col items-center gap-3">
          <LoadingSpinner />
          <p class="text-xs text-white/40 font-bold uppercase tracking-widest animate-pulse">Spostamento nel Vault...</p>
        </div>

        <form v-else @submit.prevent="handlePromote" class="p-6 space-y-5">
          <div class="flex items-center gap-3 p-3 border border-white/5 rounded-xl bg-white/[0.01]">
            <span class="text-base font-bold text-white truncate flex-grow">
              {{ selectedItem?.local_title || selectedItem?.title }}
            </span>
          </div>

          <div class="space-y-2">
            <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Formato</label>
            <div class="grid grid-cols-3 gap-2">
              <button
                v-for="opt in formatOptions"
                :key="opt"
                type="button"
                @click="format = opt"
                :class="format === opt ? 'bg-brand-secondary/20 border-brand-secondary text-white' : 'bg-white/5 border-white/5 text-white/60'"
                class="py-2 border rounded-xl text-xs font-bold transition-all"
              >
                {{ opt }}
              </button>
            </div>
          </div>

          <div class="space-y-2">
            <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Condizione</label>
            <select v-model="condition" class="apple-input">
              <option v-for="c in conditionOptions" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>

          <div class="space-y-2">
            <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Note personali</label>
            <textarea v-model="personalNotes" rows="2" placeholder="Note d'acquisto, edizione..." class="apple-input resize-none"></textarea>
          </div>

          <div class="flex gap-3 pt-4 border-t border-white/5">
            <button type="submit" class="apple-button apple-button-primary flex-grow">Conferma Acquisto</button>
            <button type="button" @click="showPromoteModal = false" class="apple-button apple-button-secondary">Annulla</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
