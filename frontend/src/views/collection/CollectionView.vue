<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { api } from '@/stores/api'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import AlbumCard from '@/components/AlbumCard.vue'
import { FORMAT_OPTIONS as formatOptions, CONDITION_OPTIONS as conditionOptions, GENRE_OPTIONS as genreOptions } from '@/constants/music'

const route = useRoute()

const copies = ref([])
const albums = ref([])
const artists = ref([])
const loading = ref(true)
const search = ref('')
const filterFormat = ref('')
const showForm = ref(false)
const formError = ref('')
const formLoading = ref(false)
const tab = ref('existing') // 'existing' | 'new'

const form = ref({
  id_album: '',
  format: 'Vinile',
  condition: 'Nuovo',
  personalNotes: ''
})

const formNew = ref({
  title: '',
  artist_ids: [],
  releaseYear: '',
  genre: '',
  format: 'Vinile',
  condition: 'Nuovo',
  personalNotes: ''
})
const searchInput = ref('')
const isDropdownOpen = ref(false)

const filteredAlbumsForSelect = computed(() => {
  const query = searchInput.value.toLowerCase().trim()
  if (!query) return albums.value
  return albums.value.filter(album => {
    const titleMatch = album.title?.toLowerCase().includes(query)
    const artistMatch = album.artists?.some(a => a.name?.toLowerCase().includes(query))
    return titleMatch || artistMatch
  })
})

function getAlbumLabel(album) {
  if (!album) return ''
  const artistsStr = album.artists?.map(a => a.name).join(', ') || 'Artista'
  const yearStr = album.releaseYear ? ` (${album.releaseYear})` : ''
  return `${album.title} — ${artistsStr}${yearStr}`
}

function onSearchFocus() {
  isDropdownOpen.value = true
  searchInput.value = ''
}

function selectAlbumForCopy(album) {
  form.value.id_album = album.id_album
  searchInput.value = getAlbumLabel(album)
  isDropdownOpen.value = false
}

function closeDropdown() {
  isDropdownOpen.value = false
  const selected = albums.value.find(a => a.id_album === form.value.id_album)
  if (selected) {
    searchInput.value = getAlbumLabel(selected)
  } else {
    searchInput.value = ''
  }
}

const artistSearchInput = ref('')
const isArtistDropdownOpen = ref(false)
const inlineArtistLoading = ref(false)

