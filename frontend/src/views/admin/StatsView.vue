<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/stores/api'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import PageHeader from '@/components/PageHeader.vue'

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
  <div class="space-y-8 animate-fade-in">
    <!-- Header -->
    <PageHeader title="Statistiche Piattaforma" subtitle="Panoramica sull'utilizzo e la crescita di GrooveBox." />

    <ErrorMessage v-if="error" :message="error" />

    <!-- Loading -->
    <LoadingSpinner v-if="loading" />

    <div v-else-if="stats" class="space-y-8">
      <!-- KPI Grid -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <div class="glass-panel p-6 rounded-apple-2xl text-center space-y-2 border border-white/5">
          <p class="text-[10px] font-bold uppercase tracking-widest text-white/30">Collector Attivi</p>
          <p class="text-4xl font-extrabold text-white tracking-tight">{{ stats.totals.users }}</p>
        </div>
        <div class="glass-panel p-6 rounded-apple-2xl text-center space-y-2 border border-white/5">
          <p class="text-[10px] font-bold uppercase tracking-widest text-white/30">Album a Catalogo</p>
          <p class="text-4xl font-extrabold text-white tracking-tight">{{ stats.totals.albums }}</p>
        </div>
        <div class="glass-panel p-6 rounded-apple-2xl text-center space-y-2 border border-white/5">
          <p class="text-[10px] font-bold uppercase tracking-widest text-white/30">Artisti Registrati</p>
          <p class="text-4xl font-extrabold text-white tracking-tight">{{ stats.totals.artists }}</p>
        </div>
        <div class="glass-panel p-6 rounded-apple-2xl text-center space-y-2 border border-white/5">
          <p class="text-[10px] font-bold uppercase tracking-widest text-white/30">Copie Fisiche</p>
          <p class="text-4xl font-extrabold text-brand-secondary tracking-tight">{{ stats.totals.physical_copies }}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Distribuzione formati -->
        <div class="glass-panel p-8 rounded-apple-2xl border border-white/5 shadow-xl space-y-6">
          <h2 class="text-xl font-bold">Distribuzione Formati</h2>
          <div v-if="stats.formats_distribution.length > 0" class="space-y-4">
            <div v-for="fmt in stats.formats_distribution" :key="fmt.format"
                 class="space-y-2">
              <div class="flex items-center justify-between text-sm font-semibold">
                <span class="text-white/80">{{ fmt.format }}</span>
                <span class="text-white/40">{{ fmt.count }} copie</span>
              </div>
              <div class="bg-white/5 rounded-full h-2 overflow-hidden border border-white/5">
                <div class="bg-gradient-to-r from-brand-secondary to-brand-secondary/80 h-full rounded-full transition-all duration-700"
                     :style="{ width: `${(fmt.count / stats.totals.physical_copies * 100)}%` }">
                </div>
              </div>
            </div>
          </div>
          <p v-else class="text-sm font-semibold text-white/30 italic">Nessun dato disponibile.</p>
        </div>

        <!-- Album piu' collezionati -->
        <div class="glass-panel p-8 rounded-apple-2xl border border-white/5 shadow-xl space-y-6">
          <h2 class="text-xl font-bold">I 10 Album più Collezionati</h2>
          <div v-if="stats.top_collected_albums.length > 0" class="space-y-4">
            <div v-for="(album, index) in stats.top_collected_albums" :key="album.id_album"
                 class="flex items-center gap-4 text-sm font-semibold p-2 rounded-xl hover:bg-white/[0.01] transition-colors">
              <span class="w-6 h-6 bg-brand-secondary/15 border border-brand-secondary/20 text-brand-secondary
                           rounded-full flex items-center justify-center text-[10px] font-extrabold shrink-0">
                {{ index + 1 }}
              </span>
              <span class="flex-grow truncate text-white/80">{{ album.title }}</span>
              <span class="text-white/40 text-xs shrink-0">{{ album.copies_count }} copie</span>
            </div>
          </div>
          <p v-else class="text-sm font-semibold text-white/30 italic">Nessun dato disponibile.</p>
        </div>
      </div>

      <!-- Ultimi album aggiunti -->
      <div class="glass-panel p-8 rounded-apple-2xl border border-white/5 shadow-xl space-y-6">
        <h2 class="text-xl font-bold">Ultimi Ingressi in Catalogo</h2>
        <div v-if="stats.recent_albums.length > 0" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <div v-for="album in stats.recent_albums" :key="album.id_album"
               class="p-4 bg-white/5 border border-white/5 rounded-2xl flex flex-col gap-3">
            <div class="w-10 h-10 bg-white/5 border border-white/5 rounded-xl flex items-center justify-center text-lg shrink-0">
              &#127925;
            </div>
            <div class="min-w-0">
              <p class="font-bold text-white/90 truncate leading-tight">{{ album.title }}</p>
              <div class="flex gap-2 text-[10px] font-bold text-white/20 uppercase tracking-wide mt-1">
                <span v-if="album.releaseYear">{{ album.releaseYear }}</span>
                <span v-if="album.releaseYear && album.genre">&middot;</span>
                <span v-if="album.genre" class="truncate">{{ album.genre }}</span>
              </div>
            </div>
          </div>
        </div>
        <p v-else class="text-sm font-semibold text-white/30 italic">Nessun album nel catalogo.</p>
      </div>
    </div>
  </div>
</template>
