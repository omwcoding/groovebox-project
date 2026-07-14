<!--
GrooveBox - Pagina Dettaglio Artista
====================================
Mostra le informazioni di un artista e l'elenco (discografia) degli album ad esso correlati.
Fornisce agli amministratori i controlli per la rinomina o cancellazione dell'artista.
-->

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/stores/api'
import BackButton from '@/components/BackButton.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const artist = ref(null)
const loading = ref(true)
const editing = ref(false)
const error = ref('')
const editName = ref('')

function formatBiography(text) {
  if (!text) return ''
  return text
    .replace(/\[a=([^\]]+)\]/g, '$1')
    .replace(/\[[lra]=([^\]]+)\]/g, '$1')
    .replace(/\[\/?(b|i|u)\]/g, '')
}

onMounted(async () => {
  try {
    const res = await api.get(`/artists/${route.params.id}`)
    artist.value = res.data
  } catch (err) {
    error.value = err.message || 'Artista non trovato'
  } finally {
    loading.value = false
  }
})

function startEdit() {
  editName.value = artist.value.name
  editing.value = true
}

async function handleSave() {
  try {
    const res = await api.put(`/artists/${artist.value.id_artist}`, { name: editName.value })
    artist.value.name = res.data.name
    editing.value = false
  } catch (err) {
    error.value = err.message || 'Errore durante l\'aggiornamento'
  }
}

async function handleDelete() {
  if (!confirm(`Eliminare l'artista "${artist.value.name}"?`)) return
  try {
    await api.delete(`/artists/${artist.value.id_artist}`)
    router.push('/artists')
  } catch (err) {
    error.value = err.message || 'Errore durante l\'eliminazione'
  }
}
const searchQuery = ref('')

const filteredAlbums = computed(() => {
  if (!artist.value || !artist.value.albums) return []
  return artist.value.albums.filter(album => 
    album.title.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})
</script>

<template>
  <div class="space-y-6 animate-fade-in max-w-3xl mx-auto">
    <BackButton />

    <LoadingSpinner v-if="loading" />
    
    <div v-else-if="error && !artist" class="py-20 text-center text-rose-400 font-semibold">{{ error }}</div>

    <div v-else-if="artist" class="glass-panel p-8 rounded-apple-2xl shadow-2xl border border-white/10 relative">
      <ErrorMessage v-if="error" :message="error" />

      <!-- Header artista -->
      <div class="flex flex-col sm:flex-row items-center sm:items-start gap-6 pb-6 border-b border-white/5">
        <div class="w-20 h-20 bg-white/5 border border-white/5 rounded-full flex items-center justify-center overflow-hidden shrink-0">
          <img v-if="artist.image_path" :src="`/api/artists/${artist.id_artist}/image`" class="w-full h-full object-cover" />
          <span v-else class="text-4xl">&#127908;</span>
        </div>
        
        <div class="min-w-0 flex-grow text-center sm:text-left space-y-1">
          <div v-if="!editing" class="space-y-2">
            <div class="flex items-center gap-3 justify-center sm:justify-start flex-wrap">
              <h1 class="text-3xl md:text-4xl font-extrabold tracking-tight bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
                {{ artist.name }}
              </h1>
              <a 
                v-if="artist.discogs_id" 
                :href="`https://www.discogs.com/artist/${artist.discogs_id}`" 
                target="_blank" 
                class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white/5 hover:bg-white/10 border border-white/10 text-white/50 hover:text-white rounded-full text-[10px] font-bold tracking-wider uppercase transition-all"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>
                Discogs
              </a>
            </div>
            <p class="text-white/40 text-sm font-semibold tracking-tight">
              {{ artist.albums?.length || 0 }} album associati nel catalogo
            </p>
          </div>
          
          <form v-else @submit.prevent="handleSave" class="flex flex-col sm:flex-row gap-3 pt-2">
            <input v-model="editName" type="text" required class="apple-input" />
            <div class="flex gap-2">
              <button type="submit" class="apple-button apple-button-primary py-2.5">
                Salva
              </button>
              <button type="button" @click="editing = false" class="apple-button apple-button-secondary py-2.5">
                Annulla
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Azioni Admin -->
      <div v-if="authStore.isAdmin && !editing" class="flex gap-3 pt-6">
        <button @click="startEdit"
          class="apple-button apple-button-primary py-2 text-sm">
          Modifica Artista
        </button>
        <button @click="handleDelete"
          class="apple-button apple-button-secondary py-2 text-sm !text-brand-accent hover:!bg-brand-accent/10 hover:!border-brand-accent/25">
          Elimina
        </button>
      </div>

      <!-- Biografia (da Discogs) -->
      <div v-if="artist.biography" class="pt-6 border-t border-white/5 pb-2">
        <h3 class="text-xs font-bold uppercase tracking-widest text-white/30 mb-3">Biografia</h3>
        <p class="text-sm text-white/70 leading-relaxed whitespace-pre-wrap font-medium">
          {{ formatBiography(artist.biography) }}
        </p>
      </div>

      <!-- Discografia -->
      <div class="pt-8 mt-8 border-t border-white/5 space-y-6">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div class="space-y-1">
            <h2 class="text-xl font-bold">Discografia</h2>
            <p class="text-xs text-white/30 font-semibold uppercase tracking-wider">
              {{ filteredAlbums.length }} di {{ artist.albums?.length || 0 }} album trovati
            </p>
          </div>

          <!-- Ricerca Discografia -->
          <div class="relative max-w-xs w-full" v-if="artist.albums?.length > 0">
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Cerca album..." 
              class="apple-input !py-2 !pl-9 !text-xs" 
            />
            <span class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            </span>
          </div>
        </div>
        
        <div v-if="filteredAlbums.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <RouterLink
            v-for="album in filteredAlbums" :key="album.id_album"
            :to="`/albums/${album.id_album}`"
            class="group p-4 bg-white/5 border border-white/5 hover:border-brand-secondary/30 rounded-2xl transition-all flex items-center gap-4 hover:shadow-lg hover:shadow-brand-secondary/5"
          >
            <div class="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center text-xl shrink-0 group-hover:scale-105 transition-transform duration-300">
              &#127925;
            </div>
            <div class="min-w-0 flex-grow">
              <p class="font-bold group-hover:text-brand-secondary transition-colors truncate">{{ album.title }}</p>
              <div class="flex gap-2 text-xs text-white/30 font-semibold uppercase tracking-wider mt-0.5">
                <span v-if="album.releaseYear">{{ album.releaseYear }}</span>
                <span v-if="album.releaseYear && album.genre">&middot;</span>
                <span v-if="album.genre" class="truncate">{{ album.genre }}</span>
              </div>
            </div>
          </RouterLink>
        </div>
        
        <p v-else class="text-white/30 text-sm font-semibold italic">Nessun album associato a questo artista.</p>
      </div>
    </div>
  </div>
</template>
