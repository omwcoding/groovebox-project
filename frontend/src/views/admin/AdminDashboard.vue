<!--
Mint - Pannello Amministrazione Unificato (AdminDashboard)
============================================================
Pannello di controllo per la moderazione degli utenti, gestione segnalazioni,
insights di business con export, monitoraggio tecnico e manutenzione cache.
-->
<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { api } from '@/stores/api'

const route = useRoute()
const activeTab = ref(route.query.tab || 'reports') // 'reports' | 'users' | 'insights' | 'technical'

watch(() => route.query.tab, (newTab) => {
  if (newTab) {
    activeTab.value = newTab
  }
})

const loading = ref(false)
const error = ref('')
const message = ref('')

// Data States
const reports = ref([])
const users = ref([])
const technicalStats = ref(null)
const businessStats = ref(null)
const auditLogs = ref([])

// Detail Modal States
const selectedUser = ref(null)
const loadingUserDetail = ref(false)
const userDetailData = ref(null)

// Confirmation Modal States
const showConfirmModal = ref(false)
const confirmMessage = ref('')
const confirmAction = ref(null)

// Filters & Search
const searchUserQuery = ref('')

// Computed Reports Sorting & Filtering
const sortedReports = computed(() => {
  return [...reports.value].sort((a, b) => {
    if (a.status === 'pending' && b.status !== 'pending') return -1
    if (a.status !== 'pending' && b.status === 'pending') return 1
    return new Date(b.created_at) - new Date(a.created_at)
  })
})

const filteredReports = computed(() => {
  return sortedReports.value
})

onMounted(() => {
  fetchData()
})

async function fetchData() {
  loading.value = true
  error.value = ''
  try {
    const [repRes, usrRes, techRes, bizRes, auditRes] = await Promise.all([
      api.get('/admin/reports'),
      api.get('/admin/users'),
      api.get('/admin/stats/technical'),
      api.get('/admin/stats/business'),
      api.get('/admin/audit-logs')
    ])
    
    reports.value = repRes.data || []
    users.value = usrRes.data || []
    technicalStats.value = techRes.data || null
    businessStats.value = bizRes.data || null
    auditLogs.value = auditRes.data || []
  } catch (err) {
    error.value = err.message || "Errore nel caricamento dei dati di amministrazione."
  } finally {
    loading.value = false
  }
}

// User Actions
async function toggleBan(user) {
  try {
    const res = await api.put(`/admin/users/${user.id_user}/ban`)
    user.is_banned = res.data.is_banned
    message.value = res.message || "Stato utente aggiornato."
    setTimeout(() => message.value = '', 3000)
    // Reload audit logs
    const auditRes = await api.get('/admin/audit-logs')
    auditLogs.value = auditRes.data || []
  } catch (err) {
    error.value = err.message || "Impossibile aggiornare lo stato dell'utente."
  }
}

async function openUserDetail(user) {
  selectedUser.value = user
  userDetailData.value = null
  loadingUserDetail.value = true
  try {
    const res = await api.get(`/users/${user.id_user}`)
    userDetailData.value = res.data
  } catch (err) {
    error.value = err.message || "Impossibile recuperare i dettagli dell'utente."
  } finally {
    loadingUserDetail.value = false
  }
}

function closeUserDetail() {
  selectedUser.value = null
  userDetailData.value = null
}

async function toggleBanInModal() {
  if (!userDetailData.value) return
  const user = userDetailData.value
  await toggleBan(user)
  const listUser = users.value.find(u => u.id_user === user.id_user)
  if (listUser) {
    listUser.is_banned = user.is_banned
  }
}

async function adminWipeBio(userId) {
  try {
    const res = await api.put(`/admin/users/${userId}/wipe-bio`)
    message.value = res.message || "Biografia azzerata."
    setTimeout(() => message.value = '', 3000)
    if (userDetailData.value && userDetailData.value.id_user === userId) {
      userDetailData.value.bio = null
    }
    const auditRes = await api.get('/admin/audit-logs')
    auditLogs.value = auditRes.data || []
  } catch (err) {
    error.value = err.message || "Impossibile azzerare la biografia."
  }
}

async function adminWipeAvatar(userId) {
  try {
    const res = await api.put(`/admin/users/${userId}/wipe-avatar`)
    message.value = res.message || "Foto profilo rimossa."
    setTimeout(() => message.value = '', 3000)
    if (userDetailData.value && userDetailData.value.id_user === userId) {
      userDetailData.value.avatar_path = null
    }
    const auditRes = await api.get('/admin/audit-logs')
    auditLogs.value = auditRes.data || []
  } catch (err) {
    error.value = err.message || "Impossibile rimuovere la foto profilo."
  }
}

