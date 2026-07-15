<script setup>
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppNavbar from '@/components/AppNavbar.vue'

const authStore = useAuthStore()
</script>

<template>
  <div class="min-h-screen bg-brand-background text-brand-foreground font-sans selection:bg-brand-secondary selection:text-white overflow-x-hidden antialiased flex flex-col">

    <main 
      class="w-full flex-grow flex flex-col"
      :class="{ 'pt-28 pb-20 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto': authStore.isAuthenticated }"
    >
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>
    <AppNavbar v-if="authStore.isAuthenticated" />
  </div>
</template>