const filteredArtistsForSelect = computed(() => {
  const query = artistSearchInput.value.toLowerCase().trim()
  if (!query) return []
  return artists.value.filter(a => 
    !formNew.value.artist_ids.includes(a.id_artist) &&
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
  if (!formNew.value.artist_ids.includes(artist.id_artist)) {
    formNew.value.artist_ids.push(artist.id_artist)
  }
  artistSearchInput.value = ''
  isArtistDropdownOpen.value = false
}

async function createAndAssociateArtist(name) {
  if (!name.trim()) return
  inlineArtistLoading.value = true
  try {
    const res = await api.post('/artists', { name: name.trim() })
    artists.value.unshift(res.data)
    formNew.value.artist_ids.push(res.data.id_artist)
    artistSearchInput.value = ''
    isArtistDropdownOpen.value = false
  } catch (err) {
    formError.value = err.message || "Errore durante la creazione dell'artista"
  } finally {
    inlineArtistLoading.value = false
  }
}

function closeArtistDropdown() {
  isArtistDropdownOpen.value = false
}

function toggleArtist(id) {
  const idx = formNew.value.artist_ids.indexOf(id)
  if (idx >= 0) {
    formNew.value.artist_ids.splice(idx, 1)
  } else {
    formNew.value.artist_ids.push(id)
  }
}

const filteredCopies = computed(() => {
  return copies.value.filter(c => {
    const matchesSearch = !search.value.trim() || 
      c.album_title?.toLowerCase().includes(search.value.toLowerCase()) ||
      c.genre?.toLowerCase().includes(search.value.toLowerCase()) ||
      c.artists?.some(ar => ar.name.toLowerCase().includes(search.value.toLowerCase()))
    
    const matchesFormat = !filterFormat.value || c.format === filterFormat.value
    
    return matchesSearch && matchesFormat
  })
})

onMounted(async () => {
  try {
    const [copiesRes, albumsRes, artistsRes] = await Promise.all([
      api.get('/copies'),
      api.get('/albums'),
      api.get('/artists')
    ])
    copies.value = copiesRes.data
    albums.value = albumsRes.data
    artists.value = artistsRes.data

    // Auto-apri form se arrivo da pagina album con query param
    if (route.query.addAlbum) {
      const albumId = parseInt(route.query.addAlbum)
      form.value.id_album = albumId
      showForm.value = true
      tab.value = 'existing'
      
      const selected = albums.value.find(a => a.id_album === albumId)
      if (selected) {
        searchInput.value = getAlbumLabel(selected)
      }
    }
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
})

function resetForm() {
  form.value = { id_album: '', format: 'Vinile', condition: 'Nuovo', personalNotes: '' }
  formNew.value = { title: '', artist_ids: [], releaseYear: '', genre: '', format: 'Vinile', condition: 'Nuovo', personalNotes: '' }
  formError.value = ''
  showForm.value = false
  searchInput.value = ''
  isDropdownOpen.value = false
  artistSearchInput.value = ''
  isArtistDropdownOpen.value = false
}

async function handleCreate() {
  formError.value = ''
  formLoading.value = true
  
  try {
    if (tab.value === 'existing') {
      if (!form.value.id_album || !form.value.format || !form.value.condition) {
        formError.value = 'Seleziona un album valido dalla lista, formato e condizione sono obbligatori'
        formLoading.value = false
        return
      }
      
      const res = await api.post('/copies', {
        id_album: parseInt(form.value.id_album),
        format: form.value.format,
        condition: form.value.condition,
        personalNotes: form.value.personalNotes || null
      })
      copies.value.unshift(res.data)
      resetForm()
    } else {
      // TAB 'new' - Creazione a cascata tramite singola API transazionale
      const title = formNew.value.title.trim()
      const artistIds = formNew.value.artist_ids
      const format = formNew.value.format
      const condition = formNew.value.condition
      
      if (!title || !artistIds || artistIds.length === 0 || !format || !condition) {
        formError.value = 'Titolo, almeno un Artista, Formato e Condizione sono obbligatori'
        formLoading.value = false
        return
      }
      
      const res = await api.post('/copies/cascade', {
        title: title,
        artist_ids: artistIds,
        releaseYear: formNew.value.releaseYear ? parseInt(formNew.value.releaseYear) : null,
        genre: formNew.value.genre || null,
        format: format,
        condition: condition,
        personalNotes: formNew.value.personalNotes || null
      })
      
      copies.value.unshift(res.data)
      
      // Sincronizza lo stato degli album e artisti per consentire selezioni successive dal catalogo
      const [albumsRes, artistsRes] = await Promise.all([
        api.get('/albums'),
        api.get('/artists')
      ])
      albums.value = albumsRes.data
      artists.value = artistsRes.data
      
      resetForm()
    }
  } catch (err) {
    formError.value = err.message || "Errore durante l'inserimento"
  } finally {
    formLoading.value = false
  }
}
</script>

<template>
  <div class="space-y-8 animate-fade-in pb-20">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6">
      <div class="space-y-1">
        <h1 class="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
          La tua collezione
        </h1>
        <p class="text-white/40 text-lg font-medium">{{ filteredCopies.length }} copie salvate nel tuo archivio.</p>
      </div>
      
      <button @click="showForm = !showForm"
        class="apple-button apple-button-primary shadow-xl shadow-white/5 self-start sm:self-auto">
        <svg v-if="!showForm" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        {{ showForm ? 'Annulla' : 'Aggiungi Copia' }}
      </button>
    </div>

    <!-- Form nuova copia -->
    <transition name="page">
      <div v-if="showForm" class="glass-panel p-6 md:p-8 rounded-apple-2xl shadow-2xl">
        <h3 class="text-2xl font-bold mb-6 text-center">Registra una copia fisica</h3>
        <ErrorMessage v-if="formError" :message="formError" />
        
        <!-- Apple-style Segmented Control -->
        <div class="flex p-1 bg-white/5 border border-white/5 rounded-2xl mb-8 max-w-sm mx-auto">
          <button 
            type="button"
            @click="tab = 'existing'" 
            :class="tab === 'existing' ? 'bg-white/10 text-white shadow-lg' : 'text-white/40 hover:text-white/60'" 
            class="flex-grow py-2.5 rounded-xl text-xs font-bold transition-all"
          >
            Dall'Hub
          </button>
          <button 
            type="button"
            @click="tab = 'new'" 
            :class="tab === 'new' ? 'bg-white/10 text-white shadow-lg' : 'text-white/40 hover:text-white/60'" 
            class="flex-grow py-2.5 rounded-xl text-xs font-bold transition-all"
          >
            Nuovo Disco
          </button>
        </div>

        <form @submit.prevent="handleCreate" class="space-y-6">
          <!-- TAB 1: Existing Album -->
          <div v-if="tab === 'existing'" class="space-y-6 relative z-50">
            <!-- Overlay invisibile per chiudere la tendina al click fuori -->
            <div v-if="isDropdownOpen" @click="closeDropdown" class="fixed inset-0 z-40 bg-transparent"></div>

            <div class="space-y-2 relative z-50">
              <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Seleziona Album *</label>
              <div class="relative">
                <input 
                  type="text"
                  v-model="searchInput"
                  @focus="onSearchFocus"
                  placeholder="Digita per cercare un album..."
                  class="apple-input pr-10 cursor-pointer"
                  required
                />
                <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                </div>

                <!-- Lista a comparsa -->
                <div v-if="isDropdownOpen" class="absolute left-0 right-0 mt-2 max-h-60 overflow-y-auto bg-black/95 backdrop-blur-md border border-white/10 rounded-2xl shadow-2xl z-50 animate-fade-in divide-y divide-white/5">
                  <div 
                    v-for="album in filteredAlbumsForSelect" 
                    :key="album.id_album"
                    @click="selectAlbumForCopy(album)"
                    class="p-3 text-sm text-white/80 hover:text-white hover:bg-brand-secondary/20 cursor-pointer transition-colors text-left"
                  >
                    <span class="font-bold block">{{ album.title }}</span>
                    <span class="text-xs text-white/40 block mt-0.5">
                      {{ album.artists?.map(a => a.name).join(', ') || 'Artista' }} {{ album.releaseYear ? `(${album.releaseYear})` : '' }}
                    </span>
                  </div>
                  <div v-if="filteredAlbumsForSelect.length === 0" class="p-4 text-center text-xs text-white/30 italic">
                    Nessun album trovato nel catalogo
                  </div>
                </div>
              </div>
            </div>
            
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div class="space-y-2">
                <label for="copy-format" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Formato *</label>
                <div class="relative">
                  <select id="copy-format" v-model="form.format" required class="apple-input appearance-none cursor-pointer">
                    <option v-for="f in formatOptions" :key="f" :value="f">{{ f }}</option>
                  </select>
                  <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>
                  </div>
                </div>
              </div>
              
              <div class="space-y-2">
                <label for="copy-condition" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Condizione *</label>
                <div class="relative">
                  <select id="copy-condition" v-model="form.condition" required class="apple-input appearance-none cursor-pointer">
                    <option v-for="c in conditionOptions" :key="c" :value="c">{{ c }}</option>
                  </select>
                  <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="space-y-2">
              <label for="copy-notes" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Note personali</label>
              <textarea id="copy-notes" v-model="form.personalNotes" rows="2"
                class="apple-input resize-none"
                placeholder="Edizione limitata, prima stampa, firmato..."></textarea>
            </div>
          </div>

          <!-- TAB 2: New Album Creation + Copy -->
          <div v-else class="space-y-6">
            <div class="space-y-6 relative z-40">
              <!-- Overlay invisibile per chiudere la tendina al click fuori -->
              <div v-if="isArtistDropdownOpen" @click="closeArtistDropdown" class="fixed inset-0 z-30 bg-transparent"></div>

              <div class="space-y-2">
                <label for="new-album-title" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Titolo Album *</label>
                <input id="new-album-title" v-model="formNew.title" type="text" required placeholder="Es. Let It Be" class="apple-input" />
              </div>

              <!-- Selezione artisti con ricerca e aggiunta rapida -->
              <div class="space-y-3 relative z-40">
                <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Associa Artisti *</label>

                <!-- Artisti attualmente selezionati -->
                <div v-if="formNew.artist_ids.length > 0" class="flex flex-wrap gap-2 p-2 border border-white/5 rounded-2xl bg-white/[0.02]">
                  <div 
                    v-for="id in formNew.artist_ids" 
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
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div class="space-y-2">
                <label for="new-album-year" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Anno di uscita</label>
                <input id="new-album-year" v-model="formNew.releaseYear" type="number" min="1900" max="2099" placeholder="Es. 1970" class="apple-input" />
              </div>
              <div class="space-y-2">
                <label for="new-album-genre" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Genere</label>
                <select id="new-album-genre" v-model="formNew.genre" class="apple-input">
                  <option value="">Nessun genere (seleziona per modificare)</option>
                  <option v-for="g in genreOptions" :key="g" :value="g">{{ g }}</option>
                </select>
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-4 border-t border-white/5">
              <div class="space-y-2">
                <label for="new-copy-format" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Formato *</label>
                <div class="relative">
                  <select id="new-copy-format" v-model="formNew.format" required class="apple-input appearance-none cursor-pointer">
                    <option v-for="f in formatOptions" :key="f" :value="f">{{ f }}</option>
                  </select>
                  <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>
                  </div>
                </div>
              </div>
              
              <div class="space-y-2">
                <label for="new-copy-condition" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Condizione *</label>
                <div class="relative">
                  <select id="new-copy-condition" v-model="formNew.condition" required class="apple-input appearance-none cursor-pointer">
                    <option v-for="c in conditionOptions" :key="c" :value="c">{{ c }}</option>
                  </select>
                  <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="space-y-2">
              <label for="new-copy-notes" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Note personali</label>
              <textarea id="new-copy-notes" v-model="formNew.personalNotes" rows="2"
                class="apple-input resize-none"
                placeholder="Edizione limitata, prima stampa, firmato..."></textarea>
            </div>
          </div>
          
          <div class="pt-4 flex flex-col sm:flex-row gap-3">
            <button type="submit" :disabled="formLoading"
              class="apple-button apple-button-primary w-full sm:w-auto shadow-xl shadow-white/5">
              {{ formLoading ? 'Aggiunta...' : 'Registra copia' }}
            </button>
            <button type="button" @click="resetForm" class="apple-button apple-button-secondary w-full sm:w-auto">
              Annulla
            </button>
          </div>
        </form>
      </div>
    </transition>

    <!-- Filters (Floating Glass Bar) -->
    <div class="glass-panel rounded-apple-xl p-3 flex flex-col sm:flex-row gap-3 items-center border border-white/5 shadow-xl">
      <div class="relative w-full sm:flex-grow">
        <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        </div>
        <input 
          v-model="search" 
          type="text" 
          placeholder="Cerca nella tua collezione..." 
          class="w-full bg-white/5 border border-white/5 text-white text-sm rounded-full pl-11 pr-4 py-3 focus:outline-none focus:bg-white/10 transition-all font-medium placeholder:text-white/20"
        >
      </div>
      
      <div class="relative w-full sm:w-48">
        <select 
          v-model="filterFormat"
          class="w-full bg-white/5 border border-white/5 text-white text-sm rounded-full px-5 py-3 focus:outline-none focus:bg-white/10 appearance-none transition-all cursor-pointer font-medium"
        >
          <option value="">Tutti i formati</option>
          <option v-for="f in formatOptions" :key="f" :value="f">{{ f }}</option>
        </select>
        <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <LoadingSpinner v-if="loading" />

    <!-- Lista copie (Apple Grid) -->
    <div v-else-if="filteredCopies.length > 0" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-x-6 gap-y-10">
      <AlbumCard
        v-for="(copy, index) in filteredCopies"
        :key="copy.id_copy"
        :idAlbum="copy.id_album"
        :title="copy.album_title"
        :artists="copy.artists"
        :coverPath="copy.coverPath"
        :genre="copy.genre"
        :releaseYear="copy.releaseYear"
        :to="`/collection/${copy.id_copy}`"
        :format="copy.format"
        :condition="copy.condition"
        :index="index"
      />
    </div>

    <!-- Empty state -->
    <div v-else class="py-32 flex flex-col items-center justify-center gap-6 glass-panel rounded-apple-2xl border-dashed border-white/10 text-center px-10">
      <div class="bg-white/5 p-6 rounded-full">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="opacity-20"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
      </div>
      <div class="space-y-1">
        <p class="text-xl font-bold">Nessun album trovato</p>
        <p class="text-white/40 text-sm">
          {{ search ? 'Modifica i filtri di ricerca.' : 'La tua collezione personale è ancora vuota.' }}
        </p>
      </div>
      <RouterLink v-if="!search" to="/albums" class="apple-button apple-button-primary mt-2">
        Esplora il catalogo
      </RouterLink>
    </div>
  </div>
</template>
