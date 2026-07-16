<!--
Mint - Componente AppNavbar
==========================
Navbar dell'applicazione con gestione responsive. Adatta le voci di menu
visibili in base al ruolo dell'utente autenticato (Collector o Administrator).
-->

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
const mobileMenuOpen = ref(false)
const scrolled = ref(false)
const dropdownOpen = ref(false)

const handleScroll = () => {
  scrolled.value = window.scrollY > 20
}

function handleOutsideClick() {
  if (dropdownOpen.value) {
    dropdownOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  window.addEventListener('click', handleOutsideClick)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('click', handleOutsideClick)
})

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}

function toggleDropdown(e) {
  e.stopPropagation()
  dropdownOpen.value = !dropdownOpen.value
}

function closeDropdown() {
  dropdownOpen.value = false
}
</script>

<template>
  <header 
    class="fixed top-6 left-1/2 -translate-x-1/2 w-[92%] max-w-5xl z-[9999] transition-all duration-500"
    :class="{ 'top-3 w-[95%]': scrolled }"
  >
    <div class="glass-panel rounded-3xl md:rounded-full px-6 py-3 flex items-center justify-between shadow-2xl">
      
      <div class="flex items-center gap-8">
        <!-- Logo di Brand -->
        <RouterLink to="/dashboard" class="flex items-center gap-2 font-bold text-lg tracking-tight group">
          <div class="bg-brand-secondary/20 p-1.5 rounded-lg group-hover:rotate-12 transition-transform duration-300 shadow-md">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="text-brand-secondary"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></svg>
          </div>
          <span class="bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">Mint</span>
        </RouterLink>

        <!-- Menu di navigazione desktop -->
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
            to="/vault"
            class="px-4 py-2 rounded-full transition-all duration-300"
            :class="isActive('/vault') ? 'bg-white/10 text-white shadow-sm' : 'text-white/50 hover:text-white'"
          >
            Vault
          </RouterLink>

          <RouterLink
            v-if="authStore.isCollector"
            to="/wishlist"
            class="px-4 py-2 rounded-full transition-all duration-300"
            :class="isActive('/wishlist') ? 'bg-white/10 text-white shadow-sm' : 'text-white/50 hover:text-white'"
          >
            Wishlist
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
            to="/search"
            class="px-4 py-2 rounded-full transition-all duration-300"
            :class="isActive('/search') ? 'bg-white/10 text-white shadow-sm' : 'text-white/50 hover:text-white'"
          >
            Cerca
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

      <!-- Azioni utente desktop -->
      <div class="hidden md:flex items-center gap-4 relative">
        <button
          @click="toggleDropdown"
          class="flex items-center gap-2 px-3.5 py-1.5 bg-white/5 rounded-full border border-white/5 hover:bg-white/10 transition-all select-none cursor-pointer"
        >
          <img v-if="authStore.user?.avatar_path" :src="`/api/users/${authStore.user?.id_user}/avatar`" class="w-5 h-5 rounded-full object-cover" />
          <span v-else class="w-5 h-5 rounded-full bg-brand-secondary/20 flex items-center justify-center text-[10px] font-bold text-brand-secondary">
            {{ authStore.user?.name?.charAt(0) }}{{ authStore.user?.surname?.charAt(0) }}
          </span>
          <span class="text-xs font-semibold text-white/80 tracking-wide uppercase">{{ authStore.user?.username }}</span>
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="text-white/40 transition-transform duration-300" :class="{ 'rotate-180': dropdownOpen }"><polyline points="6 9 12 15 18 9"/></svg>
        </button>

        <!-- Dropdown Menu -->
        <transition name="fade">
          <div 
            v-if="dropdownOpen"
            class="absolute right-0 top-full mt-2 w-48 glass-panel !bg-brand-background/90 rounded-2xl py-2 border border-white/15 shadow-2xl z-[110]"
          >
            <RouterLink
              to="/profile"
              @click="closeDropdown"
              class="flex items-center gap-2.5 px-4 py-2.5 text-xs font-semibold text-white/60 hover:text-white hover:bg-white/5 transition-all"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="opacity-50"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              Il mio Profilo
            </RouterLink>
            <RouterLink
              to="/profile?edit=true"
              @click="closeDropdown"
              class="flex items-center gap-2.5 px-4 py-2.5 text-xs font-semibold text-white/60 hover:text-white hover:bg-white/5 transition-all"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="opacity-50"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
              Modifica Profilo
            </RouterLink>
            <hr class="border-white/5 my-1" />
            <button
              @click="handleLogout(); closeDropdown()"
              class="w-full flex items-center gap-2.5 px-4 py-2.5 text-xs font-semibold text-brand-accent hover:bg-brand-accent/5 transition-all text-left cursor-pointer"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="opacity-70"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
              Esci
            </button>
          </div>
        </transition>
      </div>

      <!-- Toggle menu responsive per dispositivi mobile -->
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

    <!-- Drawer mobile -->
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
          to="/vault" @click="mobileMenuOpen = false" 
          class="px-4 py-2.5 rounded-2xl hover:bg-white/5 transition text-sm font-semibold"
          :class="isActive('/vault') ? 'bg-white/10 text-white' : 'text-white/60'"
        >
          Il mio Vault
        </RouterLink>

        <RouterLink 
          v-if="authStore.isCollector"
          to="/wishlist" @click="mobileMenuOpen = false" 
          class="px-4 py-2.5 rounded-2xl hover:bg-white/5 transition text-sm font-semibold"
          :class="isActive('/wishlist') ? 'bg-white/10 text-white' : 'text-white/60'"
        >
          Wishlist
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
          to="/search" @click="mobileMenuOpen = false" 
          class="px-4 py-2.5 rounded-2xl hover:bg-white/5 transition text-sm font-semibold"
          :class="isActive('/search') ? 'bg-white/10 text-white' : 'text-white/60'"
        >
          Cerca musica
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
            <img v-if="authStore.user?.avatar_path" :src="`/api/users/${authStore.user?.id_user}/avatar`" class="w-6 h-6 rounded-full object-cover" />
            <span v-else class="w-6 h-6 rounded-full bg-brand-secondary/20 flex items-center justify-center text-[10px] font-bold text-brand-secondary">
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
