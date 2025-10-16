import React from 'react'
import { format, parseISO, addDays } from 'date-fns'
import { es } from 'date-fns/locale'

const CancellationPolicyPreview = ({ policy, checkInDate, totalAmount }) => {
  if (!policy) return null

  const calculateRules = () => {
    if (!checkInDate) return null

    const checkIn = parseISO(checkInDate)
    const now = new Date()
    const timeUntilCheckIn = checkIn.getTime() - now.getTime()
    
    // Convertir a la unidad configurada
    const getSeconds = (time, unit) => {
      switch (unit) {
        case 'hours': return time * 3600
        case 'days': return time * 86400
        case 'weeks': return time * 604800
        default: return time * 3600
      }
    }

    const freeCancellationSeconds = getSeconds(policy.free_cancellation_time, policy.free_cancellation_unit)
    const partialRefundSeconds = getSeconds(policy.partial_refund_time, policy.partial_refund_unit)
    const noRefundSeconds = getSeconds(policy.no_refund_time, policy.no_refund_unit)

    const timeUntilCheckInSeconds = timeUntilCheckIn / 1000

    if (timeUntilCheckInSeconds >= freeCancellationSeconds) {
      return {
        type: 'free',
        refundPercentage: 100,
        feeType: 'none',
        feeValue: 0,
        message: policy.free_cancellation_message || `Cancelación gratuita hasta ${policy.free_cancellation_time} ${policy.free_cancellation_unit} antes del check-in`
      }
    } else if (timeUntilCheckInSeconds >= partialRefundSeconds) {
      return {
        type: 'partial',
        refundPercentage: policy.partial_refund_percentage,
        feeType: policy.cancellation_fee_type,
        feeValue: policy.cancellation_fee_value,
        message: policy.partial_refund_message || `Devolución del ${policy.partial_refund_percentage}% hasta ${policy.partial_refund_time} ${policy.partial_refund_unit} antes del check-in`
      }
    } else {
      return {
        type: 'no_refund',
        refundPercentage: 0,
        feeType: policy.cancellation_fee_type,
        feeValue: policy.cancellation_fee_value,
        message: policy.no_refund_message || `Sin devolución después de ${policy.no_refund_time} ${policy.no_refund_unit} antes del check-in`
      }
    }
  }

  const rules = calculateRules()
  if (!rules) return null

  const calculateRefundAmount = () => {
    if (!totalAmount) return 0
    
    const refundAmount = (totalAmount * rules.refundPercentage) / 100
    
    // Aplicar penalidad si corresponde
    let penalty = 0
    if (rules.feeType === 'percentage') {
      penalty = (totalAmount * rules.feeValue) / 100
    } else if (rules.feeType === 'fixed') {
      penalty = rules.feeValue
    } else if (rules.feeType === 'first_night') {
      // Asumir que la primera noche es el 30% del total
      penalty = totalAmount * 0.3
    }
    
    return Math.max(0, refundAmount - penalty)
  }

  const refundAmount = calculateRefundAmount()

  const getStatusColor = (type) => {
    switch (type) {
      case 'free': return 'text-green-600 bg-green-100'
      case 'partial': return 'text-yellow-600 bg-yellow-100'
      case 'no_refund': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = (type) => {
    switch (type) {
      case 'free': return '✅'
      case 'partial': return '⚠️'
      case 'no_refund': return '❌'
      default: return 'ℹ️'
    }
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Vista Previa de la Política
        </h3>
        <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(rules.type)}`}>
          <span className="mr-2">{getStatusIcon(rules.type)}</span>
          {rules.type === 'free' && 'Cancelación Gratuita'}
          {rules.type === 'partial' && 'Devolución Parcial'}
          {rules.type === 'no_refund' && 'Sin Devolución'}
        </div>
      </div>

      <div className="space-y-4">
        {/* Información de la reserva */}
        {checkInDate && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Información de la Reserva</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Check-in:</span>
                <span className="ml-2 font-medium">
                  {format(parseISO(checkInDate), 'dd/MM/yyyy', { locale: es })}
                </span>
              </div>
              {totalAmount && (
                <div>
                  <span className="text-gray-600">Total:</span>
                  <span className="ml-2 font-medium">${totalAmount.toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Reglas de cancelación */}
        <div className="space-y-3">
          <h4 className="font-medium text-gray-900">Reglas de Cancelación</h4>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Cancelación Gratuita</span>
              <span className="text-sm font-medium">
                {policy.free_cancellation_time} {policy.free_cancellation_unit} antes
              </span>
            </div>
            
            <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Devolución Parcial</span>
              <span className="text-sm font-medium">
                {policy.partial_refund_time} {policy.partial_refund_unit} antes ({policy.partial_refund_percentage}%)
              </span>
            </div>
            
            <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Sin Devolución</span>
              <span className="text-sm font-medium">
                {policy.no_refund_time} {policy.no_refund_unit} antes
              </span>
            </div>
          </div>
        </div>

        {/* Cálculo de devolución */}
        {totalAmount && (
          <div className="bg-blue-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Cálculo de Devolución</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Monto total:</span>
                <span className="font-medium">${totalAmount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Devolución ({rules.refundPercentage}%):</span>
                <span className="font-medium">
                  ${((totalAmount * rules.refundPercentage) / 100).toLocaleString()}
                </span>
              </div>
              {rules.feeType !== 'none' && (
                <div className="flex justify-between text-red-600">
                  <span>Penalidad:</span>
                  <span className="font-medium">
                    -${rules.feeType === 'percentage' 
                      ? ((totalAmount * rules.feeValue) / 100).toLocaleString()
                      : rules.feeValue.toLocaleString()
                    }
                  </span>
                </div>
              )}
              <div className="flex justify-between text-lg font-semibold border-t border-blue-200 pt-2">
                <span>Devolución final:</span>
                <span className={refundAmount > 0 ? 'text-green-600' : 'text-red-600'}>
                  ${refundAmount.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Mensaje personalizado */}
        <div className="bg-amber-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">Mensaje para el Huésped</h4>
          <p className="text-sm text-gray-700">{rules.message}</p>
        </div>

        {/* Restricciones */}
        <div className="space-y-2">
          <h4 className="font-medium text-gray-900">Restricciones</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
            <div className="flex items-center">
              <span className={`w-2 h-2 rounded-full mr-2 ${policy.allow_cancellation_after_checkin ? 'bg-green-500' : 'bg-red-500'}`}></span>
              Cancelación después del check-in
            </div>
            <div className="flex items-center">
              <span className={`w-2 h-2 rounded-full mr-2 ${policy.allow_cancellation_after_checkout ? 'bg-green-500' : 'bg-red-500'}`}></span>
              Cancelación después del check-out
            </div>
            <div className="flex items-center">
              <span className={`w-2 h-2 rounded-full mr-2 ${policy.allow_cancellation_no_show ? 'bg-green-500' : 'bg-red-500'}`}></span>
              Cancelación de no-show
            </div>
            <div className="flex items-center">
              <span className={`w-2 h-2 rounded-full mr-2 ${policy.allow_cancellation_early_checkout ? 'bg-green-500' : 'bg-red-500'}`}></span>
              Cancelación por salida anticipada
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CancellationPolicyPreview
