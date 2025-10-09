import { useMemo, useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import ReservationHistoricalModal from 'src/components/modals/ReservationHistoricalModal'
import PaymentDetailModal from 'src/components/modals/PaymentDetailModal'
import { useList } from 'src/hooks/useList'
import { useUserHotels } from 'src/hooks/useUserHotels'
import SelectAsync from 'src/components/selects/SelectAsync'
import { Formik } from 'formik'
import { format, parseISO } from 'date-fns'
import { convertToDecimal, getStatusLabel, getResStatusList } from './utils'
import Filter from 'src/components/Filter'
import Badge from 'src/components/Badge'

export default function Payments() {
  const { t } = useTranslation()
  const [historyReservationId, setHistoryReservationId] = useState(null)
  const [historyReservation, setHistoryReservation] = useState(null)
  const [paymentDetailOpen, setPaymentDetailOpen] = useState(false)
  const [selectedReservation, setSelectedReservation] = useState(null)
  const [filters, setFilters] = useState({ 
    search: '', 
    hotel: '', 
    room: '', 
    status: '', 
    dateFrom: '', 
    dateTo: '' 
  })
  const didMountRef = useRef(false)
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()
  
  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'reservations',
    params: { 
      search: filters.search, 
      hotel: filters.hotel || undefined, 
      room: filters.room || undefined, 
      status: filters.status || undefined,
    },
  })

  const displayResults = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase()
    const from = filters.dateFrom ? new Date(filters.dateFrom) : null
    const to = filters.dateTo ? new Date(filters.dateTo) : null
    let arr = results || []
    
    // Filtrar reservas que necesitan pago (pending) y las que ya pagaron (confirmed en adelante)
    arr = arr.filter((r) => r.status === 'pending' || r.status === 'confirmed' || r.status === 'check_in' || r.status === 'check_out')
    
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

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.history')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('payments.title')}</h1>
        </div>
      </div>
      <PaymentDetailModal
        isOpen={paymentDetailOpen}
        onClose={() => { setPaymentDetailOpen(false); setSelectedReservation(null) }}
        reservationId={selectedReservation?.id}
        reservationData={selectedReservation}
      />

      <Filter>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">{t('common.search')}</label>
            <input
              className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-64 transition-all"
              placeholder={t('payments.search_placeholder')}
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
                    title={t('common.hotel')}
                    name='hotel'
                    resource='hotels'
                    placeholder={t('common.all')}
                    getOptionLabel={(h) => h?.name}
                    getOptionValue={(h) => h?.id}
                    extraParams={!isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {}}
                    onValueChange={(opt, val) => setFilters((f) => ({ ...f, hotel: String(val || '') }))}
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
            <label className="text-xs text-aloja-gray-800/60">{t('common.status')}</label>
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full"
              value={filters.status}
              onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
            >
              <option value="">{t('common.all')}</option>
              {getResStatusList(t).map((s) => (
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
          { key: 'display_name', header: t('dashboard.reservations_management.table_headers.reservation'), sortable: true, render: (r) => (
            <div className="flex items-center gap-2">
              <button
                className="link"
                onClick={() => {
                  setSelectedReservation(r)
                  setPaymentDetailOpen(true)
                }}
              >
                {r.display_name}
              </button>
            </div>
          ) },
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
          { 
            key: 'status', 
            header: t('dashboard.reservations_management.table_headers.status'), 
            sortable: true, 
            render: (r) => (
              <Badge variant={`reservation-${r.status}`} size="sm">
                {getStatusLabel(r.status, t)}
              </Badge>
            ) 
          },
          {
            key: 'payment_status',
            header: t('payments.table.payment_status'),
            sortable: true,
            render: (r) => {
              // Basar el estado de pago en el estado real de la reserva
              // pending = pendiente, confirmed/check_in/check_out = pagado
              const isPaid = r.status === 'confirmed' || r.status === 'check_in' || r.status === 'check_out'
              const paymentVariant = isPaid ? 'payment-paid' : 'payment-pending'
              const paymentText = isPaid 
                ? t('payments.payment_status.paid') 
                : t('payments.payment_status.pending')
              
              return (
                <Badge variant={paymentVariant} size="sm">
                  {paymentText}
                </Badge>
              )
            }
          },
        ]}
      />

      {hasNextPage && (
        <div>
          <button className="px-3 py-2 rounded-md border" onClick={() => fetchNextPage()}>
            {t('common.load_more')}
          </button>
        </div>
      )}
    </div>
  )
}
