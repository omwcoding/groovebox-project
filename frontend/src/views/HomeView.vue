<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <!-- Hero Section -->
    <div class="flex-1 flex flex-col items-center justify-center px-6 text-center">
      <div class="mb-8">
        <span class="text-6xl">&#127926;</span>
      </div>
      <h1 class="text-5xl md:text-6xl font-extrabold tracking-tight mb-4">
        Groove<span class="text-violet-400">Box</span>
      </h1>
      <p class="text-lg md:text-xl text-slate-400 max-w-2xl mb-10 leading-relaxed">
        Il catalogo collaborativo per collezionisti di dischi.
        Organizza la tua collezione, esplora il catalogo comunitario
        e condividi la passione per la musica in formato fisico.
      </p>
      <div class="flex flex-col sm:flex-row gap-4">
        <RouterLink
          to="/register"
          class="px-8 py-3 bg-violet-600 hover:bg-violet-500 text-white font-semibold rounded-xl
                 transition-all duration-200 hover:shadow-lg hover:shadow-violet-600/25"
        >
          Crea il tuo account
        </RouterLink>
        <RouterLink
          to="/login"
          class="px-8 py-3 border border-slate-700 hover:border-slate-500 text-slate-300
                 hover:text-white font-semibold rounded-xl transition-all duration-200"
        >
          Accedi
        </RouterLink>
      </div>
    </div>

    <!-- Footer -->
    <footer class="py-6 text-center text-sm text-slate-600">
      GrooveBox &mdash; Progetto di Programmazione per il Web
    </footer>
  </div>
</template>
