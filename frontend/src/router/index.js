/**
 * Mint - Vue Router Configurazione
 * =====================================
 * Definisce le rotte applicative del frontend con caricamento lazy dei componenti
 * e implementa la guard di navigazione globale per il controllo degli accessi
 * basato sullo stato di autenticazione e sul ruolo dell'utente.
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const HomeView = () => import('@/views/dashboard/HomeView.vue')
const LoginView = () => import('@/views/auth/LoginView.vue')
const RegisterView = () => import('@/views/auth/RegisterView.vue')
const DashboardView = () => import('@/views/dashboard/DashboardView.vue')
const AlbumCatalog = () => import('@/views/catalog/AlbumCatalog.vue')
const AlbumDetail = () => import('@/views/catalog/AlbumDetail.vue')
const ArtistCatalog = () => import('@/views/catalog/ArtistCatalog.vue')
const ArtistDetail = () => import('@/views/catalog/ArtistDetail.vue')
const VaultView = () => import('@/views/vault/VaultView.vue')
const VaultDetail = () => import('@/views/vault/VaultDetail.vue')
const AdminDashboard = () => import('@/views/admin/AdminDashboard.vue')
const ProfileView = () => import('@/views/dashboard/ProfileView.vue')
const WishlistView = () => import('@/views/wishlist/WishlistView.vue')
const ProfileShareView = () => import('@/views/vault/ProfileShareView.vue')

const routes = [
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
  {
    path: '/search',
    name: 'search',
    component: AlbumCatalog,
    meta: { requiresAuth: true }
  },
  {
    path: '/albums',
    redirect: '/search'
  },
  {
    path: '/albums/:id',
    name: 'album-detail',
    component: AlbumDetail,
    meta: { requiresAuth: true }
  },
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
  {
    path: '/vault',
    name: 'vault',
    component: VaultView,
    meta: { requiresAuth: true, role: 'collector' }
  },
  {
    path: '/wishlist',
    name: 'wishlist',
    component: WishlistView,
    meta: { requiresAuth: true, role: 'collector' }
  },
  {
    path: '/vault/:id',
    name: 'vault-detail',
    component: VaultDetail,
    meta: { requiresAuth: true, role: 'collector' }
  },
  {
    path: '/share/:username',
    name: 'profile-share',
    component: ProfileShareView
  },
  {
    path: '/collection',
    redirect: '/vault'
  },
  {
    path: '/collection/:id',
    redirect: to => `/vault/${to.params.id}`
  },
  {
    path: '/admin',
    name: 'admin',
    component: AdminDashboard,
    meta: { requiresAuth: true, role: 'administrator' }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  // Controllo per rotte protette che richiedono autenticazione
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login' }
  }

  // Controllo autorizzativo basato sul ruolo dell'utente
  if (to.meta.role && authStore.user?.role !== to.meta.role) {
    return { name: 'dashboard' }
  }

  // Reindirizzamento degli utenti autenticati che tentano di accedere a pagine guest
  if (to.meta.guest && authStore.isAuthenticated) {
    return { name: 'dashboard' }
  }
})

export default router
