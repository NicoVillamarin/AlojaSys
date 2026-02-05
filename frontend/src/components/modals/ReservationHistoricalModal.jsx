import React, { useEffect, useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import ModalLayout from 'src/layouts/ModalLayout'
import Timeline from 'src/components/Timeline'
import Tabs from 'src/components/Tabs'

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

function formatCurrency(amount) {
  if (!amount && amount !== 0) return '—'
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
  }).format(amount)
}

function renderNoShowDetails(detail, t) {
  const snapshot = detail.snapshot || {}
  const eventType = detail.event_type
  
  if (eventType === 'no_show_penalty') {
    const penaltyAmount = snapshot.penalty_amount
    const cancellationRules = snapshot.cancellation_rules || {}
    const penaltyType = snapshot.penalty_type || 'no_show_automatic'
    
    return (
      <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
        <div className="font-semibold text-amber-900 mb-2">Detalles de Penalidad NO-SHOW</div>
        <div className="space-y-1.5 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-700">Monto de penalidad:</span>
            <span className="font-semibold text-amber-900">{formatCurrency(penaltyAmount)}</span>
          </div>
          {cancellationRules.type && (
            <div className="flex justify-between">
              <span className="text-gray-700">Tipo de política:</span>
              <span className="text-gray-900">{cancellationRules.type}</span>
            </div>
          )}
          {cancellationRules.cancellation_type && (
            <div className="flex justify-between">
              <span className="text-gray-700">Tipo de cancelación:</span>
              <span className="text-gray-900">{cancellationRules.cancellation_type}</span>
            </div>
          )}
          {penaltyType && (
            <div className="flex justify-between">
              <span className="text-gray-700">Tipo de penalidad:</span>
              <span className="text-gray-900">{penaltyType === 'no_show_automatic' ? 'Automática' : penaltyType}</span>
            </div>
          )}
        </div>
      </div>
    )
  }
  
  if (eventType === 'no_show_processed') {
    const totalPaid = snapshot.total_paid
    const penaltyAmount = snapshot.penalty_amount || 0
    const refundAmount = snapshot.refund_amount || 0
    const cancellationRules = snapshot.cancellation_rules || {}
    const penaltyResult = snapshot.penalty_result || {}
    const refundResult = snapshot.refund_result || {}
    
    return (
      <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
        <div className="font-semibold text-amber-900 mb-2">Resumen de Procesamiento NO-SHOW</div>
        <div className="space-y-2 text-sm">
          <div className="grid grid-cols-2 gap-2">
            <div className="flex justify-between">
              <span className="text-gray-700">Total pagado:</span>
              <span className="font-semibold text-gray-900">{formatCurrency(totalPaid)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">Penalidad aplicada:</span>
              <span className="font-semibold text-amber-900">{formatCurrency(penaltyAmount)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">Reembolso calculado:</span>
              <span className="font-semibold text-green-700">{formatCurrency(refundAmount)}</span>
            </div>
            {refundResult.method && (
              <div className="flex justify-between">
                <span className="text-gray-700">Método de reembolso:</span>
                <span className="text-gray-900">{refundResult.method}</span>
              </div>
            )}
          </div>
          {cancellationRules.type && (
            <div className="pt-2 border-t border-amber-300">
              <div className="text-xs text-gray-600 mb-1">Política aplicada:</div>
              <div className="text-sm text-gray-900">{cancellationRules.type}</div>
            </div>
          )}
          {penaltyResult.status && (
            <div className="pt-2 border-t border-amber-300">
              <div className="text-xs text-gray-600 mb-1">Estado de penalidad:</div>
              <div className="text-sm text-gray-900">{penaltyResult.status}</div>
            </div>
          )}
        </div>
      </div>
    )
  }
  
  return null
}

function renderCancellationDetails(detail, t) {
  const eventType = detail.event_type
  if (eventType !== 'cancel') return null
  
  const fieldsChanged = detail.fields_changed || {}
  const snapshot = detail.snapshot || {}
  
  // Información de cancelación puede estar en fields_changed o snapshot
  const cancellationReason = fieldsChanged.cancellation_reason || snapshot.cancellation_reason || 'No especificado'
  const totalPaid = fieldsChanged.total_paid || snapshot.total_paid || 0
  const penaltyAmount = fieldsChanged.penalty_amount || snapshot.penalty_amount || 0
  const refundAmount = fieldsChanged.refund_amount || snapshot.refund_amount || 0
  const isManual = fieldsChanged.manual_cancellation !== false // Por defecto true si no está especificado
  
  return (
    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
      <div className="font-semibold text-red-900 mb-2">Detalles de Cancelación</div>
      <div className="space-y-2 text-sm">
        <div>
          <span className="text-gray-700">Motivo de cancelación:</span>
          <div className="mt-1 text-gray-900 font-medium">{cancellationReason}</div>
        </div>
        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-red-300">
          <div className="flex justify-between">
            <span className="text-gray-700">Total pagado:</span>
            <span className="font-semibold text-gray-900">{formatCurrency(totalPaid)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-700">Penalidad:</span>
            <span className="font-semibold text-red-700">{formatCurrency(penaltyAmount)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-700">Reembolso:</span>
            <span className="font-semibold text-green-700">{formatCurrency(refundAmount)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-700">Tipo:</span>
            <span className="text-gray-900">{isManual ? 'Manual' : 'Automática'}</span>
          </div>
        </div>
        {fieldsChanged.refund_method && (
          <div className="pt-2 border-t border-red-300">
            <div className="text-xs text-gray-600 mb-1">Método de reembolso:</div>
            <div className="text-sm text-gray-900">{fieldsChanged.refund_method}</div>
          </div>
        )}
      </div>
    </div>
  )
}

// Función para consolidar información de no-show desde el timeline
function consolidateNoShowInfo(timeline, t) {
  // Buscar eventos de no-show en el timeline
  const noShowEvents = timeline.filter(item => {
    // Puede ser un change_log con event_type
    if (item.type === 'change_log') {
      const d = item.detail || {}
      return d.event_type === 'no_show_penalty' || d.event_type === 'no_show_processed'
    }
    // O puede ser un status_change que cambió a no_show
    if (item.type === 'status_change') {
      const d = item.detail || {}
      return d.to === 'no_show'
    }
    return false
  })
  
  if (noShowEvents.length === 0) {
    return null
  }
  
  // Buscar el evento más completo (no_show_processed tiene más info)
  const processedEvent = noShowEvents.find(item => item.detail?.event_type === 'no_show_processed')
  const penaltyEvent = noShowEvents.find(item => item.detail?.event_type === 'no_show_penalty')
  
  const event = processedEvent || penaltyEvent
  const snapshot = event?.detail?.snapshot || {}
  
  return {
    totalPaid: snapshot.total_paid,
    penaltyAmount: snapshot.penalty_amount || 0,
    refundAmount: snapshot.refund_amount || 0,
    cancellationRules: snapshot.cancellation_rules || {},
    penaltyResult: snapshot.penalty_result || {},
    refundResult: snapshot.refund_result || {},
    penaltyType: snapshot.penalty_type || 'no_show_automatic',
    processedAt: event?.changed_at,
    processedBy: event?.changed_by,
  }
}

// Función para consolidar información de cancelación desde el timeline
function consolidateCancellationInfo(timeline, t) {
  // Buscar eventos de cancelación en el timeline
  const cancelEvents = timeline.filter(item => {
    // Puede ser un change_log con event_type 'cancel'
    if (item.type === 'change_log') {
      const d = item.detail || {}
      return d.event_type === 'cancel'
    }
    // O puede ser un status_change que cambió a cancelled
    if (item.type === 'status_change') {
      const d = item.detail || {}
      return d.to === 'cancelled'
    }
    return false
  })
  
  if (cancelEvents.length === 0) {
    return null
  }
  
  // Tomar el evento de cancelación más reciente (el primero porque están ordenados por fecha descendente)
  const cancelEvent = cancelEvents[0]
  const d = cancelEvent.detail || {}
  const fieldsChanged = d.fields_changed || {}
  const snapshot = d.snapshot || {}
  
  return {
    cancellationReason: fieldsChanged.cancellation_reason || snapshot.cancellation_reason || 'No especificado',
    totalPaid: fieldsChanged.total_paid || snapshot.total_paid || 0,
    penaltyAmount: fieldsChanged.penalty_amount || snapshot.penalty_amount || 0,
    refundAmount: fieldsChanged.refund_amount || snapshot.refund_amount || 0,
    isManual: fieldsChanged.manual_cancellation !== false,
    refundMethod: fieldsChanged.refund_method || snapshot.refund_method,
    cancelledAt: cancelEvent.changed_at,
    cancelledBy: cancelEvent.changed_by,
    message: d.message,
  }
}

export default function ReservationHistoricalModal({ reservationId, onClose, isDetail = true, displayName, reservationStatus }) {
  const { t } = useTranslation()
  const [data, setData] = useState(null)
  const [reservationData, setReservationData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('timeline')

  useEffect(() => {
    if (!reservationId) return
    const base = getApiURL() || ''
    setLoading(true)
    setError(null)
    
    // Cargar histórico
    Promise.all([
      fetchWithAuth(`${base}/api/reservations/${reservationId}/history/`, { method: 'GET' }),
      // También cargar datos de la reserva para obtener información adicional
      fetchWithAuth(`${base}/api/reservations/${reservationId}/`, { method: 'GET' }).catch(() => null)
    ])
      .then(([historyJson, reservationJson]) => {
        setData(historyJson)
        setReservationData(reservationJson)
      })
      .catch(err => setError(err.message || t('reservation_historical_modal.error', { message: 'Error cargando histórico' })))
      .finally(() => setLoading(false))
  }, [reservationId])

  const timeline = data?.timeline || []

  // Consolida eventos que ocurren en el mismo instante y elimina duplicados
  const consolidatedTimeline = useMemo(() => {
    if (!Array.isArray(timeline) || timeline.length === 0) return []

    // Agrupar por segundo
    const groups = new Map()
    for (const item of timeline) {
      const ts = Math.floor(new Date(item.changed_at).getTime() / 1000)
      if (!groups.has(ts)) groups.set(ts, [])
      groups.get(ts).push(item)
    }

    const result = []

    // Prioridad de eventos (más descriptivos primero)
    const eventPriority = {
      cancel: 1,
      no_show_processed: 1,
      no_show_penalty: 2,
      check_in: 3,
      check_out: 3,
      status_change: 4,
      status_changed: 5,
      updated: 6,
      created: 7,
    }

    for (const [, items] of groups) {
      // Separar por tipo
      const changeLogs = items.filter(i => i.type === 'change_log')
      const statusChanges = items.filter(i => i.type === 'status_change')

      // Encontrar el mejor change_log (si existe)
      let bestChangeLog = null
      for (const cl of changeLogs) {
        const et = cl.detail?.event_type || 'updated'
        if (!bestChangeLog) bestChangeLog = cl
        const bestEt = bestChangeLog.detail?.event_type || 'updated'
        const a = eventPriority[et] ?? 100
        const b = eventPriority[bestEt] ?? 100
        if (a < b) bestChangeLog = cl
      }

      if (bestChangeLog) {
        // Si hay change_log prioritario y un status_change relacionado, ignorar el status_change duplicado
        const et = bestChangeLog.detail?.event_type
        if (["cancel", "check_in", "check_out", "no_show_penalty", "no_show_processed"].includes(et)) {
          // No añadimos los status_change del mismo segundo
          result.push(bestChangeLog)
          continue
        }
        // Si el bestChangeLog es un status_changed genérico y también hay un status_change,
        // preferimos el status_change y descartamos el change_log genérico
        if (et === 'status_changed' && statusChanges.length > 0) {
          // caemos abajo y agregamos el status_change
        } else if (et === 'updated' && statusChanges.length > 0) {
          // Evitamos mostrar updated si hubo cambio de estado simultáneo
          // caemos abajo y agregamos el status_change
        } else {
          result.push(bestChangeLog)
          continue
        }
      }

      // Si llegamos aquí: o no había change_log relevante o preferimos el status_change
      if (statusChanges.length > 0) {
        // Tomar uno solo (son equivalentes en el mismo segundo)
        result.push(statusChanges[0])
      } else {
        // No hay status_change ni change_log relevante (caso raro): tomar el primero
        result.push(items[0])
      }
    }

    // Ordenar por fecha descendente
    const sorted = result.sort((a, b) => new Date(b.changed_at) - new Date(a.changed_at))

    // Deduplicar eventos muy parecidos dentro de una ventana corta (5s)
    const signature = (it) => {
      if (it.type === 'status_change') {
        const d = it.detail || {}
        return `status:${d.from || ''}->${d.to || ''}`
      }
      const et = it.detail?.event_type || 'updated'
      return `event:${et}`
    }

    const deduped = []
    for (const item of sorted) {
      const last = deduped[deduped.length - 1]
      if (!last) { deduped.push(item); continue }
      const dt = Math.abs(new Date(last.changed_at).getTime() - new Date(item.changed_at).getTime())
      if (dt <= 5000 && signature(last) === signature(item)) {
        // duplicado cercano: mantener solo el primero (más reciente por sorting)
        continue
      }
      deduped.push(item)
    }

    return deduped
  }, [timeline])

  const timelineItems = consolidatedTimeline.map((item, i) => {
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
      if (isStatus) {
        if (d.to === 'no_show') return 'bg-amber-500'
        if (d.to === 'cancelled') return 'bg-red-500'
        return 'bg-aloja-gold'
      }
      const eventType = d.event_type
      const colorMap = {
        created: 'bg-green-500',
        updated: 'bg-blue-500',
        check_in: 'bg-aloja-gold',
        check_out: 'bg-purple-500',
        cancel: 'bg-red-500',
        charge_added: 'bg-orange-500',
        payment_added: 'bg-green-600',
        no_show_penalty: 'bg-amber-600',
        no_show_processed: 'bg-amber-500',
      }
      return colorMap[eventType] || 'bg-aloja-navy'
    }
    
    const by = item.changed_by?.username || item.changed_by?.email || (item.changed_by ? `Usuario #${item.changed_by.id}` : 'Sistema')
    
    // Renderizar detalles específicos de no-show o cancelación
    const noShowDetails = !isStatus && (d.event_type === 'no_show_penalty' || d.event_type === 'no_show_processed')
      ? renderNoShowDetails(d, t)
      : null
    
    const cancellationDetails = !isStatus && d.event_type === 'cancel'
      ? renderCancellationDetails(d, t)
      : null
    
    // Mostrar notas en cambios de estado si están disponibles
    const statusNotes = isStatus && d.notes ? (
      <div className="mt-2 p-2 bg-gray-50 rounded text-sm text-gray-700">
        <span className="font-medium">Nota:</span> {d.notes}
      </div>
    ) : null
    
    const tooltip = (
      <div>
        <div className="font-semibold text-aloja-navy mb-2">{label}</div>
        <div className="text-xs text-gray-500 mb-1">{when.toLocaleString()}</div>
        <div className="text-xs text-gray-600 mb-3">{t('reservation_historical_modal.timeline.by')} {by}</div>
        {statusNotes}
        {!!d.message && <div className="mb-2 text-sm">{d.message}</div>}
        {noShowDetails}
        {cancellationDetails}
        {!isStatus && d.fields_changed && !noShowDetails && !cancellationDetails && (
          Array.isArray(d.fields_changed) ? (
            <ul className="list-disc pl-4 space-y-0.5">
              {d.fields_changed.map((field, idx) => (
                <li key={idx}>{labelForField(field, t)}</li>
              ))}
            </ul>
          ) : (
            <div className="space-y-1">
              {Object.entries(d.fields_changed)
                .filter(([field]) => {
                  return !['cancellation_reason', 'penalty_amount', 'refund_amount', 'total_paid'].includes(field)
                })
                .map(([field, change]) => (
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
    
    const tsId = (() => {
      try { return String(new Date(item.changed_at).getTime()) } catch { return String(i) }
    })()
    
    return {
      id: `${tsId}-${item.type}`,
      date: when,
      title: label,
      color: getColorByEvent(),
      tooltip,
    }
  })

  // Determinar si mostrar tabs (solo para cancelled o no_show)
  const showTabs = reservationStatus === 'cancelled' || reservationStatus === 'no_show'
  
  // Consolidar información de detalles
  const noShowInfo = useMemo(() => {
    if (reservationStatus === 'no_show') {
      const info = consolidateNoShowInfo(timeline, t)
      return info
    }
    return null
  }, [timeline, reservationStatus, t])
  
  const cancellationInfo = useMemo(() => {
    if (reservationStatus === 'cancelled') {
      const info = consolidateCancellationInfo(timeline, t)
      return info
    }
    return null
  }, [timeline, reservationStatus, t])
  
  // Determinar si es una reserva antigua (sin información detallada)
  const isOldReservation = useMemo(() => {
    if (reservationStatus === 'cancelled' && cancellationInfo) {
      return cancellationInfo.totalPaid === 0 && 
             cancellationInfo.penaltyAmount === 0 && 
             cancellationInfo.refundAmount === 0 &&
             !cancellationInfo.refundMethod
    }
    if (reservationStatus === 'no_show' && noShowInfo) {
      return noShowInfo.totalPaid === 0 && 
             noShowInfo.penaltyAmount === 0 && 
             noShowInfo.refundAmount === 0
    }
    return false
  }, [cancellationInfo, noShowInfo, reservationStatus])
  
  // Renderizar vista de detalles consolidados
  const renderDetailsView = () => {
    if (reservationStatus === 'no_show') {
      if (!noShowInfo) {
        return (
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="font-semibold text-amber-900 mb-2">Reserva NO-SHOW</div>
            <p className="text-sm text-gray-700">
              Esta reserva fue marcada como NO-SHOW, pero no se encontró información detallada de penalidades o reembolsos en el histórico.
            </p>
          </div>
        )
      }
      
      if (isOldReservation) {
        return (
          <div className="space-y-4">
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <div className="font-semibold text-amber-900 mb-3 text-lg">Reserva NO-SHOW</div>
              {noShowInfo.processedAt && (
                <div className="mt-4 pt-4 border-t border-amber-300 text-xs text-gray-600">
                  <div>Procesado el: {formatDateStr(noShowInfo.processedAt)}</div>
                  {noShowInfo.processedBy && (
                    <div>Por: {noShowInfo.processedBy?.username || noShowInfo.processedBy?.email || 'Sistema'}</div>
                  )}
                </div>
              )}
              <div className="mt-4 pt-4 border-t border-amber-300">
                <p className="text-sm text-gray-600">
                  Esta reserva fue marcada como NO-SHOW antes de implementar el sistema de penalidades automáticas. 
                  Por lo tanto, no hay información detallada de penalidades o reembolsos disponibles.
                </p>
              </div>
            </div>
            {noShowDetails}
          </div>
        )
      }
      
      return (
        <div className="space-y-4">
          {noShowDetails}
        </div>
      )
    }
    
    if (reservationStatus === 'cancelled') {
      if (!cancellationInfo) {
        return (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="font-semibold text-red-900 mb-2">Reserva Cancelada</div>
            <p className="text-sm text-gray-700">
              Esta reserva fue cancelada, pero no se encontró información detallada de penalidades o reembolsos en el histórico.
            </p>
          </div>
        )
      }
      
      if (isOldReservation) {
        return (
          <div className="space-y-4">
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="font-semibold text-red-900 mb-3 text-lg">Reserva Cancelada</div>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-gray-700">Motivo de cancelación:</span>
                  <div className="mt-1 text-gray-900 font-medium">{cancellationInfo.cancellationReason}</div>
                </div>
                {cancellationInfo.cancelledAt && (
                  <div className="mt-4 pt-4 border-t border-red-300 text-xs text-gray-600">
                    <div>Cancelada el: {formatDateStr(cancellationInfo.cancelledAt)}</div>
                    {cancellationInfo.cancelledBy && (
                      <div>Por: {cancellationInfo.cancelledBy?.username || cancellationInfo.cancelledBy?.email || 'Sistema'}</div>
                    )}
                  </div>
                )}
              </div>
              <div className="mt-4 pt-4 border-t border-red-300">
                <p className="text-sm text-gray-600">
                  Esta reserva fue cancelada antes de implementar el sistema de penalidades automáticas. 
                  Por lo tanto, no hay información detallada de penalidades o reembolsos disponibles.
                </p>
              </div>
            </div>
            {cancellationDetails}
          </div>
        )
      }
      
      return (
        <div className="space-y-4">
          {cancellationDetails}
        </div>
      )
    }
    
    return null
  }

  const reservationDetails = reservationData ? (
    <div className="p-3">
      <h3 className="font-semibold text-gray-900 mb-2">Detalles de la Reserva</h3>
      <div className="space-y-1.5 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-700">ID de Reserva:</span>
          <span className="font-semibold text-gray-900">{reservationData.id}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Estado:</span>
          <span className="font-semibold text-gray-900">{reservationData.status}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Fecha de Creación:</span>
          <span className="font-semibold text-gray-900">{formatDateStr(reservationData.created_at)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Fecha de Actualización:</span>
          <span className="font-semibold text-gray-900">{formatDateStr(reservationData.updated_at)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Precio Total:</span>
          <span className="font-semibold text-gray-900">{formatCurrency(reservationData.total_price)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Estado de Pago:</span>
          <span className="font-semibold text-gray-900">{reservationData.payment_status}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Canal:</span>
          <span className="font-semibold text-gray-900">{reservationData.channel}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Guests:</span>
          <span className="font-semibold text-gray-900">{summarizeGuestsData(reservationData.guests_data, t)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Check-in:</span>
          <span className="font-semibold text-gray-900">{formatDateStr(reservationData.check_in)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Check-out:</span>
          <span className="font-semibold text-gray-900">{formatDateStr(reservationData.check_out)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Duración:</span>
          <span className="font-semibold text-gray-900">{reservationData.duration} días</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Tipo de Pago:</span>
          <span className="font-semibold text-gray-900">{reservationData.payment_type}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Tipo de Habitación:</span>
          <span className="font-semibold text-gray-900">
            {reservationData.room_type_alias || reservationData.room_type_name || reservationData.room_type}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Número de Habitación:</span>
          <span className="font-semibold text-gray-900">{reservationData.room_number}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Nombre del Cliente:</span>
          <span className="font-semibold text-gray-900">{reservationData.customer_name}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Email del Cliente:</span>
          <span className="font-semibold text-gray-900">{reservationData.customer_email}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Teléfono del Cliente:</span>
          <span className="font-semibold text-gray-900">{reservationData.customer_phone}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Dirección del Cliente:</span>
          <span className="font-semibold text-gray-900">{reservationData.customer_address}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Notas:</span>
          <span className="font-semibold text-gray-900">{reservationData.notes}</span>
        </div>
      </div>
    </div>
  ) : null

  const noShowDetails = noShowInfo ? (
    <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
      <div className="font-semibold text-amber-900 mb-2">Resumen de NO-SHOW</div>
      <div className="space-y-2 text-sm">
        <div className="grid grid-cols-2 gap-2">
          <div className="flex justify-between">
            <span className="text-gray-700">Total pagado:</span>
            <span className="font-semibold text-gray-900">{formatCurrency(noShowInfo.totalPaid)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-700">Penalidad aplicada:</span>
            <span className="font-semibold text-amber-900">{formatCurrency(noShowInfo.penaltyAmount)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-700">Reembolso calculado:</span>
            <span className="font-semibold text-green-700">{formatCurrency(noShowInfo.refundAmount)}</span>
          </div>
          {noShowInfo.penaltyType && (
            <div className="flex justify-between">
              <span className="text-gray-700">Tipo de penalidad:</span>
              <span className="text-gray-900">{noShowInfo.penaltyType === 'no_show_automatic' ? 'Automática' : noShowInfo.penaltyType}</span>
            </div>
          )}
        </div>
        {noShowInfo.cancellationRules.type && (
          <div className="pt-2 border-t border-amber-300">
            <div className="text-xs text-gray-600 mb-1">Política aplicada:</div>
            <div className="text-sm text-gray-900">{noShowInfo.cancellationRules.type}</div>
          </div>
        )}
        {noShowInfo.penaltyResult.status && (
          <div className="pt-2 border-t border-amber-300">
            <div className="text-xs text-gray-600 mb-1">Estado de penalidad:</div>
            <div className="text-sm text-gray-900">{noShowInfo.penaltyResult.status}</div>
          </div>
        )}
      </div>
    </div>
  ) : null

  const cancellationDetails = cancellationInfo ? (
    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
      <div className="font-semibold text-red-900 mb-2">Detalles de Cancelación</div>
      <div className="space-y-2 text-sm">
        <div>
          <span className="text-gray-700">Motivo de cancelación:</span>
          <div className="mt-1 text-gray-900 font-medium">{cancellationInfo.cancellationReason}</div>
        </div>
        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-red-300">
          <div className="flex justify-between">
            <span className="text-gray-700">Total pagado:</span>
            <span className="font-semibold text-gray-900">{formatCurrency(cancellationInfo.totalPaid)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-700">Penalidad:</span>
            <span className="font-semibold text-red-700">{formatCurrency(cancellationInfo.penaltyAmount)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-700">Reembolso:</span>
            <span className="font-semibold text-green-700">{formatCurrency(cancellationInfo.refundAmount)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-700">Tipo:</span>
            <span className="text-gray-900">{cancellationInfo.isManual ? 'Manual' : 'Automática'}</span>
          </div>
        </div>
        {cancellationInfo.refundMethod && (
          <div className="pt-2 border-t border-red-300">
            <div className="text-xs text-gray-600 mb-1">Método de reembolso:</div>
            <div className="text-sm text-gray-900">{cancellationInfo.refundMethod}</div>
          </div>
        )}
      </div>
    </div>
  ) : null

  const tabs = showTabs ? [
    { id: 'timeline', label: 'Histórico', icon: '📅' },
    { id: 'details', label: 'Detalles', icon: '📋' },
  ] : []

  return (
    <ModalLayout
      isOpen={!!reservationId}
      title={`Histórico — ${displayName || `Reserva N° ${reservationId}`}`}
      onClose={onClose}
      isDetail={isDetail}
      size="lg"
    >
      {loading && <p className="text-gray-500">{t('reservation_historical_modal.loading')}</p>}
      {error && <p className="text-red-600">{t('reservation_historical_modal.error', { message: error })}</p>}
      
      {!loading && !error && (
        <>
          {showTabs && tabs.length > 0 && (
            <Tabs
              tabs={tabs}
              activeTab={activeTab}
              onTabChange={setActiveTab}
              className="mb-4"
            />
          )}
          
          {activeTab === 'timeline' && (
            <>
              {timeline.length === 0 && (
                <p className="text-gray-500 text-center">{t('reservation_historical_modal.no_events')}</p>
              )}
              {timeline.length > 0 && (
                <Timeline items={timelineItems} />
              )}
            </>
          )}
          
          {activeTab === 'details' && (
            <>
              {renderDetailsView() || (
                <div className="p-4">
                  <p className="text-gray-500 text-center">No hay información de detalles disponible</p>
                </div>
              )}
            </>
          )}
          
          {!showTabs && (
            <>
              {timeline.length === 0 && (
                <p className="text-gray-500 text-center">{t('reservation_historical_modal.no_events')}</p>
              )}
              {timeline.length > 0 && (
                <Timeline items={timelineItems} />
              )}
            </>
          )}
        </>
      )}
    </ModalLayout>
  )
}