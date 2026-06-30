/**
 * GrooveBox — Vue Router
 *
 * Rotte derivate dall'albero di navigazione (doc 4.2).
 * Navigation guard per protezione rotte e controllo ruoli.
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// --- Views ---
import HomeView from '@/views/HomeView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import DashboardView from '@/views/DashboardView.vue'
import AlbumCatalog from '@/views/AlbumCatalog.vue'
import AlbumDetail from '@/views/AlbumDetail.vue'
import ArtistCatalog from '@/views/ArtistCatalog.vue'
import ArtistDetail from '@/views/ArtistDetail.vue'
import CollectionView from '@/views/CollectionView.vue'
import CopyDetail from '@/views/CopyDetail.vue'
import UserList from '@/views/UserList.vue'
import ProfileView from '@/views/ProfileView.vue'
import StatsView from '@/views/StatsView.vue'

// --- Definizione rotte ---
const routes = [
  // Pagine pubbliche (guest)
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { guest: true }
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { guest: true }
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
    meta: { guest: true }
  },

  // Pagine autenticate (comuni)
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'profile',
    component: ProfileView,
    meta: { requiresAuth: true }
  },

  // Catalogo Album (VE + VD)
  {
    path: '/albums',
    name: 'albums',
    component: AlbumCatalog,
    meta: { requiresAuth: true }
  },
  {
    path: '/albums/:id',
    name: 'album-detail',
    component: AlbumDetail,
    meta: { requiresAuth: true }
  },

  // Catalogo Artisti (VE + VD)
  {
    path: '/artists',
    name: 'artists',
    component: ArtistCatalog,
    meta: { requiresAuth: true }
  },
  {
    path: '/artists/:id',
    name: 'artist-detail',
    component: ArtistDetail,
    meta: { requiresAuth: true }
  },

  // La Tua Collezione — solo Collector (VE + VD)
  {
    path: '/collection',
    name: 'collection',
    component: CollectionView,
    meta: { requiresAuth: true, role: 'collector' }
  },
  {
    path: '/collection/:id',
    name: 'copy-detail',
    component: CopyDetail,
    meta: { requiresAuth: true, role: 'collector' }
  },

  // Gestione Utenti — solo Admin (VE)
  {
    path: '/users',
    name: 'users',
    component: UserList,
    meta: { requiresAuth: true, role: 'administrator' }
  },

  // Statistiche e Report — solo Admin (VE)
  {
    path: '/stats',
    name: 'stats',
    component: StatsView,
    meta: { requiresAuth: true, role: 'administrator' }
  },

  // Catch-all: redirige alla home
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// --- Navigation Guard globale ---
router.beforeEach((to) => {
  const authStore = useAuthStore()

  // Se la rotta richiede autenticazione e l'utente non e' loggato
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login' }
  }

  // Se la rotta richiede un ruolo specifico
  if (to.meta.role && authStore.user?.role !== to.meta.role) {
    return { name: 'dashboard' }
  }

  // Se l'utente e' gia' loggato e visita pagine guest (login/register/home)
  if (to.meta.guest && authStore.isAuthenticated) {
    return { name: 'dashboard' }
  }
})

export default router