function triggerConfirm(messageText, actionCallback) {
  confirmMessage.value = messageText
  confirmAction.value = actionCallback
  showConfirmModal.value = true
}

function runConfirmedAction() {
  if (confirmAction.value) {
    confirmAction.value()
  }
  showConfirmModal.value = false
  confirmAction.value = null
}

// Report Actions
async function resolveReport(reportId, action) {
  try {
    const res = await api.put(`/admin/reports/${reportId}/resolve`, { action })
    message.value = res.message || "Segnalazione risolta con successo."
    setTimeout(() => message.value = '', 3000)
    
    // Refresh all data
    await fetchData()
  } catch (err) {
    error.value = err.message || "Impossibile risolvere la segnalazione."
  }
}

// Maintenance Actions
const cleaningCache = ref(false)
async function triggerCacheCleanup() {
  if (cleaningCache.value) return
  cleaningCache.value = true
  try {
    const res = await api.post('/admin/maintenance/refresh-expired-cache')
    message.value = res.message || "Pulizia cache completata."
    setTimeout(() => message.value = '', 3000)
    
    // Refresh technical stats & audit logs
    const [techRes, auditRes] = await Promise.all([
      api.get('/admin/stats/technical'),
      api.get('/admin/audit-logs')
    ])
    technicalStats.value = techRes.data || null
    auditLogs.value = auditRes.data || []
  } catch (err) {
    error.value = err.message || "Errore durante la pulizia della cache."
  } finally {
    cleaningCache.value = false
  }
}

// Export Business Data
function exportBusinessData() {
  if (!businessStats.value) return
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(businessStats.value, null, 4))
  const downloadAnchor = document.createElement('a')
  downloadAnchor.setAttribute("href", dataStr)
  downloadAnchor.setAttribute("download", `mint_business_insights_${new Date().toISOString().slice(0,10)}.json`)
  document.body.appendChild(downloadAnchor)
  downloadAnchor.click()
  downloadAnchor.remove()
}

// Computed Filtered Users
const filteredUsers = computed(() => {
  const query = searchUserQuery.value.toLowerCase().trim()
  if (!query) return users.value
  return users.value.filter(u => 
    u.username.toLowerCase().includes(query) ||
    u.email.toLowerCase().includes(query) ||
    `${u.name} ${u.surname}`.toLowerCase().includes(query)
  )
})

