import React, { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { useList } from 'src/hooks/useList'
import { useUserHotels } from 'src/hooks/useUserHotels'
import Button from 'src/components/Button'
import SelectStandalone from 'src/components/selects/SelectStandalone'
import Filter from 'src/components/Filter'
import ReservationsModal from 'src/components/modals/ReservationsModal'
import { format, parseISO, startOfDay, endOfDay } from 'date-fns'
import { es } from 'date-fns/locale'
import 'src/styles/calendar.css'

const ReservationsCalendar = () => {
  const { t, i18n } = useTranslation()
  const [showModal, setShowModal] = useState(false)
  const [editReservation, setEditReservation] = useState(null)
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [filters, setFilters] = useState({ 
    search: '', 
    hotel: '', 
    room: '', 
    status: '' 
  })
  
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()
  
  // Obtener hoteles para el filtro
  const { results: hotels } = useList({
    resource: 'hotels',
    params: !isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {},
  })
  
  // Obtener habitaciones para el filtro
  const { results: allRooms } = useList({
    resource: 'rooms',
    params: { hotel: filters.hotel || undefined },
  })
  
  // Obtener habitaciones con sus reservas
  const { results: rooms, isPending, refetch } = useList({
    resource: 'rooms',
    params: { 
      search: filters.search,
      hotel: filters.hotel || undefined,
      room: filters.room || undefined,
      status: filters.status || undefined,
    },
  })

  // Lista de estados para el filtro
  const statusList = useMemo(() => [
    { value: "pending", label: "Pendiente" },
    { value: "confirmed", label: "Confirmada" },
    { value: "check_in", label: "Check-in" },
    { value: "check_out", label: "Check-out" },
    { value: "cancelled", label: "Cancelada" },
    { value: "no_show", label: "No Show" }
  ], [])

  // Función para obtener color según estado
  const getStatusColor = (status) => {
    const colors = {
      'pending': '#F59E0B',      // Amarillo
      'confirmed': '#3B82F6',    // Azul
      'check_in': '#10B981',     // Verde
      'check_out': '#6B7280',    // Gris
      'cancelled': '#EF4444',    // Rojo
      'no_show': '#8B5CF6',      // Púrpura
    }
    return colors[status] || '#6B7280'
  }

  // Convertir reservas a eventos del calendario
  const calendarEvents = useMemo(() => {
    if (!rooms) return []
    
    const events = []
    
    rooms.forEach(room => {
      // Agregar reserva actual si existe
      if (room.current_reservation) {
        const reservation = room.current_reservation
        events.push({
          id: `current-${reservation.id}`,
          title: `${room.name} - ${reservation.guest_name}`,
          start: reservation.check_in,
          end: reservation.check_out,
          backgroundColor: getStatusColor(reservation.status),
          borderColor: getStatusColor(reservation.status),
          textColor: '#FFFFFF',
          extendedProps: {
            room: room,
            reservation: reservation,
            type: 'current'
          }
        })
      }
      
      // Agregar reservas futuras
      if (room.future_reservations && room.future_reservations.length > 0) {
        room.future_reservations.forEach(reservation => {
          events.push({
            id: `future-${reservation.id}`,
            title: `${room.name} - ${reservation.guest_name}`,
            start: reservation.check_in,
            end: reservation.check_out,
            backgroundColor: getStatusColor(reservation.status),
            borderColor: getStatusColor(reservation.status),
            textColor: '#FFFFFF',
            extendedProps: {
              room: room,
              reservation: reservation,
              type: 'future'
            }
          })
        })
      }
    })
    
    return events
  }, [rooms, getStatusColor])

  // Manejar clic en evento
  const handleEventClick = (clickInfo) => {
    setSelectedEvent(clickInfo.event)
  }

  // Manejar clic en fecha vacía para crear nueva reserva
  const handleDateClick = (dateClickInfo) => {
    setShowModal(true)
  }

  // Manejar selección de rango de fechas
  const handleSelect = (selectInfo) => {
    setShowModal(true)
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('dashboard.reservations_management.title')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">Calendario de Reservas</h1>
        </div>
        <Button variant="primary" size="md" onClick={() => setShowModal(true)}>
          {t('dashboard.reservations_management.create_reservation')}
        </Button>
      </div>

      <ReservationsModal 
        isOpen={showModal} 
        onClose={() => setShowModal(false)} 
        onSuccess={refetch} 
      />
      
      <ReservationsModal 
        isOpen={!!editReservation} 
        onClose={() => setEditReservation(null)} 
        isEdit={true} 
        reservation={editReservation} 
        onSuccess={refetch} 
      />

      <Filter>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">{t('common.search')}</label>
            <input
              className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-64 transition-all"
              placeholder="Buscar habitación o huésped..."
              value={filters.search}
              onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
            />
          </div>

          <div className="w-56">
            <SelectStandalone
              title={t('dashboard.reservations_management.hotel')}
              className="w-full"
              value={hotels?.find(h => String(h.id) === String(filters.hotel)) || null}
              onChange={(option) => setFilters((f) => ({ ...f, hotel: option ? String(option.id) : '' }))}
              options={hotels || []}
              getOptionLabel={(h) => h?.name}
              getOptionValue={(h) => h?.id}
              placeholder={t('dashboard.reservations_management.all')}
              isClearable
              isSearchable
            />
          </div>

          <div className="w-56">
            <SelectStandalone
              title={t('dashboard.reservations_management.room')}
              className="w-full"
              value={allRooms?.find(r => String(r.id) === String(filters.room)) || null}
              onChange={(option) => setFilters((f) => ({ ...f, room: option ? String(option.id) : '' }))}
              options={allRooms || []}
              getOptionLabel={(r) => r?.name || r?.number || `#${r?.id}`}
              getOptionValue={(r) => r?.id}
              placeholder={t('dashboard.reservations_management.all_rooms')}
              isClearable
              isSearchable
            />
          </div>

          <div className="w-56">
            <SelectStandalone
              title={t('dashboard.reservations_management.status')}
              className="w-full"
              value={statusList.find(s => String(s.value) === String(filters.status)) || null}
              onChange={(option) => setFilters((f) => ({ ...f, status: option ? String(option.value) : '' }))}
              options={[
                { value: "", label: t('dashboard.reservations_management.all') },
                ...statusList
              ]}
              placeholder={t('dashboard.reservations_management.all')}
              isClearable
              isSearchable
            />
          </div>

          <div className="ml-auto">
            <button 
              className="px-3 py-2 rounded-md border text-sm" 
              onClick={() => setFilters({ search: '', hotel: '', room: '', status: '' })}
            >
              Limpiar filtros
            </button>
          </div>
        </div>
      </Filter>

      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 overflow-hidden">
        <FullCalendar
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView="dayGridMonth"
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
          }}
          events={calendarEvents}
          eventClick={handleEventClick}
          dateClick={handleDateClick}
          selectable={true}
          selectMirror={true}
          select={handleSelect}
          height="auto"
          locale={i18n.language === 'es' ? 'es' : 'en'}
          buttonText={{
            today: 'Hoy',
            month: 'Mes',
            week: 'Semana',
            day: 'Día'
          }}
          eventDisplay="block"
          dayMaxEvents={3}
          moreLinkClick="popover"
          eventClassNames={(event) => {
            const status = event.extendedProps?.reservation?.status
            return status ? [`reservation-${status}`] : []
          }}
        />
      </div>

      {/* Modal moderno para mostrar detalles del evento */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white/95 backdrop-blur-md rounded-2xl p-8 max-w-md w-full shadow-2xl border border-white/20 animate-in fade-in-0 zoom-in-95 duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-2 h-8 bg-gradient-to-b from-blue-500 to-blue-600 rounded-full"></div>
              <h3 className="text-xl font-bold text-gray-900">Detalles de la Reserva</h3>
            </div>
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 font-bold text-sm">🏨</span>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Habitación</p>
                  <p className="font-semibold text-gray-900">{selectedEvent.extendedProps?.room?.name || 'N/A'}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-green-600 font-bold text-sm">👤</span>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Huésped</p>
                  <p className="font-semibold text-gray-900">{selectedEvent.extendedProps?.reservation?.guest_name || 'N/A'}</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-gray-50 rounded-xl">
                  <p className="text-sm text-gray-500">Check-in</p>
                  <p className="font-semibold text-gray-900">
                    {selectedEvent.extendedProps?.reservation?.check_in ? format(parseISO(selectedEvent.extendedProps.reservation.check_in), 'dd/MM/yyyy') : 'N/A'}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-xl">
                  <p className="text-sm text-gray-500">Check-out</p>
                  <p className="font-semibold text-gray-900">
                    {selectedEvent.extendedProps?.reservation?.check_out ? format(parseISO(selectedEvent.extendedProps.reservation.check_out), 'dd/MM/yyyy') : 'N/A'}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <span className="text-purple-600 font-bold text-sm">📊</span>
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-500">Estado</p>
                  <p className="font-semibold text-gray-900 capitalize">{selectedEvent.extendedProps?.reservation?.status || 'N/A'}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">Tipo</p>
                  <p className="font-semibold text-gray-900">{selectedEvent.extendedProps?.type === 'current' ? 'Actual' : 'Futura'}</p>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-8">
              <button 
                className="px-6 py-3 text-gray-600 hover:text-gray-800 font-semibold rounded-xl hover:bg-gray-100 transition-all duration-200"
                onClick={() => setSelectedEvent(null)}
              >
                Cerrar
              </button>
              <button 
                className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-semibold rounded-xl hover:from-blue-600 hover:to-blue-700 transform hover:scale-105 transition-all duration-200 shadow-lg hover:shadow-xl"
                onClick={() => {
                  if (selectedEvent.extendedProps?.reservation) {
                    setEditReservation(selectedEvent.extendedProps.reservation)
                    setSelectedEvent(null)
                  }
                }}
              >
                Editar Reserva
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ReservationsCalendar