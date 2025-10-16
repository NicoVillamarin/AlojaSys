import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import Button from 'src/components/Button'
import CheckIcon from 'src/assets/icons/CheckIcon'
import XIcon from 'src/assets/icons/Xicon'
import { useUpdate } from 'src/hooks/useUpdate'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

const RefundDetailsModal = ({ isOpen, onClose, refund, onSuccess }) => {
  const { t } = useTranslation()

  const { mutate: updateRefund, isPending: updating } = useUpdate({
    resource: 'payments/refunds',
    onSuccess: (data) => {
      console.log('Refund updated successfully:', data)
      onSuccess && onSuccess(data)
      onClose && onClose()
    },
    onError: (error) => {
      console.error('Error updating refund status:', error)
    }
  })

  if (!refund) return null

  const getStatusIcon = (status) => {
    const statusConfig = {
      'pending': { icon: <XIcon color="orange" />, label: t('payments.refunds.status.pending'), color: 'text-orange-600' },
      'processing': { icon: <XIcon color="blue" />, label: t('payments.refunds.status.processing'), color: 'text-blue-600' },
      'completed': { icon: <CheckIcon color="green" />, label: t('payments.refunds.status.completed'), color: 'text-green-600' },
      'failed': { icon: <XIcon color="red" />, label: t('payments.refunds.status.failed'), color: 'text-red-600' },
      'cancelled': { icon: <XIcon color="gray" />, label: t('payments.refunds.status.cancelled'), color: 'text-gray-600' }
    }
    return statusConfig[status] || { icon: <XIcon color="gray" />, label: status, color: 'text-gray-600' }
  }

  const getMethodLabel = (method) => {
    const methods = {
      'cash': t('payments.refunds.methods.cash'),
      'bank_transfer': t('payments.refunds.methods.bank_transfer'),
      'credit_card': t('payments.refunds.methods.credit_card'),
      'voucher': t('payments.refunds.methods.voucher'),
      'original_payment': t('payments.refunds.methods.original_payment')
    }
    return methods[method] || method
  }

  const getReasonLabel = (reason) => {
    const reasons = {
      'cancellation': t('payments.refunds.reasons.cancellation'),
      'partial_cancellation': t('payments.refunds.reasons.partial_cancellation'),
      'overpayment': t('payments.refunds.reasons.overpayment'),
      'discount_applied': t('payments.refunds.reasons.discount_applied'),
      'admin_adjustment': t('payments.refunds.reasons.admin_adjustment'),
      'customer_request': t('payments.refunds.reasons.customer_request'),
      'system_error': t('payments.refunds.reasons.system_error')
    }
    return reasons[reason] || reason
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    try {
      return format(new Date(dateString), 'dd/MM/yyyy HH:mm', { locale: es })
    } catch {
      return dateString
    }
  }

  const formatAmount = (amount) => {
    if (!amount) return '$0.00'
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 2
    }).format(amount)
  }

  const handleStatusUpdate = (newStatus) => {
    console.log('Updating refund status:', { id: refund.id, newStatus, currentStatus: refund.status })
    updateRefund({ id: refund.id, body: { status: newStatus } })
  }

  const statusInfo = getStatusIcon(refund.status)
  const canUpdateStatus = ['pending', 'processing'].includes(refund.status)

  return (
    <ModalLayout 
      isOpen={isOpen} 
      onClose={onClose} 
      title={t('payments.refunds.details_title', { id: refund.id })}
      size="lg"
      showFooter={false}
    >
      <div className="space-y-6">
        {/* Información básica */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700">{t('payments.refunds.refund_id')}</label>
              <p className="text-lg font-semibold text-gray-900">N° {refund.id}</p>
            </div>
            
            <div>
              <label className="text-sm font-medium text-gray-700">{t('payments.refunds.reservation_id')}</label>
              <p className="text-lg font-semibold text-gray-900">N° {refund.reservation_id}</p>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">{t('payments.refunds.amount')}</label>
              <p className="text-2xl font-bold text-green-600">{formatAmount(refund.amount)}</p>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">{t('payments.refunds.status_label')}</label>
              <div className="flex items-center gap-2 mt-1">
                {statusInfo.icon}
                <span className={`text-lg font-semibold ${statusInfo.color}`}>{statusInfo.label}</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700">{t('payments.refunds.method')}</label>
              <p className="text-lg font-semibold text-gray-900">{getMethodLabel(refund.refund_method)}</p>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">{t('payments.refunds.reason')}</label>
              <p className="text-lg font-semibold text-gray-900">{getReasonLabel(refund.reason)}</p>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">{t('payments.refunds.processing_days')}</label>
              <p className="text-lg font-semibold text-gray-900">{refund.processing_days} {t('common.days')}</p>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">{t('payments.refunds.created_at')}</label>
              <p className="text-lg font-semibold text-gray-900">{formatDate(refund.created_at)}</p>
            </div>
          </div>
        </div>

        {/* Motivo de Cancelación */}
        {refund.reason === 'cancellation' && (
          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('payments.refunds.cancellation_reason')}</h3>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h4 className="text-sm font-medium text-red-800">
                    {t('payments.refunds.cancellation_reason_title')}
                  </h4>
                  <p className="text-sm text-red-700 mt-1">
                    {(() => {
                      console.log('Debug notas del reembolso:', {
                        notes: refund.notes,
                        includesMotivo: refund.notes && refund.notes.includes('Motivo:'),
                        splitResult: refund.notes ? refund.notes.split('Motivo: ') : null
                      })
                      
                      if (refund.notes && refund.notes.includes('Motivo:')) {
                        return refund.notes.split('Motivo: ')[1]
                      }
                      return 'Motivo no especificado - Notas: ' + (refund.notes || 'Sin notas')
                    })()}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Información adicional */}
        {(refund.external_reference || refund.notes) && (
          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('payments.refunds.additional_info')}</h3>
            
            {refund.external_reference && (
              <div className="mb-4">
                <label className="text-sm font-medium text-gray-700">{t('payments.refunds.external_reference')}</label>
                <p className="text-lg font-semibold text-gray-900">{refund.external_reference}</p>
              </div>
            )}

            {refund.notes && (
              <div>
                <label className="text-sm font-medium text-gray-700">{t('payments.refunds.notes')}</label>
                <p className="text-lg font-semibold text-gray-900 whitespace-pre-wrap">{refund.notes}</p>
              </div>
            )}
          </div>
        )}

        {/* Fechas importantes */}
        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('payments.refunds.timeline')}</h3>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm font-medium text-gray-700">{t('payments.refunds.created_at')}</span>
              <span className="text-sm text-gray-900">{formatDate(refund.created_at)}</span>
            </div>
            
            {refund.updated_at && (
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-sm font-medium text-gray-700">{t('payments.refunds.updated_at')}</span>
                <span className="text-sm text-gray-900">{formatDate(refund.updated_at)}</span>
              </div>
            )}
            
            {refund.processed_at && (
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-sm font-medium text-gray-700">{t('payments.refunds.processed_at')}</span>
                <span className="text-sm text-gray-900">{formatDate(refund.processed_at)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Acciones */}
        {canUpdateStatus && (
          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('payments.refunds.actions')}</h3>
            
            <div className="flex gap-3">
              {refund.status === 'pending' && (
                <Button
                  variant="primary"
                  size="md"
                  onClick={() => handleStatusUpdate('processing')}
                  disabled={updating}
                >
                  {updating ? t('common.updating') : t('payments.refunds.mark_processing')}
                </Button>
              )}
              
              {refund.status === 'processing' && (
                <Button
                  variant="success"
                  size="md"
                  onClick={() => handleStatusUpdate('completed')}
                  disabled={updating}
                >
                  {updating ? t('common.updating') : t('payments.refunds.mark_completed')}
                </Button>
              )}
              
              <Button
                variant="danger"
                size="md"
                onClick={() => handleStatusUpdate('failed')}
                disabled={updating}
              >
                {updating ? t('common.updating') : t('payments.refunds.mark_failed')}
              </Button>
            </div>
          </div>
        )}
      </div>
    </ModalLayout>
  )
}

export default RefundDetailsModal
