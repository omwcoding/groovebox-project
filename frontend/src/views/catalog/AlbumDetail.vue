<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/stores/api'
import BackButton from '@/components/BackButton.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import DetailField from '@/components/DetailField.vue'
import { GENRE_OPTIONS } from '@/constants/music'

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
          <img v-if="album.coverPath"
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
              <h1 class="text-3xl md:text-4xl font-extrabold tracking-tight mb-2">{{ album.title }}</h1>
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
              <DetailField label="Anno di uscita" :value="album.releaseYear" />
              <DetailField label="Genere" :value="album.genre" />
              <DetailField v-if="authStore.isAdmin" label="Inserito da" class="col-span-2 sm:col-span-1">
                <span v-if="album.id_user === null" class="font-semibold text-white/40">
                  Utente eliminato
                </span>
                <RouterLink v-else :to="`/users/${album.id_user}`" class="font-semibold text-brand-secondary hover:underline">
                  @{{ album.creator_username || 'Sistema' }}
                </RouterLink>
              </DetailField>
            </div>
          </div>

          <div class="mt-12 pt-6 border-t border-white/5">
            <!-- Azione Collector: aggiungi alla collezione -->
            <div v-if="authStore.isCollector">
              <RouterLink :to="{ path: '/collection', query: { addAlbum: album.id_album } }"
                class="apple-button apple-button-primary w-full flex items-center justify-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
                Aggiungi alla mia collezione
              </RouterLink>
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
        
        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-2">
            <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Anno</label>
            <input v-model="form.releaseYear" type="number" min="1900" max="2099" class="apple-input" />
          </div>
          <div class="space-y-2">
            <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Genere</label>
            <select v-model="form.genre" class="apple-input">
              <option value="">Nessun genere (seleziona per modificare)</option>
              <option v-for="g in GENRE_OPTIONS" :key="g" :value="g">{{ g }}</option>
            </select>
          </div>
        </div>

        <div v-if="allArtists.length" class="space-y-3">
          <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Associa Artisti</label>
          <div class="flex flex-wrap gap-2 max-h-48 overflow-y-auto p-1.5 border border-white/5 rounded-2xl bg-white/5">
            <button v-for="artist in allArtists" :key="artist.id_artist" type="button"
              @click="toggleArtist(artist.id_artist)"
              class="px-3 py-1.5 rounded-full text-xs font-semibold transition-all border"
              :class="form.artist_ids.includes(artist.id_artist)
                ? 'bg-brand-secondary border-brand-secondary text-white shadow-md'
                : 'bg-white/5 border-white/5 text-white/60 hover:border-white/20 hover:text-white'">
              {{ artist.name }}
            </button>
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
    </div>
  </div>
</template>
