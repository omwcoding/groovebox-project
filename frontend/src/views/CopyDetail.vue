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
  <div class="space-y-6 animate-fade-in max-w-4xl mx-auto">
    <RouterLink to="/collection" class="inline-flex items-center gap-2 text-sm font-semibold opacity-50 hover:opacity-100 transition-opacity">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
      Torna alla collezione
    </RouterLink>

    <div v-if="loading" class="py-20 flex flex-col items-center justify-center gap-4 opacity-40">
      <div class="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
      <p class="text-sm font-semibold tracking-widest uppercase">Caricamento</p>
    </div>
    
    <div v-else-if="error && !copy" class="py-20 text-center text-rose-400 font-semibold">{{ error }}</div>

    <div v-else-if="copy" class="glass-panel rounded-apple-2xl overflow-hidden shadow-2xl border border-white/10 relative">
      <div v-if="error" class="m-6 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold rounded-2xl px-4 py-3">
        {{ error }}
      </div>

      <!-- Vista lettura -->
      <div v-if="!editing" class="flex flex-col md:flex-row">
        <!-- Left Side: Cover Art -->
        <div class="w-full md:w-1/2 aspect-square bg-white/5 flex items-center justify-center border-b md:border-b-0 md:border-r border-white/5 relative overflow-hidden">
          <img v-if="copy.coverPath"
            :src="`/api/albums/${copy.id_album}/cover`"
            :alt="copy.album_title"
            class="w-full h-full object-cover"
          />
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="opacity-15"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
        </div>

        <!-- Right Side: Content -->
        <div class="flex-grow p-8 md:p-12 flex flex-col justify-between">
          <div class="space-y-6">
            <div>
              <RouterLink :to="`/albums/${copy.id_album}`" class="text-3xl font-extrabold tracking-tight hover:text-brand-secondary transition-colors line-clamp-2">
                {{ copy.album_title }}
              </RouterLink>
              
              <div v-if="copy.artists?.length" class="flex flex-wrap gap-2 mt-3 mb-1">
                <RouterLink
                  v-for="artist in copy.artists" :key="artist.id_artist"
                  :to="`/artists/${artist.id_artist}`"
                  class="px-3 py-1 bg-brand-secondary/15 border border-brand-secondary/20 text-brand-secondary
                         rounded-full text-xs font-bold hover:bg-brand-secondary/25 transition-all"
                >
                  {{ artist.name }}
                </RouterLink>
              </div>

              <div class="flex flex-wrap gap-2 mt-4">
                <span class="px-3.5 py-1 bg-brand-secondary/15 border border-brand-secondary/20 text-brand-secondary text-xs font-bold uppercase tracking-wider rounded-full">
                  {{ copy.format }}
                </span>
                <span class="px-3.5 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold uppercase tracking-wider rounded-full">
                  {{ copy.condition }}
                </span>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-6 pt-6 border-t border-white/5 text-sm">
              <div class="space-y-1">
                <p class="text-[10px] font-bold uppercase tracking-widest text-white/30">Genere</p>
                <p class="font-semibold text-white/80">{{ copy.genre || '—' }}</p>
              </div>
              <div class="space-y-1">
                <p class="text-[10px] font-bold uppercase tracking-widest text-white/30">Aggiunto il</p>
                <p class="font-semibold text-white/80">{{ copy.addedDate }}</p>
              </div>
            </div>

            <div v-if="copy.personalNotes" class="pt-6 border-t border-white/5 space-y-2">
              <p class="text-[10px] font-bold uppercase tracking-widest text-white/30">Note personali</p>
              <p class="text-sm text-white/60 leading-relaxed italic bg-white/5 border border-white/5 rounded-2xl p-4">
                "{{ copy.personalNotes }}"
              </p>
            </div>
          </div>

          <div class="flex flex-col sm:flex-row gap-3 mt-12 pt-6 border-t border-white/5">
            <button @click="startEdit"
              class="apple-button apple-button-primary w-full sm:flex-1">
              Modifica Copia
            </button>
            <button @click="handleDelete"
              class="apple-button apple-button-secondary w-full sm:flex-1 !text-brand-accent hover:!bg-brand-accent/10 hover:!border-brand-accent/25">
              Rimuovi Copia
            </button>
          </div>
        </div>
      </div>

      <!-- Vista modifica -->
      <form v-else @submit.prevent="handleSave" class="p-8 space-y-6">
        <h3 class="text-2xl font-bold mb-6 text-center">Modifica Copia: {{ copy.album_title }}</h3>
        
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div class="space-y-2">
            <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Formato</label>
            <div class="relative">
              <select v-model="form.format" required class="apple-input appearance-none cursor-pointer">
                <option v-for="f in formatOptions" :key="f" :value="f">{{ f }}</option>
              </select>
              <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>
              </div>
            </div>
          </div>
          
          <div class="space-y-2">
            <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Condizione</label>
            <div class="relative">
              <select v-model="form.condition" required class="apple-input appearance-none cursor-pointer">
                <option v-for="c in conditionOptions" :key="c" :value="c">{{ c }}</option>
              </select>
              <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>
              </div>
            </div>
          </div>
        </div>
        
        <div class="space-y-2">
          <label class="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-1">Note personali</label>
          <textarea v-model="form.personalNotes" rows="3" class="apple-input resize-none"></textarea>
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
