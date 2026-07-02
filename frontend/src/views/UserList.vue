<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/stores/api'

const users = ref([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const res = await api.get('/users')
    users.value = res.data
  } catch (err) {
    error.value = err.message || 'Errore nel caricamento utenti'
  } finally {
    loading.value = false
  }
})

async function handleDeleteUser(user) {
  if (!confirm(`Eliminare l'utente "${user.username}" e tutti i suoi dati?`)) return
  try {
    await api.delete(`/users/${user.id_user}`)
    users.value = users.value.filter(u => u.id_user !== user.id_user)
  } catch (err) {
    error.value = err.message || 'Errore durante l\'eliminazione'
  }
}
</script>

<template>
  <div class="space-y-8 animate-fade-in">
    <div class="space-y-1">
      <h1 class="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
        Gestione Utenti
      </h1>
      <p class="text-white/40 text-lg font-medium">{{ users.length }} collezionisti registrati in piattaforma.</p>
    </div>

    <div v-if="error" class="mb-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold rounded-2xl px-4 py-3">
      {{ error }}
    </div>

    <div v-if="loading" class="py-20 flex flex-col items-center justify-center gap-4 opacity-40">
      <div class="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
      <p class="text-sm font-semibold tracking-widest uppercase">Caricamento</p>
    </div>

    <div v-else-if="users.length > 0" class="glass-panel rounded-apple-2xl overflow-hidden shadow-2xl">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-white/5 bg-white/[0.01]">
              <th class="text-left px-6 py-5 text-[10px] font-bold uppercase tracking-widest text-white/30">Profilo</th>
              <th class="text-left px-6 py-5 text-[10px] font-bold uppercase tracking-widest text-white/30 hidden sm:table-cell">Indirizzo Email</th>
              <th class="text-left px-6 py-5 text-[10px] font-bold uppercase tracking-widest text-white/30 hidden md:table-cell">Ruolo</th>
              <th class="text-right px-6 py-5 text-[10px] font-bold uppercase tracking-widest text-white/30">Moderazione</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id_user"
                class="border-b border-white/5 last:border-0 hover:bg-white/[0.02] transition-colors">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-full bg-brand-secondary/20 flex items-center justify-center text-xs font-bold text-brand-secondary shrink-0">
                    {{ user.name?.charAt(0) }}{{ user.surname?.charAt(0) }}
                  </div>
                  <div>
                    <p class="font-bold text-white/95">{{ user.name }} {{ user.surname }}</p>
                    <p class="text-xs text-white/30 font-medium">@{{ user.username }}</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 text-white/60 font-medium hidden sm:table-cell">{{ user.email }}</td>
              <td class="px-6 py-4 hidden md:table-cell">
                <span class="px-3 py-1 bg-brand-secondary/15 border border-brand-secondary/20 text-brand-secondary text-xs font-bold rounded-full">
                  {{ user.role }}
                </span>
              </td>
              <td class="px-6 py-4 text-right">
                <button @click="handleDeleteUser(user)"
                  class="px-4 py-2 text-xs font-bold uppercase tracking-widest text-brand-accent bg-brand-accent/5 border border-brand-accent/20 hover:bg-brand-accent/15 rounded-full transition-all">
                  Rimuovi
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else class="py-20 flex flex-col items-center justify-center gap-6 glass-panel rounded-apple-2xl border-dashed border-white/10 text-center px-10">
      <div class="bg-white/5 p-6 rounded-full">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="opacity-20"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
      </div>
      <div class="space-y-1">
        <p class="text-xl font-bold">Nessun utente registrato</p>
        <p class="text-white/40 text-sm">Non ci sono collector iscritti in questo momento.</p>
      </div>
    </div>
  </div>
</template>
