import { useState, useEffect, forwardRef } from 'react'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import Badge from 'src/components/Badge'

const PaymentStatusBadge = forwardRef(({ reservationId, reservationData }, ref) => {
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)

  // Cargar pagos de la reserva
  useEffect(() => {
    if (!reservationId) return

    const loadPayments = async () => {
      try {
        setLoading(true)
        const response = await fetchWithAuth(`${getApiURL()}/api/reservations/${reservationId}/payments/`)
        setPayments(response || [])
      } catch (err) {
        console.error('Error cargando pagos:', err)
      } finally {
        setLoading(false)
      }
    }

    loadPayments()
  }, [reservationId, reservationData?.total_price, reservationData?.total_paid])

  if (loading) {
    return (
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
        <span className="text-gray-400 text-xs">Cargando...</span>
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
  // Determinar si hay señas:
  // - Si el backend marcó explícitamente is_deposit=true, es seña
  // - Heurística: si hay algún pago explícito que sea menor al total, es seña
  //   (pero NO aplicar heurística si el pago es igual o casi igual al total - podría ser pago total con rounding)
  const hasDeposits = payments.some(p => {
    // Si el backend marcó explícitamente is_deposit, usar ese valor
    if (p.is_deposit === true) return true
    if (p.is_deposit === false) return false
    // Heurística: solo considerar seña si el monto es significativamente menor al total
    // (más de 1 peso de diferencia para evitar problemas de redondeo)
    return parseFloat(p.amount || 0) + 1.0 < totalPrice
  })

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
    <div ref={ref} className="flex items-center gap-2 cursor-help">
      <Badge variant={paymentStatus.variant} size="sm">
        {paymentStatus.text}
      </Badge>
      {hasDeposits && (
        <Badge variant="payment-deposit" size="sm">
          Con Seña
        </Badge>
      )}
    </div>
  )
})

export default PaymentStatusBadge
