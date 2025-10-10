import fetchWithAuth from './fetchWithAuth'
import { getApiURL } from './utils'

/**
 * Servicio para manejar políticas de pago
 */
export const paymentPolicyService = {
  /**
   * Obtiene la política de pago activa para un hotel
   * @param {number} hotelId - ID del hotel
   * @returns {Promise<Object>} Política de pago activa
   */
  async getActivePolicyForHotel(hotelId) {
    try {
      const data = await fetchWithAuth(`${getApiURL()}/api/payments/policies/?hotel=${hotelId}&is_active=true&is_default=true`)
      
      if (data.results && data.results.length > 0) {
        return data.results[0] // Retorna la política por defecto
      }
      
      // Si no hay política por defecto, buscar cualquier política activa
      const fallbackData = await fetchWithAuth(`${getApiURL()}/api/payments/policies/?hotel=${hotelId}&is_active=true`)
      
      if (fallbackData.results && fallbackData.results.length > 0) {
        return fallbackData.results[0]
      }
      
      return null
    } catch (error) {
      console.error('Error obteniendo política de pago:', error)
      return null
    }
  },

  /**
   * Calcula el monto de la seña según la política
   * @param {Object} policy - Política de pago
   * @param {number} totalAmount - Monto total de la reserva
   * @returns {Object} Información del depósito
   */
  calculateDeposit(policy, totalAmount) {
    if (!policy || policy.deposit_type === 'none') {
      return {
        required: false,
        amount: 0,
        percentage: 0,
        type: 'none'
      }
    }

    let amount = 0
    if (policy.deposit_type === 'percentage') {
      amount = (totalAmount * policy.deposit_value) / 100
    } else if (policy.deposit_type === 'fixed') {
      amount = policy.deposit_value
    }

    return {
      required: true,
      amount: Math.round(amount * 100) / 100, // Redondear a 2 decimales
      percentage: policy.deposit_type === 'percentage' ? policy.deposit_value : 0,
      type: policy.deposit_type,
      due: policy.deposit_due,
      daysBefore: policy.deposit_days_before,
      balanceDue: policy.balance_due
    }
  },

  /**
   * Obtiene los métodos de pago habilitados para una política
   * @param {Object} policy - Política de pago
   * @returns {Array} Lista de métodos de pago
   */
  getEnabledMethods(policy) {
    if (!policy || !policy.methods) {
      return []
    }
    return policy.methods.filter(method => method.is_active)
  }
}
