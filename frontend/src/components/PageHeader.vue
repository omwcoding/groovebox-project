<!--
Mint - Componente PageHeader
=================================
Header standard per le pagine principali del frontend. Gestisce la visualizzazione
di un titolo principale e di un sottotitolo descrittivo opzionale.
-->

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  }
})
</script>

<template>
  <div class="space-y-1">
    <h1 class="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
      {{ title }}
    </h1>
    <p v-if="subtitle" class="text-white/40 text-lg font-medium">
      {{ subtitle }}
    </p>
  </div>
</template>
