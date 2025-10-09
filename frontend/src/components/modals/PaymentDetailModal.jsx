import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import Badge from 'src/components/Badge'
import { format, parseISO } from 'date-fns'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import CardCreditIcon from 'src/assets/icons/CardCreditIcon'
import CheckCircleIcon from 'src/assets/icons/CheckCircleIcon'
import ExclamationTriangleIcon from 'src/assets/icons/ExclamationTriangleIcon'
import ClockIcon from 'src/assets/icons/ClockIcon'
import CrashIcon from 'src/assets/icons/CrashIcon'
import TranfCrash from 'src/assets/icons/TranfCrash'
import PostnetIcon from 'src/assets/icons/PostnetIcon'

const PaymentDetailModal = ({ 
  isOpen, 
  onClose, 
  reservationId, 
  reservationData 
}) => {
  const { t } = useTranslation()
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!isOpen || !reservationId) return
    
    const loadPayments = async () => {
      setLoading(true)
      setError(null)
      try {
        const base = getApiURL() || ''
        const response = await fetchWithAuth(`${base}/api/payments/reservation/${reservationId}/payments/`, { 
          method: 'GET' 
        })
        setPayments(response.results || response || [])
      } catch (err) {
        setError(err.message || 'Error cargando pagos')
        console.error('Error loading payments:', err)
      } finally {
        setLoading(false)
      }
    }

    loadPayments()
  }, [isOpen, reservationId])

  const getPaymentMethodIcon = (payment) => {
    const method = payment.method?.toLowerCase()
    const type = payment.type
    
    if (type === 'manual') {
      switch (method) {
        case 'cash':
          return <div className="w-9 h-9 rounded-full bg-green-100 flex items-center justify-center text-green-600 text-xs font-bold">
            <CrashIcon />
          </div>
        case 'transfer':
          return <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-xs font-bold">
            <TranfCrash />
          </div>
        case 'pos':
        case 'postnet':
          return <div className="w-9 h-9 rounded-full bg-orange-100 flex items-center justify-center text-orange-600 text-xs font-bold">
            <PostnetIcon />
          </div>
        default:
          return  <div className="w-9 h-9 rounded-full bg-green-100 flex items-center justify-center text-green-600 text-xs font-bold">
            <CardCreditIcon />
            </div>
      }
    } else {
      // Pagos online (Mercado Pago)
      return  <div className="w-9 h-9 rounded-full bg-green-100 flex items-center justify-center text-green-600 text-xs font-bold">
      <CardCreditIcon />
      </div>
    }
  }

  const getPaymentStatusVariant = (status) => {
    switch (status?.toLowerCase()) {
      case 'approved':
        return 'success'
      case 'pending':
      case 'created':
        return 'warning'
      case 'rejected':
        return 'error'
      case 'cancelled':
        return 'default'
      default:
        return 'default'
    }
  }

  const getPaymentMethodLabel = (payment) => {
    const method = payment.method?.toLowerCase()
    const type = payment.type
    
    const methodLabels = {
      'mercado_pago': t('payments.methods.mercado_pago'),
      'card': t('payments.methods.card'),
      'credit_card': t('payments.methods.card'),
      'debit_card': t('payments.methods.card'),
      'cash': t('payments.methods.cash'),
      'transfer': t('payments.methods.transfer'),
      'pos': t('payments.methods.pos'),
      'postnet': t('payments.methods.pos'),
      'check': t('payments.methods.check'),
      'other': t('payments.methods.other')
    }
    
    return methodLabels[method] || t('payments.methods.other')
  }

  const totalPaid = payments
    .filter(p => p.status === 'approved')
    .reduce((sum, p) => sum + (parseFloat(p.amount) || 0), 0)

  const reservationTotal = parseFloat(reservationData?.total_price) || 0
  const remainingAmount = Math.max(0, reservationTotal - totalPaid)

  if (!isOpen) return null

  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={onClose}
      title={t('payments.detail_modal.title', { 
        reservation: reservationData?.display_name || `#${reservationId}` 
      })}
      size="lg"
    >
      <div className="space-y-6">
        {/* Resumen de pagos */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              {t('payments.detail_modal.summary')}
            </h3>
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="w-5 h-5 text-blue-600" />
              <span className="text-sm text-gray-600">
                {t('payments.detail_modal.total_reservation')}
              </span>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                $ {reservationTotal.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">
                {t('payments.detail_modal.total_amount')}
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                $ {totalPaid.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">
                {t('payments.detail_modal.paid_amount')}
              </div>
            </div>
            
            <div className="text-center">
              <div className={`text-2xl font-bold ${remainingAmount > 0 ? 'text-orange-600' : 'text-green-600'}`}>
                $ {remainingAmount.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">
                {remainingAmount > 0 
                  ? t('payments.detail_modal.remaining_amount')
                  : t('payments.detail_modal.fully_paid')
                }
              </div>
            </div>
          </div>

          {/* Barra de progreso */}
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>{t('payments.detail_modal.payment_progress')}</span>
              <span>{reservationTotal > 0 ? Math.round((totalPaid / reservationTotal) * 100) : 0}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-green-500 to-green-600 h-2 rounded-full transition-all duration-300"
                style={{ 
                  width: reservationTotal > 0 ? `${Math.min((totalPaid / reservationTotal) * 100, 100)}%` : '0%' 
                }}
              />
            </div>
          </div>
        </div>

        {/* Lista de pagos */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {t('payments.detail_modal.payment_history')}
          </h3>

          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2 text-gray-600">{t('common.loading')}</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
              <ExclamationTriangleIcon className="w-8 h-8 text-red-500 mx-auto mb-2" />
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {!loading && !error && payments.length === 0 && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <ClockIcon className="w-8 h-8 text-gray-400" />
              </div>
              <h4 className="text-lg font-medium text-gray-900 mb-2">
                {t('payments.detail_modal.no_payments_title')}
              </h4>
              <p className="text-gray-600 max-w-md mx-auto">
                {t('payments.detail_modal.no_payments_description')}
              </p>
            </div>
          )}

          {!loading && !error && payments.length > 0 && (
            <div className="space-y-3">
              {/* Nota informativa si hay inconsistencias */}
              {totalPaid === 0 && reservationData?.status && ['confirmed', 'check_in', 'check_out'].includes(reservationData.status) && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                  <div className="flex items-start gap-3">
                    <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-medium text-yellow-800">
                        {t('payments.detail_modal.inconsistency_warning_title')}
                      </h4>
                      <p className="text-sm text-yellow-700 mt-1">
                        {t('payments.detail_modal.inconsistency_warning_description')}
                      </p>
                    </div>
                  </div>
                </div>
              )}
              
              {payments.map((payment, index) => (
                <div 
                  key={payment.id || index}
                  className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex-shrink-0">
                      {getPaymentMethodIcon(payment)}
                    </div>
                      <div>
                        <div className="font-medium text-gray-900">
                          {getPaymentMethodLabel(payment)}
                        </div>
                        <div className="text-sm text-gray-600">
                          {payment.created_at 
                            ? format(parseISO(payment.created_at), 'dd/MM/yyyy HH:mm')
                            : '—'
                        }
                        </div>
                        {payment.type === 'online' && payment.reference && (
                          <div className="text-xs text-gray-500">
                            {t('payments.detail_modal.reference')}: {payment.reference}
                          </div>
                        )}
                        {payment.type === 'manual' && (
                          <div className="text-xs text-gray-500">
                            {t('payments.detail_modal.manual_payment')}
                          </div>
                        )}
                        {payment.description && (
                          <div className="text-xs text-gray-500">
                            {payment.description}
                          </div>
                        )}
                      </div>
                  </div>
                    
                    <div className="text-right">
                      <div className="text-lg font-semibold text-gray-900">
                        $ {parseFloat(payment.amount || 0).toLocaleString()}
                      </div>
                      <Badge 
                        variant={getPaymentStatusVariant(payment.status)} 
                        size="sm"
                      >
                        {t(`payments.statuses.${payment.status}`, payment.status)}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </ModalLayout>
  )
}

export default PaymentDetailModal