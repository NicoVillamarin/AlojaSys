import { useState, useEffect } from 'react'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import Badge from 'src/components/Badge'

const PaymentTooltip = ({ reservationId, reservationData }) => {
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Cargar pagos de la reserva
  useEffect(() => {
    if (!reservationId) return

    const loadPayments = async () => {
      try {
        setLoading(true)
        setError(null)
        
        const response = await fetchWithAuth(`${getApiURL()}/api/reservations/${reservationId}/payments/`)
        setPayments(response || [])
      } catch (err) {
        console.error('Error cargando pagos:', err)
        setError('Error cargando pagos')
      } finally {
        setLoading(false)
      }
    }

    loadPayments()
  }, [reservationId])

  if (loading) {
    return (
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
        <span className="text-gray-400 text-xs">Cargando...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 bg-red-400 rounded-full"></div>
        <span className="text-red-400 text-xs">Error</span>
      </div>
    )
  }

  if (!payments || payments.length === 0) {
    return (
      <div className="flex items-center gap-2">
        <Badge variant="payment-pending" size="sm">
          Sin Pagos
        </Badge>
      </div>
    )
  }

  // Calcular totales
  const totalPaid = payments.reduce((sum, payment) => sum + parseFloat(payment.amount || 0), 0)
  const totalPrice = parseFloat(reservationData?.total_price || 0)
  const balanceDue = totalPrice - totalPaid
  const isFullyPaid = balanceDue <= 0.01
  const hasDeposits = payments.some(p => p.is_deposit)
  const hasFullPayments = payments.some(p => !p.is_deposit)

  // Determinar el estado del pago
  const getPaymentStatus = () => {
    if (isFullyPaid) {
      return { variant: 'payment-paid', text: 'Pagado' }
    } else if (totalPaid > 0) {
      return { variant: 'payment-partial', text: 'Pago Parcial' }
    } else {
      return { variant: 'payment-pending', text: 'Pendiente' }
    }
  }

  const paymentStatus = getPaymentStatus()

  // Contenido del tooltip
  const tooltipContent = (
    <div className="space-y-3 min-w-[280px]">
      {/* Header con estado principal */}
      <div className="flex items-center justify-between">
        <span className="font-semibold text-gray-100">Estado de Pagos</span>
        <div className="flex items-center gap-2">
          <Badge variant={paymentStatus.variant} size="sm">
            {paymentStatus.text}
          </Badge>
          {hasDeposits && (
            <Badge variant="payment-deposit" size="sm">
              Con Seña
            </Badge>
          )}
        </div>
      </div>

      {/* Resumen financiero */}
      <div className="space-y-2">
        <div className="flex justify-between items-center py-1 border-b border-gray-700">
          <span className="text-gray-300">Total Reserva:</span>
          <span className="font-semibold text-white">
            ${totalPrice.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
          </span>
        </div>
        
        <div className="flex justify-between items-center py-1 border-b border-gray-700">
          <span className="text-gray-300">Total Pagado:</span>
          <span className="font-semibold text-green-400">
            ${totalPaid.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
          </span>
        </div>

        {!isFullyPaid && (
          <div className="flex justify-between items-center py-1 border-b border-gray-700">
            <span className="text-gray-300">Saldo Pendiente:</span>
            <span className="font-semibold text-red-400">
              ${balanceDue.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
            </span>
          </div>
        )}
      </div>

      {/* Lista de pagos individuales */}
      {payments.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-200 border-b border-gray-700 pb-1">
            Pagos Realizados:
          </div>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {payments.map((payment, index) => (
              <div key={payment.id || index} className="flex justify-between items-center py-1 px-2 bg-gray-800 rounded">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    payment.is_deposit ? 'bg-blue-400' : 'bg-green-400'
                  }`}></div>
                  <span className="text-gray-300 text-xs">
                    {payment.is_deposit ? 'Seña' : 'Pago'}
                  </span>
                  <span className="text-gray-400 text-xs">
                    ({payment.method})
                  </span>
                </div>
                <span className="font-medium text-white text-xs">
                  ${parseFloat(payment.amount || 0).toLocaleString('es-AR', { minimumFractionDigits: 2 })}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer con información adicional */}
      <div className="text-xs text-gray-400 pt-2 border-t border-gray-700">
        {isFullyPaid ? (
          <span className="text-green-400">✓ Reserva completamente pagada</span>
        ) : (
          <span>Saldo pendiente se cobrará según política del hotel</span>
        )}
      </div>
    </div>
  )

  // Solo mostrar el contenido del tooltip, no el trigger
  return tooltipContent
}

export default PaymentTooltip