// Formatting dates
function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="space-y-8 animate-fade-in pb-20">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-6">
      <div class="space-y-1">
        <h1 class="text-4xl font-black tracking-tight text-white/95 bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">
          Pannello di Amministrazione
        </h1>
        <p class="text-sm text-white/40 font-medium">
          Mint Condition V2 &middot; Gestisci la community, monitora l'infrastruttura e ottieni statistiche di mercato.
        </p>
      </div>
      <button 
        @click="fetchData" 
        :disabled="loading"
        class="self-start md:self-center px-4 py-2 bg-white/5 border border-white/10 hover:bg-white/10 text-white/80 rounded-2xl text-xs font-semibold tracking-wide transition-all cursor-pointer flex items-center gap-1.5 shadow-md"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" :class="{ 'animate-spin': loading }"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
        Ricarica Dati
      </button>
    </div>

    <!-- Banner dei Messaggi -->
    <transition name="fade">
      <div v-if="message" class="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm rounded-2xl shadow-lg">
        {{ message }}
      </div>
    </transition>

    <div v-if="error" class="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm rounded-2xl shadow-lg">
      {{ error }}
    </div>

    <!-- Navigation Tabs -->
    <div class="flex border-b border-white/5 p-1 bg-white/5 rounded-2xl max-w-2xl">
      <button 
        @click="activeTab = 'reports'"
        :class="activeTab === 'reports' ? 'bg-white/10 text-white shadow-lg' : 'text-white/40 hover:text-white/60'"
        class="flex-1 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer"
      >
        Segnalazioni
        <span v-if="reports.filter(r => r.status === 'pending').length > 0" class="px-2 py-0.5 bg-rose-500 text-white text-[9px] font-black rounded-full">
          {{ reports.filter(r => r.status === 'pending').length }}
        </span>
      </button>
      <button 
        @click="activeTab = 'users'"
        :class="activeTab === 'users' ? 'bg-white/10 text-white shadow-lg' : 'text-white/40 hover:text-white/60'"
        class="flex-1 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer"
      >
        Utenti
      </button>
      <button 
        @click="activeTab = 'insights'"
        :class="activeTab === 'insights' ? 'bg-white/10 text-white shadow-lg' : 'text-white/40 hover:text-white/60'"
        class="flex-1 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer"
      >
        Insights & Export
      </button>
      <button 
        @click="activeTab = 'technical'"
        :class="activeTab === 'technical' ? 'bg-white/10 text-white shadow-lg' : 'text-white/40 hover:text-white/60'"
        class="flex-1 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer"
      >
        Stato Tecnico
      </button>
    </div>

    <LoadingSpinner v-if="loading && !reports.length && !users.length" />

    <!-- Views Container -->
    <div v-else class="space-y-6">
      
      <!-- TAB 1: SEGNALAZIONI -->
      <div v-if="activeTab === 'reports'" class="space-y-4 animate-fade-in">
        
        <div v-if="filteredReports.length === 0" class="text-center py-20 text-white/30 italic glass-panel rounded-3xl">
          Nessuna segnalazione trovata.
        </div>
        <div v-else class="grid grid-cols-1 gap-4">
          <div 
            v-for="rep in filteredReports" 
            :key="rep.id_report" 
            class="glass-panel p-5 border rounded-3xl flex flex-col md:flex-row justify-between md:items-center gap-4 transition-all duration-300"
            :class="rep.status === 'pending' ? 'border-white/10 bg-white/[0.02]' : 'border-white/5 opacity-50 bg-black/20'"
          >
            <div class="space-y-3 flex-grow">
              <div class="flex items-center gap-3">
                <span class="px-2.5 py-1 text-[9px] font-black uppercase tracking-wider rounded" :class="{
                  'bg-rose-500/20 text-rose-400 border border-rose-500/30': rep.status === 'pending',
                  'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30': rep.status === 'resolved',
                  'bg-white/5 text-white/40 border border-white/10': rep.status === 'dismissed'
                }">
                  {{ rep.status }}
                </span>
                <span class="px-2.5 py-1 text-[9px] font-black uppercase tracking-wider rounded border" :class="{
                  'bg-purple-500/15 border-purple-500/30 text-purple-400': rep.category === 'avatar',
                  'bg-amber-500/15 border-amber-500/30 text-amber-400': rep.category === 'bio',
                  'bg-rose-500/15 border-rose-500/30 text-rose-400': rep.category === 'username',
                  'bg-red-500/15 border-red-500/30 text-red-400': rep.category === 'spam',
                  'bg-white/5 border-white/10 text-white/60': rep.category === 'other'
                }">
                  {{ rep.category }}
                </span>
                <span class="text-xs text-white/30">{{ formatDate(rep.created_at) }}</span>
              </div>
              <p class="text-sm font-semibold text-white/80">
                L'utente <span class="text-white font-bold">@{{ rep.reporter_username }}</span> ha segnalato <span class="text-white font-bold">@{{ rep.reported_username }}</span>
              </p>
              
              <p v-if="rep.details" class="text-xs text-white/50 bg-white/5 p-3 rounded-2xl italic leading-relaxed border border-white/5">
                Nota segnalazione: "{{ rep.details }}"
              </p>

              <!-- Evidenziazione per segnalazione Username -->
              <div v-if="rep.status === 'pending' && rep.category === 'username'" class="mt-2.5 space-y-1">
                <span class="text-[9px] font-black uppercase tracking-wider text-white/30">Nome utente da moderare</span>
                <div>
                  <div class="px-3 py-2 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-bold font-mono rounded-xl inline-flex items-center gap-1.5 shadow-sm">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                    @{{ rep.reported_username }}
                  </div>
                </div>
              </div>

              <!-- Contenuto Attuale Segnalato -->
              <div v-if="rep.status === 'pending' && (rep.category === 'bio' || rep.category === 'avatar')" class="mt-2.5 space-y-2">
                <div v-if="rep.category === 'bio'" class="space-y-1">
                  <span class="text-[9px] font-black uppercase tracking-wider text-white/30">Biografia attuale da moderare</span>
                  <blockquote class="text-xs text-white/80 italic font-mono bg-white/5 p-3 rounded-xl border border-white/5 leading-relaxed">
                    "{{ rep.reported_bio || '(Vuota)' }}"
                  </blockquote>
                </div>
                
                <div v-else-if="rep.category === 'avatar'" class="space-y-1">
                  <span class="text-[9px] font-black uppercase tracking-wider text-white/30">Avatar attuale da moderare</span>
                  <div class="flex items-center gap-3">
                    <img v-if="rep.reported_avatar_path" :src="`/api/users/${rep.id_reported}/avatar`" class="w-16 h-16 rounded-full object-cover border border-white/10 shadow-lg" />
                    <span v-else class="text-white/40 italic text-xs">(Nessun avatar impostato)</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Azioni segnalazione -->
            <div v-if="rep.status === 'pending'" class="flex flex-wrap md:flex-nowrap gap-2 shrink-0 md:self-center">
              <button 
                @click="openUserDetail({ id_user: rep.id_reported, username: rep.reported_username })"
                class="px-3.5 py-2 border border-brand-secondary/30 hover:bg-brand-secondary/15 text-brand-secondary rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 shadow-sm"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                Vedi Profilo
              </button>
              <button 
                @click="resolveReport(rep.id_report, 'dismiss')"
                class="px-3.5 py-2 border border-white/10 hover:bg-white/10 text-white/70 rounded-xl text-xs font-bold transition-all cursor-pointer"
              >
                Archivia
              </button>
              <button 
                v-if="rep.category === 'bio'"
                @click="triggerConfirm('Sei sicuro di voler azzerare la biografia di @' + rep.reported_username + '?', () => resolveReport(rep.id_report, 'wipe_bio'))"
                class="px-3.5 py-2 border border-yellow-500/20 hover:bg-yellow-500/15 text-yellow-400 rounded-xl text-xs font-bold transition-all cursor-pointer"
              >
                Azzera Bio
              </button>
              <button 
                v-if="rep.category === 'avatar'"
                @click="triggerConfirm('Sei sicuro di voler rimuovere la foto profilo di @' + rep.reported_username + '?', () => resolveReport(rep.id_report, 'wipe_avatar'))"
                class="px-3.5 py-2 border border-yellow-500/20 hover:bg-yellow-500/15 text-yellow-400 rounded-xl text-xs font-bold transition-all cursor-pointer"
              >
                Rimuovi Foto
              </button>
              <button 
                @click="triggerConfirm('Sei sicuro di voler sospendere permanentemente l\'utente @' + rep.reported_username + '?', () => resolveReport(rep.id_report, 'ban'))"
                class="px-3.5 py-2 bg-rose-500 hover:bg-rose-600 text-white rounded-xl text-xs font-bold transition-all cursor-pointer shadow-md"
              >
                Ban Utente
              </button>
            </div>
            <div v-else class="text-xs text-white/30 italic shrink-0 self-end md:self-center">
              Risolta il {{ formatDate(rep.resolved_at) }}
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 2: UTENTI -->
      <div v-if="activeTab === 'users'" class="space-y-4 animate-fade-in">
        <!-- Search bar -->
        <div class="relative w-full max-w-md">
          <input 
            v-model="searchUserQuery" 
            type="text" 
            placeholder="Cerca utente per username, nome o email..." 
            class="apple-input !pl-10 !py-3 text-sm" 
          />
          <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/20">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          </span>
        </div>

        <div class="glass-panel overflow-x-auto rounded-3xl border border-white/10">
          <table class="w-full text-left border-collapse text-sm min-w-[600px]">
            <thead>
              <tr class="border-b border-white/10 text-white/40 font-semibold text-xs uppercase tracking-wider">
                <th class="px-6 py-4">Username</th>
                <th class="px-6 py-4">Nome completo</th>
                <th class="px-6 py-4">Email</th>
                <th class="px-6 py-4">Stato</th>
                <th class="px-6 py-4 text-right">Azioni</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="u in filteredUsers" 
                :key="u.id_user" 
                class="border-b border-white/5 hover:bg-white/[0.02] transition-colors"
                :class="{ 'opacity-50 bg-black/10': u.is_banned }"
              >
                <td class="px-6 py-4 font-bold text-white/95">@{{ u.username }}</td>
                <td class="px-6 py-4 text-white/70">{{ u.name }} {{ u.surname }}</td>
                <td class="px-6 py-4 text-white/60 font-mono text-xs">{{ u.email }}</td>
                <td class="px-6 py-4">
                  <span class="px-2 py-0.5 text-[9px] font-black uppercase tracking-wider rounded" :class="u.is_banned ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'">
                    {{ u.is_banned ? 'Bannato' : 'Attivo' }}
                  </span>
                </td>
                <td class="px-6 py-4 text-right">
                  <button 
                    @click="openUserDetail(u)"
                    class="px-3.5 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white/80 rounded-lg text-xs font-bold transition-all cursor-pointer shadow-md flex items-center gap-1.5 ml-auto"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                    Vedi
                  </button>
                </td>
              </tr>
              <tr v-if="filteredUsers.length === 0">
                <td colspan="5" class="px-6 py-12 text-center text-white/30 italic">Nessun utente corrisponde ai criteri.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- TAB 3: INSIGHTS & EXPORT -->
      <div v-if="activeTab === 'insights'" class="space-y-6 animate-fade-in">
        <div v-if="!businessStats" class="text-center py-20 text-white/30 italic">Caricamento statistiche di mercato...</div>
        <template v-else>
          <!-- Totali rapidi -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="glass-panel p-5 border border-white/10 rounded-3xl space-y-1">
              <span class="text-[10px] font-black uppercase tracking-wider text-white/40">Collector iscritti</span>
              <p class="text-4xl font-black text-white/95">{{ businessStats.totals.users }}</p>
            </div>
            <div class="glass-panel p-5 border border-white/10 rounded-3xl space-y-1">
              <span class="text-[10px] font-black uppercase tracking-wider text-white/40">Album a catalogo</span>
              <p class="text-4xl font-black text-white/95">{{ businessStats.totals.albums }}</p>
            </div>
            <div class="glass-panel p-5 border border-white/10 rounded-3xl space-y-1">
              <span class="text-[10px] font-black uppercase tracking-wider text-white/40">Artisti unici</span>
              <p class="text-4xl font-black text-white/95">{{ businessStats.totals.artists }}</p>
            </div>
            <div class="glass-panel p-5 border border-white/10 rounded-3xl space-y-1">
              <span class="text-[10px] font-black uppercase tracking-wider text-white/40">Copie fisiche totali</span>
              <p class="text-4xl font-black text-white/95">{{ businessStats.totals.physical_copies }}</p>
            </div>
          </div>

          <!-- Distribuzioni e Top lists -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Formati più diffusi -->
            <div class="glass-panel p-6 border border-white/10 rounded-3xl space-y-4">
              <h3 class="font-bold text-white/90 text-sm uppercase tracking-wider border-b border-white/5 pb-3">Distribuzione supporti</h3>
              <div class="space-y-3">
                <div v-for="f in businessStats.formats_distribution" :key="f.format" class="space-y-1">
                  <div class="flex justify-between text-xs font-semibold">
                    <span class="text-white/80">{{ f.format }}</span>
                    <span class="text-white/50">{{ f.count }} copie ({{ ((f.count / (businessStats.totals.physical_copies || 1)) * 100).toFixed(0) }}%)</span>
                  </div>
                  <div class="w-full bg-white/5 h-2 rounded-full overflow-hidden border border-white/5">
                    <div class="bg-brand-secondary h-full rounded-full" :style="{ width: ((f.count / (businessStats.totals.physical_copies || 1)) * 100) + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Generi Trend -->
            <div class="glass-panel p-6 border border-white/10 rounded-3xl space-y-4">
              <h3 class="font-bold text-white/90 text-sm uppercase tracking-wider border-b border-white/5 pb-3">Generi di Tendenza</h3>
              <div class="space-y-3">
                <div v-for="g in businessStats.genres_distribution" :key="g.genre" class="space-y-1">
                  <div class="flex justify-between text-xs font-semibold">
                    <span class="text-white/85 truncate max-w-[200px]">{{ g.genre }}</span>
                    <span class="text-white/50">{{ g.count }} dischi</span>
                  </div>
                  <div class="w-full bg-white/5 h-2 rounded-full overflow-hidden border border-white/5">
                    <div class="bg-brand-secondary/85 h-full rounded-full" :style="{ width: ((g.count / (businessStats.totals.albums || 1)) * 100) + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Top Album in Vault -->
            <div class="glass-panel p-6 border border-white/10 rounded-3xl space-y-3">
              <h3 class="font-bold text-white/90 text-sm uppercase tracking-wider border-b border-white/5 pb-3">Top 10 Album più collezionati</h3>
              <ul class="divide-y divide-white/5 text-xs">
                <li v-for="(album, idx) in businessStats.top_collected_albums" :key="album.id_album" class="py-2.5 flex justify-between">
                  <span class="font-semibold text-white/80">{{ idx + 1 }}. {{ album.title }}</span>
                  <span class="text-white/40">{{ album.copies_count }} copie nel Vault</span>
                </li>
                <li v-if="businessStats.top_collected_albums.length === 0" class="py-4 text-center text-white/30 italic">Nessun dato.</li>
              </ul>
            </div>

            <!-- Sezione Export Dati -->
            <div class="glass-panel p-6 border border-white/10 rounded-3xl flex flex-col justify-between gap-6 bg-gradient-to-br from-brand-secondary/5 to-transparent">
              <div class="space-y-2">
                <h3 class="font-bold text-white/90 text-sm uppercase tracking-wider">Esportazione Insights di Mercato</h3>
                <p class="text-xs text-white/50 leading-relaxed">
                  Genera ed esporta i report statistici aggregati in formato JSON. Questi dati sono pronti per analisi commerciali di tendenza o condivisioni con le case discografiche.
                </p>
              </div>
              <button 
                @click="exportBusinessData"
                class="w-full py-3.5 bg-brand-secondary text-white hover:bg-brand-secondary/90 rounded-2xl text-xs font-bold transition-all cursor-pointer flex items-center justify-center gap-2 shadow-lg"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                Esporta Insights (JSON)
              </button>
            </div>
          </div>
        </template>
      </div>

      <!-- TAB 4: STATO TECNICO & CACHE -->
      <div v-if="activeTab === 'technical'" class="space-y-6 animate-fade-in">
        <div v-if="!technicalStats" class="text-center py-20 text-white/30 italic">Caricamento statistiche tecniche...</div>
        <template v-else>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            <!-- Limiti API Discogs -->
            <div class="glass-panel p-6 border border-white/10 rounded-3xl space-y-4 flex flex-col justify-between">
              <div class="space-y-2">
                <h3 class="font-bold text-white/90 text-sm uppercase tracking-wider">API Rate Limit (Discogs)</h3>
                <p class="text-xs text-white/40 leading-relaxed">Stato dei limiti di chiamata imposti da Discogs (Max 60 req/min).</p>
              </div>
              
              <div class="flex flex-col items-center justify-center py-4 space-y-2">
                <div class="text-5xl font-black text-white/90">
                  {{ technicalStats.discogs_api.remaining }}
                </div>
                <div class="text-[10px] text-white/40 uppercase tracking-widest font-semibold">
                  su {{ technicalStats.discogs_api.limit }} rimaste
                </div>
              </div>

              <!-- Barra di avanzamento colorata -->
              <div class="w-full bg-white/5 h-1.5 rounded-full overflow-hidden border border-white/5">
                <div 
                  class="h-full rounded-full transition-all duration-500" 
                  :class="technicalStats.discogs_api.remaining < 15 ? 'bg-rose-500' : 'bg-emerald-400'"
                  :style="{ width: ((technicalStats.discogs_api.remaining / technicalStats.discogs_api.limit) * 100) + '%' }"
                ></div>
              </div>
            </div>

            <!-- Stato Cache e Storage -->
            <div class="glass-panel p-6 border border-white/10 rounded-3xl space-y-4 flex flex-col justify-between">
              <div class="space-y-2">
                <h3 class="font-bold text-white/90 text-sm uppercase tracking-wider">Cache & Files Storage</h3>
                <p class="text-xs text-white/40 leading-relaxed">Conteggio delle risposte API memorizzate e file custoditi su Supabase Storage.</p>
              </div>

              <div class="space-y-2 text-xs font-semibold text-white/80">
                <div class="flex justify-between py-1.5 border-b border-white/5">
                  <span class="text-white/50">Risposte API in Cache:</span>
                  <span>{{ technicalStats.cache.total_entries }} record</span>
                </div>
                <div class="flex justify-between py-1.5 border-b border-white/5">
                  <span class="text-white/50">Avatar Utenti:</span>
                  <span>{{ technicalStats.storage_files.avatars }} files</span>
                </div>
                <div class="flex justify-between py-1.5 border-b border-white/5">
                  <span class="text-white/50">Copertine Album:</span>
                  <span>{{ technicalStats.storage_files.covers }} files</span>
                </div>
              </div>
              
              <button 
                @click="triggerCacheCleanup"
                :disabled="cleaningCache"
                class="w-full py-2.5 border border-yellow-500/20 hover:bg-yellow-500/10 text-yellow-400 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center justify-center gap-1.5 shadow-md"
              >
                <span v-if="cleaningCache" class="border-2 border-yellow-400/20 border-t-yellow-400 w-3 h-3 rounded-full animate-spin"></span>
                Pulisci Cache Scaduta (>30g)
              </button>
            </div>

            <!-- Audit Log Summary -->
            <div class="glass-panel p-6 border border-white/10 rounded-3xl space-y-4 md:col-span-1">
              <div class="space-y-1">
                <h3 class="font-bold text-white/90 text-sm uppercase tracking-wider">Registro Attività (Audit Logs)</h3>
                <p class="text-xs text-white/40">Ultime azioni di moderazione eseguite sulla piattaforma.</p>
              </div>

              <div class="h-44 overflow-y-auto pr-1 space-y-2.5 text-[10px] leading-relaxed select-none">
                <div v-for="log in auditLogs.slice(0, 10)" :key="log.id_log" class="p-2.5 bg-white/[0.02] border border-white/5 rounded-xl space-y-1">
                  <div class="flex justify-between font-bold text-white/50">
                    <span>@{{ log.admin_username }}</span>
                    <span>{{ formatDate(log.created_at) }}</span>
                  </div>
                  <p class="text-white/80 font-medium">{{ log.details }}</p>
                </div>
                <div v-if="auditLogs.length === 0" class="text-center py-10 text-white/20 italic">Nessun log registrato.</div>
              </div>
            </div>

          </div>
        </template>
      </div>

    </div>

    <!-- Modale Dettagli Utente per Moderazione -->
    <transition name="fade">
      <div v-if="selectedUser" class="fixed inset-0 bg-black/60 backdrop-blur-md z-[10000] flex items-center justify-center p-4">
        <div class="glass-panel max-w-md w-full p-6 space-y-6 border border-white/10 rounded-3xl relative animate-fade-in shadow-2xl">
          <button 
            @click="closeUserDetail" 
            class="absolute top-4 right-4 text-white/40 hover:text-white cursor-pointer"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" x2="6" y1="6" y2="18"/><line x1="6" x2="18" y1="6" y2="18"/></svg>
          </button>
          
          <div class="space-y-1">
            <h3 class="text-xl font-bold text-white/90">Dettagli Collector</h3>
            <p class="text-xs text-white/40">Visualizza informazioni ed effettua operazioni di moderazione.</p>
          </div>

          <div v-if="loadingUserDetail" class="flex justify-center py-10">
            <span class="border-2 border-white/20 border-t-white w-6 h-6 rounded-full animate-spin"></span>
          </div>

          <div v-else-if="userDetailData" class="space-y-5">
            <!-- Profilo Header -->
            <div class="flex items-center justify-between p-3 bg-white/[0.02] border border-white/5 rounded-2xl">
              <div class="flex items-center gap-4">
                <img v-if="userDetailData.avatar_path" :src="`/api/users/${userDetailData.id_user}/avatar`" class="w-12 h-12 rounded-full object-cover border border-white/15 animate-fade-in" />
                <div v-else class="w-12 h-12 rounded-full bg-brand-secondary/20 flex items-center justify-center text-sm font-black text-brand-secondary border border-brand-secondary/30">
                  {{ userDetailData.name?.charAt(0) }}{{ userDetailData.surname?.charAt(0) }}
                </div>
                <div class="min-w-0">
                  <p class="font-bold text-white truncate">@{{ userDetailData.username }}</p>
                  <p class="text-xs text-white/50 truncate">{{ userDetailData.name }} {{ userDetailData.surname }}</p>
                </div>
              </div>
              <button 
                v-if="userDetailData.avatar_path"
                @click="triggerConfirm('Sei sicuro di voler rimuovere la foto profilo di @' + userDetailData.username + '?', () => adminWipeAvatar(userDetailData.id_user))"
                class="px-2.5 py-1.5 border border-rose-500/30 hover:bg-rose-500/10 text-rose-400 rounded-xl text-[10px] font-bold transition-all cursor-pointer shadow-sm flex items-center gap-1 shrink-0"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                Rimuovi Foto
              </button>
            </div>

            <!-- Dettagli -->
            <div class="space-y-2.5 text-xs">
              <div class="flex justify-between py-1.5 border-b border-white/5">
                <span class="text-white/40">Email:</span>
                <span class="text-white/80 font-mono">{{ userDetailData.email }}</span>
              </div>
              <div class="flex justify-between py-1.5 border-b border-white/5">
                <span class="text-white/40">Stato Account:</span>
                <span class="px-2 py-0.5 text-[9px] font-black uppercase tracking-wider rounded" :class="userDetailData.is_banned ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'">
                  {{ userDetailData.is_banned ? 'Bannato' : 'Attivo' }}
                </span>
              </div>
              <div class="flex justify-between py-1.5 border-b border-white/5">
                <span class="text-white/40">Dischi nel Vault:</span>
                <span class="text-white/80 font-bold">{{ userDetailData.copies_count }} dischi</span>
              </div>
              <div class="flex justify-between py-1.5 border-b border-white/5">
                <span class="text-white/40">Album inseriti:</span>
                <span class="text-white/80">{{ userDetailData.albums_count }}</span>
              </div>
              <div class="flex flex-col gap-1 py-1.5 border-b border-white/5">
                <div class="flex justify-between items-center">
                  <span class="text-white/40">Biografia:</span>
                  <button 
                    v-if="userDetailData.bio"
                    @click="triggerConfirm('Sei sicuro di voler azzerare la biografia di @' + userDetailData.username + '?', () => adminWipeBio(userDetailData.id_user))"
                    class="px-2 py-0.5 border border-yellow-500/20 hover:bg-yellow-500/15 text-yellow-400 rounded-lg text-[9px] font-bold transition-all cursor-pointer shadow-sm"
                  >
                    Azzera Bio
                  </button>
                </div>
                <p class="text-white/70 italic bg-white/5 p-2.5 rounded-xl leading-relaxed">
                  {{ userDetailData.bio || '(Nessuna biografia inserita)' }}
                </p>
              </div>

              <!-- Storico Segnalazioni & Provvedimenti -->
              <div class="space-y-2 pt-1.5">
                <span class="text-[9px] font-black uppercase tracking-wider text-white/40">Storico Segnalazioni & Provvedimenti</span>
                <div class="space-y-2 max-h-36 overflow-y-auto pr-1">
                  <!-- Segnalazioni -->
                  <div v-for="r in userDetailData.reports_history" :key="r.id_report" class="p-2 bg-white/[0.02] border border-white/5 rounded-xl text-[9px] space-y-1">
                    <div class="flex justify-between font-bold">
                      <span class="px-1.5 py-0.5 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded uppercase text-[7px]">{{ r.category }}</span>
                      <span class="text-white/30 font-normal">{{ formatDate(r.created_at) }}</span>
                    </div>
                    <p v-if="r.details" class="text-white/70 italic leading-snug">"{{ r.details }}"</p>
                    <div class="flex justify-between text-[8px] text-white/30 pt-1 border-t border-white/5">
                      <span>Stato: <strong class="uppercase" :class="r.status === 'pending' ? 'text-rose-400' : 'text-emerald-400'">{{ r.status }}</strong></span>
                      <span v-if="r.resolved_at">Risolto: {{ formatDate(r.resolved_at) }}</span>
                    </div>
                  </div>
                  
                  <!-- Audit Logs (Provvedimenti) -->
                  <div v-for="a in userDetailData.audit_history" :key="a.id_log" class="p-2 bg-amber-500/5 border border-amber-500/15 rounded-xl text-[9px] space-y-1">
                    <div class="flex justify-between font-bold text-amber-400/80">
                      <span>⚠️ PROVVEDIMENTO</span>
                      <span class="text-white/30 font-normal">{{ formatDate(a.created_at) }}</span>
                    </div>
                    <p class="text-white/80 font-medium leading-snug">{{ a.details }}</p>
                  </div>
                  
                  <div v-if="!userDetailData.reports_history?.length && !userDetailData.audit_history?.length" class="text-center py-4 text-white/20 italic text-[9px]">
                    Nessuna segnalazione o provvedimento registrato.
                  </div>
                </div>
              </div>
            </div>

            <!-- Azione Ban/Unban nel modale -->
            <div class="flex gap-3 pt-2">
              <button 
                @click="closeUserDetail"
                class="flex-1 py-3 border border-white/5 bg-white/5 text-white/70 hover:bg-white/10 rounded-2xl text-xs font-bold transition-all cursor-pointer"
              >
                Chiudi
              </button>
              <button 
                @click="triggerConfirm(userDetailData.is_banned ? 'Sei sicuro di voler riattivare l\'utente @' + userDetailData.username + '?' : 'Sei sicuro di voler sospendere permanentemente l\'utente @' + userDetailData.username + '?', () => toggleBanInModal())"
                class="flex-1 py-3 text-white rounded-2xl text-xs font-bold transition-all cursor-pointer shadow-lg flex items-center justify-center gap-1.5"
                :class="userDetailData.is_banned ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-rose-500 hover:bg-rose-600'"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="4.93" x2="19.07" y1="4.93" y2="19.07"/></svg>
                {{ userDetailData.is_banned ? 'Riattiva Utente' : 'Ban Utente' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Modale di Conferma Moderazione -->
    <transition name="fade">
      <div v-if="showConfirmModal" class="fixed inset-0 bg-black/60 backdrop-blur-md z-[20000] flex items-center justify-center p-4">
        <div class="glass-panel max-w-sm w-full p-6 space-y-6 border border-white/10 rounded-3xl relative animate-scale-up shadow-2xl">
          <div class="space-y-2 text-center">
            <div class="inline-flex w-12 h-12 rounded-full bg-yellow-500/10 border border-yellow-500/20 items-center justify-center text-yellow-400 text-xl font-bold">
              ⚠️
            </div>
            <h3 class="text-lg font-bold text-white/95">Conferma Azione</h3>
            <p class="text-xs text-white/60 leading-relaxed">{{ confirmMessage }}</p>
          </div>
          
          <div class="flex gap-3">
            <button 
              @click="showConfirmModal = false; confirmAction = null"
              class="flex-1 py-3 border border-white/5 bg-white/5 text-white/70 hover:bg-white/10 rounded-2xl text-xs font-bold transition-all cursor-pointer"
            >
              Annulla
            </button>
            <button 
              @click="runConfirmedAction"
              class="flex-1 py-3 bg-brand-secondary hover:bg-brand-secondary/95 text-white rounded-2xl text-xs font-bold transition-all cursor-pointer shadow-lg"
            >
              Conferma
            </button>
          </div>
        </div>
      </div>
    </transition>

  </div>
</template>
