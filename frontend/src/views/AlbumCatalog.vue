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
  formError.value = ''
  showForm.value = false
}

async function handleCreate() {
  formError.value = ''
  if (!form.value.title.trim()) {
    formError.value = 'Il titolo e\' obbligatorio'
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
    albums.value.unshift(res.data)
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
</script>

<template>
  <div class="p-6 md:p-8 max-w-5xl mx-auto">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-bold">Catalogo Album</h1>
        <p class="text-slate-400 text-sm mt-1">{{ albums.length }} album nel catalogo</p>
      </div>
      <button
        v-if="authStore.isCollector"
        @click="showForm = !showForm"
        class="px-5 py-2.5 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium
               rounded-xl transition-all duration-200 hover:shadow-lg hover:shadow-violet-600/25"
      >
        {{ showForm ? 'Annulla' : '+ Nuovo Album' }}
      </button>
    </div>

    <!-- Form Nuovo Album -->
    <div v-if="showForm" class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 mb-6">
      <h3 class="text-lg font-semibold mb-4">Inserisci un nuovo album</h3>
      <div v-if="formError" class="mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm rounded-lg px-4 py-3">
        {{ formError }}
      </div>
      <form @submit.prevent="handleCreate" class="space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="sm:col-span-2">
            <label for="album-title" class="block text-sm font-medium text-slate-300 mb-1.5">Titolo *</label>
            <input id="album-title" v-model="form.title" type="text" required
              class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                     focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none" />
          </div>
          <div>
            <label for="album-year" class="block text-sm font-medium text-slate-300 mb-1.5">Anno</label>
            <input id="album-year" v-model="form.releaseYear" type="number" min="1900" max="2099"
              class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                     focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none" />
          </div>
        </div>
        <div>
          <label for="album-genre" class="block text-sm font-medium text-slate-300 mb-1.5">Genere</label>
          <input id="album-genre" v-model="form.genre" type="text"
            class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                   focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none" />
        </div>

        <!-- Selezione artisti -->
        <div v-if="artists.length > 0">
          <label class="block text-sm font-medium text-slate-300 mb-2">Artisti</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="artist in artists" :key="artist.id_artist"
              type="button"
              @click="toggleArtist(artist.id_artist)"
              class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border"
              :class="form.artist_ids.includes(artist.id_artist)
                ? 'bg-violet-600 border-violet-500 text-white'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-500'"
            >
              {{ artist.name }}
            </button>
          </div>
        </div>

        <button type="submit" :disabled="formLoading"
          class="px-6 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white
                 text-sm font-medium rounded-xl transition-colors">
          {{ formLoading ? 'Inserimento...' : 'Inserisci album' }}
        </button>
      </form>
    </div>

    <!-- Barra ricerca -->
    <div class="mb-6">
      <input
        v-model="search"
        type="text"
        placeholder="Cerca per titolo, genere o artista..."
        class="w-full px-4 py-2.5 bg-slate-900/80 border border-slate-800 rounded-xl text-slate-100
               placeholder-slate-500 focus:border-violet-500 focus:ring-1 focus:ring-violet-500
               transition-colors outline-none"
      />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-16 text-slate-400">
      Caricamento catalogo...
    </div>

    <!-- Lista album -->
    <div v-else-if="filteredAlbums.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <RouterLink
        v-for="album in filteredAlbums" :key="album.id_album"
        :to="`/albums/${album.id_album}`"
        class="group bg-slate-900/80 border border-slate-800 hover:border-violet-500/40 rounded-2xl
               p-5 transition-all duration-200 hover:shadow-lg hover:shadow-violet-600/5"
      >
        <!-- Cover placeholder -->
        <div class="w-full aspect-square bg-slate-800 rounded-xl mb-4 flex items-center justify-center
                    text-4xl group-hover:bg-slate-700/80 transition-colors">
          &#127925;
        </div>
        <h3 class="font-semibold text-lg mb-1 group-hover:text-violet-400 transition-colors truncate">
          {{ album.title }}
        </h3>
        <p class="text-sm text-slate-400 truncate">
          {{ album.artists?.map(a => a.name).join(', ') || 'Artista sconosciuto' }}
        </p>
        <div class="flex items-center gap-2 mt-2 text-xs text-slate-500">
          <span v-if="album.releaseYear">{{ album.releaseYear }}</span>
          <span v-if="album.releaseYear && album.genre">&middot;</span>
          <span v-if="album.genre">{{ album.genre }}</span>
        </div>
      </RouterLink>
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-16">
      <div class="text-5xl mb-4">&#127925;</div>
      <p class="text-slate-400">
        {{ search ? 'Nessun album trovato per la ricerca.' : 'Il catalogo e\' ancora vuoto.' }}
      </p>
    </div>
  </div>
</template>
