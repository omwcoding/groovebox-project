<script setup>
import { useAuthStore } from '@/stores/auth'
import { RouterLink } from 'vue-router'

const authStore = useAuthStore()
</script>

<template>
  <div class="p-6 md:p-8 max-w-5xl mx-auto">
    <!-- Benvenuto -->
    <div class="mb-10">
      <h1 class="text-3xl font-bold mb-2">
        Ciao, <span class="text-violet-400">{{ authStore.user?.name }}</span> &#128075;
      </h1>
      <p class="text-slate-400">
        {{ authStore.isAdmin ? 'Pannello di amministrazione GrooveBox' : 'Benvenuto nella tua GrooveBox' }}
      </p>
    </div>

    <!-- Quick Links — Collector -->
    <div v-if="authStore.isCollector" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <RouterLink
        to="/collection"
        class="group bg-slate-900/80 border border-slate-800 hover:border-violet-500/50
               rounded-2xl p-6 transition-all duration-200 hover:shadow-lg hover:shadow-violet-600/5"
      >
        <div class="text-3xl mb-3">&#128191;</div>
        <h3 class="font-semibold text-lg mb-1 group-hover:text-violet-400 transition-colors">La Tua Collezione</h3>
        <p class="text-sm text-slate-400">Gestisci le tue copie fisiche</p>
      </RouterLink>

      <RouterLink
        to="/albums"
        class="group bg-slate-900/80 border border-slate-800 hover:border-violet-500/50
               rounded-2xl p-6 transition-all duration-200 hover:shadow-lg hover:shadow-violet-600/5"
      >
        <div class="text-3xl mb-3">&#127925;</div>
        <h3 class="font-semibold text-lg mb-1 group-hover:text-violet-400 transition-colors">Catalogo Album</h3>
        <p class="text-sm text-slate-400">Esplora e aggiungi nuovi album</p>
      </RouterLink>

      <RouterLink
        to="/artists"
        class="group bg-slate-900/80 border border-slate-800 hover:border-violet-500/50
               rounded-2xl p-6 transition-all duration-200 hover:shadow-lg hover:shadow-violet-600/5"
      >
        <div class="text-3xl mb-3">&#127908;</div>
        <h3 class="font-semibold text-lg mb-1 group-hover:text-violet-400 transition-colors">Catalogo Artisti</h3>
        <p class="text-sm text-slate-400">Scopri gli artisti nel catalogo</p>
      </RouterLink>
    </div>

    <!-- Quick Links — Admin -->
    <div v-if="authStore.isAdmin" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <RouterLink
        to="/users"
        class="group bg-slate-900/80 border border-slate-800 hover:border-violet-500/50
               rounded-2xl p-6 transition-all duration-200 hover:shadow-lg hover:shadow-violet-600/5"
      >
        <div class="text-3xl mb-3">&#128101;</div>
        <h3 class="font-semibold text-lg mb-1 group-hover:text-violet-400 transition-colors">Gestione Utenti</h3>
        <p class="text-sm text-slate-400">Elenco e moderazione Collector</p>
      </RouterLink>

      <RouterLink
        to="/albums"
        class="group bg-slate-900/80 border border-slate-800 hover:border-violet-500/50
               rounded-2xl p-6 transition-all duration-200 hover:shadow-lg hover:shadow-violet-600/5"
      >
        <div class="text-3xl mb-3">&#127925;</div>
        <h3 class="font-semibold text-lg mb-1 group-hover:text-violet-400 transition-colors">Catalogo Album</h3>
        <p class="text-sm text-slate-400">Modera il catalogo globale</p>
      </RouterLink>

      <RouterLink
        to="/artists"
        class="group bg-slate-900/80 border border-slate-800 hover:border-violet-500/50
               rounded-2xl p-6 transition-all duration-200 hover:shadow-lg hover:shadow-violet-600/5"
      >
        <div class="text-3xl mb-3">&#127908;</div>
        <h3 class="font-semibold text-lg mb-1 group-hover:text-violet-400 transition-colors">Catalogo Artisti</h3>
        <p class="text-sm text-slate-400">Gestisci gli artisti</p>
      </RouterLink>

      <RouterLink
        to="/stats"
        class="group bg-slate-900/80 border border-slate-800 hover:border-violet-500/50
               rounded-2xl p-6 transition-all duration-200 hover:shadow-lg hover:shadow-violet-600/5"
      >
        <div class="text-3xl mb-3">&#128202;</div>
        <h3 class="font-semibold text-lg mb-1 group-hover:text-violet-400 transition-colors">Statistiche</h3>
        <p class="text-sm text-slate-400">Report e dati della piattaforma</p>
      </RouterLink>
    </div>
  </div>
</template>
