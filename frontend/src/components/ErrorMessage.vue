<script setup>
defineProps({
  message: {
    type: String,
    required: true
  }
})
</script>

<template>
  <div class="mb-6 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold rounded-2xl px-4 py-3">
    {{ message }}
  </div>
</template>
