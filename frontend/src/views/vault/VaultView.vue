<!--
Mint - Pagina del Vault Utente
=============================
Consente la visualizzazione del proprio archivio musicale in due modalità:
1. Scaffale (ripiani 3D con animazioni interattive).
2. Griglia (layout a griglia pulita con card informative).
-->

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/stores/api'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import PageHeader from '@/components/PageHeader.vue'
import VaultShelf from '@/components/VaultShelf.vue'
import AddToVaultModal from '@/components/AddToVaultModal.vue'

const copies = ref([])
const loading = ref(true)
const search = ref('')
const filterFormat = ref('')
const viewMode = ref('shelf') // 'shelf' | 'grid'
const showAddModal = ref(false)

const filteredCopies = computed(() => {
  return copies.value.filter(c => {
    const matchesSearch = !search.value.trim() || 
      c.album_title?.toLowerCase().includes(search.value.toLowerCase()) ||
      c.genre?.toLowerCase().includes(search.value.toLowerCase()) ||
      c.artists?.some(ar => ar.name.toLowerCase().includes(search.value.toLowerCase()))
    
    const matchesFormat = !filterFormat.value || c.format === filterFormat.value
    
    return matchesSearch && matchesFormat
  })
})

async function fetchCopies() {
  try {
    const res = await api.get('/copies')
    copies.value = res.data
  } catch (err) {
    // Gestione errore silenziosa
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchCopies()
})

function handleRecordAdded() {
  fetchCopies()
}
</script>

<template>
  <div class="space-y-8 animate-fade-in pb-20">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6">
      <div class="space-y-1">
        <h1 class="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
          Il tuo Vault
        </h1>
        <p class="text-white/40 text-lg font-medium">
          {{ filteredCopies.length }} dischi fisici custoditi.
        </p>
      </div>
      
      <!-- Pulsante Aggiungi Disco -->
      <button 
        @click="showAddModal = true"
        class="apple-button apple-button-primary shadow-xl shadow-brand-secondary/5 self-start sm:self-auto flex items-center justify-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
        Aggiungi Disco
      </button>
    </div>

    <!-- Barra dei Filtri e Controlli Visualizzazione -->
    <div class="flex flex-col md:flex-row items-center gap-4 py-4 border-y border-white/5 justify-between">
      <!-- Filtri input e select -->
      <div class="flex flex-col sm:flex-row items-center gap-4 w-full md:max-w-xl">
        <!-- Input di Ricerca -->
        <div class="relative w-full">
          <input 
            v-model="search" 
            type="text" 
            placeholder="Cerca per titolo, artista, genere..." 
            class="apple-input !pl-10 !py-2.5 text-sm" 
          />
          <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/20">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          </span>
        </div>

        <!-- Filtro Formato -->
        <div class="relative w-full sm:w-48 shrink-0">
          <select v-model="filterFormat" class="apple-input !py-2.5 !pr-10 text-sm appearance-none cursor-pointer">
            <option value="">Tutti i formati</option>
            <option value="Vinile">Vinile</option>
            <option value="CD">CD</option>
            <option value="Cassetta">Cassetta</option>
          </select>
          <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>
          </div>
        </div>
      </div>

      <!-- Toggle Layout (Scaffale / Griglia) -->
      <div class="flex items-center p-1 bg-white/5 border border-white/5 rounded-2xl shrink-0 self-end md:self-auto">
        <button 
          @click="viewMode = 'shelf'"
          :class="viewMode === 'shelf' ? 'bg-white/10 text-white shadow-lg' : 'text-white/40 hover:text-white/60'"
          class="px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5"
          title="Vista Scaffale"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>
          Scaffale
        </button>
        <button 
          @click="viewMode = 'grid'"
          :class="viewMode === 'grid' ? 'bg-white/10 text-white shadow-lg' : 'text-white/40 hover:text-white/60'"
          class="px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5"
          title="Vista Griglia"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>
          Griglia
        </button>
      </div>
    </div>

    <!-- Spinner Caricamento -->
    <LoadingSpinner v-if="loading" />

    <!-- Visualizzazioni -->
    <template v-else>
      <!-- Vista Scaffale (Default) -->
      <div v-if="viewMode === 'shelf'" class="animate-fade-in">
        <VaultShelf :copies="filteredCopies" />
      </div>

      <!-- Vista Griglia classica -->
      <div v-else class="animate-fade-in">
        <div v-if="filteredCopies.length === 0" class="text-center py-20 text-white/30 italic">
          Nessun disco corrisponde ai filtri di ricerca.
        </div>
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          <RouterLink
            v-for="copy in filteredCopies" 
            :key="copy.id_copy"
            :to="`/vault/${copy.id_copy}`"
            class="group glass-card p-4 flex gap-4 hover:scale-[1.02] hover:shadow-2xl transition-all duration-300 border border-white/5"
          >
            <!-- Cover Art -->
            <div class="w-20 h-20 bg-white/5 rounded-xl overflow-hidden shrink-0 flex items-center justify-center relative">
              <img v-if="copy.coverPath" :src="`/api/albums/${copy.id_album}/cover`" class="w-full h-full object-cover" />
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="opacity-15"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
            </div>
            <!-- Metadata -->
            <div class="min-w-0 flex flex-col justify-between py-1 flex-grow">
              <div>
                <p class="font-bold text-white/90 group-hover:text-brand-secondary transition-colors truncate">{{ copy.album_title }}</p>
                <p class="text-xs text-white/50 truncate">{{ copy.artists?.map(a => a.name).join(', ') || 'Artista' }}</p>
              </div>
              <div class="flex gap-2 text-[10px] font-bold uppercase tracking-wider">
                <span class="px-2 py-0.5 bg-brand-secondary/15 border border-brand-secondary/20 text-brand-secondary rounded">
                  {{ copy.format }}
                </span>
                <span class="px-2 py-0.5 bg-white/5 border border-white/10 text-white/60 rounded">
                  {{ copy.condition }}
                </span>
              </div>
            </div>
          </RouterLink>
        </div>
      </div>
    </template>

    <!-- Modale AddToVault -->
    <AddToVaultModal 
      v-if="showAddModal" 
      @close="showAddModal = false" 
      @added="handleRecordAdded" 
    />
  </div>
</template>
