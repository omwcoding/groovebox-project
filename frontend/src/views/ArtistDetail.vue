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
  <div class="p-6 md:p-8 max-w-3xl mx-auto">
    <RouterLink to="/artists" class="inline-flex items-center text-sm text-slate-400 hover:text-violet-400 mb-6 transition-colors">
      &larr; Torna al catalogo artisti
    </RouterLink>

    <div v-if="loading" class="text-center py-16 text-slate-400">Caricamento...</div>
    <div v-else-if="error && !artist" class="text-center py-16 text-rose-400">{{ error }}</div>

    <div v-else-if="artist" class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8">
      <div v-if="error" class="mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm rounded-lg px-4 py-3">
        {{ error }}
      </div>

      <!-- Header artista -->
      <div class="flex items-center gap-5 mb-6">
        <div class="w-20 h-20 bg-slate-800 rounded-full flex items-center justify-center text-4xl shrink-0">
          &#127908;
        </div>
        <div class="min-w-0 flex-1">
          <div v-if="!editing">
            <h1 class="text-2xl md:text-3xl font-bold">{{ artist.name }}</h1>
            <p class="text-slate-400 text-sm mt-1">
              {{ artist.albums?.length || 0 }} album nel catalogo
            </p>
          </div>
          <form v-else @submit.prevent="handleSave" class="flex gap-3">
            <input v-model="editName" type="text" required
              class="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                     focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none" />
            <button type="submit" class="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-xl transition-colors">
              Salva
            </button>
            <button type="button" @click="editing = false" class="px-4 py-2 border border-slate-700 text-slate-300 text-sm rounded-xl transition-colors">
              Annulla
            </button>
          </form>
        </div>
      </div>

      <!-- Azioni Admin -->
      <div v-if="authStore.isAdmin && !editing" class="flex gap-3 mb-6">
        <button @click="startEdit"
          class="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-xl transition-colors">
          Modifica
        </button>
        <button @click="handleDelete"
          class="px-4 py-2 border border-rose-500/30 text-rose-400 hover:bg-rose-500/10 text-sm font-medium rounded-xl transition-colors">
          Elimina
        </button>
      </div>

      <!-- Discografia -->
      <div class="border-t border-slate-800 pt-6">
        <h2 class="text-lg font-semibold mb-4">Discografia</h2>
        <div v-if="artist.albums?.length > 0" class="space-y-3">
          <RouterLink
            v-for="album in artist.albums" :key="album.id_album"
            :to="`/albums/${album.id_album}`"
            class="flex items-center gap-4 p-4 bg-slate-800/50 border border-slate-700/50
                   hover:border-violet-500/40 rounded-xl transition-colors group"
          >
            <div class="w-12 h-12 bg-slate-700 rounded-lg flex items-center justify-center text-xl
                        group-hover:bg-slate-600/80 transition-colors shrink-0">
              &#127925;
            </div>
            <div class="min-w-0 flex-1">
              <p class="font-medium group-hover:text-violet-400 transition-colors truncate">{{ album.title }}</p>
              <div class="flex gap-2 text-xs text-slate-500">
                <span v-if="album.releaseYear">{{ album.releaseYear }}</span>
                <span v-if="album.releaseYear && album.genre">&middot;</span>
                <span v-if="album.genre">{{ album.genre }}</span>
              </div>
            </div>
          </RouterLink>
        </div>
        <p v-else class="text-slate-500 text-sm">Nessun album associato a questo artista.</p>
      </div>
    </div>
  </div>
</template>
