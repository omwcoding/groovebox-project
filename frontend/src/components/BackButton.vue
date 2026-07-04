<script setup>
import { useRouter, RouterLink } from 'vue-router'

const props = defineProps({
  to: {
    type: String,
    default: ''
  },
  label: {
    type: String,
    default: 'Indietro'
  }
})

const router = useRouter()
</script>

<template>
  <RouterLink 
    v-if="to" 
    :to="to" 
    class="inline-flex items-center gap-2 text-sm font-semibold opacity-50 hover:opacity-100 transition-opacity"
  >
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="m15 18-6-6 6-6"/>
    </svg>
    {{ label }}
  </RouterLink>
  
  <button 
    v-else 
    @click="router.back()" 
    class="inline-flex items-center gap-2 text-sm font-semibold opacity-50 hover:opacity-100 transition-opacity cursor-pointer text-left"
  >
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="m15 18-6-6 6-6"/>
    </svg>
    {{ label }}
  </button>
</template>
