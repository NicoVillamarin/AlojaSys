import { useMemo, useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import ReservationHistoricalModal from 'src/components/modals/ReservationHistoricalModal'
import MultiRoomReservationDetailModal from 'src/components/modals/MultiRoomReservationDetailModal'
import GuestDetailsModal from 'src/components/modals/GuestDetailsModal'
import { useList } from 'src/hooks/useList'
import { useDispatchAction } from 'src/hooks/useDispatchAction'
import ReservationsModal from 'src/components/modals/ReservationsModal'
import Button from 'src/components/Button'
import ExportButton from 'src/components/ExportButton'
import SelectAsync from 'src/components/selects/SelectAsync'
import { Formik } from 'formik'
import { format, parseISO } from 'date-fns'
import { convertToDecimal, getStatusLabel, getResStatusList } from './utils'
import Filter from 'src/components/Filter'
import { useUserHotels } from 'src/hooks/useUserHotels'
import Badge from 'src/components/Badge'
import WhatsappIcon from 'src/assets/icons/WhatsappIcon'
import GlobalIcon from 'src/assets/icons/GlobalIcon'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import { usePermissions } from 'src/hooks/usePermissions'
import { showErrorConfirm, showSuccess } from 'src/services/toast'
import { exportJsonToExcel } from 'src/utils/exportExcel'


export default function ReservationHistorical() {
  const { t } = useTranslation()

  // Permisos de reservas para histórico
  const canViewReservation = usePermissions('reservations.view_reservation')
  const canAddReservation = usePermissions('reservations.add_reservation')
  const canChangeReservation = usePermissions('reservations.change_reservation')
  const canDeleteReservation = usePermissions('reservations.delete_reservation')
  const [showModal, setShowModal] = useState(false)
  const [editReservation, setEditReservation] = useState(null)
  const [historyReservationId, setHistoryReservationId] = useState(null)
  const [historyReservation, setHistoryReservation] = useState(null)
  const [showMultiRoomDetail, setShowMultiRoomDetail] = useState(false)
  const [selectedMultiRoomGroup, setSelectedMultiRoomGroup] = useState(null)
  const [guestDetailsOpen, setGuestDetailsOpen] = useState(false)
  const [guestDetailsReservation, setGuestDetailsReservation] = useState(null)
  const [filters, setFilters] = useState({ search: '', hotel: '', room: '', status: '', dateFrom: '', dateTo: '' })
  const [isExporting, setIsExporting] = useState(false)
  const didMountRef = useRef(false)
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()
  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'reservations',
    params: { 
      search: filters.search, 
      hotel: filters.hotel || undefined, 
      room: filters.room || undefined, 
      status: filters.status || undefined,
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
      ordering: '-id', // Ordenar por ID descendente (más recientes primero)
      page_size: 100, // Cargar suficientes resultados para el histórico (puede usar "Cargar más" si necesita más)
    },
    enabled: canViewReservation,
  })

  const { mutate: doAction, isPending: acting } = useDispatchAction({ resource: 'reservations', onSuccess: () => refetch() })

  const normalizeReservationForExport = (r, { groupCode = '', isFromGroup = false } = {}) => {
    const isOta = r?.is_ota || r?.external_id
    const channel = r?.channel_display || r?.channel || (isOta ? 'OTA' : 'Directo')

    const safeDate = (value, fmt) => {
      if (!value) return ''
      try {
        return format(parseISO(value), fmt)
      } catch {
        return String(value)
      }
    }

    return {
      ID: r?.id ?? '',
      Reserva: r?.display_name ?? '',
      Huésped: r?.guest_name ?? '',
      Responsable: r?.created_by_name ?? '',
      Hotel: r?.hotel_name ?? '',
      Habitación: r?.room_name ?? '',
      Canal: channel,
      'Check-in': safeDate(r?.check_in, 'dd/MM/yyyy'),
      'Check-out': safeDate(r?.check_out, 'dd/MM/yyyy'),
      Creada: safeDate(r?.created_at, 'dd/MM/yyyy HH:mm'),
      Huéspedes: r?.guests ?? '',
      Total: typeof r?.total_price === 'number' ? r.total_price : (parseFloat(r?.total_price) || 0),
      Estado: getStatusLabel(r?.status, t),
      Grupo: groupCode || r?.group_code || '',
      'Multi-habitación': isFromGroup ? 'Sí' : 'No',
      Overbooking: r?.overbooking_flag ? 'Sí' : 'No',
      'Pagada por': r?.paid_by || '',
    }
  }

  const handleExportExcel = async () => {
    if (!displayResults?.length) {
      showErrorConfirm('No hay reservas para exportar con los filtros actuales.')
      return
    }

    try {
      setIsExporting(true)
      const rows = []
      for (const r of displayResults) {
        if (r?.is_group && Array.isArray(r.group_reservations) && r.group_reservations.length > 0) {
          for (const rr of r.group_reservations) {
            rows.push(normalizeReservationForExport(rr, { groupCode: r.group_code || '', isFromGroup: true }))
          }
        } else {
          rows.push(normalizeReservationForExport(r, { groupCode: r?.group_code || '', isFromGroup: false }))
        }
      }

      const today = format(new Date(), 'yyyy-MM-dd')
      await exportJsonToExcel({
        rows,
        filename: `reservas_historico_${today}.xlsx`,
        sheetName: 'Reservas',
      })
      showSuccess('Excel generado correctamente.')
    } catch (error) {
      console.error('Error exportando reservas:', error)
      showErrorConfirm('No se pudo exportar el Excel. Revisá la consola para más detalle.')
    } finally {
      setIsExporting(false)
    }
  }

  const displayResults = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase()
    let arr = results || []
    
    if (q) {
      arr = arr.filter((r) => {
        const guest = String(r.guest_name ?? '').toLowerCase()
        const hotel = String(r.hotel_name ?? '').toLowerCase()
        const room = String(r.room_name ?? '').toLowerCase()
        const status = String(r.status ?? '').toLowerCase()
        const group = String(r.group_code ?? '').toLowerCase()
        return guest.includes(q) || hotel.includes(q) || room.includes(q) || status.includes(q) || group.includes(q)
      })
    }
    
    // Agrupar por group_code para reservas multi-habitación (igual que en ReservationsGestions)
    const groupedByCode = {}
    const singles = []
    for (const r of arr) {
      if (r.group_code) {
        if (!groupedByCode[r.group_code]) groupedByCode[r.group_code] = []
        groupedByCode[r.group_code].push(r)
      } else {
        singles.push(r)
      }
    }

    const groupRows = []
    Object.values(groupedByCode).forEach((group) => {
      if (group.length === 1) {
        // Grupo de una sola habitación: se muestra como reserva normal
        singles.push(group[0])
        return
      }
      const first = group[0]
      const roomsCount = group.length
      const totalPrice = group.reduce(
        (sum, item) => sum + (parseFloat(item.total_price) || 0),
        0
      )
      const totalGuests = group.reduce(
        (sum, item) => sum + (parseInt(item.guests) || 0),
        0
      )

      groupRows.push({
        ...first,
        // Meta para UI
        is_group: true,
        group_reservations: group,
        rooms_count: roomsCount,
        // Sobrescribir campos que queremos mostrar agregados
        total_price: totalPrice,
        guests: totalGuests,
      })
    })

    const finalArr = [...singles, ...groupRows]

    // Ordenar por ID descendente por defecto (más recientes primero)
    finalArr.sort((a, b) => (b.id || 0) - (a.id || 0))
    return finalArr
  }, [results, filters.search])

  useEffect(() => {
    if (!didMountRef.current) { didMountRef.current = true; return }
    const id = setTimeout(() => refetch(), 400)
    return () => clearTimeout(id)
  }, [filters.search, filters.hotel, filters.room, filters.status, filters.dateFrom, filters.dateTo, refetch])

  const canCheckIn = (r) => canChangeReservation && r.status === 'confirmed'
  const canCheckOut = (r) => canChangeReservation && r.status === 'check_in'
  const isOtaReservation = (r) => !!(r?.is_ota || r?.external_id)
  const canCancel = (r) =>
    canDeleteReservation &&
    !isOtaReservation(r) &&
    (r.status === 'pending' || r.status === 'confirmed')
  const canConfirm = (r) => canChangeReservation && r.status === 'pending'
  const canEdit = (r) => canChangeReservation && r.status === 'pending' // Solo se puede editar si está pendiente

  const onCheckIn = (r) => {
    if (!canCheckIn(r)) return
    doAction({ action: `${r.id}/check_in`, body: {}, method: 'POST' })
  }
  const onCheckOut = (r) => {
    if (!canCheckOut(r)) return
    doAction({ action: `${r.id}/check_out`, body: {}, method: 'POST' })
  }
  const onCancel = (r) => {
    if (!canCancel(r)) return
    doAction({ action: `${r.id}/cancel`, body: {}, method: 'POST' })
  }
  const onConfirm = (r) => {
    if (!canConfirm(r)) return
    doAction({ action: `${r.id}`, body: { status: 'confirmed' }, method: 'PATCH' })
  }
  const onEdit = (r) => {
    if (!canEdit(r)) return
    setEditReservation(r)
  }

  // Si no tiene permiso para ver reservas, mostrar mensaje
  if (!canViewReservation) {
    return (
      <div className="p-6 text-center text-gray-600">
        {t('sidebar.no_permission_history', 'No tenés permiso para ver el histórico de reservas.')}
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.history')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('sidebar.reservations_history')}</h1>
        </div>
        <div className="flex gap-2">
          <ExportButton
            onClick={handleExportExcel}
            isPending={isExporting}
            loadingText="Exportando..."
          >
            Exportar Excel
          </ExportButton>
        </div>
      </div>

      <ReservationsModal 
        isOpen={canAddReservation && showModal} 
        onClose={() => setShowModal(false)} 
        onSuccess={refetch} 
      />
      <ReservationsModal 
        isOpen={!!editReservation && canChangeReservation} 
        onClose={() => setEditReservation(null)} 
        isEdit={true} 
        reservation={editReservation} 
        onSuccess={refetch} 
      />
      {!!historyReservationId && (
        <ReservationHistoricalModal
          reservationId={historyReservationId}
          displayName={historyReservation?.display_name}
          reservationStatus={historyReservation?.status}
          onClose={() => { setHistoryReservationId(null); setHistoryReservation(null) }}
        />
      )}
      <MultiRoomReservationDetailModal
        isOpen={showMultiRoomDetail}
        onClose={() => {
          setShowMultiRoomDetail(false);
          setSelectedMultiRoomGroup(null);
        }}
        groupCode={selectedMultiRoomGroup?.groupCode}
        groupReservations={selectedMultiRoomGroup?.groupReservations}
      />
      <GuestDetailsModal
        isOpen={guestDetailsOpen}
        onClose={() => {
          setGuestDetailsOpen(false)
          setGuestDetailsReservation(null)
        }}
        reservation={guestDetailsReservation}
      />

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
            <button className="px-3 py-2 rounded-md border" onClick={() => setFilters({ search: '', hotel: '', room: '', status: '', dateFrom: '', dateTo: '' })}>
              {t('dashboard.reservations_management.clear_filters')}
            </button>
          </div>
        </div>
     </Filter>

      <TableGeneric
        adaptiveHeight={true}
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          { 
            key: 'display_name', 
            header: t('dashboard.reservations_management.table_headers.reservation'), 
            sortable: true, 
            render: (r) => {
              if (r.is_group && r.group_code) {
                const roomsCount =
                  r.rooms_count || (r.group_reservations?.length ?? 0) || 1;
                return (
                  <div className="flex flex-col">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedMultiRoomGroup({
                          groupCode: r.group_code,
                          groupReservations: r.group_reservations || [],
                        });
                        setShowMultiRoomDetail(true);
                      }}
                      className="text-left text-blue-600 hover:text-blue-800 hover:underline"
                      title="Click para ver detalle de todas las habitaciones"
                    >
                      {r.display_name}
                    </button>
                    <span className="text-[11px] text-blue-700 font-semibold">
                      Multi-habitación · {roomsCount} hab.
                    </span>
                  </div>
                );
              }
              return (
                <span
                  role="button"
                  tabIndex={0}
                  className="link cursor-pointer"
                  onClick={() => { setHistoryReservation(r); setHistoryReservationId(r.id) }}
                  onKeyDown={(e) => { if (e.key === 'Enter') { setHistoryReservation(r); setHistoryReservationId(r.id) } }}
                >
                  {r.display_name}
                </span>
              );
            }
          },
          {
            key: 'guest_name',
            header: t('dashboard.reservations_management.table_headers.guest'),
            sortable: true,
            render: (r) => (
              <button
                type="button"
                className="text-blue-600 hover:text-blue-800 cursor-pointer text-left"
                onClick={(e) => {
                  e.stopPropagation()
                  setGuestDetailsReservation(r)
                  setGuestDetailsOpen(true)
                }}
                title="Ver datos del huésped"
              >
                {r.guest_name || '—'}
              </button>
            ),
          },
          {
            key: 'created_by_name',
            header: t('dashboard.reservations_management.table_headers.responsible', 'Responsable'),
            sortable: true,
            accessor: (r) => r?.created_by_name ?? '',
            render: (r) => (
              <span className={r?.created_by_name ? 'text-aloja-navy' : 'text-gray-400'}>
                {r?.created_by_name || '—'}
              </span>
            ),
          },
          { key: 'hotel_name', header: t('dashboard.reservations_management.table_headers.hotel'), sortable: true },
          { 
            key: 'room_name', 
            header: t('dashboard.reservations_management.table_headers.room'), 
            sortable: true,
            render: (r) => {
              if (r.is_group && r.group_code) {
                const roomsCount =
                  r.rooms_count || (r.group_reservations?.length ?? 0) || 1;
                return (
                  <span>
                    {roomsCount === 1
                      ? r.room_name || ''
                      : `${roomsCount} habitaciones`}
                  </span>
                );
              }
              return r.room_name;
            }
          },
          {
            key: 'channel',
            header: t('dashboard.reservations_management.table_headers.channel'),
            sortable: true,
            render: (r) => {
              const isOta = r.is_ota || r.external_id
              const channel = r.channel_display || r.channel || 'Directo'
              const channelValue = r.channel || 'direct'
              
              // Colores según el canal
              const getChannelBadge = () => {
                if (!isOta) {
                  if (channelValue === 'whatsapp') {
                    return (
                      <Badge variant="warning" size="sm" icon={WhatsappIcon}>
                        WhatsApp
                      </Badge>
                    )
                  }
                  if (channelValue === 'website') {
                    return (
                      <Badge variant="info" size="sm" icon={GlobalIcon}>
                        Sitio Web
                      </Badge>
                    )
                  }
                  return (
                    <Badge variant="directo" size="sm">
                      Directo
                    </Badge>
                  )
                }
                
                // Badge según el tipo de canal OTA
                // Detectar Google Calendar por notes o external_id
                const isGoogle = (r.notes || '').toLowerCase().includes('google calendar') || 
                                (r.external_id || '').includes('@google.com')
                
                switch (channelValue) {
                  case 'booking':
                    return (
                      <Badge variant="booking" size="sm">
                        Booking
                      </Badge>
                    )
                  case 'airbnb':
                    return (
                      <Badge variant="airbnb" size="sm">
                        Airbnb
                      </Badge>
                    )
                  case 'expedia':
                    return (
                      <Badge variant="airbnb" size="sm">
                        Expedia
                      </Badge>
                    )
                  case 'other':
                    if (isGoogle) {
                      return (
                        <Badge variant="google" size="sm">
                          Google Calendar
                        </Badge>
                      )
                    }
                    return (
                      <Badge variant="warning" size="sm">
                        {channel}
                      </Badge>
                    )
                  default:
                    return (
                      <Badge variant="warning" size="sm">
                        {channel}
                      </Badge>
                    )
                }
              }

              return (
                <div className="flex items-center gap-1">
                  {getChannelBadge()}
                </div>
              )
            }
          },
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
              <div className="flex items-center gap-1 flex-wrap">
                <Badge variant={`reservation-${r.status}`} size="sm">
                  {getStatusLabel(r.status, t)}
                </Badge>
                {r.overbooking_flag && (
                  <Badge variant="warning" size="sm">
                    Overbooking
                  </Badge>
                )}
                {r.paid_by === 'ota' && (() => {
                  let channelName = r.channel_display || r.channel || 'OTA'
                  if (!r.channel_display && r.channel) {
                    channelName = r.channel.charAt(0).toUpperCase() + r.channel.slice(1)
                  }
                  return (
                    <Badge variant="success" size="sm">
                      Pagada por {channelName}
                    </Badge>
                  )
                })()}
                {r.paid_by === 'hotel' && (
                  <Badge variant="info" size="sm">
                    Pago directo
                  </Badge>
                )}
              </div>
            ) 
          },
        ]}
      />

      {hasNextPage && (
        <div className="flex justify-center pt-2">
          <button
            type="button"
            className="px-5 py-2.5 rounded-lg bg-aloja-navy text-white font-medium shadow-sm hover:bg-aloja-navy/90 focus:ring-2 focus:ring-aloja-navy/30 focus:ring-offset-1 transition-colors"
            onClick={() => fetchNextPage()}
          >
            {t('common.load_more')}
          </button>
        </div>
      )}
    </div>
  )
}