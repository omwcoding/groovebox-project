<!--
Mint - Pagina Home della Dashboard Interna
=========================================
Funge da pannello di smistamento per gli utenti autenticati, esponendo collegamenti rapidi 
differenziati in base al ruolo dell'utente (Collector o Administrator).
-->

<script setup>
import { useAuthStore } from '@/stores/auth'
import { RouterLink } from 'vue-router'

const authStore = useAuthStore()
</script>

<template>
  <div class="space-y-12 animate-fade-in">
    <!-- Benvenuto -->
    <div class="space-y-2">
      <h1 class="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
        Ciao, {{ authStore.user?.name }}
      </h1>
      <p class="text-white/40 text-lg font-medium">
        {{ authStore.isAdmin ? 'Pannello di controllo Mint' : 'Esplora e gestisci il tuo archivio musicale.' }}
      </p>
    </div>

    <!-- Quick Links — Collector -->
    <div v-if="authStore.isCollector" class="grid grid-cols-1 sm:grid-cols-2 gap-6 max-w-4xl mx-auto">
      <RouterLink
        to="/collection"
        class="group glass-card p-6 flex flex-col gap-6 hover:scale-[1.02] hover:shadow-2xl hover:shadow-brand-secondary/5"
      >
        <div class="w-12 h-12 bg-brand-secondary/10 border border-brand-secondary/20 rounded-2xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform duration-300">
          &#128191;
        </div>
        <div class="space-y-1">
          <h3 class="font-bold text-lg group-hover:text-brand-secondary transition-colors">La Tua Collezione</h3>
          <p class="text-sm text-white/40">Visualizza, modifica e gestisci le tue copie fisiche private.</p>
        </div>
      </RouterLink>

      <RouterLink
        to="/albums"
        class="group glass-card p-6 flex flex-col gap-6 hover:scale-[1.02] hover:shadow-2xl hover:shadow-brand-secondary/5"
      >
        <div class="w-12 h-12 bg-brand-secondary/10 border border-brand-secondary/20 rounded-2xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform duration-300">
          &#127925;
        </div>
        <div class="space-y-1">
          <h3 class="font-bold text-lg group-hover:text-brand-secondary transition-colors">Catalogo Album</h3>
          <p class="text-sm text-white/40">Esplora il catalogo della community o inserisci un nuovo album.</p>
        </div>
      </RouterLink>
    </div>

    <!-- Quick Links — Admin -->
    <div v-if="authStore.isAdmin" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <RouterLink
        to="/admin?tab=users"
        class="group glass-card p-6 flex flex-col gap-6 hover:scale-[1.02] hover:shadow-2xl hover:shadow-brand-secondary/5"
      >
        <div class="w-12 h-12 bg-brand-secondary/10 border border-brand-secondary/20 rounded-2xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform duration-300">
          &#128101;
        </div>
        <div class="space-y-1">
          <h3 class="font-bold text-lg group-hover:text-brand-secondary transition-colors">Gestione Utenti</h3>
          <p class="text-sm text-white/40">Modera i profili collector registrati.</p>
        </div>
      </RouterLink>

      <RouterLink
        to="/albums"
        class="group glass-card p-6 flex flex-col gap-6 hover:scale-[1.02] hover:shadow-2xl hover:shadow-brand-secondary/5"
      >
        <div class="w-12 h-12 bg-brand-secondary/10 border border-brand-secondary/20 rounded-2xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform duration-300">
          &#127925;
        </div>
        <div class="space-y-1">
          <h3 class="font-bold text-lg group-hover:text-brand-secondary transition-colors">Modera Album</h3>
          <p class="text-sm text-white/40">Modifica o elimina gli album dal catalogo.</p>
        </div>
      </RouterLink>

      <RouterLink
        to="/artists"
        class="group glass-card p-6 flex flex-col gap-6 hover:scale-[1.02] hover:shadow-2xl hover:shadow-brand-secondary/5"
      >
        <div class="w-12 h-12 bg-brand-secondary/10 border border-brand-secondary/20 rounded-2xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform duration-300">
          &#127908;
        </div>
        <div class="space-y-1">
          <h3 class="font-bold text-lg group-hover:text-brand-secondary transition-colors">Modera Artisti</h3>
          <p class="text-sm text-white/40">Gestisci i nomi degli artisti nel catalogo.</p>
        </div>
      </RouterLink>

      <RouterLink
        to="/admin?tab=insights"
        class="group glass-card p-6 flex flex-col gap-6 hover:scale-[1.02] hover:shadow-2xl hover:shadow-brand-secondary/5"
      >
        <div class="w-12 h-12 bg-brand-secondary/10 border border-brand-secondary/20 rounded-2xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform duration-300">
          &#128202;
        </div>
        <div class="space-y-1">
          <h3 class="font-bold text-lg group-hover:text-brand-secondary transition-colors">Statistiche</h3>
          <p class="text-sm text-white/40">Monitora l'andamento della piattaforma.</p>
        </div>
      </RouterLink>
    </div>
  </div>
</template>
