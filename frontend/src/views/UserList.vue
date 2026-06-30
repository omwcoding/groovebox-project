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
  <div class="p-6 md:p-8 max-w-5xl mx-auto">
    <div class="mb-6">
      <h1 class="text-3xl font-bold">Gestione Utenti</h1>
      <p class="text-slate-400 text-sm mt-1">{{ users.length }} collector registrati</p>
    </div>

    <div v-if="error" class="mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm rounded-lg px-4 py-3">
      {{ error }}
    </div>

    <div v-if="loading" class="text-center py-16 text-slate-400">Caricamento utenti...</div>

    <div v-else-if="users.length > 0" class="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-slate-800">
            <th class="text-left px-5 py-4 text-slate-400 font-medium">Utente</th>
            <th class="text-left px-5 py-4 text-slate-400 font-medium hidden sm:table-cell">Email</th>
            <th class="text-left px-5 py-4 text-slate-400 font-medium hidden md:table-cell">Ruolo</th>
            <th class="text-right px-5 py-4 text-slate-400 font-medium">Azioni</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id_user"
              class="border-b border-slate-800/50 last:border-0 hover:bg-slate-800/30 transition-colors">
            <td class="px-5 py-4">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-violet-600 flex items-center justify-center text-xs font-bold text-white shrink-0">
                  {{ user.name?.charAt(0) }}{{ user.surname?.charAt(0) }}
                </div>
                <div>
                  <p class="font-medium">{{ user.name }} {{ user.surname }}</p>
                  <p class="text-xs text-slate-500">@{{ user.username }}</p>
                </div>
              </div>
            </td>
            <td class="px-5 py-4 text-slate-400 hidden sm:table-cell">{{ user.email }}</td>
            <td class="px-5 py-4 hidden md:table-cell">
              <span class="px-2.5 py-1 bg-violet-500/10 border border-violet-500/30 text-violet-400 text-xs font-medium rounded-lg">
                {{ user.role }}
              </span>
            </td>
            <td class="px-5 py-4 text-right">
              <button @click="handleDeleteUser(user)"
                class="px-3 py-1.5 text-xs text-slate-400 hover:text-rose-400 border border-slate-700
                       hover:border-rose-500/30 rounded-lg transition-colors">
                Elimina
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="text-center py-16">
      <div class="text-5xl mb-4">&#128101;</div>
      <p class="text-slate-400">Nessun collector registrato.</p>
    </div>
  </div>
</template>
