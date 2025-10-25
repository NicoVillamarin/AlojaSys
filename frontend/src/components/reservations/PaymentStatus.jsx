import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import Badge from 'src/components/Badge'

const PaymentStatus = ({ reservationId, reservationData }) => {
  const { t } = useTranslation()
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
      <div className="text-xs text-gray-500">
        Cargando pagos...
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-xs text-red-500">
        Error cargando pagos
      </div>
    )
  }

  if (!payments || payments.length === 0) {
    return (
      <div className="text-xs text-gray-500">
        Sin pagos
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

  return (
    <div className="space-y-2">
      {/* Estado principal del pago */}
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

      {/* Detalles de pagos */}
      <div className="text-xs text-gray-600 space-y-1">
        <div className="flex justify-between">
          <span>Total Reserva:</span>
          <span className="font-medium">
            ${totalPrice.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span>Total Pagado:</span>
          <span className="font-medium text-green-600">
            ${totalPaid.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
          </span>
        </div>

        {!isFullyPaid && (
          <div className="flex justify-between">
            <span>Saldo Pendiente:</span>
            <span className="font-medium text-red-600">
              ${balanceDue.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
            </span>
          </div>
        )}
      </div>

      {/* Lista de pagos individuales */}
      {payments.length > 0 && (
        <div className="text-xs">
          <div className="font-medium text-gray-700 mb-1">Pagos Realizados:</div>
          <div className="space-y-1">
            {payments.map((payment, index) => (
              <div key={payment.id || index} className="flex justify-between items-center">
                <div className="flex items-center gap-1">
                  <span className="text-gray-600">
                    {payment.is_deposit ? 'Seña' : 'Pago'}
                  </span>
                  <span className="text-gray-500">
                    ({payment.method})
                  </span>
                </div>
                <span className="font-medium">
                  ${parseFloat(payment.amount || 0).toLocaleString('es-AR', { minimumFractionDigits: 2 })}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default PaymentStatus
