<!--
Mint - Pagina Ricerca Unificata (Catalogo Album)
==============================================
Consente la ricerca globale all'interno del catalogo locale e su Discogs API.
Gestisce l'importazione in background al click dei risultati esterni.
Include un modulo collassabile per l'aggiunta manuale di nuovi album.
-->

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/stores/api'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import AlbumCard from '@/components/AlbumCard.vue'
import { GENRE_OPTIONS } from '@/constants/music'

const authStore = useAuthStore()
const router = useRouter()

const localAlbums = ref([])
const searchResults = ref([])
const loading = ref(true)
const searchQuery = ref('')
const hasSearched = ref(false)
const searchLoading = ref(false)

const showManualForm = ref(false)
const formError = ref('')
const formLoading = ref(false)
const importLoading = ref(false)

const form = ref({
  title: '',
  releaseYear: '',
  genre: '',
  artist_ids: []
})
const coverFile = ref(null)
const coverPreview = ref(null)

const artists = ref([])

onMounted(async () => {
  try {
    const [albumRes, artistRes] = await Promise.all([
      api.get('/albums'),
      api.get('/artists')
    ])
    localAlbums.value = albumRes.data
    artists.value = artistRes.data
  } catch (_) {
    // Gestione silenziosa
  } finally {
    loading.value = false
  }
})

// Debouncing per la ricerca unificata
let debounceTimeout = null
watch(searchQuery, (newVal) => {
  clearTimeout(debounceTimeout)
  if (!newVal.trim()) {
    searchResults.value = []
    hasSearched.value = false
    return
  }
  searchLoading.value = true
  debounceTimeout = setTimeout(async () => {
    try {
      const res = await api.get(`/discogs/search/unified?q=${encodeURIComponent(newVal.trim())}`)
      searchResults.value = res.data
      hasSearched.value = true
    } catch (err) {
      formError.value = err.message || 'Errore durante la ricerca unificata'
    } finally {
      searchLoading.value = false
    }
  }, 400)
})

// Gestione click sul risultato della ricerca
async function handleSelectResult(item) {
  if (item.source === 'local') {
    router.push(`/albums/${item.id_album}`)
  } else {
    // Importazione automatica da Discogs al click
    importLoading.value = true
    formError.value = ''
    try {
      const res = await api.post('/discogs/import/album', { discogs_id: item.discogs_id })
      const newAlbum = res.data
      router.push(`/albums/${newAlbum.id_album}`)
    } catch (err) {
      formError.value = err.message || "Errore durante l'importazione automatica"
      importLoading.value = false
    }
  }
}

// Upload copertina per form manuale
function handleCoverPick(e) {
  const file = e.target.files[0]
  if (!file) return
  coverFile.value = file
  coverPreview.value = URL.createObjectURL(file)
}

function resetForm() {
  form.value = { title: '', releaseYear: '', genre: '', artist_ids: [] }
  coverFile.value = null
  coverPreview.value = null
  formError.value = ''
  showManualForm.value = false
  artistSearchInput.value = ''
  isArtistDropdownOpen.value = false
}

// Aggiunta manuale album
async function handleCreateManual() {
  formError.value = ''
  if (!form.value.title.trim()) {
    formError.value = 'Il titolo è obbligatorio'
    return
  }
  formLoading.value = true
  try {
    const payload = {
      title: form.value.title,
      releaseYear: form.value.releaseYear ? parseInt(form.value.releaseYear) : null,
      genre: form.value.genre || null,
      artist_ids: form.value.artist_ids
    }
    const res = await api.post('/albums', payload)
    const newAlbum = res.data

    if (coverFile.value) {
      const fd = new FormData()
      fd.append('file', coverFile.value)
      try {
        const coverRes = await api.post(`/albums/${newAlbum.id_album}/cover`, fd)
        newAlbum.coverPath = coverRes.coverPath
      } catch (_) {}
    }

    localAlbums.value.unshift(newAlbum)
    resetForm()
    router.push(`/albums/${newAlbum.id_album}`)
  } catch (err) {
    formError.value = err.message || 'Errore durante la creazione manuale'
  } finally {
    formLoading.value = false
  }
}

