<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/stores/api'

const authStore = useAuthStore()

const artists = ref([])
const loading = ref(true)
const search = ref('')
const showForm = ref(false)
const formError = ref('')
const formLoading = ref(false)
const formName = ref('')

const filteredArtists = computed(() => {
  if (!search.value.trim()) return artists.value
  const q = search.value.toLowerCase()
  return artists.value.filter(a => a.name.toLowerCase().includes(q))
})

onMounted(async () => {
  try {
    const res = await api.get('/artists')
    artists.value = res.data
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
})

async function handleCreate() {
  formError.value = ''
  if (!formName.value.trim()) {
    formError.value = 'Il nome e\' obbligatorio'
    return
  }
  formLoading.value = true
  try {
    const res = await api.post('/artists', { name: formName.value.trim() })
    artists.value.unshift(res.data)
    formName.value = ''
    showForm.value = false
  } catch (err) {
    formError.value = err.message || 'Errore durante la creazione'
  } finally {
    formLoading.value = false
  }
}
</script>

<template>
  <div class="p-6 md:p-8 max-w-5xl mx-auto">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-bold">Catalogo Artisti</h1>
        <p class="text-slate-400 text-sm mt-1">{{ artists.length }} artisti nel catalogo</p>
      </div>
      <button
        @click="showForm = !showForm"
        class="px-5 py-2.5 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium
               rounded-xl transition-all duration-200 hover:shadow-lg hover:shadow-violet-600/25"
      >
        {{ showForm ? 'Annulla' : '+ Nuovo Artista' }}
      </button>
    </div>

    <!-- Form rapido -->
    <div v-if="showForm" class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 mb-6">
      <div v-if="formError" class="mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm rounded-lg px-4 py-3">
        {{ formError }}
      </div>
      <form @submit.prevent="handleCreate" class="flex gap-3">
        <input v-model="formName" type="text" required placeholder="Nome artista"
          class="flex-1 px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                 placeholder-slate-500 focus:border-violet-500 focus:ring-1 focus:ring-violet-500
                 transition-colors outline-none" />
        <button type="submit" :disabled="formLoading"
          class="px-6 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white
                 text-sm font-medium rounded-xl transition-colors whitespace-nowrap">
          {{ formLoading ? 'Creazione...' : 'Aggiungi' }}
        </button>
      </form>
    </div>

    <!-- Barra ricerca -->
    <div class="mb-6">
      <input v-model="search" type="text" placeholder="Cerca un artista..."
        class="w-full px-4 py-2.5 bg-slate-900/80 border border-slate-800 rounded-xl text-slate-100
               placeholder-slate-500 focus:border-violet-500 focus:ring-1 focus:ring-violet-500
               transition-colors outline-none" />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-16 text-slate-400">Caricamento artisti...</div>

    <!-- Lista artisti -->
    <div v-else-if="filteredArtists.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <RouterLink
        v-for="artist in filteredArtists" :key="artist.id_artist"
        :to="`/artists/${artist.id_artist}`"
        class="group bg-slate-900/80 border border-slate-800 hover:border-violet-500/40 rounded-2xl
               p-5 transition-all duration-200 hover:shadow-lg hover:shadow-violet-600/5 flex items-center gap-4"
      >
        <div class="w-14 h-14 bg-slate-800 rounded-full flex items-center justify-center text-2xl
                    group-hover:bg-slate-700/80 transition-colors shrink-0">
          &#127908;
        </div>
        <div class="min-w-0">
          <h3 class="font-semibold text-lg group-hover:text-violet-400 transition-colors truncate">
            {{ artist.name }}
          </h3>
        </div>
      </RouterLink>
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-16">
      <div class="text-5xl mb-4">&#127908;</div>
      <p class="text-slate-400">
        {{ search ? 'Nessun artista trovato.' : 'Nessun artista nel catalogo.' }}
      </p>
    </div>
  </div>
</template>
