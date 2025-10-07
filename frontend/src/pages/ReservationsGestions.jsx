import { useMemo, useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import { useDispatchAction } from 'src/hooks/useDispatchAction'
import ReservationsModal from 'src/components/modals/ReservationsModal'
import Button from 'src/components/Button'
import SelectAsync from 'src/components/selects/SelectAsync'
import { Formik } from 'formik'
import { format, parseISO } from 'date-fns'
import { convertToDecimal, getStatusLabel, RES_STATUS } from './utils'
import Filter from 'src/components/Filter'
import { useUserHotels } from 'src/hooks/useUserHotels'



export default function ReservationsGestions() {
  const { t, i18n } = useTranslation()
  const [showModal, setShowModal] = useState(false)
  const [editReservation, setEditReservation] = useState(null)
  const [filters, setFilters] = useState({ search: '', hotel: '', room: '', status: '', dateFrom: '', dateTo: '' })
  const didMountRef = useRef(false)
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()
  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'reservations',
    params: { 
      search: filters.search,
      hotel: filters.hotel || undefined,
      room: filters.room || undefined,
      status: filters.status || undefined,
      show_historical: true,
    },
  })

  const { mutate: doAction, isPending: acting } = useDispatchAction({ resource: 'reservations', onSuccess: () => refetch() })

  const displayResults = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase()
    const from = filters.dateFrom ? new Date(filters.dateFrom) : null
    const to = filters.dateTo ? new Date(filters.dateTo) : null
    let arr = results || []
    // Excluir reservas finalizadas (check_out) de la gestión
    arr = arr.filter((r) => r.status !== 'check_out' && r.status !== 'cancelled' && r.status !== 'no_show')
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
    console.log(t('dashboard.reservations_management.console_messages.check_in_for'), r.id, t('dashboard.reservations_management.console_messages.current_status'), r.status)
    doAction({ action: `${r.id}/check_in`, body: {}, method: 'POST' })
  }
  const onCheckOut = (r) => {
    console.log(t('dashboard.reservations_management.console_messages.check_out_for'), r.id, t('dashboard.reservations_management.console_messages.current_status'), r.status)
    doAction({ action: `${r.id}/check_out`, body: {}, method: 'POST' })
  }
  const onCancel = (r) => {
    console.log(t('dashboard.reservations_management.console_messages.cancel_for'), r.id, t('dashboard.reservations_management.console_messages.current_status'), r.status)
    doAction({ action: `${r.id}/cancel`, body: {}, method: 'POST' })
  }
  const onConfirm = (r) => {
    console.log(t('dashboard.reservations_management.console_messages.confirm_for'), r.id, t('dashboard.reservations_management.console_messages.current_status'), r.status)
    doAction({ action: `${r.id}`, body: { status: 'confirmed' }, method: 'PATCH' })
  }
  const onEdit = (r) => {
    console.log(t('dashboard.reservations_management.console_messages.edit_reservation'), r.id, t('dashboard.reservations_management.console_messages.current_status'), r.status)
    setEditReservation(r)
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('dashboard.reservations_management.title')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('dashboard.reservations_management.subtitle')}</h1>
        </div>
        <Button variant="primary" size="md" onClick={() => setShowModal(true)}>
          {t('dashboard.reservations_management.create_reservation')}
        </Button>
      </div>

      <ReservationsModal isOpen={showModal} onClose={() => setShowModal(false)} onSuccess={refetch} />
      <ReservationsModal isOpen={!!editReservation} onClose={() => setEditReservation(null)} isEdit={true} reservation={editReservation} onSuccess={refetch} />

     <Filter>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">{t('common.search')}</label>
            <input
              className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-64 transition-all"
              placeholder={t('dashboard.reservations_management.search_placeholder')}
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
                    title={t('dashboard.reservations_management.hotel')}
                    name='hotel'
                    resource='hotels'
                    placeholder={t('dashboard.reservations_management.all')}
                    getOptionLabel={(h) => h?.name}
                    getOptionValue={(h) => h?.id}
                    onValueChange={(opt, val) => setFilters((f) => ({ ...f, hotel: String(val || '') }))}
                    extraParams={!isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {}}
                  />
                </div>

                <div className="w-56">
                  <SelectAsync
                    title={t('dashboard.reservations_management.room')}
                    name='room'
                    resource='rooms'
                    placeholder={t('dashboard.reservations_management.all_rooms')}
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
            <label className="text-xs text-aloja-gray-800/60">{t('dashboard.reservations_management.status')}</label>
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full"
              value={filters.status}
              onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
            >
              <option value="">{t('dashboard.reservations_management.all')}</option>
              {RES_STATUS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">{t('dashboard.reservations_management.from')}</label>
            <input type="date" className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
              value={filters.dateFrom}
              onChange={(e) => setFilters((f) => ({ ...f, dateFrom: e.target.value }))}
            />
          </div>
          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">{t('dashboard.reservations_management.to')}</label>
            <input type="date" className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
              value={filters.dateTo}
              onChange={(e) => setFilters((f) => ({ ...f, dateTo: e.target.value }))}
            />
          </div>

          <div className="ml-auto">
            <button className="px-3 py-2 rounded-md border text-sm" onClick={() => setFilters({ search: '', hotel: '', room: '', status: '', dateFrom: '', dateTo: '' })}>
              {t('dashboard.reservations_management.clear_filters')}
            </button>
          </div>
        </div>
     </Filter>

      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          { key: 'display_name', header: t('dashboard.reservations_management.table_headers.reservation'), sortable: true },
          { key: 'guest_name', header: t('dashboard.reservations_management.table_headers.guest'), sortable: true },
          { key: 'hotel_name', header: t('dashboard.reservations_management.table_headers.hotel'), sortable: true },
          { key: 'room_name', header: t('dashboard.reservations_management.table_headers.room'), sortable: true },
          {
            key: 'check_in',
            header: t('dashboard.reservations_management.table_headers.check_in'),
            sortable: true,
            accessor: (e) => e.check_in ? format(parseISO(e.check_in), 'dd/MM/yyyy') : '',
            render: (e) => e.check_in ? format(parseISO(e.check_in), 'dd/MM/yyyy') : '',
          },
          {
            key: 'check_out',
            header: t('dashboard.reservations_management.table_headers.check_out'),
            sortable: true,
            accessor: (e) => e.check_out ? format(parseISO(e.check_out), 'dd/MM/yyyy') : '',
            render: (e) => e.check_out ? format(parseISO(e.check_out), 'dd/MM/yyyy') : '',
          },
          {
            key: 'created_at',
            header: t('dashboard.reservations_management.table_headers.created'),
            sortable: true,
            accessor: (e) => e.created_at ? format(parseISO(e.created_at), 'dd/MM/yyyy HH:mm') : '',
            render: (e) => e.created_at ? format(parseISO(e.created_at), 'dd/MM/yyyy HH:mm') : '',
          },
          { key: 'guests', header: t('dashboard.reservations_management.table_headers.guests_count'), sortable: true, right: true },
          { key: 'total_price', header: t('dashboard.reservations_management.table_headers.total'), sortable: true, right: true, render: (r) => `$ ${convertToDecimal(r.total_price)}` },
          { key: 'status', header: t('dashboard.reservations_management.table_headers.status'), sortable: true, render: (r) => <span>{getStatusLabel(r.status, t)}</span> },
          {
            key: 'actions', header: t('dashboard.reservations_management.table_headers.actions'), sortable: false, right: true,
            render: (r) => (
              <div className="flex justify-end items-center gap-2">
                <button
                  className={`px-2 py-1 rounded text-xs border transition-colors
                    ${canEdit(r)
                      ? 'bg-blue-50 text-blue-700 border-blue-300 hover:bg-blue-100'
                      : 'opacity-40 cursor-not-allowed bg-blue-50 text-blue-700 border-blue-300'}
                  `}
                  disabled={!canEdit(r) || acting}
                  onClick={() => onEdit(r)}
                >
                  {t('dashboard.reservations_management.actions.edit')}
                </button>
                <button
                  className={`px-2 py-1 rounded text-xs border transition-colors
                    ${canConfirm(r)
                      ? 'bg-aloja-navy text-white border-aloja-navy hover:bg-aloja-navy2'
                      : 'opacity-40 cursor-not-allowed bg-aloja-navy text-white border-aloja-navy'}
                  `}
                  disabled={!canConfirm(r) || acting}
                  onClick={() => onConfirm(r)}
                >
                  {t('dashboard.reservations_management.actions.confirm')}
                </button>
                <button
                  className={`px-2 py-1 rounded text-xs border transition-colors
                    ${canCheckIn(r)
                      ? 'bg-aloja-gold text-aloja-navy border-aloja-gold hover:brightness-95'
                      : 'opacity-40 cursor-not-allowed bg-aloja-gold text-aloja-navy border-aloja-gold'}
                  `}
                  disabled={!canCheckIn(r) || acting}
                  onClick={() => onCheckIn(r)}
                >
                  {t('dashboard.reservations_management.actions.check_in')}
                </button>
                <button
                  className={`px-2 py-1 rounded text-xs border transition-colors
                    ${canCheckOut(r)
                      ? 'bg-white text-aloja-navy border-aloja-navy hover:bg-aloja-navy/5'
                      : 'opacity-40 cursor-not-allowed bg-white text-aloja-navy border-aloja-navy'}
                  `}
                  disabled={!canCheckOut(r) || acting}
                  onClick={() => onCheckOut(r)}
                >
                  {t('dashboard.reservations_management.actions.check_out')}
                </button>
                <button
                  className={`px-2 py-1 rounded text-xs border transition-colors
                    ${canCancel(r)
                      ? 'bg-red-50 text-red-700 border-red-300 hover:bg-red-100'
                      : 'opacity-40 cursor-not-allowed bg-red-50 text-red-700 border-red-300'}
                  `}
                  disabled={!canCancel(r) || acting}
                  onClick={() => onCancel(r)}
                >
                  {t('dashboard.reservations_management.actions.cancel')}
                </button>
              </div>
            )
          }
        ]}
      />

      {hasNextPage && (displayResults?.length >= 50) && (
        <div>
          <button className="px-3 py-2 rounded-md border" onClick={() => fetchNextPage()}>
            {t('dashboard.reservations_management.load_more')}
          </button>
        </div>
      )}
    </div>
  )
}