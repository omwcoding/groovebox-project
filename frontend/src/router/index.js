/**
 * GrooveBox — Vue Router
 *
 * Rotte derivate dall'albero di navigazione (doc 4.2).
 * Navigation guard per protezione rotte e controllo ruoli.
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// --- Views (Lazy Loaded for optimization) ---
import HomeView from '@/views/HomeView.vue'
import LoginView from '@/views/LoginView.vue'

const RegisterView = () => import('@/views/RegisterView.vue')
const DashboardView = () => import('@/views/DashboardView.vue')
const AlbumCatalog = () => import('@/views/AlbumCatalog.vue')
const AlbumDetail = () => import('@/views/AlbumDetail.vue')
const ArtistCatalog = () => import('@/views/ArtistCatalog.vue')
const ArtistDetail = () => import('@/views/ArtistDetail.vue')
const CollectionView = () => import('@/views/CollectionView.vue')
const CopyDetail = () => import('@/views/CopyDetail.vue')
const UserList = () => import('@/views/UserList.vue')
const UserDetail = () => import('@/views/UserDetail.vue')
const ProfileView = () => import('@/views/ProfileView.vue')
const StatsView = () => import('@/views/StatsView.vue')

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
    meta: { requiresAuth: true, role: 'administrator' }
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

  // Gestione Utenti — solo Admin (VE + VD)
  {
    path: '/users',
    name: 'users',
    component: UserList,
    meta: { requiresAuth: true, role: 'administrator' }
  },
  {
    path: '/users/:id',
    name: 'user-detail',
    component: UserDetail,
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
