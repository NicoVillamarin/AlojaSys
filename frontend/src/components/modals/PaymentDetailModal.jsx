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
  const [activeTab, setActiveTab] = useState('payments') // 'payments' o 'attachments'

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

  // Función para obtener archivos adjuntos de los pagos
  const getAttachments = () => {
    const attachments = []
    
    payments.forEach(payment => {
      // Transferencias bancarias con comprobantes
      if (payment.type === 'bank_transfer' && payment.receipt_url) {
        attachments.push({
          id: `transfer_${payment.id}`,
          type: 'receipt',
          name: payment.receipt_filename || t('payments.attachments.receipt'),
          url: payment.receipt_url,
          paymentId: payment.id,
          paymentType: t('payments.method.bank_transfer'),
          amount: payment.amount,
          date: payment.created_at,
          description: `${t('payments.attachments.receipt')} - ${payment.bank_name || 'Banco'}`
        })
      }
      
      // Otros tipos de archivos que podrían existir en el futuro
      // (vouchers, contratos, etc.)
    })
    
    return attachments
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

        {/* Pestañas */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('payments')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'payments'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {t('payments.detail_modal.payment_history')}
            </button>
            <button
              onClick={() => setActiveTab('attachments')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'attachments'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Archivos Adjuntos ({getAttachments().length})
            </button>
          </nav>
        </div>

        {/* Contenido de las pestañas */}
        {activeTab === 'payments' && (
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
        )}

        {activeTab === 'attachments' && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {t('payments.attachments.title')}
            </h3>
            
            {getAttachments().length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h4 className="text-lg font-medium text-gray-900 mb-2">
                  {t('payments.attachments.no_attachments')}
                </h4>
                <p className="text-gray-600 max-w-md mx-auto">
                  {t('payments.attachments.no_attachments_description')}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {getAttachments().map((attachment) => (
                  <div 
                    key={attachment.id}
                    className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex-shrink-0">
                          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-gray-900 truncate">
                            {attachment.name}
                          </div>
                          <div className="text-sm text-gray-600">
                            {attachment.description}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {attachment.paymentType} • ${parseFloat(attachment.amount || 0).toLocaleString()} • 
                            {attachment.date ? format(parseISO(attachment.date), 'dd/MM/yyyy HH:mm') : '—'}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <a
                          href={attachment.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                          {t('payments.attachments.view')}
                        </a>
                        <a
                          href={attachment.url}
                          download={attachment.name}
                          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          {t('payments.attachments.download')}
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </ModalLayout>
  )
}

export default PaymentDetailModal