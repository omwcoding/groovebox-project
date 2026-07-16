<!--
Mint - Componente AddToVaultModal
=================================
Modale unificata per aggiungere un album al Vault tramite Zero-Click Import.
Cerca contemporaneamente nel DB locale e tramite le API di Discogs.
-->

<script setup>
import { ref, computed } from 'vue'
import { api } from '@/stores/api'
import ErrorMessage from '@/components/ErrorMessage.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { FORMAT_OPTIONS as formatOptions, CONDITION_OPTIONS as conditionOptions } from '@/constants/music'

const emit = defineEmits(['close', 'added'])

const searchInput = ref('')
const searchLoading = ref(false)
const searchResults = ref([])
const hasSearched = ref(false)

const selectedAlbum = ref(null)
const format = ref('Vinile')
const condition = ref('Nuovo')
const personal_notes = ref('')

const formError = ref('')
const formLoading = ref(false)

// Cerca nel DB locale + Discogs
async function handleSearch() {
  const query = searchInput.value.trim()
  if (!query) return

  searchLoading.value = true
  hasSearched.value = true
  formError.value = ''
  
  try {
    const res = await api.get(`/discogs/search/unified?q=${encodeURIComponent(query)}`)
    searchResults.value = res.data
  } catch (err) {
    formError.value = err.message || 'Errore durante la ricerca'
  } finally {
    searchLoading.value = false
  }
}

function selectAlbum(album) {
  selectedAlbum.value = album
  formError.value = ''
}

function resetSelection() {
  selectedAlbum.value = null
  format.value = 'Vinile'
  condition.value = 'Nuovo'
  personal_notes.value = ''
  formError.value = ''
}

async function handleSubmit() {
  if (!selectedAlbum.value) return

  formLoading.value = true
  formError.value = ''

  try {
    let albumId = null

    // 1. Se il disco proviene da Discogs, lo importiamo prima nel DB locale
    if (selectedAlbum.value.source === 'discogs') {
      const importRes = await api.post('/discogs/import/album', {
        discogs_id: selectedAlbum.value.discogs_id
      })
      albumId = importRes.data.id_album
    } else {
      albumId = selectedAlbum.value.id_album
    }

    // 2. Aggiunge la copia fisica legata all'album localizzato
    await api.post('/copies', {
      id_album: albumId,
      format: format.value,
      condition: condition.value,
      personal_notes: personal_notes.value.trim() || null
    })

    emit('added')
    emit('close')
  } catch (err) {
    formError.value = err.message || 'Errore durante il salvataggio nel Vault'
  } finally {
    formLoading.value = false
  }
}

const getSourceBadgeClass = (source) => {
  return source === 'local' 
    ? 'bg-brand-secondary/15 border-brand-secondary/30 text-brand-secondary' 
    : 'bg-white/5 border-white/10 text-white/50'
}
</script>

