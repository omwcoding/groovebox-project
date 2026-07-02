<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
const mobileMenuOpen = ref(false)
const scrolled = ref(false)

const handleScroll = () => {
  scrolled.value = window.scrollY > 20
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<template>
  <header 
    class="fixed top-6 left-1/2 -translate-x-1/2 w-[92%] max-w-5xl z-[100] transition-all duration-500"
    :class="{ 'top-3 w-[95%]': scrolled }"
  >
    <div class="glass-panel rounded-3xl md:rounded-full px-6 py-3 flex items-center justify-between shadow-2xl">
      
      <!-- Brand & Desktop Nav -->
      <div class="flex items-center gap-8">
        <!-- Logo -->
        <RouterLink to="/dashboard" class="flex items-center gap-2 font-bold text-lg tracking-tight group">
          <div class="bg-brand-secondary/20 p-1.5 rounded-lg group-hover:rotate-12 transition-transform duration-300 shadow-md">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="text-brand-secondary"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
          </div>
          <span class="bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">GrooveBox</span>
        </RouterLink>

        <!-- Links Desktop -->
        <nav class="hidden md:flex items-center gap-1.5 text-sm font-medium">
          <RouterLink
            to="/dashboard"
            class="px-4 py-2 rounded-full transition-all duration-300"
            :class="isActive('/dashboard') ? 'bg-white/10 text-white shadow-sm' : 'text-white/50 hover:text-white'"
          >
            Dashboard
          </RouterLink>
          
          <RouterLink
            v-if="authStore.isCollector"
            to="/collection"
            class="px-4 py-2 rounded-full transition-all duration-300"
            :class="isActive('/collection') ? 'bg-white/10 text-white shadow-sm' : 'text-white/50 hover:text-white'"
          >
            Libreria
          </RouterLink>

          <RouterLink
            v-if="authStore.isAdmin"
            to="/users"
            class="px-4 py-2 rounded-full transition-all duration-300"
            :class="isActive('/users') ? 'bg-white/10 text-white shadow-sm' : 'text-white/50 hover:text-white'"
          >
            Utenti
          </RouterLink>

          <RouterLink
            to="/albums"
            class="px-4 py-2 rounded-full transition-all duration-300"
            :class="isActive('/albums') ? 'bg-white/10 text-white shadow-sm' : 'text-white/50 hover:text-white'"
          >
            Album
          </RouterLink>

          <RouterLink
            v-if="authStore.isAdmin"
            to="/artists"
            class="px-4 py-2 rounded-full transition-all duration-300"
            :class="isActive('/artists') ? 'bg-white/10 text-white shadow-sm' : 'text-white/50 hover:text-white'"
          >
            Artisti
          </RouterLink>

          <RouterLink
            v-if="authStore.isAdmin"
            to="/stats"
            class="px-4 py-2 rounded-full transition-all duration-300"
            :class="isActive('/stats') ? 'bg-white/10 text-white shadow-sm' : 'text-white/50 hover:text-white'"
          >
            Statistiche
          </RouterLink>
        </nav>
      </div>

      <!-- Right Side Actions (Desktop) -->
      <div class="hidden md:flex items-center gap-4">
        <RouterLink
          to="/profile"
          class="flex items-center gap-2 px-3.5 py-1.5 bg-white/5 rounded-full border border-white/5 hover:bg-white/10 transition-all"
        >
          <span class="w-5 h-5 rounded-full bg-brand-secondary/20 flex items-center justify-center text-[10px] font-bold text-brand-secondary">
            {{ authStore.user?.name?.charAt(0) }}{{ authStore.user?.surname?.charAt(0) }}
          </span>
          <span class="text-xs font-semibold text-white/80 tracking-wide uppercase">{{ authStore.user?.username }}</span>
        </RouterLink>
        <button
          @click="handleLogout"
          class="text-xs font-bold text-white/40 hover:text-brand-accent transition-colors uppercase tracking-widest"
        >
          Esci
        </button>
      </div>

      <!-- Mobile Menu Toggle -->
      <button
        @click="mobileMenuOpen = !mobileMenuOpen"
        class="md:hidden p-1.5 text-white/70 hover:text-white hover:bg-white/5 rounded-xl transition-all"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line v-if="!mobileMenuOpen" x1="3" x2="21" y1="12" y2="12"/>
          <line v-if="!mobileMenuOpen" x1="3" x2="21" y1="6" y2="6"/>
          <line v-if="!mobileMenuOpen" x1="3" x2="21" y1="18" y2="18"/>
          <path v-else d="M18 6 6 18M6 6l12 12"/>
        </svg>
      </button>

    </div>

    <!-- Mobile Drawer -->
    <transition name="fade">
      <div 
        v-if="mobileMenuOpen" 
        class="md:hidden mt-3 glass-panel rounded-3xl p-4 flex flex-col gap-2 border border-white/10 shadow-2xl animate-fade-in"
      >
        <RouterLink 
          to="/dashboard" @click="mobileMenuOpen = false" 
          class="px-4 py-2.5 rounded-2xl hover:bg-white/5 transition text-sm font-semibold"
          :class="isActive('/dashboard') ? 'bg-white/10 text-white' : 'text-white/60'"
        >
          Dashboard
        </RouterLink>
        <RouterLink 
          v-if="authStore.isCollector"
          to="/collection" @click="mobileMenuOpen = false" 
          class="px-4 py-2.5 rounded-2xl hover:bg-white/5 transition text-sm font-semibold"
          :class="isActive('/collection') ? 'bg-white/10 text-white' : 'text-white/60'"
        >
          La mia collezione
        </RouterLink>
        <RouterLink 
          v-if="authStore.isAdmin"
          to="/users" @click="mobileMenuOpen = false" 
          class="px-4 py-2.5 rounded-2xl hover:bg-white/5 transition text-sm font-semibold"
          :class="isActive('/users') ? 'bg-white/10 text-white' : 'text-white/60'"
        >
          Gestione utenti
        </RouterLink>
        <RouterLink 
          to="/albums" @click="mobileMenuOpen = false" 
          class="px-4 py-2.5 rounded-2xl hover:bg-white/5 transition text-sm font-semibold"
          :class="isActive('/albums') ? 'bg-white/10 text-white' : 'text-white/60'"
        >
          Catalogo album
        </RouterLink>
        <RouterLink 
          v-if="authStore.isAdmin"
          to="/artists" @click="mobileMenuOpen = false" 
          class="px-4 py-2.5 rounded-2xl hover:bg-white/5 transition text-sm font-semibold"
          :class="isActive('/artists') ? 'bg-white/10 text-white' : 'text-white/60'"
        >
          Catalogo artisti
        </RouterLink>
        <RouterLink 
          v-if="authStore.isAdmin"
          to="/stats" @click="mobileMenuOpen = false" 
          class="px-4 py-2.5 rounded-2xl hover:bg-white/5 transition text-sm font-semibold"
          :class="isActive('/stats') ? 'bg-white/10 text-white' : 'text-white/60'"
        >
          Statistiche
        </RouterLink>
        <hr class="border-white/5 my-1" />
        <div class="flex items-center justify-between px-4 py-2.5">
          <RouterLink to="/profile" @click="mobileMenuOpen = false" class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-full bg-brand-secondary/20 flex items-center justify-center text-[10px] font-bold text-brand-secondary">
              {{ authStore.user?.name?.charAt(0) }}
            </span>
            <span class="text-sm font-semibold text-white/70">{{ authStore.user?.username }}</span>
          </RouterLink>
          <button @click="handleLogout(); mobileMenuOpen = false" class="text-xs font-bold text-brand-accent uppercase tracking-widest">
            Esci
          </button>
        </div>
      </div>
    </transition>
  </header>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
