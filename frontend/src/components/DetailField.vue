<script setup>
defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    default: '—'
  }
})
</script>

<template>
  <div class="space-y-1">
    <p class="text-[10px] font-bold uppercase tracking-widest text-white/30">{{ label }}</p>
    <p class="font-semibold text-white/80">
      <slot>{{ value }}</slot>
    </p>
  </div>
</template>
