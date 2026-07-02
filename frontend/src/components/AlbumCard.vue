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
  coverPath: {
    type: String,
    default: null
  },
  genre: {
    type: String,
    default: ''
  },
  releaseYear: {
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
</script>

<template>
  <RouterLink 
    :to="to"
    class="group flex flex-col gap-4 animate-slide-up"
    :style="{ animationDelay: `${index * 30}ms` }"
  >
    <!-- Album Art / Placeholder -->
    <div class="aspect-square glass-card overflow-hidden relative group-hover:scale-[1.02] group-hover:shadow-2xl group-hover:shadow-brand-secondary/10 transition-all duration-500 flex items-center justify-center">
      <img v-if="coverPath"
        :src="`/api/albums/${idAlbum}/cover`"
        :alt="title"
        class="w-full h-full object-cover"
      />
      <div v-else class="w-full h-full flex items-center justify-center bg-white/5">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="opacity-15 group-hover:opacity-30 group-hover:rotate-12 transition-all duration-500">
          <circle cx="12" cy="12" r="10"/>
          <path d="M6 12c0-1.7.7-3.2 1.8-4.2"/>
          <circle cx="12" cy="12" r="2"/>
          <path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/>
        </svg>
      </div>
      
      <!-- Format Badge -->
      <div v-if="format" class="absolute bottom-3 right-3 z-10">
         <span class="inline-flex items-center px-3 py-1 bg-black/60 backdrop-blur-md rounded-full text-[9px] font-bold uppercase tracking-widest text-white/90 border border-white/15">
            {{ format }}
         </span>
      </div>

      <!-- Play Hover indicator (solo se non è una copia fisica con badge) -->
      <div v-else class="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
        <div class="w-12 h-12 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center border border-white/30 scale-90 group-hover:scale-100 transition-transform duration-500">
           <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="white" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
        </div>
      </div>
    </div>

    <!-- Info -->
    <div class="space-y-1 px-1">
      <h3 class="font-bold text-base leading-tight line-clamp-1 group-hover:text-brand-secondary transition-colors">
        {{ title }}
      </h3>
      <p class="text-white/40 text-xs font-semibold truncate">
        {{ artists?.map(a => a.name).join(', ') || 'Artista sconosciuto' }}
      </p>
      
      <div class="flex items-center justify-between text-white/30 text-[10px] font-bold uppercase tracking-wider mt-0.5">
        <div class="flex items-center gap-1.5 truncate">
          <span v-if="releaseYear">{{ releaseYear }}</span>
          <span v-if="releaseYear && genre">&middot;</span>
          <span v-if="genre" class="truncate">{{ genre }}</span>
        </div>
        <span v-if="condition" class="text-emerald-400 font-extrabold shrink-0 ml-2">{{ condition }}</span>
      </div>
    </div>
  </RouterLink>
</template>
