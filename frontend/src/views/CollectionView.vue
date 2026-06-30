<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { api } from '@/stores/api'

const route = useRoute()

const copies = ref([])
const albums = ref([])
const loading = ref(true)
const search = ref('')
const showForm = ref(false)
const formError = ref('')
const formLoading = ref(false)

const form = ref({
  id_album: '',
  format: '',
  condition: '',
  personalNotes: ''
})

const formatOptions = ['Vinile', 'CD', 'Cassetta', 'Musicassetta', 'Mini Disc', 'Altro']
const conditionOptions = ['Mint', 'Near Mint', 'Very Good Plus', 'Very Good', 'Good Plus', 'Good', 'Fair', 'Poor']

const filteredCopies = computed(() => {
  if (!search.value.trim()) return copies.value
  const q = search.value.toLowerCase()
  return copies.value.filter(c =>
    c.album_title?.toLowerCase().includes(q) ||
    c.format?.toLowerCase().includes(q) ||
    c.condition?.toLowerCase().includes(q) ||
    c.genre?.toLowerCase().includes(q)
  )
})

onMounted(async () => {
  try {
    const [copiesRes, albumsRes] = await Promise.all([
      api.get('/copies'),
      api.get('/albums')
    ])
    copies.value = copiesRes.data
    albums.value = albumsRes.data

    // Auto-apri form se arrivo da pagina album con query param
    if (route.query.addAlbum) {
      form.value.id_album = parseInt(route.query.addAlbum)
      showForm.value = true
    }
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
})

function resetForm() {
  form.value = { id_album: '', format: '', condition: '', personalNotes: '' }
  formError.value = ''
  showForm.value = false
}

async function handleCreate() {
  formError.value = ''
  if (!form.value.id_album || !form.value.format || !form.value.condition) {
    formError.value = 'Album, formato e condizione sono obbligatori'
    return
  }
  formLoading.value = true
  try {
    const res = await api.post('/copies', {
      id_album: parseInt(form.value.id_album),
      format: form.value.format,
      condition: form.value.condition,
      personalNotes: form.value.personalNotes || null
    })
    copies.value.unshift(res.data)
    resetForm()
  } catch (err) {
    formError.value = err.message || 'Errore durante l\'aggiunta'
  } finally {
    formLoading.value = false
  }
}

async function handleDeleteCopy(copy) {
  if (!confirm(`Rimuovere "${copy.album_title}" dalla collezione?`)) return
  try {
    await api.delete(`/copies/${copy.id_copy}`)
    copies.value = copies.value.filter(c => c.id_copy !== copy.id_copy)
  } catch (err) {
    console.error(err)
  }
}
</script>

<template>
  <div class="p-6 md:p-8 max-w-5xl mx-auto">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-bold">La Tua Collezione</h1>
        <p class="text-slate-400 text-sm mt-1">{{ copies.length }} copie fisiche</p>
      </div>
      <button @click="showForm = !showForm"
        class="px-5 py-2.5 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium
               rounded-xl transition-all duration-200 hover:shadow-lg hover:shadow-violet-600/25">
        {{ showForm ? 'Annulla' : '+ Aggiungi Copia' }}
      </button>
    </div>

    <!-- Form nuova copia -->
    <div v-if="showForm" class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 mb-6">
      <h3 class="text-lg font-semibold mb-4">Aggiungi una copia alla collezione</h3>
      <div v-if="formError" class="mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm rounded-lg px-4 py-3">
        {{ formError }}
      </div>
      <form @submit.prevent="handleCreate" class="space-y-4">
        <div>
          <label for="copy-album" class="block text-sm font-medium text-slate-300 mb-1.5">Album *</label>
          <select id="copy-album" v-model="form.id_album" required
            class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                   focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none">
            <option value="" disabled>Seleziona un album</option>
            <option v-for="album in albums" :key="album.id_album" :value="album.id_album">
              {{ album.title }} {{ album.releaseYear ? `(${album.releaseYear})` : '' }}
            </option>
          </select>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label for="copy-format" class="block text-sm font-medium text-slate-300 mb-1.5">Formato *</label>
            <select id="copy-format" v-model="form.format" required
              class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                     focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none">
              <option value="" disabled>Seleziona formato</option>
              <option v-for="f in formatOptions" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
          <div>
            <label for="copy-condition" class="block text-sm font-medium text-slate-300 mb-1.5">Condizione *</label>
            <select id="copy-condition" v-model="form.condition" required
              class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                     focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none">
              <option value="" disabled>Seleziona condizione</option>
              <option v-for="c in conditionOptions" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
        </div>
        <div>
          <label for="copy-notes" class="block text-sm font-medium text-slate-300 mb-1.5">Note personali</label>
          <textarea id="copy-notes" v-model="form.personalNotes" rows="2"
            class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                   placeholder-slate-500 focus:border-violet-500 focus:ring-1 focus:ring-violet-500
                   transition-colors outline-none resize-none"
            placeholder="Es. Prima stampa UK, edizione speciale..."></textarea>
        </div>
        <button type="submit" :disabled="formLoading"
          class="px-6 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white
                 text-sm font-medium rounded-xl transition-colors">
          {{ formLoading ? 'Aggiunta...' : 'Aggiungi alla collezione' }}
        </button>
      </form>
    </div>

    <!-- Barra ricerca -->
    <div class="mb-6">
      <input v-model="search" type="text" placeholder="Cerca nella tua collezione..."
        class="w-full px-4 py-2.5 bg-slate-900/80 border border-slate-800 rounded-xl text-slate-100
               placeholder-slate-500 focus:border-violet-500 focus:ring-1 focus:ring-violet-500
               transition-colors outline-none" />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-16 text-slate-400">Caricamento collezione...</div>

    <!-- Lista copie -->
    <div v-else-if="filteredCopies.length > 0" class="space-y-3">
      <div
        v-for="copy in filteredCopies" :key="copy.id_copy"
        class="bg-slate-900/80 border border-slate-800 rounded-2xl p-5
               flex flex-col sm:flex-row sm:items-center gap-4 hover:border-slate-700 transition-colors"
      >
        <!-- Info album -->
        <RouterLink :to="`/albums/${copy.id_album}`" class="flex items-center gap-4 flex-1 min-w-0 group">
          <div class="w-14 h-14 bg-slate-800 rounded-xl flex items-center justify-center text-2xl
                      group-hover:bg-slate-700/80 transition-colors shrink-0">
            &#128191;
          </div>
          <div class="min-w-0">
            <h3 class="font-semibold group-hover:text-violet-400 transition-colors truncate">{{ copy.album_title }}</h3>
            <div class="flex flex-wrap gap-2 text-xs text-slate-500 mt-1">
              <span v-if="copy.releaseYear">{{ copy.releaseYear }}</span>
              <span v-if="copy.genre">&middot; {{ copy.genre }}</span>
            </div>
          </div>
        </RouterLink>

        <!-- Dettagli copia -->
        <div class="flex items-center gap-3 shrink-0">
          <span class="px-2.5 py-1 bg-violet-500/10 border border-violet-500/30 text-violet-400 text-xs font-medium rounded-lg">
            {{ copy.format }}
          </span>
          <span class="px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium rounded-lg">
            {{ copy.condition }}
          </span>
          <RouterLink :to="`/collection/${copy.id_copy}`"
            class="px-3 py-1.5 text-xs text-slate-400 hover:text-violet-400 transition-colors">
            Dettagli
          </RouterLink>
          <button @click="handleDeleteCopy(copy)"
            class="px-3 py-1.5 text-xs text-slate-400 hover:text-rose-400 transition-colors">
            Rimuovi
          </button>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-16">
      <div class="text-5xl mb-4">&#128191;</div>
      <p class="text-slate-400 mb-4">
        {{ search ? 'Nessuna copia trovata.' : 'La tua collezione e\' ancora vuota.' }}
      </p>
      <RouterLink v-if="!search" to="/albums"
        class="inline-flex px-5 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-xl transition-colors">
        Esplora il catalogo
      </RouterLink>
    </div>
  </div>
</template>
