<!--
Mint - Pagina Dettaglio Album
==================================
Mostra le informazioni dettagliate di un album specifico. Consente agli amministratori
la modifica o l'eliminazione della scheda, e ai collezionisti l'aggiunta rapida
alla propria libreria personale.
-->

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/stores/api'
import BackButton from '@/components/BackButton.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import DetailField from '@/components/DetailField.vue'
import { GENRE_OPTIONS, FORMAT_OPTIONS as formatOptions, CONDITION_OPTIONS as conditionOptions } from '@/constants/music'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const album = ref(null)
const loading = ref(true)
const editing = ref(false)
const error = ref('')
const allArtists = ref([])

const form = ref({ title: '', release_year: '', genre: '', artist_ids: [] })
const coverFile = ref(null)
const coverPreview = ref(null)

const artistSearchInput = ref('')
const isArtistDropdownOpen = ref(false)

const filteredArtistsForSelect = computed(() => {
  const query = artistSearchInput.value.toLowerCase().trim()
  if (!query) return []
  return allArtists.value.filter(a => 
    !form.value.artist_ids.includes(a.id_artist) &&
    a.name.toLowerCase().includes(query)
  )
})

const showCreateOption = computed(() => {
  const query = artistSearchInput.value.trim()
  if (!query) return false
  return !allArtists.value.some(a => a.name.toLowerCase() === query.toLowerCase())
})

function getArtistNameById(id) {
  const a = allArtists.value.find(ar => ar.id_artist === id)
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
    allArtists.value.unshift(res.data)
    form.value.artist_ids.push(res.data.id_artist)
    artistSearchInput.value = ''
    isArtistDropdownOpen.value = false
  } catch (err) {
    error.value = err.message || "Errore durante la creazione dell'artista"
  }
}

function closeArtistDropdown() {
  isArtistDropdownOpen.value = false
}

function handleCoverPick(e) {
  const file = e.target.files[0]
  if (!file) return
  coverFile.value = file
  coverPreview.value = URL.createObjectURL(file)
}

onMounted(async () => {
  try {
    const res = await api.get(`/albums/${route.params.id}`)
    album.value = res.data
    if (authStore.isAdmin) {
      const artistRes = await api.get('/artists')
      allArtists.value = artistRes.data
    }
  } catch (err) {
    error.value = err.message || 'Album non trovato'
  } finally {
    loading.value = false
  }
})

const showAddCopyModal = ref(false)
const format = ref('Vinile')
const condition = ref('Nuovo')
const personal_notes = ref('')
const actionLoading = ref(false)
const successMessage = ref('')

async function addToWishlist() {
  actionLoading.value = true
  error.value = ''
  successMessage.value = ''
  try {
    await api.post('/wishlist', {
      id_album: album.value.id_album
    })
    successMessage.value = 'Album aggiunto alla Wishlist!'
  } catch (err) {
    error.value = err.message || "Errore durante l'aggiunta alla wishlist"
  } finally {
    actionLoading.value = false
  }
}

async function addToCollection() {
  actionLoading.value = true
  error.value = ''
  successMessage.value = ''
  try {
    await api.post('/copies', {
      id_album: album.value.id_album,
      format: format.value,
      condition: condition.value,
      personal_notes: personal_notes.value.trim() || null
    })
    successMessage.value = 'Disco aggiunto al Vault!'
    showAddCopyModal.value = false
  } catch (err) {
    error.value = err.message || "Errore durante l'aggiunta al Vault"
  } finally {
    actionLoading.value = false
  }
}

function startEdit() {
  form.value = {
    title: album.value.title,
    release_year: album.value.release_year || '',
    genre: album.value.genre || '',
    artist_ids: album.value.artists?.map(a => a.id_artist) || []
  }
  coverFile.value = null
  coverPreview.value = null
  artistSearchInput.value = ''
  isArtistDropdownOpen.value = false
  editing.value = true
}

function toggleArtist(id) {
  const idx = form.value.artist_ids.indexOf(id)
  if (idx >= 0) form.value.artist_ids.splice(idx, 1)
  else form.value.artist_ids.push(id)
}

async function handleSave() {
  try {
    const payload = {
      title: form.value.title,
      release_year: form.value.release_year ? parseInt(form.value.release_year) : null,
      genre: form.value.genre || null,
      artist_ids: form.value.artist_ids
    }
    const res = await api.put(`/albums/${album.value.id_album}`, payload)
    const updatedAlbum = res.data

    // Upload copertina se selezionata
    if (coverFile.value) {
      const fd = new FormData()
      fd.append('file', coverFile.value)
      try {
        const coverRes = await api.post(`/albums/${album.value.id_album}/cover`, fd)
        updatedAlbum.cover_path = coverRes.cover_path
      } catch (_) { /* cover non bloccante */ }
    }

    album.value = updatedAlbum
    editing.value = false
  } catch (err) {
    error.value = err.message || 'Errore durante l\'aggiornamento'
  }
}

