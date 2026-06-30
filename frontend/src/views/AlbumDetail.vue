<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/stores/api'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const album = ref(null)
const loading = ref(true)
const editing = ref(false)
const error = ref('')
const allArtists = ref([])

const form = ref({ title: '', releaseYear: '', genre: '', artist_ids: [] })

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

function startEdit() {
  form.value = {
    title: album.value.title,
    releaseYear: album.value.releaseYear || '',
    genre: album.value.genre || '',
    artist_ids: album.value.artists?.map(a => a.id_artist) || []
  }
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
      releaseYear: form.value.releaseYear ? parseInt(form.value.releaseYear) : null,
      genre: form.value.genre || null,
      artist_ids: form.value.artist_ids
    }
    const res = await api.put(`/albums/${album.value.id_album}`, payload)
    album.value = res.data
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
  <div class="p-6 md:p-8 max-w-3xl mx-auto">
    <!-- Back link -->
    <RouterLink to="/albums" class="inline-flex items-center text-sm text-slate-400 hover:text-violet-400 mb-6 transition-colors">
      &larr; Torna al catalogo
    </RouterLink>

    <div v-if="loading" class="text-center py-16 text-slate-400">Caricamento...</div>
    <div v-else-if="error && !album" class="text-center py-16 text-rose-400">{{ error }}</div>

    <div v-else-if="album" class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8">
      <!-- Errore inline -->
      <div v-if="error" class="mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm rounded-lg px-4 py-3">
        {{ error }}
      </div>

      <!-- Vista lettura -->
      <div v-if="!editing">
        <div class="flex flex-col sm:flex-row gap-6">
          <!-- Cover -->
          <div class="w-full sm:w-48 aspect-square bg-slate-800 rounded-xl flex items-center justify-center text-5xl shrink-0">
            &#127925;
          </div>

          <div class="flex-1 min-w-0">
            <h1 class="text-2xl md:text-3xl font-bold mb-2">{{ album.title }}</h1>

            <div class="space-y-2 text-sm">
              <div v-if="album.artists?.length" class="flex flex-wrap gap-2">
                <RouterLink
                  v-for="artist in album.artists" :key="artist.id_artist"
                  :to="`/artists/${artist.id_artist}`"
                  class="px-3 py-1 bg-violet-500/10 border border-violet-500/30 text-violet-400
                         rounded-lg hover:bg-violet-500/20 transition-colors"
                >
                  {{ artist.name }}
                </RouterLink>
              </div>
              <p v-if="album.releaseYear" class="text-slate-400">
                <span class="text-slate-500">Anno:</span> {{ album.releaseYear }}
              </p>
              <p v-if="album.genre" class="text-slate-400">
                <span class="text-slate-500">Genere:</span> {{ album.genre }}
              </p>
            </div>
          </div>
        </div>

        <!-- Azioni Admin -->
        <div v-if="authStore.isAdmin" class="flex gap-3 pt-6 mt-6 border-t border-slate-800">
          <button @click="startEdit"
            class="px-5 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-xl transition-colors">
            Modifica
          </button>
          <button @click="handleDelete"
            class="px-5 py-2 border border-rose-500/30 text-rose-400 hover:bg-rose-500/10 text-sm font-medium rounded-xl transition-colors">
            Elimina
          </button>
        </div>

        <!-- Azione Collector: aggiungi alla collezione -->
        <div v-if="authStore.isCollector" class="pt-6 mt-6 border-t border-slate-800">
          <RouterLink :to="{ path: '/collection', query: { addAlbum: album.id_album } }"
            class="inline-flex px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-xl transition-colors">
            + Aggiungi alla mia collezione
          </RouterLink>
        </div>
      </div>

      <!-- Vista modifica (Admin) -->
      <form v-else @submit.prevent="handleSave" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-1.5">Titolo</label>
          <input v-model="form.title" type="text" required
            class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                   focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1.5">Anno</label>
            <input v-model="form.releaseYear" type="number" min="1900" max="2099"
              class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                     focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1.5">Genere</label>
            <input v-model="form.genre" type="text"
              class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                     focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none" />
          </div>
        </div>
        <div v-if="allArtists.length">
          <label class="block text-sm font-medium text-slate-300 mb-2">Artisti</label>
          <div class="flex flex-wrap gap-2">
            <button v-for="artist in allArtists" :key="artist.id_artist" type="button"
              @click="toggleArtist(artist.id_artist)"
              class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border"
              :class="form.artist_ids.includes(artist.id_artist)
                ? 'bg-violet-600 border-violet-500 text-white'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-500'">
              {{ artist.name }}
            </button>
          </div>
        </div>
        <div class="flex gap-3 pt-2">
          <button type="submit" class="px-5 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-xl transition-colors">
            Salva
          </button>
          <button type="button" @click="editing = false" class="px-5 py-2 border border-slate-700 text-slate-300 text-sm font-medium rounded-xl transition-colors">
            Annulla
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
