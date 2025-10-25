import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from 'src/stores/useAuthStore'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import Swal from 'sweetalert2'

const DepositModal = ({ 
  isOpen, 
  onClose, 
  reservationId, 
  reservationData,
  onDepositPaid 
}) => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [depositInfo, setDepositInfo] = useState(null)
  const [formData, setFormData] = useState({
    amount: '',
    method: 'cash',
    notes: '',
    send_to_afip: false
  })

  // Cargar información de depósito cuando se abre el modal
  useEffect(() => {
    if (isOpen && reservationId) {
      loadDepositInfo()
    }
  }, [isOpen, reservationId])

  const loadDepositInfo = async () => {
    try {
      setLoading(true)
      // Aquí deberías llamar a un endpoint que calcule la información del depósito
      // Por ahora simulamos con datos de la reserva
      if (reservationData) {
        const totalPrice = parseFloat(reservationData.total_price || 0)
        const depositAmount = totalPrice * 0.5 // 50% por defecto, esto debería venir del backend
        
        setDepositInfo({
          required: true,
          amount: depositAmount,
          percentage: 50,
          type: 'percentage',
          due: 'confirmation',
          balance_due: 'check_in'
        })
        
        setFormData(prev => ({
          ...prev,
          amount: depositAmount.toString()
        }))
      }
    } catch (error) {
      console.error('Error cargando información de depósito:', error)
      Swal.fire({
        title: 'Error',
        text: 'No se pudo cargar la información del depósito',
        icon: 'error'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!depositInfo || !depositInfo.required) {
      Swal.fire({
        title: 'Error',
        text: 'No se requiere depósito para esta reserva',
        icon: 'error'
      })
      return
    }

    const amount = parseFloat(formData.amount)
    if (amount <= 0) {
      Swal.fire({
        title: 'Error',
        text: 'El monto debe ser mayor a 0',
        icon: 'error'
      })
      return
    }

    if (amount > depositInfo.amount) {
      Swal.fire({
        title: 'Error',
        text: `El monto no puede exceder $${depositInfo.amount.toFixed(2)} (según política)`,
        icon: 'error'
      })
      return
    }

    try {
      setLoading(true)
      
      const response = await fetchWithAuth(`${getApiURL()}/api/payments/create-deposit/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          reservation_id: reservationId,
          amount: amount,
          method: formData.method,
          send_to_afip: formData.send_to_afip,
          notes: formData.notes
        })
      })

      if (response) {
        Swal.fire({
          title: 'Seña Creada',
          text: `Seña de $${amount.toFixed(2)} creada exitosamente`,
          icon: 'success',
          confirmButtonText: 'OK'
        })
        
        onDepositPaid?.(response)
        onClose()
      }
    } catch (error) {
      console.error('Error creando seña:', error)
      Swal.fire({
        title: 'Error',
        text: `Error creando seña: ${error.message || 'Error desconocido'}`,
        icon: 'error'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleAmountChange = (e) => {
    const value = e.target.value
    setFormData(prev => ({ ...prev, amount: value }))
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            Crear Seña/Depósito
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {loading && !depositInfo ? (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Cargando información...</p>
          </div>
        ) : depositInfo && depositInfo.required ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Información del depósito */}
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-medium text-blue-900 mb-2">Información del Depósito</h3>
              <div className="space-y-1 text-sm">
                <p><span className="font-medium">Monto requerido:</span> ${depositInfo.amount.toFixed(2)}</p>
                <p><span className="font-medium">Tipo:</span> {depositInfo.type === 'percentage' ? 'Porcentaje' : 'Monto fijo'}</p>
                {depositInfo.percentage > 0 && (
                  <p><span className="font-medium">Porcentaje:</span> {depositInfo.percentage}%</p>
                )}
                <p><span className="font-medium">Vencimiento:</span> Al confirmar</p>
                <p><span className="font-medium">Saldo pendiente:</span> Al check-in</p>
              </div>
            </div>

            {/* Monto del depósito */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Monto del Depósito *
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                max={depositInfo.amount}
                value={formData.amount}
                onChange={handleAmountChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0.00"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Máximo: ${depositInfo.amount.toFixed(2)}
              </p>
            </div>

            {/* Método de pago */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Método de Pago *
              </label>
              <select
                value={formData.method}
                onChange={(e) => setFormData(prev => ({ ...prev, method: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value="cash">Efectivo</option>
                <option value="card">Tarjeta</option>
                <option value="transfer">Transferencia</option>
                <option value="mercadopago">Mercado Pago</option>
              </select>
            </div>

            {/* Notas */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notas (opcional)
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows="3"
                placeholder="Notas adicionales sobre el depósito..."
              />
            </div>

            {/* Opción de facturación AFIP */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="send_to_afip"
                checked={formData.send_to_afip}
                onChange={(e) => setFormData(prev => ({ ...prev, send_to_afip: e.target.checked }))}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="send_to_afip" className="ml-2 text-sm text-gray-700">
                Generar factura AFIP para la seña
              </label>
            </div>

            {/* Botones */}
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                disabled={loading}
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Creando...' : 'Crear Seña'}
              </button>
            </div>
          </form>
        ) : (
          <div className="text-center py-4">
            <p className="text-gray-600">No se requiere depósito para esta reserva</p>
            <button
              onClick={onClose}
              className="mt-4 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Cerrar
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default DepositModal
