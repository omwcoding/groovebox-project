<!--
Mint - Componente AlbumCard
================================
Rappresentazione visuale sintetica (scheda) di un album, utilizzata sia nel catalogo
generale che nella collezione dell'utente. Gestisce fallback per immagini assenti
e classi dinamiche in base alle condizioni del supporto.
-->

<script setup>
import { RouterLink } from 'vue-router'

defineProps({
  idAlbum: {
    type: Number,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  artists: {
    type: Array,
    default: () => []
  },
  cover_path: {
    type: String,
    default: null
  },
  genre: {
    type: String,
    default: ''
  },
  release_year: {
    type: [Number, String],
    default: ''
  },
  to: {
    type: String,
    required: true
  },
  format: {
    type: String,
    default: null
  },
  condition: {
    type: String,
    default: null
  },
  index: {
    type: Number,
    default: 0
  }
})

const getConditionClass = (cond) => {
  if (!cond) return ''
  switch (cond) {
    case 'Nuovo':
      return 'text-emerald-400'
    case 'Come nuovo':
      return 'text-sky-400'
    case 'Buono':
      return 'text-yellow-300'
    case 'Discreto':
      return 'text-orange-500'
    case 'Rovinato':
      return 'text-rose-500'
    default:
      return 'text-white/40'
  }
}
</script>

<template>
  <RouterLink 
    :to="to"
    class="group flex flex-col gap-4 animate-slide-up"
    :style="{ animationDelay: `${index * 30}ms` }"
  >
    <!-- Copertina o SVG di fallback -->
    <div class="w-full aspect-square rounded-apple-2xl overflow-hidden bg-white/5 relative group-hover:scale-[1.02] group-hover:shadow-2xl group-hover:shadow-brand-secondary/10 transition-all duration-500">
      <img v-if="cover_path"
        :src="`/api/albums/${idAlbum}/cover`"
        :alt="title"
        class="absolute inset-0 w-full h-full object-cover"
      />
      <div v-else class="absolute inset-0 flex items-center justify-center bg-white/5">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="opacity-15 group-hover:opacity-30 group-hover:rotate-12 transition-all duration-500">
          <circle cx="12" cy="12" r="10"/>
          <path d="M6 12c0-1.7.7-3.2 1.8-4.2"/>
          <circle cx="12" cy="12" r="2"/>
          <path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/>
        </svg>
      </div>
      
      <!-- Indicatore del formato del supporto fisico -->
      <div v-if="format" class="absolute bottom-3 right-3 z-10">
         <span class="inline-flex items-center px-3 py-1 bg-black/60 backdrop-blur-md rounded-full text-[9px] font-bold uppercase tracking-widest text-white/90 border border-white/15">
            {{ format }}
         </span>
      </div>
    </div>

    <!-- Metadati descrittivi dell'album -->
    <div class="space-y-1.5 px-1 flex flex-col justify-between h-20">
      <div>
        <h3 class="font-bold text-base leading-snug line-clamp-1 group-hover:text-brand-secondary transition-colors" :title="title">
          {{ title }}
        </h3>
        <p class="text-white/40 text-xs font-semibold truncate mt-0.5">
          {{ artists?.map(a => a.name).join(', ') || 'Artista sconosciuto' }}
        </p>
      </div>
      
      <div class="flex items-center justify-between text-white/30 text-[10px] font-bold uppercase tracking-wider">
        <div class="flex items-center gap-1.5 truncate">
          <span v-if="release_year">{{ release_year }}</span>
          <span v-if="release_year && genre">&middot;</span>
          <span v-if="genre" class="truncate">{{ genre }}</span>
        </div>
        <span v-if="condition" :class="[getConditionClass(condition), 'font-extrabold shrink-0 ml-2']">{{ condition }}</span>
      </div>
    </div>
  </RouterLink>
</template>
