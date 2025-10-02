import { useMemo, useRef, useState, useEffect } from 'react'
import TableGeneric from 'src/components/TableGeneric'
import ReservationHistoricalModal from 'src/components/modals/ReservationHistoricalModal'
import { useList } from 'src/hooks/useList'
import { useDispatchAction } from 'src/hooks/useDispatchAction'
import ReservationsModal from 'src/components/modals/ReservationsModal'
import Button from 'src/components/Button'
import SelectAsync from 'src/components/selects/SelectAsync'
import { Formik } from 'formik'
import { format, parseISO } from 'date-fns'
import { getStatusLabel, RES_STATUS } from './utils'
import Filter from 'src/components/Filter'
import { useUserHotels } from 'src/hooks/useUserHotels'



export default function ReservationHistorical() {
  const [showModal, setShowModal] = useState(false)
  const [editReservation, setEditReservation] = useState(null)
  const [historyReservationId, setHistoryReservationId] = useState(null)
  const [historyReservation, setHistoryReservation] = useState(null)
  const [filters, setFilters] = useState({ search: '', hotel: '', room: '', status: '', dateFrom: '', dateTo: '' })
  const didMountRef = useRef(false)
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()
  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'reservations',
    params: { search: filters.search, hotel: filters.hotel || undefined, room: filters.room || undefined, status: filters.status || undefined },
  })

  const { mutate: doAction, isPending: acting } = useDispatchAction({ resource: 'reservations', onSuccess: () => refetch() })

  const displayResults = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase()
    const from = filters.dateFrom ? new Date(filters.dateFrom) : null
    const to = filters.dateTo ? new Date(filters.dateTo) : null
    let arr = results || []
    if (q) {
      arr = arr.filter((r) => {
        const guest = String(r.guest_name ?? '').toLowerCase()
        const hotel = String(r.hotel_name ?? '').toLowerCase()
        const room = String(r.room_name ?? '').toLowerCase()
        const status = String(r.status ?? '').toLowerCase()
        return guest.includes(q) || hotel.includes(q) || room.includes(q) || status.includes(q)
      })
    }
    if (from || to) {
      arr = arr.filter((r) => {
        const ci = new Date(r.check_in)
        const co = new Date(r.check_out)
        if (from && co < from) return false
        if (to && ci > to) return false
        return true
      })
    }
    return arr
  }, [results, filters.search, filters.dateFrom, filters.dateTo])

  useEffect(() => {
    if (!didMountRef.current) { didMountRef.current = true; return }
    const id = setTimeout(() => refetch(), 400)
    return () => clearTimeout(id)
  }, [filters.search, filters.hotel, filters.room, filters.status, refetch])

  const canCheckIn = (r) => r.status === 'confirmed'
  const canCheckOut = (r) => r.status === 'check_in'
  const canCancel = (r) => r.status === 'pending' || r.status === 'confirmed'
  const canConfirm = (r) => r.status === 'pending'
  const canEdit = (r) => r.status === 'pending' // Solo se puede editar si está pendiente

  const onCheckIn = (r) => {
    console.log('Check-in para reserva:', r.id, 'estado actual:', r.status)
    doAction({ action: `${r.id}/check_in`, body: {}, method: 'POST' })
  }
  const onCheckOut = (r) => {
    console.log('Check-out para reserva:', r.id, 'estado actual:', r.status)
    doAction({ action: `${r.id}/check_out`, body: {}, method: 'POST' })
  }
  const onCancel = (r) => {
    console.log('Cancelar para reserva:', r.id, 'estado actual:', r.status)
    doAction({ action: `${r.id}/cancel`, body: {}, method: 'POST' })
  }
  const onConfirm = (r) => {
    console.log('Confirmar para reserva:', r.id, 'estado actual:', r.status)
    doAction({ action: `${r.id}`, body: { status: 'confirmed' }, method: 'PATCH' })
  }
  const onEdit = (r) => {
    console.log('Editar reserva:', r.id, 'estado actual:', r.status)
    setEditReservation(r)
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">Operación</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">Histórico de Reservas</h1>
        </div>
      </div>

      <ReservationsModal isOpen={showModal} onClose={() => setShowModal(false)} onSuccess={refetch} />
      <ReservationsModal isOpen={!!editReservation} onClose={() => setEditReservation(null)} isEdit={true} reservation={editReservation} onSuccess={refetch} />
      {!!historyReservationId && (
        <ReservationHistoricalModal
          reservationId={historyReservationId}
          displayName={historyReservation?.display_name}
          onClose={() => { setHistoryReservationId(null); setHistoryReservation(null) }}
        />
      )}

     <Filter>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">Buscar</label>
            <input
              className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-64 transition-all"
              placeholder="Huésped, hotel, habitación…"
              value={filters.search}
              onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
            />
          </div>

          <Formik
            enableReinitialize
            initialValues={{ hotel: filters.hotel, room: filters.room }}
            onSubmit={() => { }}
          >
            {() => (
              <>
                <div className="w-56">
                  <SelectAsync
                    title='Hotel'
                    name='hotel'
                    resource='hotels'
                    placeholder='Todos'
                    getOptionLabel={(h) => h?.name}
                    getOptionValue={(h) => h?.id}
                    extraParams={!isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {}}
                    onValueChange={(opt, val) => setFilters((f) => ({ ...f, hotel: String(val || '') }))}
                  />
                </div>

                <div className="w-56">
                  <SelectAsync
                    title='Habitación'
                    name='room'
                    resource='rooms'
                    placeholder='Todas'
                    getOptionLabel={(r) => r?.name || r?.number || `#${r?.id}`}
                    getOptionValue={(r) => r?.id}
                    extraParams={{ hotel: filters.hotel || undefined }}
                    onValueChange={(opt, val) => setFilters((f) => ({ ...f, room: String(val || '') }))}
                  />
                </div>
              </>
            )}
          </Formik>

          <div className="w-56">
            <label className="text-xs text-aloja-gray-800/60">Estado</label>
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full"
              value={filters.status}
              onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
            >
              <option value="">Todos</option>
              {RES_STATUS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">Desde</label>
            <input type="date" className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
              value={filters.dateFrom}
              onChange={(e) => setFilters((f) => ({ ...f, dateFrom: e.target.value }))}
            />
          </div>
          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">Hasta</label>
            <input type="date" className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
              value={filters.dateTo}
              onChange={(e) => setFilters((f) => ({ ...f, dateTo: e.target.value }))}
            />
          </div>

          <div className="ml-auto">
            <button className="px-3 py-2 rounded-md border text-sm" onClick={() => setFilters({ search: '', hotel: '', room: '', status: '', dateFrom: '', dateTo: '' })}>
              Limpiar filtros
            </button>
          </div>
        </div>
     </Filter>

      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          { key: 'display_name', header: 'Reserva', sortable: true, render: (r) => (
            <button
              className="link"
              onClick={() => { setHistoryReservation(r); setHistoryReservationId(r.id) }}
            >
              {r.display_name}
            </button>
          ) },
          { key: 'guest_name', header: 'Huésped', sortable: true },
          { key: 'hotel_name', header: 'Hotel', sortable: true },
          { key: 'room_name', header: 'Habitación', sortable: true },
          {
            key: 'check_in',
            header: 'Check-in',
            sortable: true,
            accessor: (e) => e.check_in ? format(parseISO(e.check_in), 'dd/MM/yyyy') : '',
            render: (e) => e.check_in ? format(parseISO(e.check_in), 'dd/MM/yyyy') : '',
          },
          {
            key: 'check_out',
            header: 'Check-out',
            sortable: true,
            accessor: (e) => e.check_out ? format(parseISO(e.check_out), 'dd/MM/yyyy') : '',
            render: (e) => e.check_out ? format(parseISO(e.check_out), 'dd/MM/yyyy') : '',
          },
          {
            key: 'created_at',
            header: 'Creada',
            sortable: true,
            accessor: (e) => e.created_at ? format(parseISO(e.created_at), 'dd/MM/yyyy HH:mm') : '',
            render: (e) => e.created_at ? format(parseISO(e.created_at), 'dd/MM/yyyy HH:mm') : '',
          },
          { key: 'guests', header: 'Cantidad de huéspedes', sortable: true, right: true },
          { key: 'total_price', header: 'Total', sortable: true, right: true },
          { key: 'status', header: 'Estado', sortable: true, render: (r) => <span>{getStatusLabel(r.status)}</span> },
        ]}
      />

      {hasNextPage && (
        <div>
          <button className="px-3 py-2 rounded-md border" onClick={() => fetchNextPage()}>
            Cargar más
          </button>
        </div>
      )}
    </div>
  )
}