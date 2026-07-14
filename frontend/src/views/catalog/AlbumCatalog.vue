<!--
GrooveBox - Pagina Catalogo Album
=================================
Consente la visualizzazione dei dischi registrati a catalogo tramite filtri di ricerca.
Include il form di inserimento per nuovi album (riservato ai Collector) con ricerca
e associazione dinamica degli artisti.
-->

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/stores/api'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import AlbumCard from '@/components/AlbumCard.vue'
import { GENRE_OPTIONS } from '@/constants/music'

const authStore = useAuthStore()

const albums = ref([])
const artists = ref([])
const loading = ref(true)
const search = ref('')
const showForm = ref(false)
const formError = ref('')
const formLoading = ref(false)

const form = ref({
  title: '',
  releaseYear: '',
  genre: '',
  artist_ids: []
})
const coverFile = ref(null)
const coverPreview = ref(null)

// Discogs search and import state
const activeTab = ref('discogs')
const discogsQuery = ref('')
const discogsResults = ref([])
const discogsSearchLoading = ref(false)
const discogsImportLoadingId = ref(null)

async function handleDiscogsSearch() {
  const query = discogsQuery.value.trim()
  if (!query) return
  discogsSearchLoading.value = true
  formError.value = ''
  try {
    const res = await api.get(`/discogs/search/album?q=${encodeURIComponent(query)}`)
    discogsResults.value = res.data
  } catch (err) {
    formError.value = err.message || 'Errore nella ricerca su Discogs'
  } finally {
    discogsSearchLoading.value = false
  }
}

async function handleDiscogsImport(discogsId) {
  discogsImportLoadingId.value = discogsId
  formError.value = ''
  try {
    const res = await api.post('/discogs/import/album', { discogs_id: discogsId })
    albums.value.unshift(res.data)
    
    // Aggiorna gli artisti locali in caso siano stati inseriti nuovi artisti durante l'import
    const artistRes = await api.get('/artists')
    artists.value = artistRes.data
    
    resetForm()
  } catch (err) {
    formError.value = err.message || "Errore durante l'importazione"
  } finally {
    discogsImportLoadingId.value = null
  }
}

function handleCoverPick(e) {
  const file = e.target.files[0]
  if (!file) return
  coverFile.value = file
  coverPreview.value = URL.createObjectURL(file)
}

const filteredAlbums = computed(() => {
  if (!search.value.trim()) return albums.value
  const q = search.value.toLowerCase()
  return albums.value.filter(a =>
    a.title.toLowerCase().includes(q) ||
    a.genre?.toLowerCase().includes(q) ||
    a.artists?.some(ar => ar.name.toLowerCase().includes(q))
  )
})

onMounted(async () => {
  try {
    const [albumRes, artistRes] = await Promise.all([
      api.get('/albums'),
      api.get('/artists')
    ])
    albums.value = albumRes.data
    artists.value = artistRes.data
  } catch (_) {
    // Errore silenzioso: la UI mostra già uno stato vuoto
  } finally {
    loading.value = false
  }
})

function resetForm() {
  form.value = { title: '', releaseYear: '', genre: '', artist_ids: [] }
  coverFile.value = null
  coverPreview.value = null
  formError.value = ''
  showForm.value = false
  artistSearchInput.value = ''
  isArtistDropdownOpen.value = false
  discogsQuery.value = ''
  discogsResults.value = []
}

async function handleCreate() {
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

    // Upload copertina se selezionata
    if (coverFile.value) {
      const fd = new FormData()
      fd.append('file', coverFile.value)
      try {
        const coverRes = await api.post(`/albums/${newAlbum.id_album}/cover`, fd)
        newAlbum.coverPath = coverRes.coverPath
      } catch (_) { /* cover non bloccante */ }
    }

    albums.value.unshift(newAlbum)
    resetForm()
  } catch (err) {
    formError.value = err.message || 'Errore durante la creazione'
  } finally {
    formLoading.value = false
  }
}

function toggleArtist(id) {
  const idx = form.value.artist_ids.indexOf(id)
  if (idx >= 0) form.value.artist_ids.splice(idx, 1)
  else form.value.artist_ids.push(id)
}

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

function closeArtistDropdown() {
  isArtistDropdownOpen.value = false
}
</script>

