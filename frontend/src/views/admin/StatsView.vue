<!--
GrooveBox - Dashboard Statistiche Piattaforma (Amministrazione)
===============================================================
Fornisce metriche aggregate sui dati inseriti a sistema, classifiche dei collezionisti
e grafici per la distribuzione dei supporti fisici. Accessibile solo agli amministratori.
-->

<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '@/stores/api'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import PageHeader from '@/components/PageHeader.vue'

const stats = ref(null)
const loading = ref(true)
const error = ref('')

const activeTab = ref('overview') // 'overview' | 'media' | 'leaderboard'
// Circonferenza per calcolo SVG Donut Chart (raggio = 50)
const circumference = 314.159

const donutSlices = computed(() => {
  if (!stats.value || !stats.value.formats_distribution) return []
  let accumulatedPercentage = 0
  const total = stats.value.totals.physical_copies || 1
  
  return stats.value.formats_distribution.map((fmt) => {
    const percentage = fmt.count / total
    const strokeDashArray = `${percentage * circumference} ${circumference}`
    const strokeDashOffset = -accumulatedPercentage * circumference
    accumulatedPercentage += percentage
    
    // Colori associati a ciascun formato per un contrasto perfetto
    let color = '#a855f7' // Viola (default)
    if (fmt.format === 'Vinile') color = '#f43f5e' // Rosa/Rosso
    else if (fmt.format === 'CD') color = '#3b82f6' // Blu
    else if (fmt.format === 'Cassetta') color = '#10b981' // Smeraldo/Verde
    
    return {
      ...fmt,
      percentage: Math.round(percentage * 100),
      strokeDashArray,
      strokeDashOffset,
      color
    }
  })
})

