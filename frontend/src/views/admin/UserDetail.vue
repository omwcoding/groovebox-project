<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/stores/api'
import BackButton from '@/components/BackButton.vue'
import DetailField from '@/components/DetailField.vue'

const route = useRoute()
const router = useRouter()

const user = ref(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const res = await api.get(`/users/${route.params.id}`)
    user.value = res.data
  } catch (err) {
    error.value = err.message || 'Utente non trovato'
  } finally {
    loading.value = false
  }
})

async function handleDelete() {
  if (!confirm(`Sei sicuro di voler eliminare definitivamente l'utente "${user.value.username}" e tutte le sue copie fisiche?`)) return
  try {
    await api.delete(`/users/${user.value.id_user}`)
    router.push('/users')
  } catch (err) {
    error.value = err.message || 'Errore durante l\'eliminazione'
  }
}
</script>

<template>
  <div class="space-y-6 animate-fade-in max-w-3xl mx-auto">
    <!-- Back button -->
    <BackButton />

    <div v-if="loading" class="py-20 flex flex-col items-center justify-center gap-4 opacity-40">
      <div class="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
      <p class="text-sm font-semibold tracking-widest uppercase">Caricamento</p>
    </div>
    
    <div v-else-if="error && !user" class="py-20 text-center text-rose-400 font-semibold">{{ error }}</div>

    <div v-else-if="user" class="glass-panel p-8 rounded-apple-2xl shadow-2xl border border-white/10 relative">
      <div v-if="error" class="mb-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold rounded-2xl px-4 py-3">
        {{ error }}
      </div>

      <!-- Header Profilo -->
      <div class="flex flex-col sm:flex-row items-center sm:items-start gap-6 pb-6 border-b border-white/5">
        <div class="w-20 h-20 bg-brand-secondary/15 border border-brand-secondary/20 rounded-full flex items-center justify-center text-[28px] font-bold text-brand-secondary shrink-0">
          {{ user.name?.charAt(0) }}{{ user.surname?.charAt(0) }}
        </div>
        
        <div class="min-w-0 flex-grow text-center sm:text-left space-y-1">
          <h1 class="text-3xl md:text-4xl font-extrabold tracking-tight bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
            {{ user.name }} {{ user.surname }}
          </h1>
          <p class="text-white/40 text-sm font-semibold tracking-tight">
            @{{ user.username }}
          </p>
        </div>
      </div>

      <!-- Informazioni dettagliate -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 py-6 border-b border-white/5 text-sm">
        <DetailField label="Nome" :value="user.name" />
        <DetailField label="Cognome" :value="user.surname" />
        <DetailField label="Indirizzo Email" :value="user.email" />
        <DetailField label="Ruolo Account">
          <span class="inline-flex px-3 py-1 bg-brand-secondary/15 border border-brand-secondary/20 text-brand-secondary text-xs font-bold rounded-full">
            {{ user.role }}
          </span>
        </DetailField>
      </div>

      <!-- Azioni Moderazione Admin -->
      <div class="flex gap-3 pt-6">
        <button @click="handleDelete"
          class="apple-button apple-button-secondary py-2.5 text-sm !text-brand-accent hover:!bg-brand-accent/10 hover:!border-brand-accent/25">
          Elimina definitamente
        </button>
      </div>
    </div>
  </div>
</template>
