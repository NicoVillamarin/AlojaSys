import React, { useMemo } from 'react'
import ModalLayout from 'src/layouts/ModalLayout'

function normalizeGuestsFromReservation(reservation) {
  if (!reservation) return []

  const collect = (res) => {
    const arr = Array.isArray(res?.guests_data) ? res.guests_data : []
    return arr
      .filter(Boolean)
      .map((g) => ({
        name: g?.name || '',
        document: g?.document || '',
        email: g?.email || '',
        phone: g?.phone || '',
        address: g?.address || '',
        is_primary: g?.is_primary === true,
      }))
  }

  let guests = collect(reservation)

  // Si es una fila de grupo (multi-habitación), mergear huéspedes de todas las reservas del grupo
  if (reservation?.is_group && Array.isArray(reservation?.group_reservations)) {
    const merged = []
    for (const r of reservation.group_reservations) merged.push(...collect(r))
    guests = merged
  }

  // Deduplicar por documento/email/nombre
  const seen = new Set()
  const keyOf = (g) => {
    const doc = (g.document || '').trim()
    const email = (g.email || '').trim().toLowerCase()
    const name = (g.name || '').trim().toLowerCase()
    return doc || email || name || JSON.stringify(g)
  }

  const uniq = []
  for (const g of guests) {
    const k = keyOf(g)
    if (seen.has(k)) continue
    seen.add(k)
    uniq.push(g)
  }

  // Asegurar que el principal quede primero (si hay)
  uniq.sort((a, b) => (b.is_primary === true) - (a.is_primary === true))
  return uniq
}

function FieldRow({ label, value }) {
  const v = value ? String(value) : '—'
  return (
    <div className="flex items-start justify-between gap-4 py-2 border-b border-gray-100 last:border-b-0">
      <div className="text-xs text-aloja-gray-800/60">{label}</div>
      <div className="text-sm text-aloja-gray-900 font-medium text-right break-words">{v}</div>
    </div>
  )
}

export default function GuestDetailsModal({ isOpen, onClose, reservation }) {
  const guests = useMemo(() => normalizeGuestsFromReservation(reservation), [reservation])

  const title = useMemo(() => {
    if (!reservation) return 'Huésped'
    const prefix = reservation?.display_name || (reservation?.id ? `Reserva #${reservation.id}` : 'Reserva')
    return `Huésped — ${prefix}`
  }, [reservation])

  return (
    <ModalLayout isOpen={!!isOpen} onClose={onClose} title={title} size="lg" isDetail={true}>
      {!reservation ? (
        <div className="text-gray-600">No hay datos para mostrar.</div>
      ) : (
        <div className="space-y-4">
          {/* Resumen */}
          <div className="p-3 rounded-lg bg-gray-50 border border-gray-200">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-sm">
              <div>
                <div className="text-xs text-aloja-gray-800/60">Huésped principal</div>
                <div className="font-semibold text-aloja-navy">
                  {reservation?.guest_name || guests?.find((g) => g.is_primary)?.name || '—'}
                </div>
              </div>
              <div>
                <div className="text-xs text-aloja-gray-800/60">Hotel</div>
                <div className="font-semibold text-aloja-navy">{reservation?.hotel_name || '—'}</div>
              </div>
              <div>
                <div className="text-xs text-aloja-gray-800/60">Habitación</div>
                <div className="font-semibold text-aloja-navy">
                  {reservation?.is_group ? 'Multi-habitación' : (reservation?.room_name || '—')}
                </div>
              </div>
            </div>
          </div>

          {/* Lista de huéspedes */}
          {guests.length === 0 ? (
            <div className="text-gray-600">
              No hay información detallada de huéspedes (guests_data).
            </div>
          ) : (
            <div className="space-y-3">
              {guests.map((g, idx) => (
                <div key={`${g.document || g.email || g.name || idx}`} className="border border-gray-200 rounded-lg">
                  <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
                    <div className="font-semibold text-aloja-navy">
                      {g.name || `Huésped #${idx + 1}`}
                    </div>
                    {g.is_primary ? (
                      <span className="text-xs px-2 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                        Principal
                      </span>
                    ) : null}
                  </div>
                  <div className="px-4 py-2">
                    <FieldRow label="Documento" value={g.document} />
                    <FieldRow label="Email" value={g.email} />
                    <FieldRow label="Teléfono" value={g.phone} />
                    <FieldRow label="Dirección" value={g.address} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </ModalLayout>
  )
}

