<!--
GrooveBox - Pagina Landing Pubblica
===================================
Pagina di benvenuto principale accessibile ai visitatori non autenticati.
Presenta brevemente gli obiettivi dell'applicazione e indirizza verso le pagine di accesso o registrazione.
-->

<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="min-h-screen flex flex-col justify-between relative overflow-hidden animate-fade-in">
    <!-- Background glow elements -->
    <div class="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-brand-secondary/15 rounded-full blur-[140px] animate-pulse pointer-events-none"></div>
    <div class="absolute bottom-1/4 left-1/3 w-80 h-80 bg-brand-accent/5 rounded-full blur-[120px] pointer-events-none"></div>

    <!-- Header / Brand Link -->
    <header class="w-full max-w-6xl mx-auto px-6 py-6 flex items-center justify-between z-10">
      <div class="flex items-center gap-2 font-bold text-xl tracking-tight">
        <div class="bg-brand-secondary/20 p-1.5 rounded-lg">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="text-brand-secondary"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
        </div>
        <span class="bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">GrooveBox</span>
      </div>
    </header>

    <!-- Hero Content -->
    <div class="flex-grow flex flex-col items-center justify-center px-6 text-center z-10 max-w-4xl mx-auto py-12">
      <h1 class="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 leading-tight bg-gradient-to-b from-white to-white/40 bg-clip-text text-transparent">
        La tua musica,<br />collezionata con cura.
      </h1>
      <p class="text-white/40 text-lg md:text-xl font-medium max-w-2xl mb-12 leading-relaxed">
        GrooveBox è il caveau digitale per la tua collezione musicale. 
        Consulta il catalogo della community, aggiungi i tuoi album e tieni traccia della tua collezione personale.
      </p>
      <div class="flex flex-col sm:flex-row gap-4 w-full sm:w-auto justify-center">
        <RouterLink
          to="/register"
          class="apple-button apple-button-primary text-base shadow-2xl shadow-white/5"
        >
          Registrati
        </RouterLink>
        <RouterLink
          to="/login"
          class="apple-button apple-button-secondary text-base"
        >
          Accedi
        </RouterLink>
      </div>
    </div>

    <!-- Minimal Footer -->
    <footer class="border-t border-white/5 py-8 px-6 opacity-30 hover:opacity-75 transition-opacity duration-700 z-10">
      <div class="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
        <p class="text-xs tracking-tight">GrooveBox. Progettato per collezionisti di musica.</p>
        <div class="flex gap-6 text-xs font-semibold">
          <span class="text-slate-500">Omar Balde.</span>
        </div>
      </div>
    </footer>
  </div>
</template>
