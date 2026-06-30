<script setup>
import { RouterView } from 'vue-router'
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppNavbar from '@/components/AppNavbar.vue'

const authStore = useAuthStore()

// Ripristina la sessione da localStorage al mount dell'applicazione
onMounted(() => {
  authStore.loadFromStorage()
})
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased">
    <AppNavbar v-if="authStore.isAuthenticated" />
    <main>
      <RouterView />
    </main>
  </div>
</template>
