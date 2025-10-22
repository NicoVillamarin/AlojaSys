/**
 * Servicio para Conciliación Bancaria
 */
import { getApiURL } from './utils'
import fetchWithAuth from './fetchWithAuth'

const API_BASE = `${getApiURL()}/api/payments`

export const reconciliationService = {
  // Configuración de conciliación
  getConfig: (hotelId) => fetchWithAuth(`${API_BASE}/reconciliation-configs/by_hotel/?hotel_id=${hotelId}`),

  updateConfig: (configId, data) => fetchWithAuth(`${API_BASE}/reconciliation-configs/${configId}/`, { method: 'PATCH', body: JSON.stringify(data) }),

  // Conciliaciones
  getReconciliations: (params = {}) => fetchWithAuth(`${API_BASE}/reconciliations/?${new URLSearchParams(params).toString()}`),

  getReconciliation: (id) => fetchWithAuth(`${API_BASE}/reconciliations/${id}/`),

  createReconciliation: (data) => {
    const formData = new FormData()
    formData.append('hotel', data.hotelId)
    formData.append('reconciliation_date', data.reconciliationDate)
    formData.append('csv_file', data.csvFile)

    return fetch(`${API_BASE}/reconciliations/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: formData,
    }).then(res => res.json())
  },

  processReconciliation: (id) => fetchWithAuth(`${API_BASE}/reconciliations/${id}/process/`, { method: 'POST' }),

  getReconciliationStats: (hotelId) => fetchWithAuth(`${API_BASE}/reconciliations/stats/?hotel_id=${hotelId}`),

  getReconciliationSummary: (hotelId, params = {}) => fetchWithAuth(`${API_BASE}/reconciliations/summary/?${new URLSearchParams({ hotel_id: hotelId, ...params }).toString()}`),

  // Transacciones bancarias
  getTransactions: (reconciliationId, params = {}) => fetchWithAuth(`${API_BASE}/reconciliations/${reconciliationId}/transactions/?${new URLSearchParams(params).toString()}`),

  // Matches
  getMatches: (reconciliationId, params = {}) => fetchWithAuth(`${API_BASE}/reconciliations/${reconciliationId}/matches/?${new URLSearchParams(params).toString()}`),

  approveMatch: (matchId, data) => fetchWithAuth(`${API_BASE}/reconciliation-matches/${matchId}/approve/`, { method: 'POST', body: JSON.stringify(data) }),

  rejectMatch: (matchId) => fetchWithAuth(`${API_BASE}/reconciliation-matches/${matchId}/reject/`, { method: 'POST' }),

  // Logs de auditoría
  getAuditLogs: (reconciliationId) => fetchWithAuth(`${API_BASE}/reconciliations/${reconciliationId}/audit_logs/`),

  // Utilidades
  formatAmount: (amount) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 2,
    }).format(amount)
  },

  formatDate: (date) => {
    return new Date(date).toLocaleDateString('es-AR')
  },

  formatDateTime: (date) => {
    return new Date(date).toLocaleString('es-AR')
  },

  getStatusColor: (status) => {
    const colors = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'processing': 'bg-blue-100 text-blue-800',
      'completed': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800',
      'manual_review': 'bg-orange-100 text-orange-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  },

  getStatusLabel: (status) => {
    const labels = {
      'pending': 'Pendiente',
      'processing': 'Procesando',
      'completed': 'Completada',
      'failed': 'Fallida',
      'manual_review': 'Revisión Manual',
    }
    return labels[status] || status
  },

  getMatchTypeColor: (matchType) => {
    const colors = {
      'exact': 'bg-green-100 text-green-800',
      'fuzzy': 'bg-yellow-100 text-yellow-800',
      'partial': 'bg-orange-100 text-orange-800',
      'manual': 'bg-blue-100 text-blue-800',
    }
    return colors[matchType] || 'bg-gray-100 text-gray-800'
  },

  getMatchTypeLabel: (matchType) => {
    const labels = {
      'exact': 'Exacto',
      'fuzzy': 'Aproximado',
      'partial': 'Parcial',
      'manual': 'Manual',
    }
    return labels[matchType] || matchType
  },

  // Procesar conciliación
  processReconciliation: (reconciliationId) => {
    return fetch(`${API_BASE}/reconciliations/${reconciliationId}/process/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    }).then(res => {
      if (!res.ok) {
        throw new Error('Error procesando conciliación')
      }
      return res.json()
    })
  },
}