async function handleDelete() {
  if (!confirm(`Eliminare l'album "${album.value.title}" dal catalogo?`)) return
  try {
    await api.delete(`/albums/${album.value.id_album}`)
    router.push('/albums')
  } catch (err) {
    error.value = err.message || 'Errore durante l\'eliminazione'
  }
}
</script>

<template>
  <div class="space-y-6 animate-fade-in max-w-4xl mx-auto">
    <!-- Back link -->
    <BackButton to="/albums" label="Torna al catalogo" />

    <LoadingSpinner v-if="loading" />
    
    <div v-else-if="error && !album" class="py-20 text-center text-rose-400 font-semibold">{{ error }}</div>

    <div v-else-if="album" class="glass-panel rounded-apple-2xl overflow-hidden shadow-2xl border border-white/10 relative">
      <!-- Errore inline -->
      <ErrorMessage v-if="error" :message="error" />

      <!-- Vista lettura -->
      <div v-if="!editing" class="flex flex-col md:flex-row">
        <!-- Cover Art -->
        <div class="w-full md:w-1/2 aspect-square bg-white/5 flex items-center justify-center border-b md:border-b-0 md:border-r border-white/5 relative overflow-hidden">
          <img v-if="album.cover_path"
            :src="`/api/albums/${album.id_album}/cover`"
            :alt="album.title"
            class="w-full h-full object-cover"
          />
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="opacity-15"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
        </div>

        <!-- Info / Actions -->
        <div class="flex-grow p-8 md:p-12 flex flex-col justify-between">
          <div class="space-y-6">
            <div>
              <div class="flex items-center gap-3 flex-wrap mb-2">
                <h1 class="text-3xl md:text-4xl font-extrabold tracking-tight">{{ album.title }}</h1>
                <a 
                  v-if="album.discogs_id" 
                  :href="`https://www.discogs.com/release/${album.discogs_id}`" 
                  target="_blank" 
                  class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white/5 hover:bg-white/10 border border-white/10 text-white/50 hover:text-white rounded-full text-[10px] font-bold tracking-wider uppercase transition-all"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>
                  Discogs
                </a>
                <a 
                  :href="`https://open.spotify.com/search/${encodeURIComponent(album.title + ' ' + (album.artists?.[0]?.name || ''))}`" 
                  target="_blank" 
                  class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 text-emerald-400 hover:text-emerald-300 rounded-full text-[10px] font-bold tracking-wider uppercase transition-all shadow-sm"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 12a15.3 15.3 0 0 1 7.2-2.2"/><path d="M7.3 15.2a15.7 15.7 0 0 1 9.4-3.3"/><path d="M9 9a14.8 14.8 0 0 1 5.3-1.1"/></svg>
                  Spotify
                </a>
              </div>
              <div v-if="album.artists?.length" class="flex flex-wrap gap-2 mb-6">
                <RouterLink
                  v-for="artist in album.artists" :key="artist.id_artist"
                  :to="`/artists/${artist.id_artist}`"
                  class="px-3.5 py-1 bg-brand-secondary/15 border border-brand-secondary/20 text-brand-secondary
                         rounded-full text-xs font-bold hover:bg-brand-secondary/25 transition-all"
                >
                  {{ artist.name }}
                </RouterLink>
              </div>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-3 gap-6 pt-6 border-t border-white/5">
              <DetailField label="Anno di uscita" :value="album.release_year" />
              <DetailField label="Genere" :value="album.genre" />
              <DetailField label="Paese di stampa" :value="album.country" />
              <DetailField label="Etichetta" :value="album.label" />
              <DetailField label="N. Catalogo" :value="album.catno" />
              <DetailField label="Codice a Barre" :value="album.barcode" />
              <DetailField v-if="authStore.isAdmin" label="Inserito da" class="col-span-2 sm:col-span-1">
                <span v-if="album.id_user === null" class="font-semibold text-white/40">
                  Utente eliminato
                </span>
                <RouterLink v-else :to="`/users/${album.id_user}`" class="font-semibold text-brand-secondary hover:underline">
                  @{{ album.creator_username || 'Sistema' }}
                </RouterLink>
              </DetailField>
            </div>

            <!-- Tracklist Section -->
            <div v-if="album.tracklist && album.tracklist.length > 0" class="pt-6 border-t border-white/5 space-y-3">
              <h3 class="text-xs font-bold uppercase tracking-widest text-white/30 ml-1">Tracce</h3>
              <div class="space-y-1 max-h-60 overflow-y-auto pr-2 divide-y divide-white/[0.03] border border-white/5 rounded-2xl bg-white/[0.01] p-4">
                <div 
                  v-for="track in album.tracklist" 
                  :key="track.position" 
                  class="flex items-center justify-between text-sm py-2.5 first:pt-0 last:pb-0 font-medium"
                >
                  <div class="flex items-center gap-3 min-w-0">
                    <span class="text-white/30 text-xs w-6 font-bold uppercase tabular-nums">{{ track.position }}</span>
                    <span class="text-white/80 truncate">{{ track.title }}</span>
                  </div>
                  <span class="text-white/40 text-xs tabular-nums font-semibold">{{ track.duration }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="mt-12 pt-6 border-t border-white/5 space-y-4">
            <div v-if="successMessage" class="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-semibold rounded-2xl text-center">
              {{ successMessage }}
            </div>

            <!-- Azione Collector: aggiungi alla collezione -->
            <div v-if="authStore.isCollector" class="flex flex-col sm:flex-row gap-3">
              <button 
                @click="showAddCopyModal = true"
                :disabled="actionLoading"
                class="apple-button apple-button-primary flex-1 flex items-center justify-center gap-2"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
                Aggiungi al Vault
              </button>
              
              <button 
                @click="addToWishlist"
                :disabled="actionLoading"
                class="apple-button apple-button-secondary flex-1 flex items-center justify-center gap-2"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
                Aggiungi alla Wishlist
              </button>
            </div>

            <!-- Azioni Admin -->
            <div v-if="authStore.isAdmin" class="flex flex-col sm:flex-row gap-3">
              <button @click="startEdit"
                class="apple-button apple-button-primary w-full sm:flex-1">
                Modifica album
              </button>
              <button @click="handleDelete"
                class="apple-button apple-button-secondary w-full sm:flex-1 !text-brand-accent hover:!bg-brand-accent/10 hover:!border-brand-accent/25">
                Rimuovi dal catalogo
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Vista modifica (Admin) -->
      <form v-else @submit.prevent="handleSave" class="p-8 space-y-6">
        <h3 class="text-2xl font-bold mb-6 text-center">Modifica Scheda Album</h3>
        <div class="space-y-2">
          <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Titolo dell'album</label>
          <input v-model="form.title" type="text" required class="apple-input" />
        </div>

        <!-- Copertina album -->
        <div class="space-y-2">
          <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Copertina</label>
          <label class="flex items-center gap-4 cursor-pointer group">
            <div class="w-20 h-20 rounded-2xl bg-white/5 border border-white/10 overflow-hidden flex items-center justify-center shrink-0 group-hover:border-white/20 transition-colors">
              <img v-if="coverPreview || album.cover_path" :src="coverPreview || `/api/albums/${album.id_album}/cover`" class="w-full h-full object-cover" />
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" class="opacity-20"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
            </div>
            <div class="space-y-1">
              <p class="text-sm font-semibold text-white/60 group-hover:text-white transition-colors">
                {{ coverFile ? coverFile.name : 'Modifica immagine di copertina' }}
              </p>
              <p class="text-[10px] text-white/30">Clicca per scegliere una nuova immagine (JPG, PNG o WebP)</p>
            </div>
            <input type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="handleCoverPick" />
          </label>
        </div>
        
        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-2">
            <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Anno</label>
            <input v-model="form.release_year" type="number" min="1900" max="2026" class="apple-input" />
          </div>
          <div class="space-y-2">
            <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Genere</label>
            <select v-model="form.genre" class="apple-input">
              <option value="">Nessun genere (seleziona per modificare)</option>
              <option v-for="g in GENRE_OPTIONS" :key="g" :value="g">{{ g }}</option>
            </select>
          </div>
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

        <div class="flex gap-3 pt-4 border-t border-white/5">
          <button type="submit" class="apple-button apple-button-primary">
            Salva modifiche
          </button>
          <button type="button" @click="editing = false" class="apple-button apple-button-secondary">
            Annulla
          </button>
        </div>
      </form>
    <!-- Modale Aggiungi al Vault -->
    <div v-if="showAddCopyModal" class="fixed inset-0 z-[150] flex items-center justify-center p-4">
      <div @click="showAddCopyModal = false" class="absolute inset-0 bg-black/60 backdrop-blur-md"></div>
      <div class="relative glass-panel w-full max-w-md rounded-apple-3xl shadow-2xl border border-white/10 overflow-hidden z-10 flex flex-col text-left">
        <div class="p-6 border-b border-white/5 flex items-center justify-between">
          <h3 class="text-xl font-bold">Aggiungi al Vault</h3>
          <button @click="showAddCopyModal = false" class="text-white/40 hover:text-white rounded-full w-8 h-8 flex items-center justify-center bg-white/5">✕</button>
        </div>

        <form @submit.prevent="addToCollection" class="p-6 space-y-5">
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
            <textarea v-model="personal_notes" rows="2" placeholder="Note d'acquisto, edizione..." class="apple-input resize-none"></textarea>
          </div>

          <div class="flex gap-3 pt-4 border-t border-white/5">
            <button type="submit" class="apple-button apple-button-primary flex-grow" :disabled="actionLoading">Aggiungi</button>
            <button type="button" @click="showAddCopyModal = false" class="apple-button apple-button-secondary">Annulla</button>
          </div>
        </form>
      </div>
    </div>
    </div>
  </div>
</template>
