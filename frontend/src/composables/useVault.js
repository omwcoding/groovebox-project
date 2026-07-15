import { ref, computed } from 'vue'
import { api } from '@/stores/api'

export function useVault(username = null) {
  const copies = ref([])
  const user = ref(null)
  const loading = ref(true)
  const error = ref('')
  const search = ref('')
  const filterFormat = ref('')

  const filteredCopies = computed(() => {
    return copies.value.filter(c => {
      const matchesSearch = !search.value.trim() || 
        c.album_title?.toLowerCase().includes(search.value.toLowerCase()) ||
        c.genre?.toLowerCase().includes(search.value.toLowerCase()) ||
        c.artists?.some(ar => ar.name.toLowerCase().includes(search.value.toLowerCase()))
      
      const matchesFormat = !filterFormat.value || c.format === filterFormat.value
      
      return matchesSearch && matchesFormat
    })
  })

  async function fetchCopies() {
    loading.value = true
    error.value = ''
    try {
      if (username) {
        const res = await api.get(`/users/share/${username}`)
        user.value = res.data.user
        copies.value = res.data.copies
      } else {
        const res = await api.get('/copies')
        copies.value = res.data
      }
    } catch (err) {
      error.value = err.message || 'Errore nel caricamento del Vault.'
    } finally {
      loading.value = false
    }
  }

  async function fetchCopy(id) {
    loading.value = true
    error.value = ''
    try {
      const res = await api.get(`/copies/${id}`)
      return res.data
    } catch (err) {
      error.value = err.message || 'Copia non trovata nel Vault'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateCopy(id, payload) {
    error.value = ''
    try {
      const res = await api.put(`/copies/${id}`, payload)
      return res.data
    } catch (err) {
      error.value = err.message || 'Errore durante l\'aggiornamento'
      throw err
    }
  }

  async function deleteCopy(id) {
    error.value = ''
    try {
      await api.delete(`/copies/${id}`)
    } catch (err) {
      error.value = err.message || 'Errore durante l\'eliminazione'
      throw err
    }
  }

  return {
    copies,
    user,
    loading,
    error,
    search,
    filterFormat,
    filteredCopies,
    fetchCopies,
    fetchCopy,
    updateCopy,
    deleteCopy
  }
}
