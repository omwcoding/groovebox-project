<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/stores/api'

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
  } catch (err) {
    console.error(err)
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

const showNewArtistInput = ref(false)
const newArtistName = ref('')
const inlineArtistLoading = ref(false)

async function handleInlineArtistCreate() {
  if (!newArtistName.value.trim()) return
  inlineArtistLoading.value = true
  try {
    const res = await api.post('/artists', { name: newArtistName.value.trim() })
    artists.value.unshift(res.data)
    form.value.artist_ids.push(res.data.id_artist)
    newArtistName.value = ''
    showNewArtistInput.value = false
  } catch (err) {
    formError.value = err.message || "Errore durante la creazione dell'artista"
  } finally {
    inlineArtistLoading.value = false
  }
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
        <h3 class="text-2xl font-bold mb-6 text-center">Pubblica un nuovo album</h3>
        <div v-if="formError" class="mb-6 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold rounded-2xl px-4 py-3">
          {{ formError }}
        </div>
        <form @submit.prevent="handleCreate" class="space-y-6">
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div class="sm:col-span-2 space-y-2">
              <label for="album-title" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Titolo dell'album *</label>
              <input id="album-title" v-model="form.title" type="text" required placeholder="Es. Abbey Road" class="apple-input" />
            </div>
            <div class="space-y-2">
              <label for="album-year" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Anno di uscita</label>
              <input id="album-year" v-model="form.releaseYear" type="number" min="1900" max="2099" placeholder="Es. 1969" class="apple-input" />
            </div>
          </div>
          <div class="space-y-2">
            <label for="album-genre" class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Genere</label>
            <input id="album-genre" v-model="form.genre" type="text" placeholder="Es. Rock, Pop..." class="apple-input" />
          </div>

          <!-- Selezione artisti -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Associa Artisti</label>
              <button 
                type="button"
                @click="showNewArtistInput = !showNewArtistInput"
                class="text-xs font-bold text-brand-secondary hover:underline"
              >
                {{ showNewArtistInput ? 'Usa Esistenti' : '+ Nuovo Artista' }}
              </button>
            </div>

            <!-- Input rapido artista inline -->
            <div v-if="showNewArtistInput" class="flex gap-2 animate-fade-in">
              <input 
                v-model="newArtistName" 
                type="text" 
                placeholder="Nome nuovo artista" 
                class="apple-input !py-2.5 !rounded-full"
                @keyup.enter.prevent="handleInlineArtistCreate"
              />
              <button 
                type="button" 
                @click="handleInlineArtistCreate" 
                :disabled="inlineArtistLoading"
                class="apple-button apple-button-primary !py-2.5 !px-4 text-xs shrink-0"
              >
                Aggiungi
              </button>
            </div>

            <div v-if="artists.length > 0" class="flex flex-wrap gap-2 max-h-48 overflow-y-auto p-1 border border-white/5 rounded-2xl bg-white/5">
              <button
                v-for="artist in artists" :key="artist.id_artist"
                type="button"
                @click="toggleArtist(artist.id_artist)"
                class="px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 border"
                :class="form.artist_ids.includes(artist.id_artist)
                  ? 'bg-brand-secondary border-brand-secondary text-white shadow-md shadow-brand-secondary/20'
                  : 'bg-white/5 border-white/5 text-white/60 hover:border-white/20 hover:text-white'"
              >
                {{ artist.name }}
              </button>
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
    <div v-if="loading" class="py-20 flex flex-col items-center justify-center gap-4 opacity-40">
      <div class="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
      <p class="text-sm font-semibold tracking-widest uppercase">Caricamento</p>
    </div>

    <!-- Lista album (Apple Grid) -->
    <div v-else-if="filteredAlbums.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-x-6 gap-y-10">
      <RouterLink
        v-for="(album, index) in filteredAlbums" :key="album.id_album"
        :to="`/albums/${album.id_album}`"
        class="group flex flex-col gap-4 animate-slide-up"
        :style="{ animationDelay: `${index * 30}ms` }"
      >
        <!-- Album Art / Placeholder -->
        <div class="aspect-square glass-card overflow-hidden relative group-hover:scale-[1.02] group-hover:shadow-2xl group-hover:shadow-brand-secondary/10 transition-all duration-500 flex items-center justify-center">
          <img v-if="album.coverPath"
            :src="`/api/albums/${album.id_album}/cover`"
            :alt="album.title"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center bg-white/5">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="opacity-15 group-hover:opacity-30 group-hover:rotate-12 transition-all duration-500"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
          </div>
          
          <!-- Hover indicator -->
          <div class="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <div class="w-12 h-12 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center border border-white/30 scale-90 group-hover:scale-100 transition-transform duration-500">
               <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="white" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
            </div>
          </div>
        </div>

        <!-- Info -->
        <div class="space-y-1 px-1">
          <h3 class="font-bold text-base leading-tight line-clamp-1 group-hover:text-brand-secondary transition-colors">
            {{ album.title }}
          </h3>
          <p class="text-white/40 text-sm font-semibold tracking-tight truncate">
            {{ album.artists?.map(a => a.name).join(', ') || 'Artista sconosciuto' }}
          </p>
          <div class="flex items-center gap-2 mt-1 text-[10px] font-bold text-white/20 uppercase tracking-wider">
            <span v-if="album.releaseYear">{{ album.releaseYear }}</span>
            <span v-if="album.releaseYear && album.genre">&middot;</span>
            <span v-if="album.genre" class="truncate">{{ album.genre }}</span>
          </div>
        </div>
      </RouterLink>
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
