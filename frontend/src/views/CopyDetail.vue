<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { api } from '@/stores/api'

const route = useRoute()
const router = useRouter()

const copy = ref(null)
const loading = ref(true)
const editing = ref(false)
const error = ref('')

const formatOptions = ['Vinile', 'CD', 'Cassetta', 'Musicassetta', 'Mini Disc', 'Altro']
const conditionOptions = ['Mint', 'Near Mint', 'Very Good Plus', 'Very Good', 'Good Plus', 'Good', 'Fair', 'Poor']

const form = ref({ format: '', condition: '', personalNotes: '' })

onMounted(async () => {
  try {
    const res = await api.get(`/copies/${route.params.id}`)
    copy.value = res.data
  } catch (err) {
    error.value = err.message || 'Copia non trovata'
  } finally {
    loading.value = false
  }
})

function startEdit() {
  form.value = {
    format: copy.value.format,
    condition: copy.value.condition,
    personalNotes: copy.value.personalNotes || ''
  }
  editing.value = true
}

async function handleSave() {
  try {
    const res = await api.put(`/copies/${copy.value.id_copy}`, {
      format: form.value.format,
      condition: form.value.condition,
      personalNotes: form.value.personalNotes || null
    })
    copy.value = res.data
    editing.value = false
  } catch (err) {
    error.value = err.message || 'Errore durante l\'aggiornamento'
  }
}

async function handleDelete() {
  if (!confirm('Rimuovere questa copia dalla collezione?')) return
  try {
    await api.delete(`/copies/${copy.value.id_copy}`)
    router.push('/collection')
  } catch (err) {
    error.value = err.message || 'Errore durante l\'eliminazione'
  }
}
</script>

<template>
  <div class="p-6 md:p-8 max-w-3xl mx-auto">
    <RouterLink to="/collection" class="inline-flex items-center text-sm text-slate-400 hover:text-violet-400 mb-6 transition-colors">
      &larr; Torna alla collezione
    </RouterLink>

    <div v-if="loading" class="text-center py-16 text-slate-400">Caricamento...</div>
    <div v-else-if="error && !copy" class="text-center py-16 text-rose-400">{{ error }}</div>

    <div v-else-if="copy" class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8">
      <div v-if="error" class="mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm rounded-lg px-4 py-3">
        {{ error }}
      </div>

      <!-- Vista lettura -->
      <div v-if="!editing">
        <div class="flex items-start gap-5 mb-6">
          <div class="w-20 h-20 bg-slate-800 rounded-xl flex items-center justify-center text-4xl shrink-0">
            &#128191;
          </div>
          <div>
            <RouterLink :to="`/albums/${copy.id_album}`" class="text-xl font-bold hover:text-violet-400 transition-colors">
              {{ copy.album_title }}
            </RouterLink>
            <div class="flex flex-wrap gap-2 mt-2">
              <span class="px-2.5 py-1 bg-violet-500/10 border border-violet-500/30 text-violet-400 text-xs font-medium rounded-lg">
                {{ copy.format }}
              </span>
              <span class="px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium rounded-lg">
                {{ copy.condition }}
              </span>
            </div>
          </div>
        </div>

        <div class="space-y-3 text-sm border-t border-slate-800 pt-6">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <span class="text-slate-500 block mb-1">Anno</span>
              <span>{{ copy.releaseYear || '—' }}</span>
            </div>
            <div>
              <span class="text-slate-500 block mb-1">Genere</span>
              <span>{{ copy.genre || '—' }}</span>
            </div>
            <div>
              <span class="text-slate-500 block mb-1">Aggiunta il</span>
              <span>{{ copy.addedDate }}</span>
            </div>
          </div>
          <div v-if="copy.personalNotes" class="pt-2">
            <span class="text-slate-500 block mb-1">Note personali</span>
            <p class="text-slate-300 bg-slate-800/50 rounded-lg px-4 py-3">{{ copy.personalNotes }}</p>
          </div>
        </div>

        <div class="flex gap-3 pt-6 mt-6 border-t border-slate-800">
          <button @click="startEdit"
            class="px-5 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-xl transition-colors">
            Modifica
          </button>
          <button @click="handleDelete"
            class="px-5 py-2 border border-rose-500/30 text-rose-400 hover:bg-rose-500/10 text-sm font-medium rounded-xl transition-colors">
            Rimuovi dalla collezione
          </button>
        </div>
      </div>

      <!-- Vista modifica -->
      <form v-else @submit.prevent="handleSave" class="space-y-4">
        <h3 class="text-lg font-semibold mb-2">Modifica copia: {{ copy.album_title }}</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1.5">Formato</label>
            <select v-model="form.format" required
              class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                     focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none">
              <option v-for="f in formatOptions" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1.5">Condizione</label>
            <select v-model="form.condition" required
              class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                     focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none">
              <option v-for="c in conditionOptions" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-1.5">Note personali</label>
          <textarea v-model="form.personalNotes" rows="3"
            class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100
                   focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors outline-none resize-none"></textarea>
        </div>
        <div class="flex gap-3">
          <button type="submit" class="px-5 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-xl transition-colors">
            Salva
          </button>
          <button type="button" @click="editing = false" class="px-5 py-2 border border-slate-700 text-slate-300 text-sm rounded-xl transition-colors">
            Annulla
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
