<script setup>
import { ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const route = useRoute()
const mobileMenuOpen = ref(false)

function handleLogout() {
  authStore.logout()
  // Il navigation guard redirigera' automaticamente al login
}

/** Controlla se la rotta corrente inizia con il path dato. */
function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<template>
  <nav class="bg-slate-900/90 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6">
      <div class="flex items-center justify-between h-16">

        <!-- Logo -->
        <RouterLink to="/dashboard" class="flex items-center gap-2 shrink-0">
          <span class="text-xl">&#127926;</span>
          <span class="text-xl font-bold">
            Groove<span class="text-violet-400">Box</span>
          </span>
        </RouterLink>

        <!-- Links Desktop -->
        <div class="hidden md:flex items-center gap-1">
          <!-- Collector links -->
          <template v-if="authStore.isCollector">
            <RouterLink
              to="/collection"
              class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="isActive('/collection')
                ? 'text-violet-400 bg-violet-500/10'
                : 'text-slate-300 hover:text-white hover:bg-slate-800'"
            >
              La Mia Collezione
            </RouterLink>
          </template>

          <!-- Admin links -->
          <template v-if="authStore.isAdmin">
            <RouterLink
              to="/users"
              class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="isActive('/users')
                ? 'text-violet-400 bg-violet-500/10'
                : 'text-slate-300 hover:text-white hover:bg-slate-800'"
            >
              Utenti
            </RouterLink>
          </template>

          <!-- Links comuni -->
          <RouterLink
            to="/albums"
            class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="isActive('/albums')
              ? 'text-violet-400 bg-violet-500/10'
              : 'text-slate-300 hover:text-white hover:bg-slate-800'"
          >
            Album
          </RouterLink>

          <RouterLink
            to="/artists"
            class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="isActive('/artists')
              ? 'text-violet-400 bg-violet-500/10'
              : 'text-slate-300 hover:text-white hover:bg-slate-800'"
          >
            Artisti
          </RouterLink>

          <!-- Admin: Statistiche -->
          <template v-if="authStore.isAdmin">
            <RouterLink
              to="/stats"
              class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="isActive('/stats')
                ? 'text-violet-400 bg-violet-500/10'
                : 'text-slate-300 hover:text-white hover:bg-slate-800'"
            >
              Statistiche
            </RouterLink>
          </template>
        </div>

        <!-- User Menu Desktop -->
        <div class="hidden md:flex items-center gap-3">
          <RouterLink
            to="/profile"
            class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm
                   text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <span class="w-7 h-7 rounded-full bg-violet-600 flex items-center justify-center
                         text-xs font-bold text-white">
              {{ authStore.user?.name?.charAt(0) }}{{ authStore.user?.surname?.charAt(0) }}
            </span>
            <span>{{ authStore.user?.username }}</span>
          </RouterLink>
          <button
            @click="handleLogout"
            class="px-3 py-1.5 rounded-lg text-sm text-slate-400 hover:text-rose-400
                   hover:bg-slate-800 transition-colors"
          >
            Esci
          </button>
        </div>

        <!-- Mobile Menu Toggle -->
        <button
          @click="mobileMenuOpen = !mobileMenuOpen"
          class="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              v-if="!mobileMenuOpen"
              stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 6h16M4 12h16M4 18h16"
            />
            <path
              v-else
              stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <!-- Mobile Menu -->
      <div v-if="mobileMenuOpen" class="md:hidden pb-4 space-y-1">
        <template v-if="authStore.isCollector">
          <RouterLink
            to="/collection" @click="mobileMenuOpen = false"
            class="block px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800"
          >
            La Mia Collezione
          </RouterLink>
        </template>
        <template v-if="authStore.isAdmin">
          <RouterLink
            to="/users" @click="mobileMenuOpen = false"
            class="block px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800"
          >
            Utenti
          </RouterLink>
        </template>
        <RouterLink
          to="/albums" @click="mobileMenuOpen = false"
          class="block px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800"
        >
          Album
        </RouterLink>
        <RouterLink
          to="/artists" @click="mobileMenuOpen = false"
          class="block px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800"
        >
          Artisti
        </RouterLink>
        <template v-if="authStore.isAdmin">
          <RouterLink
            to="/stats" @click="mobileMenuOpen = false"
            class="block px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800"
          >
            Statistiche
          </RouterLink>
        </template>
        <hr class="border-slate-800 my-2" />
        <RouterLink
          to="/profile" @click="mobileMenuOpen = false"
          class="block px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800"
        >
          Profilo
        </RouterLink>
        <button
          @click="handleLogout(); mobileMenuOpen = false"
          class="w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-rose-400 hover:bg-slate-800"
        >
          Esci
        </button>
      </div>
    </div>
  </nav>
</template>