// Gestione associazione artisti nel form manuale
const artistSearchInput = ref('')
const isArtistDropdownOpen = ref(false)

const filteredArtistsForSelect = computed(() => {
  const query = artistSearchInput.value.toLowerCase().trim()
  if (!query) return []
  return artists.value.filter(a => 
    !form.value.artist_ids.includes(a.id_artist) &&
    a.name.toLowerCase().includes(query)
  )
})

const showCreateOption = computed(() => {
  const query = artistSearchInput.value.trim()
  if (!query) return false
  return !artists.value.some(a => a.name.toLowerCase() === query.toLowerCase())
})

function getArtistNameById(id) {
  const a = artists.value.find(ar => ar.id_artist === id)
  return a ? a.name : ''
}

function associateExistingArtist(artist) {
  if (!form.value.artist_ids.includes(artist.id_artist)) {
    form.value.artist_ids.push(artist.id_artist)
  }
  artistSearchInput.value = ''
  isArtistDropdownOpen.value = false
}

async function createAndAssociateArtist(name) {
  if (!name.trim()) return
  try {
    const res = await api.post('/artists', { name: name.trim() })
    artists.value.unshift(res.data)
    form.value.artist_ids.push(res.data.id_artist)
    artistSearchInput.value = ''
    isArtistDropdownOpen.value = false
  } catch (err) {
    formError.value = err.message || "Errore durante la creazione dell'artista"
  }
}

function toggleArtist(id) {
  const idx = form.value.artist_ids.indexOf(id)
  if (idx >= 0) form.value.artist_ids.splice(idx, 1)
  else form.value.artist_ids.push(id)
}
</script>

