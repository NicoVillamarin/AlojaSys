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
  const [step, setStep] = useState('calculation') // 'calculation', 'confirmation' o 'success'
  const [cancellationReason, setCancellationReason] = useState('')
  const [cancellationRules, setCancellationRules] = useState(null)
  const [refundMethod, setRefundMethod] = useState('money') // 'money' o 'voucher'

  const { mutate: cancelReservation, isPending: cancelling } = useDispatchAction({
    resource: 'reservations',
    onSuccess: (data) => {
      if (data.action === 'cancelled') {
        // Mostrar información detallada del reembolso antes de cerrar
        setCancellationData(data)
        setStep('success')
      } else if (data.action === 'calculation') {
        setCancellationData(data)
        setStep('confirmation')
      }
    }
  })

  useEffect(() => {
    if (isOpen && reservation) {
      fetchCancellationRules()
      fetchCancellationCalculation()
    } else if (!isOpen) {
      // Limpiar estado cuando se cierra el modal
      setCancellationReason('')
      setError(null)
      setStep('calculation')
      setCancellationRules(null)
      setCancellationData(null)
      setRefundMethod('money')
    }
  }, [isOpen, reservation])

  const fetchCancellationRules = async () => {
    if (!reservation) return

    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(`${getApiURL()}/api/reservations/${reservation.id}/cancellation_rules/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        }
      })

      if (response.ok) {
        const data = await response.json()
        setCancellationRules(data)
      }
    } catch (err) {
    }
  }

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
        cancellation_reason: cancellationReason.trim(),
        refund_method: refundMethod
      }, // Confirmar cancelación con motivo y método de reembolso
      method: 'POST'
    })
  }

  const getCancellationType = () => {
    if (!cancellationData?.cancellation_rules) return 'unknown'
    const rules = cancellationData.cancellation_rules
    if (rules.cancellation_type === 'free') return 'free'
    if (rules.cancellation_type === 'partial') return 'partial'
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

  const hasAutoRefund = () => {
    return cancellationRules?.applied_cancellation_policy?.auto_refund_on_cancel || false
  }

  const getRefundMethod = () => {
    // Determinar método de reembolso sugerido basado en los pagos existentes
    if (!cancellationData?.reservation) return 'original_payment'
    
    // Aquí podrías agregar lógica para determinar el método basado en los pagos
    // Por ahora, asumimos que siempre es el método original
    return 'original_payment'
  }

  const getRefundMethodLabel = (method) => {
    const methods = {
      'cash': 'Efectivo',
      'bank_transfer': 'Transferencia Bancaria',
      'credit_card': 'Tarjeta de Crédito',
      'voucher': 'Voucher de Crédito',
      'original_payment': 'Método de Pago Original'
    }
    return methods[method] || method
  }

  const hasGatewayRefundSupport = () => {
    // Verificar si la pasarela de pago soporta reembolsos automáticos
    // Por ahora, asumimos que MercadoPago sí lo soporta
    return true
  }

  const getRefundDetails = () => {
    return cancellationData?.refund || null
  }

  const getCancellationDetails = () => {
    return cancellationData?.cancellation_details || null
  }

  const getRefundStatusBadgeVariant = (status) => {
    switch (status) {
      case 'completed': return 'success'
      case 'processing': return 'warning'
      case 'pending': return 'neutral'
      case 'failed': return 'error'
      case 'cancelled': return 'error'
      default: return 'neutral'
    }
  }

  const getRefundStatusText = (status) => {
    switch (status) {
      case 'completed': return 'Completado'
      case 'processing': return 'Procesando'
      case 'pending': return 'Pendiente'
      case 'failed': return 'Fallido'
      case 'cancelled': return 'Cancelado'
      default: return 'Desconocido'
    }
  }

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString('es-AR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleCloseSuccess = () => {
    onSuccess && onSuccess()
    onClose && onClose()
  }

  if (!reservation) return null

  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={step === 'success' ? handleCloseSuccess : onClose}
      title={
        step === 'calculation' ? "Calculando Cancelación..." :
        step === 'confirmation' ? "Cancelar Reserva" :
        step === 'success' ? "Cancelación Exitosa" : "Cancelar Reserva"
      }
      size="lg"
      onSubmit={step === 'confirmation' ? handleConfirmCancel : undefined}
      submitText={step === 'confirmation' ? "Cancelar" : undefined}
      submitDisabled={loading || cancelling || (step === 'confirmation' && !cancellationReason.trim())}
      submitLoading={cancelling}
      submitVariant="danger"
      aria-labelledby="cancellation-modal-title"
      aria-describedby="cancellation-modal-description"
      customFooter={
        step === 'confirmation' ? (
          <div className="flex flex-col sm:flex-row justify-end gap-3 w-full">
            <Button
              variant="danger"
              size="md"
              onClick={onClose}
              aria-label="Cerrar modal sin cancelar"
            >
              Cerrar
            </Button>
            
            <Button
              variant="success"
              size="md"
              onClick={handleConfirmCancel}
              disabled={loading || cancelling || !cancellationReason.trim()}
              aria-label="Cancelar y solicitar reembolso"
            >
              Cancelar y solicitar reembolso
            </Button>
            
            {getFinancialSummary()?.net_refund > 0 && (
              <Button
                variant="warning"
                size="md"
                onClick={() => {
                }}
                disabled={true} // Solo disponible para staff
                aria-label="Cancelar sin reembolso (solo staff)"
              >
                Cancelar sin reembolso (Solo staff)
              </Button>
            )}
          </div>
        ) : step === 'success' ? (
          <div className="flex justify-end gap-3 w-full">
            <Button
              variant="success"
              size="md"
              onClick={handleCloseSuccess}
              aria-label="Cerrar modal"
            >
              Finalizar
            </Button>
          </div>
        ) : undefined
      }
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
          <div className="space-y-6" id="cancellation-modal-description">
            {/* Información de la Reserva */}
            <div className="bg-gray-50 rounded-lg p-4" role="region" aria-label="Detalles de la reserva">
              <h3 className="font-semibold text-gray-900 mb-3" id="reservation-details-title">Detalles de la Reserva</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600" aria-label="Número de reserva">Reserva:</span>
                  <span className="ml-2 font-medium" aria-describedby="reservation-number">{reservation.display_name}</span>
                </div>
                <div>
                  <span className="text-gray-600" aria-label="Nombre del huésped">Huésped:</span>
                  <span className="ml-2 font-medium" aria-describedby="guest-name">{reservation.guest_name}</span>
                </div>
                <div>
                  <span className="text-gray-600" aria-label="Fecha de check-in">Check-in:</span>
                  <span className="ml-2 font-medium" aria-describedby="check-in-date">{reservation.check_in}</span>
                </div>
                <div>
                  <span className="text-gray-600" aria-label="Fecha de check-out">Check-out:</span>
                  <span className="ml-2 font-medium" aria-describedby="check-out-date">{reservation.check_out}</span>
                </div>
                <div>
                  <span className="text-gray-600" aria-label="Precio total">Total:</span>
                  <span className="ml-2 font-medium" aria-describedby="total-price">{formatCurrency(reservation.total_price)}</span>
                </div>
                <div>
                  <span className="text-gray-600" aria-label="Estado de la reserva">Estado:</span>
                  <Badge variant={`reservation-${reservation.status}`} size="sm" className="ml-2" aria-describedby="reservation-status">
                    {reservation.status}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Tipo de Cancelación */}
            <div className="flex items-center justify-between p-4 bg-white border rounded-lg" role="region" aria-label="Política de cancelación aplicada">
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900">Política de Cancelación Aplicada</h4>
                <p className="text-sm text-gray-600 mt-1">
                  {(() => {
                    const message = cancellationData.cancellation_rules?.message || 'Evaluando políticas aplicables...'
                    return message
                  })()}
                </p>
                {cancellationRules?.applied_cancellation_policy && (
                  <p className="text-xs text-gray-500 mt-1">
                    Política: {cancellationRules.applied_cancellation_policy.name}
                  </p>
                )}
              </div>
              <div className="flex flex-col items-end space-y-2">
                <Badge variant={getCancellationBadgeVariant()} size="lg">
                  {getCancellationBadgeText()}
                </Badge>
                {hasAutoRefund() && (
                  <Badge variant="success" size="sm" className="animate-pulse">
                    ✓ Reembolso automático disponible
                  </Badge>
                )}
              </div>
            </div>

            {/* Resumen Financiero */}
            {getFinancialSummary() && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6" role="region" aria-label="Resumen financiero de la cancelación">
                <h5 className="font-semibold text-blue-900 mb-4 text-lg">Resumen Financiero</h5>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-blue-800" aria-label="Total pagado por el huésped">Total pagado:</span>
                    <span className="font-semibold text-blue-900 text-lg" aria-describedby="total-paid-amount">
                      {formatCurrency(getFinancialSummary().total_paid)}
                    </span>
                  </div>
                  
                  {getFinancialSummary().penalty_amount > 0 && (
                    <div className="flex justify-between items-center text-red-600">
                      <span aria-label="Penalidad aplicada por cancelación">Penalidad por cancelación:</span>
                      <span className="font-semibold" aria-describedby="penalty-amount">
                        -{formatCurrency(getFinancialSummary().penalty_amount)}
                      </span>
                    </div>
                  )}
                  
                  <div className="flex justify-between items-center text-green-600">
                    <span aria-label="Monto a devolver al huésped">Devolución:</span>
                    <span className="font-semibold" aria-describedby="refund-amount">
                      +{formatCurrency(getFinancialSummary().refund_amount)}
                    </span>
                  </div>
                  
                  <div className="border-t border-blue-300 pt-3">
                    <div className="flex justify-between items-center">
                      <span className="text-blue-900 font-semibold text-lg" aria-label="Total neto a devolver">Total a devolver:</span>
                      <span className="font-bold text-blue-900 text-xl" aria-describedby="net-refund-amount">
                        {formatCurrency(getFinancialSummary().net_refund)}
                      </span>
                    </div>
                  </div>

                  {/* Selección del método de reembolso */}
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <h4 className="text-sm font-semibold text-blue-900 mb-3">Método de Reembolso</h4>
                    <div className="space-y-3">
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input
                          type="radio"
                          name="refundMethod"
                          value="money"
                          checked={refundMethod === 'money'}
                          onChange={(e) => setRefundMethod(e.target.value)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                        />
                        <div className="flex items-center space-x-2">
                          <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                          </svg>
                          <div>
                            <div className="text-sm font-medium text-gray-900">Reembolso en Dinero</div>
                            <div className="text-xs text-gray-500">Se devuelve el dinero al método de pago original</div>
                          </div>
                        </div>
                      </label>
                      
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input
                          type="radio"
                          name="refundMethod"
                          value="voucher"
                          checked={refundMethod === 'voucher'}
                          onChange={(e) => setRefundMethod(e.target.value)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                        />
                        <div className="flex items-center space-x-2">
                          <svg className="h-5 w-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
                          </svg>
                          <div>
                            <div className="text-sm font-medium text-gray-900">Voucher de Crédito</div>
                            <div className="text-xs text-gray-500">Se genera un voucher para usar en futuras reservas</div>
                          </div>
                        </div>
                      </label>
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
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4" role="region" aria-label="Información sobre devolución automática">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">
                    {hasAutoRefund() ? 'Devolución Automática' : 'Procesamiento de Devolución'}
                  </h3>
                  <div className="mt-2 text-sm text-blue-700">
                    {hasAutoRefund() ? (
                      <>
                        <p>
                          Al confirmar la cancelación, el sistema procesará automáticamente la devolución 
                          según las políticas configuradas. La devolución se realizará por el mismo método 
                          de pago utilizado originalmente.
                        </p>
                        <p className="mt-2">
                          <strong>Tiempo de procesamiento:</strong> 1-3 días hábiles para tarjetas de crédito, 
                          inmediato para pagos en efectivo.
                        </p>
                      </>
                    ) : (
                      <>
                        <p>
                          <strong>⚠️ Reembolso manual requerido:</strong> La pasarela de pago no soporta 
                          reembolsos automáticos. Se generará un reembolso en estado 'Pendiente' que el 
                          staff debe procesar manualmente.
                        </p>
                        <p className="mt-2">
                          <strong>Próximos pasos:</strong> El equipo de administración recibirá una 
                          notificación para procesar la devolución por el método correspondiente.
                        </p>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Advertencia de Confirmación */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4" role="alert" aria-label="Advertencia sobre la cancelación">
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

        {/* Pantalla de Éxito - Cancelación Completada */}
        {step === 'success' && cancellationData && (
          <div className="space-y-6" id="cancellation-success-description">
            {/* Mensaje de Éxito */}
            <div className="text-center py-6">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
                <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">¡Cancelación Exitosa!</h3>
              <p className="text-gray-600">
                {getRefundDetails()?.generated_voucher ? (
                  <>
                    La reserva ha sido cancelada correctamente y se ha generado un voucher de crédito.
                  </>
                ) : (
                  <>
                    La reserva ha sido cancelada correctamente y el reembolso está siendo procesado.
                  </>
                )}
              </p>
            </div>

            {/* Información del Reembolso */}
            {getRefundDetails() && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-6" role="region" aria-label="Detalles del reembolso">
                <h4 className="font-semibold text-green-900 mb-4 text-lg">Información del Reembolso</h4>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-green-800 font-medium">ID del Reembolso:</span>
                      <span className="ml-2 text-green-900 font-mono">#{getRefundDetails().id}</span>
                    </div>
                    <div>
                      <span className="text-green-800 font-medium">Monto:</span>
                      <span className="ml-2 text-green-900 font-bold text-lg">
                        {formatCurrency(getRefundDetails().amount)}
                      </span>
                    </div>
                    <div>
                      <span className="text-green-800 font-medium">Estado:</span>
                      <Badge 
                        variant={getRefundStatusBadgeVariant(getRefundDetails().status)} 
                        size="sm" 
                        className="ml-2"
                      >
                        {getRefundStatusText(getRefundDetails().status)}
                      </Badge>
                    </div>
                    <div>
                      <span className="text-green-800 font-medium">Método:</span>
                      <span className="ml-2 text-green-900">
                        {getRefundMethodLabel(getRefundDetails().method)}
                      </span>
                    </div>
                  </div>

                  {getRefundDetails().external_reference && (
                    <div className="bg-green-100 rounded-lg p-3">
                      <span className="text-green-800 font-medium">Referencia Externa:</span>
                      <span className="ml-2 text-green-900 font-mono text-sm">
                        {getRefundDetails().external_reference}
                      </span>
                    </div>
                  )}

                  {getRefundDetails().processed_at && (
                    <div>
                      <span className="text-green-800 font-medium">Procesado el:</span>
                      <span className="ml-2 text-green-900">
                        {formatDateTime(getRefundDetails().processed_at)}
                      </span>
                    </div>
                  )}

                  {getRefundDetails().processing_days && !getRefundDetails().processed_at && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <div className="flex items-center">
                        <svg className="h-4 w-4 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-blue-800 text-sm">
                          <strong>Tiempo estimado de procesamiento:</strong> {getRefundDetails().processing_days} días hábiles
                        </span>
                      </div>
                    </div>
                  )}

                  {getRefundDetails().requires_manual_processing && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                      <div className="flex items-center">
                        <svg className="h-4 w-4 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                        <span className="text-yellow-800 text-sm">
                          <strong>Procesamiento manual requerido:</strong> El equipo de administración procesará este reembolso manualmente.
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Información del Voucher Generado */}
                  {getRefundDetails().generated_voucher && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center mb-3">
                        <svg className="h-5 w-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h4 className="font-semibold text-green-900">Voucher de Crédito Generado</h4>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-green-800 font-medium">Código del Voucher:</span>
                          <span className="ml-2 font-mono text-green-900 bg-green-100 px-2 py-1 rounded">
                            {getRefundDetails().generated_voucher.code}
                          </span>
                        </div>
                        <div>
                          <span className="text-green-800 font-medium">Monto:</span>
                          <span className="ml-2 text-green-900 font-bold">
                            {new Intl.NumberFormat('es-AR', {
                              style: 'currency',
                              currency: 'ARS'
                            }).format(getRefundDetails().generated_voucher.amount)}
                          </span>
                        </div>
                        <div>
                          <span className="text-green-800 font-medium">Estado:</span>
                          <span className="ml-2 text-green-900">
                            {getRefundDetails().generated_voucher.status_display}
                          </span>
                        </div>
                        <div>
                          <span className="text-green-800 font-medium">Válido hasta:</span>
                          <span className="ml-2 text-green-900">
                            {getRefundDetails().generated_voucher.expiry_date ? 
                              new Date(getRefundDetails().generated_voucher.expiry_date).toLocaleDateString('es-AR') : '—'
                            }
                          </span>
                        </div>
                      </div>
                      <div className="mt-3 p-3 bg-green-100 rounded-lg">
                        <p className="text-green-800 text-sm">
                          <strong>¡Voucher listo para usar!</strong> Este voucher puede ser utilizado para futuras reservas en el hotel. 
                          El código del voucher es: <span className="font-mono font-bold">{getRefundDetails().generated_voucher.code}</span>
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Información de Cancelación */}
            {getCancellationDetails() && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4" role="region" aria-label="Detalles de la cancelación">
                <h4 className="font-semibold text-gray-900 mb-3">Detalles de la Cancelación</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Motivo:</span>
                    <span className="ml-2 font-medium text-gray-900">{getCancellationDetails().reason}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Política aplicada:</span>
                    <span className="ml-2 font-medium text-gray-900">{getCancellationDetails().policy_applied}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Tipo de cancelación:</span>
                    <span className="ml-2 font-medium text-gray-900 capitalize">{getCancellationDetails().cancellation_type}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Cancelado por:</span>
                    <span className="ml-2 font-medium text-gray-900">{getCancellationDetails().cancelled_by?.full_name || 'Sistema'}</span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-gray-600">Fecha de cancelación:</span>
                    <span className="ml-2 font-medium text-gray-900">
                      {formatDateTime(getCancellationDetails().cancelled_at)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Resumen Financiero Final */}
            {getFinancialSummary() && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6" role="region" aria-label="Resumen financiero final">
                <h5 className="font-semibold text-blue-900 mb-4 text-lg">Resumen Financiero Final</h5>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-blue-800">Total pagado:</span>
                    <span className="font-semibold text-blue-900 text-lg">
                      {formatCurrency(getFinancialSummary().total_paid)}
                    </span>
                  </div>
                  
                  {getFinancialSummary().penalty_amount > 0 && (
                    <div className="flex justify-between items-center text-red-600">
                      <span>Penalidad aplicada:</span>
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

            {/* Información Adicional */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="flex items-start">
                <svg className="h-5 w-5 text-gray-400 mt-0.5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h4 className="text-sm font-medium text-gray-900">Próximos pasos</h4>
                  <div className="mt-2 text-sm text-gray-600">
                    <ul className="list-disc list-inside space-y-1">
                      <li>Recibirás una confirmación por email con los detalles del reembolso</li>
                      {getRefundDetails()?.generated_voucher ? (
                        <>
                          <li>Se ha generado un voucher de crédito con el código: <span className="font-mono font-bold text-green-600">{getRefundDetails().generated_voucher.code}</span></li>
                          <li>El voucher es válido hasta el {getRefundDetails().generated_voucher.expiry_date ? new Date(getRefundDetails().generated_voucher.expiry_date).toLocaleDateString('es-AR') : '—'}</li>
                          <li>Puedes usar este voucher para futuras reservas ingresando el código en el campo correspondiente</li>
                        </>
                      ) : (
                        <li>El reembolso aparecerá en tu método de pago original en los próximos días</li>
                      )}
                      <li>Si tienes preguntas, contacta al hotel directamente</li>
                    </ul>
                  </div>
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