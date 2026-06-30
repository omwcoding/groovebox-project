<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/stores/api'

const stats = ref(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const res = await api.get('/stats')
    stats.value = res.data
  } catch (err) {
    error.value = err.message || 'Errore nel caricamento statistiche'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="p-6 md:p-8 max-w-5xl mx-auto">
    <div class="mb-6">
      <h1 class="text-3xl font-bold">Statistiche e Report</h1>
      <p class="text-slate-400 text-sm mt-1">Panoramica della piattaforma GrooveBox</p>
    </div>

    <div v-if="error" class="mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm rounded-lg px-4 py-3">
      {{ error }}
    </div>

    <div v-if="loading" class="text-center py-16 text-slate-400">Caricamento statistiche...</div>

    <div v-else-if="stats" class="space-y-6">
      <!-- Contatori principali -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 text-center">
          <div class="text-3xl font-bold text-violet-400">{{ stats.totals.users }}</div>
          <div class="text-sm text-slate-400 mt-1">Collector</div>
        </div>
        <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 text-center">
          <div class="text-3xl font-bold text-violet-400">{{ stats.totals.albums }}</div>
          <div class="text-sm text-slate-400 mt-1">Album</div>
        </div>
        <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 text-center">
          <div class="text-3xl font-bold text-violet-400">{{ stats.totals.artists }}</div>
          <div class="text-sm text-slate-400 mt-1">Artisti</div>
        </div>
        <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 text-center">
          <div class="text-3xl font-bold text-violet-400">{{ stats.totals.physical_copies }}</div>
          <div class="text-sm text-slate-400 mt-1">Copie fisiche</div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Distribuzione formati -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
          <h2 class="text-lg font-semibold mb-4">Distribuzione Formati</h2>
          <div v-if="stats.formats_distribution.length > 0" class="space-y-3">
            <div v-for="fmt in stats.formats_distribution" :key="fmt.format"
                 class="flex items-center gap-3">
              <span class="text-sm text-slate-300 w-24 shrink-0">{{ fmt.format }}</span>
              <div class="flex-1 bg-slate-800 rounded-full h-3 overflow-hidden">
                <div class="bg-violet-500 h-full rounded-full transition-all duration-500"
                     :style="{ width: `${(fmt.count / stats.totals.physical_copies * 100)}%` }">
                </div>
              </div>
              <span class="text-sm text-slate-500 w-8 text-right">{{ fmt.count }}</span>
            </div>
          </div>
          <p v-else class="text-sm text-slate-500">Nessun dato disponibile.</p>
        </div>

        <!-- Album piu' collezionati -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
          <h2 class="text-lg font-semibold mb-4">Album piu' Collezionati</h2>
          <div v-if="stats.top_collected_albums.length > 0" class="space-y-3">
            <div v-for="(album, index) in stats.top_collected_albums" :key="album.id_album"
                 class="flex items-center gap-3 text-sm">
              <span class="w-6 h-6 bg-violet-500/10 border border-violet-500/30 text-violet-400
                           rounded-full flex items-center justify-center text-xs font-bold shrink-0">
                {{ index + 1 }}
              </span>
              <span class="flex-1 truncate">{{ album.title }}</span>
              <span class="text-slate-500">{{ album.copies_count }} copie</span>
            </div>
          </div>
          <p v-else class="text-sm text-slate-500">Nessun dato disponibile.</p>
        </div>
      </div>

      <!-- Ultimi album aggiunti -->
      <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
        <h2 class="text-lg font-semibold mb-4">Ultimi Album Aggiunti al Catalogo</h2>
        <div v-if="stats.recent_albums.length > 0" class="space-y-3">
          <div v-for="album in stats.recent_albums" :key="album.id_album"
               class="flex items-center gap-4 p-3 bg-slate-800/50 rounded-xl text-sm">
            <div class="w-10 h-10 bg-slate-700 rounded-lg flex items-center justify-center text-lg shrink-0">
              &#127925;
            </div>
            <div class="min-w-0 flex-1">
              <p class="font-medium truncate">{{ album.title }}</p>
              <div class="flex gap-2 text-xs text-slate-500">
                <span v-if="album.releaseYear">{{ album.releaseYear }}</span>
                <span v-if="album.genre">&middot; {{ album.genre }}</span>
              </div>
            </div>
          </div>
        </div>
        <p v-else class="text-sm text-slate-500">Nessun album nel catalogo.</p>
      </div>
    </div>
  </div>
</template>
