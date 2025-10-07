import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import ModalLayout from 'src/layouts/ModalLayout'
import Timeline from 'src/components/Timeline'

function getEventLabel(eventType, t) {
  return t(`reservation_historical_modal.event_labels.${eventType}`, eventType)
}

function getStatusLabel(status, t) {
  return t(`reservation_historical_modal.status_labels.${status}`, status)
}

function getChannelLabel(channel, t) {
  return t(`reservation_historical_modal.channel_labels.${channel}`, channel)
}

function labelForField(field, t) {
  return t(`reservation_historical_modal.field_labels.${field}`, field)
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

function summarizeGuestsData(strVal, t) {
  if (!strVal) return '—'
  try {
    const jsonLike = String(strVal).replaceAll("'", '"')
    const parsed = JSON.parse(jsonLike)
    if (Array.isArray(parsed)) {
      const names = parsed.map(g => g?.name).filter(Boolean)
      return names.length ? t('reservation_historical_modal.timeline.guests_summary', { names: names.join(', ') }) : t('reservation_historical_modal.timeline.guests_fallback')
    }
  } catch {}
  // fallback: intentar extraer nombres por regex
  const matches = [...String(strVal).matchAll(/name':\s*'([^']+)'/g)].map(m => m[1])
  return matches.length ? t('reservation_historical_modal.timeline.guests_summary', { names: matches.join(', ') }) : String(strVal)
}

function humanizeValue(field, val, t) {
  if (val === null || typeof val === 'undefined') return '—'
  const s = String(val)
  if (field === 'check_in' || field === 'check_out' || field === 'created_at' || field === 'updated_at') {
    return formatDateStr(s)
  }
  if (field === 'status') {
    return getStatusLabel(s, t)
  }
  if (field === 'channel') {
    return getChannelLabel(s, t)
  }
  if (field === 'guests_data') {
    return summarizeGuestsData(s, t)
  }
  return s
}

export default function ReservationHistoricalModal({ reservationId, onClose, isDetail = true, displayName }) {
  const { t } = useTranslation()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!reservationId) return
    const base = getApiURL() || ''
    setLoading(true)
    setError(null)
    fetchWithAuth(`${base}/api/reservations/${reservationId}/history/`, { method: 'GET' })
      .then(json => setData(json))
      .catch(err => setError(err.message || t('reservation_historical_modal.error', { message: 'Error cargando histórico' })))
      .finally(() => setLoading(false))
  }, [reservationId])

  const timeline = data?.timeline || []
  const timelineItems = timeline.map((item, i) => {
    const isStatus = item.type === 'status_change'
    const d = item.detail || {}
    const when = new Date(item.changed_at)
    const label = isStatus
      ? t('reservation_historical_modal.timeline.status_change', { 
          event: getEventLabel('status_changed', t), 
          from: d.from || '—', 
          to: d.to || '—' 
        })
      : getEventLabel(d.event_type, t)
    // Mapeo de colores por tipo de evento
    const getColorByEvent = () => {
      if (isStatus) return 'bg-aloja-gold'
      const eventType = d.event_type
      const colorMap = {
        created: 'bg-green-500',
        updated: 'bg-blue-500',
        check_in: 'bg-aloja-gold',
        check_out: 'bg-purple-500',
        cancel: 'bg-red-500',
        charge_added: 'bg-orange-500',
        payment_added: 'bg-green-600',
      }
      return colorMap[eventType] || 'bg-aloja-navy'
    }
    
    const by = item.changed_by?.username || item.changed_by?.email || (item.changed_by ? `Usuario #${item.changed_by.id}` : 'Sistema')
    
    const tooltip = (
      <div>
        <div className="font-semibold text-aloja-navy mb-2">{label}</div>
        <div className="text-xs text-gray-500 mb-1">{when.toLocaleString()}</div>
        <div className="text-xs text-gray-600 mb-3">{t('reservation_historical_modal.timeline.by')} {by}</div>
        {!!d.message && <div className="mb-2 text-sm">{d.message}</div>}
        {!isStatus && d.fields_changed && (
          Array.isArray(d.fields_changed) ? (
            <ul className="list-disc pl-4 space-y-0.5">
              {d.fields_changed.map((field, idx) => (
                <li key={idx}>{labelForField(field, t)}</li>
              ))}
            </ul>
          ) : (
            <div className="space-y-1">
              {Object.entries(d.fields_changed).map(([field, change]) => (
                <div key={field}>
                  <span className="font-medium text-gray-700">{labelForField(field, t)}</span>{' '}
                  <span className="text-gray-500">→</span>{' '}
                  <span className="text-gray-600">{humanizeValue(field, change?.old, t)}</span>{' '}
                  <span className="text-gray-500">→</span>{' '}
                  <span className="text-gray-900">{humanizeValue(field, change?.new, t)}</span>
                </div>
              ))}
            </div>
          )
        )}
      </div>
    )
    return {
      id: `${i}-${item.type}`,
      date: when,
      title: label,
      color: getColorByEvent(),
      tooltip,
    }
  })

  return (
    <ModalLayout
      isOpen={!!reservationId}
      onClose={onClose}
      title={displayName ? t('reservation_historical_modal.title_with_name', { name: displayName }) : t('reservation_historical_modal.title_with_id', { id: reservationId })}
      size="lg"
      isDetail={isDetail}
    >
      {loading && <p className="text-gray-500">{t('reservation_historical_modal.loading')}</p>}
      {error && <p className="text-red-600">{t('reservation_historical_modal.error', { message: error })}</p>}
      {!loading && !error && timeline.length === 0 && (
        <p className="text-gray-500 text-center">{t('reservation_historical_modal.no_events')}</p>
      )}

      {timeline.length > 0 && (
        <Timeline items={timelineItems} />
      )}
    </ModalLayout>
  )
}