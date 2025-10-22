import { getApiURL } from "./utils";
import fetchWithAuth from "./fetchWithAuth";

class BankTransferService {
  /**
   * Obtiene todas las transferencias bancarias
   */
  async getTransfers(params = {}) {
    const queryParams = new URLSearchParams();
    
    if (params.reservation_id) queryParams.append('reservation_id', params.reservation_id);
    if (params.hotel_id) queryParams.append('hotel_id', params.hotel_id);
    if (params.status) queryParams.append('status', params.status);
    if (params.needs_review) queryParams.append('needs_review', params.needs_review);
    if (params.search) queryParams.append('search', params.search);
    
    const response = await fetchWithAuth(
      `${getApiURL()}/api/payments/bank-transfers/?${queryParams.toString()}`
    );
    
    return response;
  }

  /**
   * Obtiene una transferencia específica por ID
   */
  async getTransfer(transferId) {
    const response = await fetchWithAuth(
      `${getApiURL()}/api/payments/bank-transfers/${transferId}/`
    );
    
    return response;
  }

  /**
   * Crea una nueva transferencia bancaria
   */
  async createTransfer(transferData) {
    const formData = new FormData();
    
    // Agregar campos requeridos
    formData.append('reservation', transferData.reservation);
    formData.append('amount', transferData.amount);
    formData.append('transfer_date', transferData.transfer_date);
    formData.append('cbu_iban', transferData.cbu_iban);
    
    // Agregar campos opcionales
    if (transferData.bank_name) formData.append('bank_name', transferData.bank_name);
    if (transferData.notes) formData.append('notes', transferData.notes);
    if (transferData.external_reference) formData.append('external_reference', transferData.external_reference);
    if (transferData.receipt_file) formData.append('receipt_file', transferData.receipt_file);
    
    const response = await fetchWithAuth(
      `${getApiURL()}/api/payments/bank-transfers/`,
      {
        method: 'POST',
        body: formData
      }
    );
    
    return response;
  }

  /**
   * Actualiza una transferencia bancaria
   */
  async updateTransfer(transferId, updateData) {
    const response = await fetchWithAuth(
      `${getApiURL()}/api/payments/bank-transfers/${transferId}/`,
      {
        method: 'PATCH',
        body: JSON.stringify(updateData)
      }
    );
    
    return response;
  }

  /**
   * Confirma una transferencia bancaria
   */
  async confirmTransfer(transferId, notes = '') {
    const response = await fetchWithAuth(
      `${getApiURL()}/api/payments/bank-transfers/${transferId}/confirm/`,
      {
        method: 'POST',
        body: JSON.stringify({ notes })
      }
    );
    
    return response;
  }

  /**
   * Rechaza una transferencia bancaria
   */
  async rejectTransfer(transferId, notes) {
    const response = await fetchWithAuth(
      `${getApiURL()}/api/payments/bank-transfers/${transferId}/reject/`,
      {
        method: 'POST',
        body: JSON.stringify({ notes })
      }
    );
    
    return response;
  }

  /**
   * Marca una transferencia como pendiente de revisión
   */
  async markPendingReview(transferId) {
    const response = await fetchWithAuth(
      `${getApiURL()}/api/payments/bank-transfers/${transferId}/mark_pending_review/`,
      {
        method: 'POST'
      }
    );
    
    return response;
  }

  /**
   * Obtiene transferencias pendientes de revisión
   */
  async getPendingReview() {
    const response = await fetchWithAuth(
      `${getApiURL()}/api/payments/bank-transfers/pending_review/`
    );
    
    return response;
  }

  /**
   * Obtiene estadísticas de transferencias bancarias
   */
  async getStats() {
    const response = await fetchWithAuth(
      `${getApiURL()}/api/payments/bank-transfers/stats/`
    );
    
    return response;
  }

  /**
   * Sube un comprobante de transferencia usando el ViewSet normal
   */
  async uploadReceipt(receiptData) {
    const formData = new FormData();
    
    // Agregar campos requeridos
    formData.append('reservation', receiptData.reservation);
    formData.append('amount', receiptData.amount);
    formData.append('transfer_date', receiptData.transfer_date);
    formData.append('cbu_iban', receiptData.cbu_iban);
    formData.append('receipt_file', receiptData.receipt_file);
    
    // Agregar campos opcionales
    if (receiptData.bank_name) formData.append('bank_name', receiptData.bank_name);
    if (receiptData.notes) formData.append('notes', receiptData.notes);
    if (receiptData.external_reference) formData.append('external_reference', receiptData.external_reference);
    
    const response = await fetchWithAuth(
      `${getApiURL()}/api/payments/bank-transfers/`,
      {
        method: 'POST',
        body: formData
      }
    );
    
    return response;
  }

  /**
   * Valida formato de CBU/IBAN
   */
  validateCbuIban(cbuIban) {
    if (!cbuIban) return { valid: false, message: 'CBU/IBAN es requerido' };
    
    const cleanCbu = cbuIban.replace(/[-\s]/g, '');
    
    // Validación de CBU argentino (22 dígitos)
    if (cleanCbu.length === 22 && /^\d{22}$/.test(cleanCbu)) {
      return { valid: true, message: 'CBU válido' };
    }
    
    // Validación de IBAN (mínimo 15 caracteres, máximo 34)
    if (cleanCbu.length >= 15 && cleanCbu.length <= 34 && /^[A-Z0-9]+$/.test(cleanCbu)) {
      return { valid: true, message: 'IBAN válido' };
    }
    
    return { valid: false, message: 'Formato de CBU/IBAN inválido' };
  }

  /**
   * Valida archivo de comprobante
   */
  validateReceiptFile(file) {
    if (!file) return { valid: false, message: 'El archivo es requerido' };
    
    // Validar tipo de archivo
    const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
      return { valid: false, message: 'Solo se permiten archivos JPG, PNG o PDF' };
    }
    
    // Validar tamaño (máximo 10MB)
    if (file.size > 10 * 1024 * 1024) {
      return { valid: false, message: 'El archivo no puede ser mayor a 10MB' };
    }
    
    return { valid: true, message: 'Archivo válido' };
  }

  /**
   * Formatea monto para mostrar
   */
  formatAmount(amount) {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS'
    }).format(parseFloat(amount));
  }

  /**
   * Formatea fecha para mostrar
   */
  formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('es-AR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  /**
   * Obtiene el color del estado
   */
  getStatusColor(status) {
    const colors = {
      'uploaded': 'bg-blue-100 text-blue-800',
      'pending_review': 'bg-yellow-100 text-yellow-800',
      'confirmed': 'bg-green-100 text-green-800',
      'rejected': 'bg-red-100 text-red-800',
      'processing': 'bg-purple-100 text-purple-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  }

  /**
   * Obtiene el icono del estado
   */
  getStatusIcon(status) {
    const icons = {
      'uploaded': '📤',
      'pending_review': '⏳',
      'confirmed': '✅',
      'rejected': '❌',
      'processing': '⚙️'
    };
    return icons[status] || '❓';
  }
}

export const bankTransferService = new BankTransferService();
export default bankTransferService;