async function handleExportStats() {
  try {
    const token = localStorage.getItem('groovebox_token')
    const headers = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    const res = await fetch('/api/stats/export', { headers })
    if (res.status === 401) {
      // Token scaduto: replica il comportamento del layer api.js
      const { useAuthStore } = await import('@/stores/auth')
      const authStore = useAuthStore()
      authStore.logout()
      window.location.href = '/login'
      return
    }
    if (!res.ok) {
      throw new Error("Errore durante l'esportazione dei dati")
    }
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'statistiche_groovebox.json'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (err) {
    alert("Impossibile esportare le statistiche")
  }
}

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
    <div class="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
      <PageHeader title="Statistiche Piattaforma" subtitle="Monitora l'utilizzo, la distribuzione e la crescita di GrooveBox." />
      
      <!-- Tab Selector & Export Button -->
      <div v-if="stats" class="flex flex-col sm:flex-row items-start sm:items-center gap-4 shrink-0">
        <!-- Pulsante Esporta JSON -->
        <button 
          @click="handleExportStats"
          class="apple-button apple-button-secondary text-xs py-2 px-4 shadow-md flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Esporta JSON
        </button>

        <!-- Selettore Tab -->
        <div class="flex bg-white/5 border border-white/5 p-1 rounded-full text-xs font-bold tracking-wide uppercase">
          <button 
            @click="activeTab = 'overview'"
            class="px-4 py-2 rounded-full transition-all duration-300"
            :class="activeTab === 'overview' ? 'bg-white text-black font-extrabold shadow-sm' : 'text-white/60 hover:text-white'"
          >
            Panoramica
          </button>
          <button 
            @click="activeTab = 'media'"
            class="px-4 py-2 rounded-full transition-all duration-300"
            :class="activeTab === 'media' ? 'bg-white text-black font-extrabold shadow-sm' : 'text-white/60 hover:text-white'"
          >
            Analisi Supporti
          </button>
          <button 
            @click="activeTab = 'leaderboard'"
            class="px-4 py-2 rounded-full transition-all duration-300"
            :class="activeTab === 'leaderboard' ? 'bg-white text-black font-extrabold shadow-sm' : 'text-white/60 hover:text-white'"
          >
            Classifica
          </button>
        </div>
      </div>
    </div>

    <ErrorMessage v-if="error" :message="error" />

    <!-- Loading -->
    <LoadingSpinner v-if="loading" />

    <div v-else-if="stats">
      <!-- 1. TABS: OVERVIEW (Panoramica Generale) -->
      <div v-if="activeTab === 'overview'" class="space-y-8 animate-fade-in">
        <!-- KPI Grid -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-6">
          <div class="glass-panel p-6 rounded-apple-2xl text-center space-y-2 border border-white/5 hover:border-white/10 transition-all">
            <p class="text-[10px] font-bold uppercase tracking-widest text-white/30">Collector Registrati</p>
            <p class="text-4xl font-extrabold text-white tracking-tight">{{ stats.totals.users }}</p>
          </div>
          <div class="glass-panel p-6 rounded-apple-2xl text-center space-y-2 border border-white/5 hover:border-white/10 transition-all">
            <p class="text-[10px] font-bold uppercase tracking-widest text-white/30">Album a Catalogo</p>
            <p class="text-4xl font-extrabold text-white tracking-tight">{{ stats.totals.albums }}</p>
          </div>
          <div class="glass-panel p-6 rounded-apple-2xl text-center space-y-2 border border-white/5 hover:border-white/10 transition-all">
            <p class="text-[10px] font-bold uppercase tracking-widest text-white/30">Artisti a Catalogo</p>
            <p class="text-4xl font-extrabold text-white tracking-tight">{{ stats.totals.artists }}</p>
          </div>
          <div class="glass-panel p-6 rounded-apple-2xl text-center space-y-2 border border-white/5 hover:border-white/10 transition-all">
            <p class="text-[10px] font-bold uppercase tracking-widest text-white/30">Copie Fisiche Possedute</p>
            <p class="text-4xl font-extrabold text-brand-secondary tracking-tight">{{ stats.totals.physical_copies }}</p>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <!-- Album piu' collezionati -->
          <div class="glass-panel p-8 rounded-apple-2xl border border-white/5 shadow-xl space-y-6 lg:col-span-2">
            <h2 class="text-xl font-bold tracking-tight">I 10 Album più Collezionati</h2>
            <div v-if="stats.top_collected_albums.length > 0" class="divide-y divide-white/5">
              <div v-for="(album, index) in stats.top_collected_albums" :key="album.id_album"
                   class="flex items-center gap-4 text-sm font-semibold py-3 first:pt-0 last:pb-0 hover:bg-white/[0.01] transition-colors">
                <span class="w-6 h-6 bg-brand-secondary/15 border border-brand-secondary/20 text-brand-secondary
                             rounded-full flex items-center justify-center text-[10px] font-extrabold shrink-0">
                  {{ index + 1 }}
                </span>
                <span class="flex-grow truncate text-white/80 font-medium">{{ album.title }}</span>
                <span class="text-white/40 text-xs shrink-0 bg-white/5 px-3 py-1 rounded-full border border-white/5">{{ album.copies_count }} copie</span>
              </div>
            </div>
            <p v-else class="text-sm font-semibold text-white/30 italic">Nessun dato disponibile.</p>
          </div>

          <!-- Ultimi album aggiunti -->
          <div class="glass-panel p-8 rounded-apple-2xl border border-white/5 shadow-xl space-y-6">
            <h2 class="text-xl font-bold tracking-tight">Ultimi Ingressi</h2>
            <div v-if="stats.recent_albums.length > 0" class="space-y-4">
              <RouterLink v-for="album in stats.recent_albums" :key="album.id_album"
                   :to="`/albums/${album.id_album}`"
                   class="group p-4 bg-white/[0.02] border border-white/5 hover:border-brand-secondary/30 rounded-2xl flex items-center gap-4 hover:shadow-lg hover:shadow-brand-secondary/5 transition-all duration-300">
                <div class="w-10 h-10 rounded-xl overflow-hidden bg-white/5 border border-white/5 flex items-center justify-center shrink-0">
                  <img 
                    v-if="album.coverPath" 
                    :src="`/api/albums/${album.id_album}/cover`" 
                    :alt="album.title" 
                    class="w-full h-full object-cover" 
                  />
                  <span v-else class="text-lg">💿</span>
                </div>
                <div class="min-w-0 flex-grow">
                  <p class="font-bold text-white/90 group-hover:text-brand-secondary transition-colors truncate leading-tight">{{ album.title }}</p>
                  <p class="text-[10px] font-bold text-white/30 uppercase tracking-wide mt-1 truncate">
                    {{ album.genre }} <span v-if="album.releaseYear">&middot; {{ album.releaseYear }}</span>
                  </p>
                </div>
              </RouterLink>
            </div>
            <p v-else class="text-sm font-semibold text-white/30 italic text-center">Nessun album nel catalogo.</p>
          </div>
        </div>

        <!-- Generi & Artisti Più Attivi -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- Distribuzione Generi Musicali -->
          <div class="glass-panel p-8 rounded-apple-2xl border border-white/5 shadow-xl space-y-6">
            <h2 class="text-xl font-bold tracking-tight">I 5 Generi Musicali più Diffusi nel Catalogo</h2>
            <div v-if="stats.genres_distribution && stats.genres_distribution.length > 0" class="space-y-4">
              <div v-for="(genre, index) in stats.genres_distribution" :key="genre.genre" class="space-y-1">
                <div class="flex justify-between text-xs font-semibold text-white/80">
                  <span>{{ index + 1 }}. {{ genre.genre }}</span>
                  <span>{{ genre.count }} album</span>
                </div>
                <div class="bg-white/5 rounded-full h-1.5 overflow-hidden">
                  <div 
                    class="bg-brand-secondary h-full rounded-full" 
                    :style="{ width: `${(genre.count / stats.totals.albums * 100)}%` }"
                  ></div>
                </div>
              </div>
            </div>
            <p v-else class="text-sm font-semibold text-white/30 italic text-center">Nessun genere registrato.</p>
          </div>

          <!-- Artisti con più Album -->
          <div class="glass-panel p-8 rounded-apple-2xl border border-white/5 shadow-xl space-y-6">
            <h2 class="text-xl font-bold tracking-tight">I 5 Artisti più Attivi nel Catalogo</h2>
            <div v-if="stats.top_artists && stats.top_artists.length > 0" class="space-y-4">
              <div v-for="(artist, index) in stats.top_artists" :key="artist.id_artist" class="space-y-1">
                <div class="flex justify-between text-xs font-semibold text-white/80">
                  <span>{{ index + 1 }}. {{ artist.name }}</span>
                  <span>{{ artist.albums_count }} album</span>
                </div>
                <div class="bg-white/5 rounded-full h-1.5 overflow-hidden">
                  <div 
                    class="bg-brand-secondary h-full rounded-full" 
                    :style="{ width: `${(artist.albums_count / stats.totals.albums * 100)}%` }"
                  ></div>
                </div>
              </div>
            </div>
            <p v-else class="text-sm font-semibold text-white/30 italic text-center">Nessun artista registrato.</p>
          </div>
        </div>
      </div>

      <!-- 2. TABS: MEDIA (Analisi Avanzata Supporti) -->
      <div v-else-if="activeTab === 'media'" class="space-y-8 animate-fade-in">
        
        <!-- Grafico Donut Interattivo dei Formati (Full width layout) -->
        <div class="glass-panel p-8 rounded-apple-2xl border border-white/5 shadow-xl space-y-8">
          <div>
            <h2 class="text-xl font-bold tracking-tight">Distribuzione dei Supporti Fisici</h2>
            <p class="text-xs text-white/40 font-medium mt-1">Passa il mouse o clicca sulle fette colorate del grafico per scoprire i dettagli.</p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-12 items-center max-w-4xl mx-auto py-4">
            <!-- Donut SVG -->
            <div class="relative w-64 h-64 mx-auto">
              <svg viewBox="0 0 140 140" class="w-full h-full">
                <!-- Sfondo vuoto del donut -->
                <circle cx="70" cy="70" r="50" fill="transparent" stroke="rgba(255,255,255,0.03)" stroke-width="12" />
                <!-- Segmenti dei formati colorati -->
                <circle 
                  v-for="slice in donutSlices" 
                  :key="slice.format" 
                  cx="70" 
                  cy="70" 
                  r="50" 
                  fill="transparent" 
                  :stroke="slice.color" 
                  stroke-width="12" 
                  :stroke-dasharray="slice.strokeDashArray" 
                  :stroke-dashoffset="slice.strokeDashOffset" 
                  transform="rotate(-90 70 70)"
                  class="donut-segment cursor-pointer"
                />
              </svg>
              <!-- Testo Centrale Statico (non ridondante) -->
              <div class="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
                <span class="text-[10px] font-bold text-white/30 uppercase tracking-widest">
                  Totale
                </span>
                <span class="text-4xl font-extrabold text-white mt-0.5">
                  {{ stats.totals.physical_copies }}
                </span>
                <span class="text-[9px] font-semibold text-white/20 mt-0.5">
                  Copie fisiche
                </span>
              </div>
            </div>

            <!-- Legenda & Statistiche barre -->
            <div class="space-y-4">
              <div 
                v-for="slice in donutSlices" 
                :key="slice.format"
                class="p-4 rounded-2xl border bg-white/[0.02] border-white/5 transition-all duration-300 hover:border-white/10"
              >
                <div class="flex items-center justify-between text-sm font-bold mb-1.5">
                  <div class="flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full shrink-0" :style="{ backgroundColor: slice.color }"></span>
                    <span class="text-white/80">{{ slice.format }}</span>
                  </div>
                  <span class="text-white" :style="{ color: slice.color }">{{ slice.percentage }}%</span>
                </div>
                <div class="bg-white/5 rounded-full h-1.5 overflow-hidden">
                  <div 
                    class="h-full rounded-full transition-all duration-700" 
                    :style="{ width: `${slice.percentage}%`, backgroundColor: slice.color }"
                  ></div>
                </div>
                <div class="flex justify-between items-center text-[10px] font-medium text-white/40 mt-1">
                  <span>{{ slice.count }} copie archiviate</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. TABS: LEADERBOARD (Classifica Collezionisti) -->
      <div v-else-if="activeTab === 'leaderboard'" class="space-y-8 animate-fade-in">
        <!-- Trophies top 3 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div 
            v-for="(collector, idx) in stats.top_collectors.slice(0, 3)" 
            :key="collector.username"
            class="glass-panel p-6 rounded-apple-2xl border text-center relative flex flex-col items-center justify-center space-y-3"
            :class="[
              idx === 0 ? 'border-amber-400/20 bg-amber-400/[0.01]' : '',
              idx === 1 ? 'border-zinc-400/20 bg-zinc-400/[0.01]' : '',
              idx === 2 ? 'border-amber-700/20 bg-amber-700/[0.01]' : ''
            ]"
          >
            <!-- Badge Trophies -->
            <div class="w-12 h-12 rounded-full flex items-center justify-center text-2xl"
                 :class="[
                   idx === 0 ? 'bg-amber-400/10 text-amber-400 border border-amber-400/20' : '',
                   idx === 1 ? 'bg-zinc-400/10 text-zinc-300 border border-zinc-400/20' : '',
                   idx === 2 ? 'bg-amber-700/10 text-amber-600 border border-amber-700/20' : ''
                 ]"
            >
              {{ idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉' }}
            </div>
            
            <div class="space-y-0.5">
              <h3 class="font-bold text-lg text-white">{{ collector.name }} {{ collector.surname }}</h3>
              <p class="text-xs text-white/40 font-medium">@{{ collector.username }}</p>
            </div>
            
            <div class="px-4 py-1.5 bg-white/5 border border-white/5 rounded-full text-xs font-bold text-white/80">
              {{ collector.copies_count }} copie in libreria
            </div>
          </div>
        </div>

        <div class="glass-panel rounded-apple-2xl border border-white/5 shadow-xl overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="border-b border-white/5 bg-white/[0.01] text-xs font-bold uppercase tracking-widest text-white/30">
                  <th class="px-6 py-4 w-16 text-center">Pos</th>
                  <th class="px-6 py-4">Nome & Cognome</th>
                  <th class="px-6 py-4">Username</th>
                  <th class="px-6 py-4 text-right">Copie Archiviate</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-white/5 text-sm font-semibold">
                <tr v-for="(collector, idx) in stats.top_collectors" :key="collector.username" class="hover:bg-white/[0.01] transition-colors">
                  <td class="px-6 py-4 text-center font-extrabold text-white/40">
                    <span v-if="idx < 3" class="text-lg">{{ idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉' }}</span>
                    <span v-else>#{{ idx + 1 }}</span>
                  </td>
                  <td class="px-6 py-4 text-white/80">{{ collector.name }} {{ collector.surname }}</td>
                  <td class="px-6 py-4 text-brand-secondary font-mono text-xs">@{{ collector.username }}</td>
                  <td class="px-6 py-4 text-right font-extrabold text-white">{{ collector.copies_count }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Classe per i segmenti del donut SVG */
.donut-segment {
  transition: stroke-dashoffset 0.3s ease;
}
</style>
