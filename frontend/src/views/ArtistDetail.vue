<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/stores/api'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const artist = ref(null)
const loading = ref(true)
const editing = ref(false)
const error = ref('')
const editName = ref('')

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
</script>

<template>
  <div class="space-y-6 animate-fade-in max-w-3xl mx-auto">
    <button 
      @click="router.back()" 
      class="inline-flex items-center gap-2 text-sm font-semibold opacity-50 hover:opacity-100 transition-opacity cursor-pointer"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
      Indietro
    </button>

    <div v-if="loading" class="py-20 flex flex-col items-center justify-center gap-4 opacity-40">
      <div class="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
      <p class="text-sm font-semibold tracking-widest uppercase">Caricamento</p>
    </div>
    
    <div v-else-if="error && !artist" class="py-20 text-center text-rose-400 font-semibold">{{ error }}</div>

    <div v-else-if="artist" class="glass-panel p-8 rounded-apple-2xl shadow-2xl border border-white/10 relative">
      <div v-if="error" class="mb-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold rounded-2xl px-4 py-3">
        {{ error }}
      </div>

      <!-- Header artista -->
      <div class="flex flex-col sm:flex-row items-center sm:items-start gap-6 pb-6 border-b border-white/5">
        <div class="w-20 h-20 bg-white/5 border border-white/5 rounded-full flex items-center justify-center text-4xl shrink-0">
          &#127908;
        </div>
        
        <div class="min-w-0 flex-grow text-center sm:text-left space-y-1">
          <div v-if="!editing" class="space-y-2">
            <h1 class="text-3xl md:text-4xl font-extrabold tracking-tight bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
              {{ artist.name }}
            </h1>
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

      <!-- Discografia -->
      <div class="pt-8 mt-8 border-t border-white/5">
        <h2 class="text-xl font-bold mb-6">Discografia</h2>
        
        <div v-if="artist.albums?.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <RouterLink
            v-for="album in artist.albums" :key="album.id_album"
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