<template>
  <div class="space-y-8 animate-fade-in pb-20">
    <!-- Overlay Caricamento Importazione -->
    <div v-if="importLoading" class="fixed inset-0 z-[200] bg-black/80 backdrop-blur-md flex flex-col items-center justify-center gap-4">
      <LoadingSpinner />
      <p class="text-xs text-white/40 font-bold uppercase tracking-widest animate-pulse">Importazione album in corso...</p>
    </div>

    <!-- Header -->
    <div class="space-y-1">
      <h1 class="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
        Esplora Musica
      </h1>
      <p class="text-white/40 text-lg font-medium">Cerca album nel catalogo locale o nel database globale di Discogs.</p>
    </div>

    <!-- Barra di Ricerca Unificata -->
    <div class="relative w-full">
      <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none opacity-30">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
      </div>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Inserisci titolo o artista..."
        class="w-full bg-white/5 border border-white/5 text-white text-sm rounded-full pl-12 pr-4 py-4 focus:outline-none focus:bg-white/10 transition-all font-medium placeholder:text-white/20"
      />
    </div>

    <ErrorMessage v-if="formError" :message="formError" />

    <!-- Spinner Ricerca -->
    <div v-if="searchLoading" class="py-20 flex justify-center">
      <LoadingSpinner />
    </div>

    <!-- STATO 1: Risultati Ricerca Unificata -->
    <div v-else-if="hasSearched" class="space-y-6">
      <h2 class="text-sm font-bold uppercase tracking-widest text-white/30 ml-1">Risultati della ricerca unificata</h2>
      
      <div v-if="searchResults.length > 0" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        <div
          v-for="album in searchResults"
          :key="album.discogs_id || album.id_album"
          @click="handleSelectResult(album)"
          class="group glass-card p-4 flex gap-4 hover:scale-[1.02] hover:shadow-2xl transition-all duration-300 border border-white/5 cursor-pointer"
        >
          <!-- Copertina -->
          <div class="w-20 h-20 bg-white/5 rounded-xl overflow-hidden shrink-0 flex items-center justify-center relative shadow-md">
            <img v-if="album.thumb || album.coverPath" :src="album.coverPath ? `/api/albums/${album.id_album}/cover` : album.thumb" class="w-full h-full object-cover" />
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="opacity-15"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
          </div>
          <!-- Info -->
          <div class="min-w-0 flex flex-col justify-between py-1 flex-grow">
            <div>
              <p class="font-bold text-white/90 group-hover:text-brand-secondary transition-colors truncate">{{ album.title }}</p>
              <p class="text-xs text-white/50 truncate">{{ album.artist_name || album.artists?.map(a => a.name).join(', ') }}</p>
            </div>
            <div class="flex gap-2 text-[10px] font-bold uppercase tracking-wider">
              <span class="px-2 py-0.5 rounded border text-[9px] font-bold uppercase tracking-wider transition-all"
                :class="album.source === 'local' ? 'bg-brand-secondary/15 border-brand-secondary/30 text-brand-secondary' : 'bg-white/5 border-white/10 text-white/40'"
              >
                {{ album.source === 'local' ? 'Nel catalogo' : 'Discogs' }}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else class="text-center py-20 text-white/30 italic text-sm">
        Nessun album trovato corrispondente alla ricerca.
      </div>
    </div>

    <!-- STATO 2: Catalogo Locale Iniziale -->
    <div v-else class="space-y-6">
      <h2 class="text-sm font-bold uppercase tracking-widest text-white/30 ml-1">Catalogo Locale</h2>
      <LoadingSpinner v-if="loading" />
      <div v-else-if="localAlbums.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-x-6 gap-y-10">
        <AlbumCard
          v-for="(album, index) in localAlbums"
          :key="album.id_album"
          :idAlbum="album.id_album"
          :title="album.title"
          :artists="album.artists"
          :coverPath="album.coverPath"
          :genre="album.genre"
          :releaseYear="album.releaseYear"
          :to="`/albums/${album.id_album}`"
          :index="index"
        />
      </div>
      <div v-else class="text-center py-20 text-white/30 italic text-sm">
        Il catalogo è vuoto. Effettua una ricerca in alto per importare o creare musica.
      </div>
    </div>

    <!-- SEZIONE INSERIMENTO MANUALE (COLLASSABILE) -->
    <div v-if="authStore.isCollector && !loading" class="pt-10 border-t border-white/5 flex flex-col items-center">
      <button 
        @click="showManualForm = !showManualForm"
        class="text-xs font-bold uppercase tracking-widest text-brand-secondary hover:text-brand-secondary/85 hover:underline flex items-center gap-1.5"
      >
        {{ showManualForm ? 'Nascondi aggiunta manuale' : 'Non trovi l\'album? Aggiungilo manualmente' }}
      </button>

      <transition name="page">
        <div v-if="showManualForm" class="w-full max-w-2xl glass-panel p-6 md:p-8 rounded-apple-2xl shadow-2xl border border-white/10 mt-6 text-left">
          <h3 class="text-xl font-bold mb-6 text-center">Inserimento Manuale Album</h3>
          
          <form @submit.prevent="handleCreateManual" class="space-y-6">
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div class="sm:col-span-2 space-y-2">
                <label for="album-title" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Titolo dell'album *</label>
                <input id="album-title" v-model="form.title" type="text" required placeholder="Es. Abbey Road" class="apple-input" />
              </div>
              <div class="space-y-2">
                <label for="album-year" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Anno di uscita</label>
                <input id="album-year" v-model="form.releaseYear" type="number" min="1900" max="2026" placeholder="Es. 1969" class="apple-input" />
              </div>
            </div>
            <div class="space-y-2">
              <label for="album-genre" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Genere</label>
              <select id="album-genre" v-model="form.genre" class="apple-input">
                <option value="">Nessun genere (seleziona per modificare)</option>
                <option v-for="g in GENRE_OPTIONS" :key="g" :value="g">{{ g }}</option>
              </select>
            </div>

            <!-- Artisti associazione -->
            <div class="space-y-3 relative z-40">
              <!-- Overlay chiusura -->
              <div v-if="isArtistDropdownOpen" @click="isArtistDropdownOpen = false" class="fixed inset-0 z-30 bg-transparent"></div>

              <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Associa Artisti *</label>
              
              <div v-if="form.artist_ids.length > 0" class="flex flex-wrap gap-2 p-2 border border-white/5 rounded-2xl bg-white/[0.02]">
                <div 
                  v-for="id in form.artist_ids" 
                  :key="id"
                  class="flex items-center gap-2 px-3 py-1.5 bg-brand-secondary/20 border border-brand-secondary/30 text-white text-xs font-semibold rounded-full hover:bg-brand-secondary/35 transition-colors"
                >
                  <span>{{ getArtistNameById(id) }}</span>
                  <button type="button" @click="toggleArtist(id)" class="text-white/40 hover:text-white rounded-full w-4 h-4 flex items-center justify-center text-[10px] bg-white/5 hover:bg-white/10">
                    ✕
                  </button>
                </div>
              </div>

              <div class="relative z-40">
                <input 
                  v-model="artistSearchInput" 
                  type="text" 
                  @focus="isArtistDropdownOpen = true"
                  placeholder="Cerca un artista o digitalo per aggiungerlo..." 
                  class="apple-input pr-10"
                  @keyup.enter.prevent="showCreateOption && createAndAssociateArtist(artistSearchInput)"
                />
                <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                </div>

                <div v-if="isArtistDropdownOpen && (filteredArtistsForSelect.length > 0 || showCreateOption)" class="absolute left-0 right-0 mt-2 max-h-52 overflow-y-auto bg-black/95 backdrop-blur-md border border-white/10 rounded-2xl shadow-2xl z-50 divide-y divide-white/5">
                  <div 
                    v-for="artist in filteredArtistsForSelect" 
                    :key="artist.id_artist"
                    @click="associateExistingArtist(artist)"
                    class="p-3 text-sm text-white/80 hover:text-white hover:bg-brand-secondary/20 cursor-pointer transition-colors text-left font-semibold"
                  >
                    {{ artist.name }}
                  </div>
                  <div 
                    v-if="showCreateOption"
                    @click="createAndAssociateArtist(artistSearchInput)"
                    class="p-3 text-sm text-brand-secondary hover:bg-brand-secondary/10 cursor-pointer transition-colors text-left font-bold flex items-center gap-2"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
                    Crea e aggiungi "{{ artistSearchInput.trim() }}"
                  </div>
                </div>
              </div>
            </div>

            <!-- Copertina -->
            <div class="space-y-2">
              <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Copertina (opzionale)</label>
              <label class="flex items-center gap-4 cursor-pointer group">
                <div class="w-20 h-20 rounded-2xl bg-white/5 border border-white/10 overflow-hidden flex items-center justify-center shrink-0 group-hover:border-white/20 transition-colors">
                  <img v-if="coverPreview" :src="coverPreview" class="w-full h-full object-cover" />
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" class="opacity-20"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                </div>
                <div class="space-y-1">
                  <p class="text-sm font-semibold text-white/60 group-hover:text-white transition-colors">{{ coverFile ? coverFile.name : 'Scegli un\'immagine' }}</p>
                  <p class="text-[10px] text-white/30">JPG, PNG o WebP</p>
                </div>
                <input type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="handleCoverPick" />
              </label>
            </div>

            <div class="pt-4 flex gap-3 border-t border-white/5">
              <button type="submit" :disabled="formLoading" class="apple-button apple-button-primary">
                {{ formLoading ? 'Salvataggio...' : 'Crea Album' }}
              </button>
              <button type="button" @click="resetForm" class="apple-button apple-button-secondary">
                Annulla
              </button>
            </div>
          </form>
        </div>
      </transition>
    </div>
  </div>
</template>
