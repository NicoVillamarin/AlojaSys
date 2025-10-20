import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import ModalLayout from 'src/layouts/ModalLayout'
import Timeline from 'src/components/Timeline'

function getEventLabel(eventType, t) {
  return t(`refund_historical_modal.event_labels.${eventType}`, eventType)
}

function getStatusLabel(status, t) {
  return t(`refund_historical_modal.status_labels.${status}`, status)
}

function getActionLabel(action, t) {
  return t(`refund_historical_modal.action_labels.${action}`, action)
}

function formatDateStr(val) {
  if (!val) return '—'
  try {
    const d = new Date(String(val).replace(' ', 'T'))
    if (Number.isNaN(d.getTime())) return String(val)
    return d.toLocaleString()
  } catch {
    return String(val)
  }
}

function formatCurrency(amount) {
  if (!amount) return '—'
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS'
  }).format(amount)
}

function getEventColor(eventType) {
  const colorMap = {
    created: 'bg-green-500',
    status_changed: 'bg-blue-500',
    processing_started: 'bg-yellow-500',
    processing_completed: 'bg-green-600',
    processing_failed: 'bg-red-500',
    external_reference_updated: 'bg-purple-500',
    notes_updated: 'bg-gray-500',
    cancelled: 'bg-red-600',
    retry_attempt: 'bg-orange-500',
    gateway_error: 'bg-red-700',
    manual_intervention: 'bg-indigo-500'
  }
  return colorMap[eventType] || 'bg-aloja-navy'
}

function getStatusColor(status) {
  const colorMap = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800'
  }
  return colorMap[status] || 'bg-gray-100 text-gray-800'
}

export default function RefundHistoricalModal({ refundId, onClose, isDetail = true, displayName }) {
  const { t } = useTranslation()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!refundId) return
    const base = getApiURL() || ''
    setLoading(true)
    setError(null)
    fetchWithAuth(`${base}/api/refunds/${refundId}/history/`, { method: 'GET' })
      .then(json => setData(json))
      .catch(err => setError(err.message || t('refund_historical_modal.error', { message: 'Error cargando histórico' })))
      .finally(() => setLoading(false))
  }, [refundId])

  const timeline = data?.timeline || []
  const timelineItems = timeline.map((item, i) => {
    const d = item.detail || {}
    const when = new Date(item.changed_at)
    const eventType = d.event_type
    const status = d.status
    
    // Crear label descriptivo
    let label = getEventLabel(eventType, t)
    if (eventType === 'status_changed') {
      label = t('refund_historical_modal.timeline.status_change', { 
        from: getStatusLabel(d.details?.old_status || 'unknown', t), 
        to: getStatusLabel(d.details?.new_status || 'unknown', t)
      })
    } else if (eventType === 'processing_completed') {
      label = t('refund_historical_modal.timeline.processing_completed', { 
        reference: d.external_reference || 'N/A'
      })
    } else if (eventType === 'processing_failed') {
      label = t('refund_historical_modal.timeline.processing_failed', { 
        error: d.error_message || 'Error desconocido'
      })
    } else if (eventType === 'retry_attempt') {
      label = t('refund_historical_modal.timeline.retry_attempt', { 
        attempt: d.details?.attempt_number || 'N/A'
      })
    }
    
    const by = item.changed_by?.username || item.changed_by?.email || (item.changed_by ? `Usuario #${item.changed_by.id}` : 'Sistema')
    
    const tooltip = (
      <div className="max-w-md">
        <div className="font-semibold text-aloja-navy mb-2">{label}</div>
        <div className="text-xs text-gray-500 mb-1">{when.toLocaleString()}</div>
        <div className="text-xs text-gray-600 mb-3">{t('refund_historical_modal.timeline.by')} {by}</div>
        
        {/* Estado actual */}
        <div className="mb-3">
          <span className="text-xs text-gray-500">Estado:</span>
          <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
            {getStatusLabel(status, t)}
          </span>
        </div>
        
        {/* Mensaje principal */}
        {d.message && (
          <div className="mb-3 text-sm text-gray-700 bg-gray-50 p-2 rounded">
            {d.message}
          </div>
        )}
        
        {/* Detalles específicos */}
        {d.details && Object.keys(d.details).length > 0 && (
          <div className="mb-3">
            <div className="text-xs font-medium text-gray-600 mb-2">Detalles:</div>
            <div className="space-y-1 text-xs">
              {Object.entries(d.details).map(([key, value]) => {
                if (key === 'amount') {
                  return (
                    <div key={key}>
                      <span className="font-medium text-gray-700">{t('refund_historical_modal.details.amount')}:</span>
                      <span className="ml-2 text-gray-600">{formatCurrency(value)}</span>
                    </div>
                  )
                } else if (key === 'external_reference') {
                  return (
                    <div key={key}>
                      <span className="font-medium text-gray-700">{t('refund_historical_modal.details.external_reference')}:</span>
                      <span className="ml-2 text-gray-600 font-mono text-xs">{value}</span>
                    </div>
                  )
                } else if (key === 'attempt_number') {
                  return (
                    <div key={key}>
                      <span className="font-medium text-gray-700">{t('refund_historical_modal.details.attempt')}:</span>
                      <span className="ml-2 text-gray-600">#{value}</span>
                    </div>
                  )
                } else if (key === 'gateway_name') {
                  return (
                    <div key={key}>
                      <span className="font-medium text-gray-700">{t('refund_historical_modal.details.gateway')}:</span>
                      <span className="ml-2 text-gray-600">{value}</span>
                    </div>
                  )
                } else if (key === 'old_status' || key === 'new_status') {
                  return (
                    <div key={key}>
                      <span className="font-medium text-gray-700">{t(`refund_historical_modal.details.${key}`)}:</span>
                      <span className="ml-2 text-gray-600">{getStatusLabel(value, t)}</span>
                    </div>
                  )
                } else {
                  return (
                    <div key={key}>
                      <span className="font-medium text-gray-700">{key}:</span>
                      <span className="ml-2 text-gray-600">{String(value)}</span>
                    </div>
                  )
                }
              })}
            </div>
          </div>
        )}
        
        {/* Error message si existe */}
        {d.error_message && (
          <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
            <div className="font-medium">Error:</div>
            <div>{d.error_message}</div>
          </div>
        )}
        
        {/* Referencia externa si existe */}
        {d.external_reference && (
          <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
            <div className="font-medium text-blue-800">Referencia Externa:</div>
            <div className="text-blue-700 font-mono">{d.external_reference}</div>
          </div>
        )}
      </div>
    )
    
    return {
      id: `${i}-${eventType}`,
      date: when,
      title: label,
      color: getEventColor(eventType),
      tooltip,
    }
  })

  return (
    <ModalLayout
      isOpen={!!refundId}
      onClose={onClose}
      title={displayName ? t('refund_historical_modal.title_with_name', { name: displayName }) : t('refund_historical_modal.title_with_id', { id: refundId })}
      size="lg"
      isDetail={isDetail}
    >
      {loading && <p className="text-gray-500">{t('refund_historical_modal.loading')}</p>}
      {error && <p className="text-red-600">{t('refund_historical_modal.error', { message: error })}</p>}
      {!loading && !error && timeline.length === 0 && (
        <p className="text-gray-500 text-center">{t('refund_historical_modal.no_events')}</p>
      )}

      {timeline.length > 0 && (
        <Timeline items={timelineItems} />
      )}
    </ModalLayout>
  )
}
