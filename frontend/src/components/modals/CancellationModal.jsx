import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import Button from 'src/components/Button'
import Badge from 'src/components/Badge'
import { useDispatchAction } from 'src/hooks/useDispatchAction'
import { getApiURL } from 'src/services/utils'
import { useAuthStore } from 'src/stores/useAuthStore'

const CancellationModal = ({ isOpen, onClose, reservation, onSuccess }) => {
  const { t } = useTranslation()
  const [cancellationData, setCancellationData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [step, setStep] = useState('calculation') // 'calculation' o 'confirmation'
  const [cancellationReason, setCancellationReason] = useState('')

  const { mutate: cancelReservation, isPending: cancelling } = useDispatchAction({
    resource: 'reservations',
    onSuccess: (data) => {
      if (data.action === 'cancelled') {
        onSuccess && onSuccess()
        onClose && onClose()
      } else if (data.action === 'calculation') {
        setCancellationData(data)
        setStep('confirmation')
      }
    }
  })

  useEffect(() => {
    if (isOpen && reservation) {
      fetchCancellationCalculation()
    } else if (!isOpen) {
      // Limpiar estado cuando se cierra el modal
      setCancellationReason('')
      setError(null)
      setStep('calculation')
    }
  }, [isOpen, reservation])

  const fetchCancellationCalculation = async () => {
    if (!reservation) return

    setLoading(true)
    setError(null)
    setStep('calculation')

    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(`${getApiURL()}/api/reservations/${reservation.id}/cancel/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ confirm: false }) // Solo calcular
      })

      if (response.ok) {
        const data = await response.json()
        setCancellationData(data)
        setStep('confirmation')
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Error al calcular la cancelación')
      }
    } catch (err) {
      setError('Error de conexión')
      console.error('Error fetching cancellation calculation:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmCancel = () => {
    if (!reservation) return
    
    if (!cancellationReason.trim()) {
      setError('El motivo de cancelación es obligatorio')
      return
    }
    
    cancelReservation({
      action: `${reservation.id}/cancel`,
      body: { 
        confirm: true,
        cancellation_reason: cancellationReason.trim()
      }, // Confirmar cancelación con motivo
      method: 'POST'
    })
  }

  const getCancellationType = () => {
    if (!cancellationData?.cancellation_rules) return 'unknown'
    
    const rules = cancellationData.cancellation_rules
    if (rules.type === 'free') return 'free'
    if (rules.type === 'partial') return 'partial'
    return 'no_refund'
  }

  const getCancellationBadgeVariant = () => {
    const type = getCancellationType()
    switch (type) {
      case 'free': return 'success'
      case 'partial': return 'warning'
      case 'no_refund': return 'error'
      default: return 'neutral'
    }
  }

  const getCancellationBadgeText = () => {
    const type = getCancellationType()
    switch (type) {
      case 'free': return 'Cancelación Gratuita'
      case 'partial': return 'Cancelación con Penalidad'
      case 'no_refund': return 'Sin Cancelación'
      default: return 'Evaluando...'
    }
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS'
    }).format(amount)
  }

  const getFinancialSummary = () => {
    if (!cancellationData?.financial_summary) return null
    return cancellationData.financial_summary
  }

  if (!reservation) return null

  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={onClose}
      title={step === 'calculation' ? "Calculando Cancelación..." : "Confirmar Cancelación"}
      size="lg"
      onSubmit={step === 'confirmation' ? handleConfirmCancel : undefined}
      submitText={step === 'confirmation' ? "Confirmar Cancelación" : undefined}
      submitDisabled={loading || cancelling || (step === 'confirmation' && !cancellationReason.trim())}
      submitLoading={cancelling}
      submitVariant="danger"
    >
      <div className="space-y-6">
        {/* Estado de Carga */}
        {loading && step === 'calculation' && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-aloja-navy mx-auto"></div>
            <p className="text-gray-600 mt-4 text-lg">Calculando políticas de cancelación...</p>
            <p className="text-gray-500 mt-2 text-sm">Esto puede tomar unos segundos</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error al calcular cancelación</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
            <div className="mt-4">
              <Button 
                variant="secondary" 
                size="sm" 
                onClick={fetchCancellationCalculation}
              >
                Reintentar
              </Button>
            </div>
          </div>
        )}

        {/* Datos de Cancelación Calculados */}
        {cancellationData && step === 'confirmation' && (
          <div className="space-y-6">
            {/* Información de la Reserva */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Detalles de la Reserva</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Reserva:</span>
                  <span className="ml-2 font-medium">{reservation.display_name}</span>
                </div>
                <div>
                  <span className="text-gray-600">Huésped:</span>
                  <span className="ml-2 font-medium">{reservation.guest_name}</span>
                </div>
                <div>
                  <span className="text-gray-600">Check-in:</span>
                  <span className="ml-2 font-medium">{reservation.check_in}</span>
                </div>
                <div>
                  <span className="text-gray-600">Check-out:</span>
                  <span className="ml-2 font-medium">{reservation.check_out}</span>
                </div>
                <div>
                  <span className="text-gray-600">Total:</span>
                  <span className="ml-2 font-medium">{formatCurrency(reservation.total_price)}</span>
                </div>
                <div>
                  <span className="text-gray-600">Estado:</span>
                  <Badge variant={`reservation-${reservation.status}`} size="sm" className="ml-2">
                    {reservation.status}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Tipo de Cancelación */}
            <div className="flex items-center justify-between p-4 bg-white border rounded-lg">
              <div>
                <h4 className="font-semibold text-gray-900">Tipo de Cancelación</h4>
                <p className="text-sm text-gray-600 mt-1">
                  {cancellationData.cancellation_rules?.message || 'Evaluando políticas aplicables...'}
                </p>
              </div>
              <Badge variant={getCancellationBadgeVariant()} size="lg">
                {getCancellationBadgeText()}
              </Badge>
            </div>

            {/* Resumen Financiero */}
            {getFinancialSummary() && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h5 className="font-semibold text-blue-900 mb-4 text-lg">Resumen Financiero</h5>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-blue-800">Total pagado:</span>
                    <span className="font-semibold text-blue-900 text-lg">
                      {formatCurrency(getFinancialSummary().total_paid)}
                    </span>
                  </div>
                  
                  {getFinancialSummary().penalty_amount > 0 && (
                    <div className="flex justify-between items-center text-red-600">
                      <span>Penalidad por cancelación:</span>
                      <span className="font-semibold">
                        -{formatCurrency(getFinancialSummary().penalty_amount)}
                      </span>
                    </div>
                  )}
                  
                  <div className="flex justify-between items-center text-green-600">
                    <span>Devolución:</span>
                    <span className="font-semibold">
                      +{formatCurrency(getFinancialSummary().refund_amount)}
                    </span>
                  </div>
                  
                  <div className="border-t border-blue-300 pt-3">
                    <div className="flex justify-between items-center">
                      <span className="text-blue-900 font-semibold text-lg">Total a devolver:</span>
                      <span className="font-bold text-blue-900 text-xl">
                        {formatCurrency(getFinancialSummary().net_refund)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Campo de Motivo de Cancelación */}
            <div className="bg-white border rounded-lg p-4">
              <label htmlFor="cancellation-reason" className="block text-sm font-medium text-gray-700 mb-2">
                Motivo de Cancelación *
              </label>
              <textarea
                id="cancellation-reason"
                value={cancellationReason}
                onChange={(e) => setCancellationReason(e.target.value)}
                placeholder="Describe el motivo de la cancelación..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                rows={3}
                required
              />
              {error && error.includes('motivo') && (
                <p className="mt-1 text-sm text-red-600">{error}</p>
              )}
            </div>

            {/* Información de Devolución Automática */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">
                    Devolución Automática
                  </h3>
                  <div className="mt-2 text-sm text-blue-700">
                    <p>
                      Al confirmar la cancelación, el sistema procesará automáticamente la devolución 
                      según las políticas configuradas. La devolución se realizará por el mismo método 
                      de pago utilizado originalmente.
                    </p>
                    <p className="mt-2">
                      <strong>Tiempo de procesamiento:</strong> 1-3 días hábiles para tarjetas de crédito, 
                      inmediato para pagos en efectivo.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Advertencia de Confirmación */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800">Confirmación Requerida</h3>
                  <p className="text-sm text-yellow-700 mt-1">
                    Esta acción cancelará la reserva permanentemente. La habitación quedará disponible para nuevas reservas.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </ModalLayout>
  )
}

export default CancellationModal