<template>
  <div class="space-y-8 animate-fade-in">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6">
      <div class="space-y-1">
        <h1 class="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
          Catalogo Album
        </h1>
        <p class="text-white/40 text-lg font-medium">{{ albums.length }} album disponibili nell'hub globale.</p>
      </div>
      
      <button
        v-if="authStore.isCollector"
        @click="showForm = !showForm"
        class="apple-button apple-button-primary shadow-xl shadow-white/5 self-start sm:self-auto"
      >
        <svg v-if="!showForm" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        {{ showForm ? 'Annulla' : 'Aggiungi disco' }}
      </button>
    </div>

    <!-- Form Nuovo Album -->
    <transition name="page">
      <div v-if="showForm" class="glass-panel p-6 md:p-8 rounded-apple-2xl shadow-2xl">
        <h3 class="text-2xl font-bold mb-4 text-center">Aggiungi un nuovo album</h3>
        
        <!-- Tab Selector -->
        <div class="flex border-b border-white/10 mb-6 justify-center">
          <button 
            type="button" 
            @click="activeTab = 'discogs'"
            :class="['px-6 py-2.5 font-bold text-sm border-b-2 transition-all', activeTab === 'discogs' ? 'border-brand-secondary text-brand-secondary font-extrabold' : 'border-transparent text-white/50 hover:text-white']"
          >
            Importa da Discogs
          </button>
          <button 
            type="button" 
            @click="activeTab = 'manual'"
            :class="['px-6 py-2.5 font-bold text-sm border-b-2 transition-all', activeTab === 'manual' ? 'border-brand-secondary text-brand-secondary font-extrabold' : 'border-transparent text-white/50 hover:text-white']"
          >
            Inserimento Manuale
          </button>
        </div>

        <ErrorMessage v-if="formError" :message="formError" />

        <!-- Tab Discogs -->
        <div v-if="activeTab === 'discogs'" class="space-y-6">
          <div class="space-y-2">
            <label for="discogs-query" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Cerca album o artista su Discogs</label>
            <div class="flex gap-3">
              <input 
                id="discogs-query" 
                v-model="discogsQuery" 
                type="text" 
                placeholder="Es. Dark Side of the Moon, Nevermind..." 
                class="apple-input flex-grow font-semibold"
                @keyup.enter="handleDiscogsSearch"
              />
              <button 
                type="button" 
                @click="handleDiscogsSearch" 
                :disabled="discogsSearchLoading"
                class="apple-button apple-button-primary shadow-lg shadow-white/5 whitespace-nowrap font-bold text-sm px-6"
              >
                {{ discogsSearchLoading ? 'Cerca...' : 'Cerca' }}
              </button>
            </div>
          </div>

          <!-- Risultati Discogs -->
          <div v-if="discogsResults.length > 0" class="space-y-3 max-h-80 overflow-y-auto divide-y divide-white/5 pr-2">
            <div 
              v-for="item in discogsResults" 
              :key="item.discogs_id"
              class="flex items-center justify-between gap-4 py-3 first:pt-0"
            >
              <div class="flex items-center gap-4 min-w-0">
                <!-- Cover thumbnail -->
                <div class="w-12 h-12 rounded-lg bg-white/5 border border-white/5 overflow-hidden flex items-center justify-center shrink-0">
                  <img v-if="item.thumb" :src="item.thumb" class="w-full h-full object-cover" referrerpolicy="no-referrer" />
                  <span v-else class="text-xl">&#127925;</span>
                </div>
                <!-- Info -->
                <div class="min-w-0">
                  <p class="font-bold text-sm text-white truncate">{{ item.title }}</p>
                  <p class="text-xs text-white/50 font-medium truncate">
                    {{ item.artist_name || 'Artista Sconosciuto' }} 
                    <span v-if="item.year" class="text-white/30">&middot; {{ item.year }}</span>
                  </p>
                  <span class="inline-block mt-1 text-[9px] font-bold uppercase tracking-wider text-brand-secondary bg-brand-secondary/10 px-2 py-0.5 rounded-full">
                    {{ item.genre }}
                  </span>
                </div>
              </div>

              <!-- Action -->
              <button 
                type="button" 
                @click="handleDiscogsImport(item.discogs_id)"
                :disabled="discogsImportLoadingId !== null"
                class="apple-button apple-button-primary !py-1.5 !px-4 text-xs shadow-md font-bold whitespace-nowrap"
              >
                <span v-if="discogsImportLoadingId === item.discogs_id">Importazione...</span>
                <span v-else>Importa</span>
              </button>
            </div>
          </div>
          <div v-else-if="discogsQuery && !discogsSearchLoading" class="text-center py-6 text-white/30 text-sm font-semibold">
            Nessun risultato trovato. Prova un'altra ricerca.
          </div>
          
          <div class="pt-4 border-t border-white/5 flex gap-3">
            <button type="button" @click="resetForm" class="apple-button apple-button-secondary w-full sm:w-auto">
              Annulla
            </button>
          </div>
        </div>

        <!-- Tab Manuale -->
        <form v-else @submit.prevent="handleCreate" class="space-y-6">
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

          <!-- Selezione artisti con ricerca e aggiunta rapida -->
          <div class="space-y-3 relative z-40">
            <!-- Overlay invisibile per chiudere la tendina al click fuori -->
            <div v-if="isArtistDropdownOpen" @click="closeArtistDropdown" class="fixed inset-0 z-30 bg-transparent"></div>

            <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Associa Artisti *</label>

            <!-- Artisti attualmente selezionati -->
            <div v-if="form.artist_ids.length > 0" class="flex flex-wrap gap-2 p-2 border border-white/5 rounded-2xl bg-white/[0.02]">
              <div 
                v-for="id in form.artist_ids" 
                :key="id"
                class="flex items-center gap-2 px-3 py-1.5 bg-brand-secondary/20 border border-brand-secondary/30 text-white text-xs font-semibold rounded-full hover:bg-brand-secondary/35 transition-colors"
              >
                <span>{{ getArtistNameById(id) }}</span>
                <button 
                  type="button" 
                  @click="toggleArtist(id)" 
                  class="text-white/40 hover:text-white rounded-full w-4 h-4 flex items-center justify-center text-[10px] bg-white/5 hover:bg-white/10"
                >
                  ✕
                </button>
              </div>
            </div>

            <!-- Input di ricerca/aggiunta -->
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

              <!-- Menu a tendina per artisti -->
              <div v-if="isArtistDropdownOpen && (filteredArtistsForSelect.length > 0 || showCreateOption)" class="absolute left-0 right-0 mt-2 max-h-52 overflow-y-auto bg-black/95 backdrop-blur-md border border-white/10 rounded-2xl shadow-2xl z-50 divide-y divide-white/5">
                <!-- Artisti Esistenti trovati -->
                <div 
                  v-for="artist in filteredArtistsForSelect" 
                  :key="artist.id_artist"
                  @click="associateExistingArtist(artist)"
                  class="p-3 text-sm text-white/80 hover:text-white hover:bg-brand-secondary/20 cursor-pointer transition-colors text-left font-semibold"
                >
                  {{ artist.name }}
                </div>
                
                <!-- Aggiungi Nuovo Artista (opzione dinamica) -->
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

          <!-- Copertina album -->
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

          <div class="pt-4 flex flex-col sm:flex-row gap-3">
            <button type="submit" :disabled="formLoading"
              class="apple-button apple-button-primary w-full sm:w-auto shadow-xl shadow-white/5">
              {{ formLoading ? 'Pubblicazione...' : 'Pubblica Album' }}
            </button>
            <button type="button" @click="resetForm" class="apple-button apple-button-secondary w-full sm:w-auto">
              Annulla
            </button>
          </div>
        </form>
      </div>
    </transition>

    <!-- Barra ricerca (Floating Glass Bar style) -->
    <div class="relative w-full">
      <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none opacity-30">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
      </div>
      <input
        v-model="search"
        type="text"
        placeholder="Filtra album per titolo, genere o artista..."
        class="w-full bg-white/5 border border-white/5 text-white text-sm rounded-full pl-11 pr-4 py-3.5 focus:outline-none focus:bg-white/10 transition-all font-medium placeholder:text-white/20"
      />
    </div>

    <!-- Loading -->
    <LoadingSpinner v-if="loading" />

    <!-- Lista album (Apple Grid) -->
    <div v-else-if="filteredAlbums.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-x-6 gap-y-10">
      <AlbumCard
        v-for="(album, index) in filteredAlbums"
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

    <!-- Empty state -->
    <div v-else class="py-20 flex flex-col items-center justify-center gap-6 glass-panel rounded-apple-2xl border-dashed border-white/10 text-center px-10">
      <div class="bg-white/5 p-6 rounded-full">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="opacity-20"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
      </div>
      <div class="space-y-1">
        <p class="text-xl font-bold">Nessun album trovato</p>
        <p class="text-white/40 text-sm">
          {{ search ? 'Modifica il filtro per cercare altri album.' : 'Il catalogo globale è ancora vuoto.' }}
        </p>
      </div>
    </div>
  </div>
</template>
