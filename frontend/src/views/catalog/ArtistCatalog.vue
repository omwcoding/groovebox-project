<!--
GrooveBox - Pagina Catalogo Artisti
===================================
Visualizza l'elenco degli artisti memorizzati a catalogo e permette la creazione 
di nuovi record tramite un'interfaccia di inserimento rapida.
-->

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/stores/api'

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
  } catch (_) {
    // Errore silenzioso: la UI mostra già lo stato vuoto
  } finally {
    loading.value = false
  }
})

async function handleCreate() {
  formError.value = ''
  if (!formName.value.trim()) {
    formError.value = 'Il nome è obbligatorio'
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
  <div class="space-y-8 animate-fade-in">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6">
      <div class="space-y-1">
        <h1 class="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
          Esplora Artisti
        </h1>
        <p class="text-white/40 text-lg font-medium">{{ artists.length }} artisti registrati nel database.</p>
      </div>
      
      <button
        @click="showForm = !showForm"
        class="apple-button apple-button-primary shadow-xl shadow-white/5 self-start sm:self-auto"
      >
        <svg v-if="!showForm" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        {{ showForm ? 'Annulla' : 'Nuovo Artista' }}
      </button>
    </div>

    <!-- Form rapido -->
    <transition name="page">
      <div v-if="showForm" class="glass-panel p-6 rounded-apple-2xl shadow-2xl">
        <div v-if="formError" class="mb-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold rounded-2xl px-4 py-3">
          {{ formError }}
        </div>
        <form @submit.prevent="handleCreate" class="flex flex-col sm:flex-row gap-3">
          <input v-model="formName" type="text" required placeholder="Nome artista (Es. Pink Floyd)"
            class="apple-input flex-grow" />
          <button type="submit" :disabled="formLoading"
            class="apple-button apple-button-primary shadow-lg shadow-white/5 whitespace-nowrap">
            {{ formLoading ? 'Aggiunta...' : 'Crea Artista' }}
          </button>
        </form>
      </div>
    </transition>

    <!-- Barra ricerca (Floating Glass Bar) -->
    <div class="relative w-full">
      <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none opacity-30">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
      </div>
      <input 
        v-model="search" 
        type="text" 
        placeholder="Cerca artista..." 
        class="w-full bg-white/5 border border-white/5 text-white text-sm rounded-full pl-11 pr-4 py-3.5 focus:outline-none focus:bg-white/10 transition-all font-medium placeholder:text-white/20"
      />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="py-20 flex flex-col items-center justify-center gap-4 opacity-40">
      <div class="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
      <p class="text-sm font-semibold tracking-widest uppercase">Caricamento</p>
    </div>

    <!-- Lista artisti -->
    <div v-else-if="filteredArtists.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
      <RouterLink
        v-for="(artist, index) in filteredArtists" :key="artist.id_artist"
        :to="`/artists/${artist.id_artist}`"
        class="group glass-card p-5 flex flex-col items-center gap-4 hover:scale-[1.02] hover:shadow-2xl hover:shadow-brand-secondary/5 text-center animate-slide-up"
        :style="{ animationDelay: `${index * 20}ms` }"
      >
        <div class="w-16 h-16 bg-white/5 border border-white/5 rounded-full flex items-center justify-center text-3xl group-hover:scale-110 group-hover:border-brand-secondary/20 transition-all duration-500 shrink-0">
          &#127908;
        </div>
        <div class="min-w-0 w-full">
          <h3 class="font-bold text-base leading-tight group-hover:text-brand-secondary transition-colors truncate px-1">
            {{ artist.name }}
          </h3>
        </div>
      </RouterLink>
    </div>

    <!-- Empty state -->
    <div v-else class="py-20 flex flex-col items-center justify-center gap-6 glass-panel rounded-apple-2xl border-dashed border-white/10 text-center px-10">
      <div class="bg-white/5 p-6 rounded-full">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="opacity-20"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>
      </div>
      <div class="space-y-1">
        <p class="text-xl font-bold">Nessun artista trovato</p>
        <p class="text-white/40 text-sm">
          {{ search ? 'Modifica la ricerca per visualizzare altri artisti.' : 'Nessun artista presente in catalogo.' }}
        </p>
      </div>
    </div>
  </div>
</template>
