import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import ModalLayout from 'src/layouts/ModalLayout'
import Badge from 'src/components/Badge'

function formatDate(dateString) {
  if (!dateString) return '—'
  try {
    const date = new Date(dateString)
    return date.toLocaleString('es-AR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return '—'
  }
}

function formatCurrency(amount) {
  if (!amount) return '—'
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS'
  }).format(parseFloat(amount))
}

function getStatusBadgeVariant(status) {
  const variants = {
    'Pendiente': 'warning',
    'Procesando': 'info',
    'Completado': 'success',
    'Fallido': 'error',
    'Cancelado': 'neutral'
  }
  return variants[status] || 'neutral'
}

function getEventTypeLabel(eventType) {
  const labels = {
    'created': 'Creado',
    'status_changed': 'Estado Cambiado',
    'processing_started': 'Procesamiento Iniciado',
    'processing_completed': 'Procesamiento Completado',
    'processing_failed': 'Procesamiento Fallido',
    'cancelled': 'Cancelado'
  }
  return labels[eventType] || eventType
}

export default function RefundDetailModal({ refundId, onClose, displayName }) {
  const { t } = useTranslation()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!refundId) return
    const base = getApiURL() || ''
    setLoading(true)
    setError(null)
    fetchWithAuth(`${base}/api/payments/refunds/${refundId}/history/`, { method: 'GET' })
      .then(json => setData(json))
      .catch(err => setError(err.message || 'Error cargando historial'))
      .finally(() => setLoading(false))
  }, [refundId])

  if (loading) {
    return (
      <ModalLayout
        isOpen={!!refundId}
        onClose={onClose}
        title={`Historial de Reembolso ${refundId ? `#${refundId}` : ''}`}
        size="lg"
        isDetail={true}
      >
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-500">Cargando historial...</div>
        </div>
      </ModalLayout>
    )
  }

  if (error) {
    return (
      <ModalLayout
        isOpen={!!refundId}
        onClose={onClose}
        title={`Historial de Reembolso ${refundId ? `#${refundId}` : ''}`}
        size="lg"
        isDetail={true}
      >
        <div className="flex items-center justify-center py-8">
          <div className="text-red-600">Error: {error}</div>
        </div>
      </ModalLayout>
    )
  }

  if (!data) {
    return (
      <ModalLayout
        isOpen={!!refundId}
        onClose={onClose}
        title={`Historial de Reembolso ${refundId ? `#${refundId}` : ''}`}
        size="lg"
        isDetail={true}
      >
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-500">No se encontró información del reembolso</div>
        </div>
      </ModalLayout>
    )
  }

  const { refund, voucher, status_changes, summary } = data

  return (
    <ModalLayout
      isOpen={!!refundId}
      onClose={onClose}
      title={`Historial de Reembolso #${refund.id}`}
      size="lg"
      isDetail={true}
    >
      <div className="space-y-6">
        {/* Información Principal del Reembolso */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Información del Reembolso</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-500">Monto</label>
              <div className="text-lg font-semibold text-green-600">{formatCurrency(refund.amount)}</div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Estado</label>
              <div className="mt-1">
                <Badge variant={getStatusBadgeVariant(refund.status)} size="sm">
                  {refund.status}
                </Badge>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Motivo</label>
              <div className="text-sm text-gray-900">{refund.reason}</div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Método de Reembolso</label>
              <div className="text-sm text-gray-900">{refund.refund_method}</div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Creado</label>
              <div className="text-sm text-gray-900">{formatDate(refund.created_at)}</div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Procesado</label>
              <div className="text-sm text-gray-900">{formatDate(refund.processed_at)}</div>
            </div>
            {refund.external_reference && (
              <div className="md:col-span-2">
                <label className="text-sm font-medium text-gray-500">Referencia Externa</label>
                <div className="text-sm font-mono bg-gray-100 px-2 py-1 rounded mt-1">
                  {refund.external_reference}
                </div>
              </div>
            )}
            {refund.notes && (
              <div className="md:col-span-2">
                <label className="text-sm font-medium text-gray-500">Notas</label>
                <div className="text-sm text-gray-900 bg-gray-100 p-2 rounded mt-1">
                  {refund.notes}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Información de la Reserva */}
        <div className="bg-blue-50 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Reserva Asociada</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-500">Reserva</label>
              <div className="text-sm font-semibold text-blue-600">{refund.reservation.display_name}</div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Hotel</label>
              <div className="text-sm text-gray-900">{refund.reservation.hotel_name}</div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Huésped</label>
              <div className="text-sm text-gray-900">{refund.reservation.guest_name}</div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Check-in</label>
              <div className="text-sm text-gray-900">{formatDate(refund.reservation.check_in)}</div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Check-out</label>
              <div className="text-sm text-gray-900">{formatDate(refund.reservation.check_out)}</div>
            </div>
          </div>
        </div>

        {/* Voucher Generado */}
        {voucher && (
          <div className="bg-green-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Voucher Generado</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Código</label>
                <div className="text-sm font-mono font-semibold text-green-600 bg-green-100 px-2 py-1 rounded">
                  {voucher.code}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Monto</label>
                <div className="text-sm font-semibold text-green-600">{formatCurrency(voucher.amount)}</div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Monto Restante</label>
                <div className="text-sm text-gray-900">{formatCurrency(voucher.remaining_amount)}</div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Estado</label>
                <div className="text-sm text-gray-900">{voucher.status}</div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Válido Hasta</label>
                <div className="text-sm text-gray-900">{formatDate(voucher.expiry_date)}</div>
              </div>
              {voucher.used_at && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Usado</label>
                  <div className="text-sm text-gray-900">{formatDate(voucher.used_at)}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Historial de Cambios */}
        {status_changes && status_changes.length > 0 && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Historial de Cambios</h3>
            <div className="space-y-3">
              {status_changes.map((change, index) => (
                <div key={index} className="border-l-4 border-blue-200 pl-4 py-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-gray-900">
                        {getEventTypeLabel(change.event_type)}
                      </span>
                      <Badge variant={getStatusBadgeVariant(change.status)} size="sm">
                        {change.status}
                      </Badge>
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatDate(change.timestamp)}
                    </div>
                  </div>
                  {change.message && (
                    <div className="text-sm text-gray-600 mt-1">{change.message}</div>
                  )}
                  {change.user && (
                    <div className="text-xs text-gray-500 mt-1">
                      Por: {change.user.username} {change.user.email && `(${change.user.email})`}
                    </div>
                  )}
                  {change.external_reference && (
                    <div className="text-xs text-gray-500 mt-1">
                      Ref: {change.external_reference}
                    </div>
                  )}
                  {change.error_message && (
                    <div className="text-xs text-red-600 mt-1 bg-red-50 p-2 rounded">
                      Error: {change.error_message}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Resumen */}
        <div className="bg-yellow-50 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Resumen</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-500">Total de Cambios</label>
              <div className="text-lg font-semibold text-gray-900">{summary.total_changes}</div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Días desde Creación</label>
              <div className="text-lg font-semibold text-gray-900">{summary.days_since_created}</div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Estado</label>
              <div className="text-lg font-semibold text-gray-900">{summary.current_status}</div>
            </div>
            {summary.is_overdue && (
              <div className="md:col-span-3">
                <div className="bg-red-100 border border-red-200 rounded p-2">
                  <div className="text-sm text-red-800 font-medium">
                    ⚠️ Este reembolso está vencido (más de {refund.processing_days} días)
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </ModalLayout>
  )
}
