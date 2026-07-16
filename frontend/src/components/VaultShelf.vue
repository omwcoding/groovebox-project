<!--
Mint - Componente VaultShelf
============================
Visualizza le copie fisiche organizzate in ripiani/scaffali con un'estetica premium.
Implementa un effetto hover interattivo in cui il vinile esce parzialmente dalla copertina.
-->

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

const props = defineProps({
  copies: {
    type: Array,
    required: true
  },
  readOnly: {
    type: Boolean,
    default: false
  }
})

// Suddivide le copie in scaffali da 4 elementi (adattabile a layout responsive)
const itemsPerShelf = 4

const shelves = computed(() => {
  const result = []
  for (let i = 0; i < props.copies.length; i += itemsPerShelf) {
    result.push(props.copies.slice(i, i + itemsPerShelf))
  }
  return result
})
</script>

<template>
  <div class="space-y-16 py-8">
    <!-- Se non ci sono dischi -->
    <div v-if="copies.length === 0" class="text-center py-20 text-white/30 italic">
      {{ readOnly ? 'Questo Vault è vuoto.' : 'Il tuo Vault è vuoto. Clicca "+ Aggiungi" per riempirlo.' }}
    </div>

    <!-- Scaffali -->
    <div 
      v-for="(shelf, shelfIndex) in shelves" 
      :key="shelfIndex"
      class="relative pb-10 pt-6 px-6 rounded-3xl bg-white/[0.01] border border-white/[0.03] shadow-inner flex flex-col items-center"
    >
      <!-- Dischi sullo scaffale -->
      <div class="flex flex-wrap gap-8 md:gap-14 justify-center items-end w-full z-10">
        <div 
          v-for="copy in shelf" 
          :key="copy.id_copy"
          class="flex flex-col items-center group/item"
        >
          <!-- Contenitore Copertina + Vinile animato -->
          <RouterLink 
            :to="readOnly ? `/albums/${copy.id_album}` : `/vault/${copy.id_copy}`"
            class="relative w-28 h-28 md:w-36 md:h-36 flex items-center justify-center select-none"
          >
            <!-- Copertina -->
            <div 
              class="absolute inset-0 z-20 transition-all duration-500 transform group-hover/item:-translate-x-3 md:group-hover/item:-translate-x-5 shadow-2xl border border-white/10 rounded-xl overflow-hidden bg-zinc-900"
            >
              <img 
                v-if="copy.cover_path" 
                :src="`/api/albums/${copy.id_album}/cover`" 
                :alt="copy.album_title" 
                class="w-full h-full object-cover" 
              />
              <div v-else class="w-full h-full flex items-center justify-center text-slate-600">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
              </div>
            </div>

            <!-- Vinile nero che scivola fuori -->
            <div 
              class="absolute right-0 w-24 h-24 md:w-32 md:h-32 rounded-full bg-[#121212] border border-neutral-900 z-10 transition-all duration-500 transform scale-95 opacity-0 group-hover/item:opacity-100 group-hover/item:translate-x-4 md:group-hover/item:translate-x-6 flex items-center justify-center shadow-2xl pointer-events-none"
            >
              <!-- Solchi del vinile -->
              <div class="absolute inset-1 rounded-full border border-neutral-800/40 opacity-70 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-neutral-900 via-black to-neutral-900"></div>
              <div class="absolute inset-4 rounded-full border border-neutral-800/20"></div>
              <div class="absolute inset-8 rounded-full border border-neutral-800/20"></div>
              
              <!-- Etichetta centrale -->
              <div class="w-7 h-7 md:w-10 md:h-10 rounded-full bg-brand-secondary/40 border border-brand-secondary/50 z-20 flex items-center justify-center">
                <div class="w-1.5 h-1.5 rounded-full bg-black"></div>
              </div>
            </div>
          </RouterLink>

          <!-- Didascalia del disco -->
          <div class="mt-4 text-center w-28 md:w-36 px-1">
            <p class="text-xs font-bold text-white/80 truncate group-hover/item:text-brand-secondary transition-colors duration-300">
              {{ copy.album_title }}
            </p>
            <p class="text-[10px] text-white/40 truncate font-semibold uppercase tracking-wider mt-0.5">
              {{ copy.artists?.map(a => a.name).join(', ') || 'Artista' }}
            </p>
          </div>
        </div>
      </div>

      <!-- Scaffale (superficie tridimensionale a effetto cristallo) -->
      <div 
        class="absolute bottom-0 left-4 right-4 h-3 bg-gradient-to-r from-white/5 via-white/15 to-white/5 rounded-lg shadow-xl border-t border-white/20 backdrop-blur-md"
      ></div>
      <!-- Spessore scaffale inferiore per profondità 3D -->
      <div 
        class="absolute bottom-[-4px] left-5 right-5 h-1 bg-black/60 rounded-b-lg filter blur-[1px]"
      ></div>
    </div>
  </div>
</template>
