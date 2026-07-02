<script setup>
defineProps({
  message: {
    type: String,
    default: 'Caricamento'
  }
})
</script>

<template>
  <div class="py-20 flex flex-col items-center justify-center gap-4 opacity-40">
    <div class="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
    <p class="text-sm font-semibold tracking-widest uppercase">{{ message }}</p>
  </div>
</template>