<template>
  <div class="fixed inset-0 z-[150] flex items-center justify-center p-4">
    <!-- Sfondo oscurato sfocato -->
    <div @click="emit('close')" class="absolute inset-0 bg-black/60 backdrop-blur-md"></div>

    <!-- Contenuto Modale -->
    <div class="relative glass-panel w-full max-w-lg rounded-apple-3xl shadow-2xl border border-white/10 overflow-hidden z-10 flex flex-col max-h-[90vh]">
      <!-- Header -->
      <div class="p-6 border-b border-white/5 flex items-center justify-between shrink-0">
        <h3 class="text-xl font-bold">Aggiungi al Vault</h3>
        <button 
          @click="emit('close')" 
          class="text-white/40 hover:text-white transition-colors rounded-full w-8 h-8 flex items-center justify-center bg-white/5"
        >
          ✕
        </button>
      </div>

      <!-- Errore globale -->
      <ErrorMessage v-if="formError" :message="formError" class="mx-6 mt-4 shrink-0" />

      <!-- Corpo scorrevole -->
      <div class="p-6 overflow-y-auto flex-grow space-y-6">
        <!-- FASE 1: Ricerca e Selezione -->
        <div v-if="!selectedAlbum" class="space-y-4">
          <!-- Input di Ricerca -->
          <form @submit.prevent="handleSearch" class="flex gap-2">
            <input 
              v-model="searchInput"
              type="text" 
              placeholder="Cerca album su Discogs o catalogo..." 
              required
              class="apple-input flex-grow"
            />
            <button type="submit" class="apple-button apple-button-primary !py-2.5 px-5 shrink-0">
              Cerca
            </button>
          </form>

          <!-- Stato di caricamento ricerca -->
          <div v-if="searchLoading" class="py-12 flex justify-center">
            <LoadingSpinner />
          </div>

          <!-- Risultati Ricerca -->
          <div v-else-if="hasSearched" class="space-y-2">
            <p class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1 mb-2">Risultati di ricerca</p>
            <div 
              v-if="searchResults.length > 0" 
              class="space-y-2 max-h-72 overflow-y-auto divide-y divide-white/5 border border-white/5 rounded-2xl bg-white/[0.01]"
            >
              <div 
                v-for="album in searchResults" 
                :key="album.discogs_id || album.id_album"
                @click="selectAlbum(album)"
                class="flex items-center gap-4 p-3 hover:bg-white/5 cursor-pointer transition-colors text-left"
              >
                <!-- Thumbnail -->
                <div class="w-10 h-10 bg-white/5 rounded-lg overflow-hidden shrink-0 flex items-center justify-center">
                  <img v-if="album.thumb || album.cover_path" :src="album.cover_path ? `/api/albums/${album.id_album}/cover` : album.thumb" class="w-full h-full object-cover" />
                  <span v-else class="text-sm">&#127925;</span>
                </div>
                
                <!-- Info -->
                <div class="min-w-0 flex-grow">
                  <span class="font-bold text-sm block truncate text-white/95">{{ album.title }}</span>
                  <span class="text-xs text-white/40 block truncate mt-0.5">
                    {{ album.artist_name || album.artists?.map(a => a.name).join(', ') }}
                    <span v-if="album.year || album.release_year"> &middot; {{ album.year || album.release_year }}</span>
                  </span>
                </div>

                <!-- Badge provenienza -->
                <span :class="[getSourceBadgeClass(album.source), 'px-2 py-0.5 border rounded text-[9px] font-bold uppercase tracking-wider shrink-0']">
                  {{ album.source === 'local' ? 'Salvato' : 'Discogs' }}
                </span>
              </div>
            </div>
            <div v-else class="text-center py-10 text-white/30 italic text-sm">
              Nessun album trovato. Controlla il titolo o prova un altro termine.
            </div>
          </div>
        </div>

        <!-- FASE 2: Configurazione della copia fisica -->
        <div v-else class="space-y-6 animate-fade-in">
          <!-- Album Selezionato Info Card -->
          <div class="flex items-center gap-4 p-4 border border-white/10 rounded-2xl bg-white/[0.02]">
            <div class="w-14 h-14 bg-white/5 border border-white/5 rounded-xl overflow-hidden shrink-0 flex items-center justify-center">
              <img v-if="selectedAlbum.thumb || selectedAlbum.cover_path" :src="selectedAlbum.cover_path ? `/api/albums/${selectedAlbum.id_album}/cover` : selectedAlbum.thumb" class="w-full h-full object-cover" />
              <span v-else class="text-xl">&#127925;</span>
            </div>
            <div class="min-w-0 flex-grow">
              <span class="font-extrabold text-white text-base block truncate">{{ selectedAlbum.title }}</span>
              <span class="text-xs text-white/40 block truncate mt-0.5">
                {{ selectedAlbum.artist_name || selectedAlbum.artists?.map(a => a.name).join(', ') }}
              </span>
            </div>
            <button 
              @click="resetSelection" 
              class="text-xs font-bold text-brand-secondary hover:underline shrink-0"
              :disabled="formLoading"
            >
              Cambia
            </button>
          </div>

          <!-- Stato di caricamento importazione/salvataggio -->
          <div v-if="formLoading" class="py-12 flex flex-col items-center gap-3">
            <LoadingSpinner />
            <p class="text-xs text-white/40 font-semibold tracking-wider uppercase animate-pulse">
              {{ selectedAlbum.source === 'discogs' ? 'Importazione album e aggiunta...' : 'Aggiunta al Vault...' }}
            </p>
          </div>

          <form v-else @submit.prevent="handleSubmit" class="space-y-5">
            <!-- Formato (Visual Grid Selectors) -->
            <div class="space-y-2">
              <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Formato</label>
              <div class="grid grid-cols-3 gap-2">
                <button
                  v-for="opt in formatOptions"
                  :key="opt"
                  type="button"
                  @click="format = opt"
                  :class="format === opt ? 'bg-brand-secondary/20 border-brand-secondary text-white shadow-lg shadow-brand-secondary/5' : 'bg-white/5 border-white/5 text-white/55 hover:bg-white/10'"
                  class="py-2.5 border rounded-xl text-xs font-bold transition-all"
                >
                  {{ opt }}
                </button>
              </div>
            </div>

            <!-- Condizione -->
            <div class="space-y-2">
              <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Condizione</label>
              <div class="relative">
                <select v-model="condition" class="apple-input appearance-none cursor-pointer">
                  <option v-for="c in conditionOptions" :key="c" :value="c">{{ c }}</option>
                </select>
                <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>
                </div>
              </div>
            </div>

            <!-- Note Personali -->
            <div class="space-y-2">
              <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Note personali</label>
              <textarea 
                v-model="personal_notes" 
                rows="2" 
                placeholder="Edizione limitata, colore vinile, note d'acquisto..." 
                class="apple-input resize-none"
              ></textarea>
            </div>

            <!-- Buttons -->
            <div class="flex gap-3 pt-4 border-t border-white/5">
              <button 
                type="submit" 
                class="apple-button apple-button-primary flex-grow justify-center"
              >
                Aggiungi al Vault
              </button>
              <button 
                type="button" 
                @click="resetSelection" 
                class="apple-button apple-button-secondary shrink-0"
              >
                Annulla
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
