import React, { useState, useEffect, useMemo, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import resourceTimelinePlugin from '@fullcalendar/resource-timeline'
import resourceDayGridPlugin from '@fullcalendar/resource-daygrid'
import scrollGridPlugin from '@fullcalendar/scrollgrid'
import { useList } from 'src/hooks/useList'
import { useUserHotels } from 'src/hooks/useUserHotels'
import { useCalendarEvents, useCalendarStats, useCalendarDragDrop } from 'src/hooks/useCalendar'
import Button from 'src/components/Button'
import SelectStandalone from 'src/components/selects/SelectStandalone'
import Filter from 'src/components/Filter'
import ReservationsModal from 'src/components/modals/ReservationsModal'
import Kpis from 'src/components/Kpis'
import { format, parseISO, startOfDay, endOfDay, isToday, isAfter, isBefore, subDays, addDays } from 'date-fns'
import { es } from 'date-fns/locale'
import Swal from 'sweetalert2'
import AlertSwal from 'src/components/AlertSwal'
import 'src/styles/calendar.css'

// Iconos para los KPIs
import ChartBarIcon from 'src/assets/icons/ChartBarIcon'
import CheckIcon from 'src/assets/icons/CheckIcon'
import ExclamationTriangleIcon from 'src/assets/icons/ExclamationTriangleIcon'
import CheckinIcon from 'src/assets/icons/CheckinIcon'
import CheckoutIcon from 'src/assets/icons/CheckoutIcon'
import CurrencyDollarIcon from 'src/assets/icons/CurrencyDollarIcon'
import CalendarIcon from 'src/assets/icons/CalendarIcon'
import EyeIcon from 'src/assets/icons/EyeIcon'
import EyeSlashIcon from 'src/assets/icons/EyeSlashIcon'
import WarningIcon from 'src/assets/icons/WarningIcon'
import InfoIcon from 'src/assets/icons/InfoIcon'
import ToggleButton from 'src/components/ToggleButton'

const ReservationsCalendar = () => {
  const { t, i18n } = useTranslation()
  const [showModal, setShowModal] = useState(false)
  const [editReservation, setEditReservation] = useState(null)
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [isModalClosing, setIsModalClosing] = useState(false)
  const [selectedDateRange, setSelectedDateRange] = useState(null)
  const [showKpis, setShowKpis] = useState(false)
  const [currentView, setCurrentView] = useState('dayGridMonth')
  const [selectedEvents, setSelectedEvents] = useState([])
  const [showLegend, setShowLegend] = useState(false)
  const [forceRender, setForceRender] = useState(0)
  const calendarRef = useRef(null)
  
  // Estados para modales de confirmación
  const [showDragDropAlert, setShowDragDropAlert] = useState(false)
  const [showResizeAlert, setShowResizeAlert] = useState(false)
  const [showSuccessModal, setShowSuccessModal] = useState(false)
  const [showErrorModal, setShowErrorModal] = useState(false)
  const [alertData, setAlertData] = useState(null)
  
  // Función para forzar re-render del calendario
  const forceCalendarRender = () => {
    // Forzar re-render del componente completo
    setForceRender(prev => prev + 1)
    
    if (calendarRef.current) {
      const calendarApi = calendarRef.current.getApi()
      
      // Método más agresivo: destruir y recrear el calendario
      const currentView = calendarApi.view.type
      const currentDate = calendarApi.getDate()
      
      // Forzar re-render múltiples veces
      calendarApi.render()
      calendarApi.updateSize()
      
      // Cambiar de vista y volver para forzar re-cálculo completo
      calendarApi.changeView('dayGridMonth')
      setTimeout(() => {
        calendarApi.changeView(currentView)
        calendarApi.gotoDate(currentDate)
        calendarApi.render()
      }, 10)
      
      // Segundo intento después de un poco más de tiempo
      setTimeout(() => {
        calendarApi.render()
        calendarApi.updateSize()
      }, 100)
    }
  }

  // Efecto para detectar cuando la pestaña vuelve a estar activa y forzar re-render
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && calendarRef.current) {
        // La pestaña volvió a estar visible, forzar re-render
        forceCalendarRender()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  // Efecto para cerrar el modal con la tecla Escape
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && selectedEvent && !isModalClosing) {
        closeEventModal()
      }
    }

    if (selectedEvent) {
      document.addEventListener('keydown', handleKeyDown)
      // Prevenir scroll del body cuando el modal está abierto
      document.body.style.overflow = 'hidden'
    } else {
      // Restaurar scroll del body cuando el modal se cierra
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'unset'
    }
  }, [selectedEvent, isModalClosing])
  
  const [filters, setFilters] = useState({ 
    search: '', 
    hotel: '', 
    room: '', 
    status: '' 
  })
  
  // Estado para el rango de fechas del calendario
  const [dateRange, setDateRange] = useState(() => {
    const today = new Date()
    const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
    const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0)
    return {
      startDate: startOfMonth.toISOString().split('T')[0],
      endDate: endOfMonth.toISOString().split('T')[0]
    }
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
  
  // Usar la nueva API de calendario
  const { 
    events: calendarEvents, 
    isPending: eventsLoading, 
    isError: eventsError, 
    refetch: refetchEvents 
  } = useCalendarEvents({
    hotel: filters.hotel || singleHotelId,
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
    includeMaintenance: true,
    includeBlocks: true,
    viewType: 'month',
    enabled: false // Deshabilitar temporalmente para evitar errores
  })
  
  // Obtener estadísticas del calendario
  const { 
    stats: calendarStats, 
    isPending: statsLoading 
  } = useCalendarStats({
    hotel: filters.hotel || singleHotelId,
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
    enabled: false // Deshabilitar temporalmente
  })

  // Hook para drag & drop
  const { mutate: dragDropMutation, isPending: dragDropLoading } = useCalendarDragDrop()
  
  // Obtener todas las reservas desde hoy en adelante
  const { results: reservations, isPending, refetch } = useList({
    resource: 'reservations',
    params: { 
      search: filters.search,
      hotel: filters.hotel || undefined,
      room: filters.room || undefined,
      status: filters.status || undefined,
      // Solo reservas desde hoy en adelante
      check_in_gte: format(new Date(), 'yyyy-MM-dd'),
    },
  })

  // Mantener compatibilidad con la API anterior para filtros (solo para KPIs)
  const { results: rooms } = useList({
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

  // Crear leyenda de colores
  const colorLegend = useMemo(() => [
    { status: 'pending', label: 'Pendiente', color: '#F59E0B', description: 'Reserva pendiente de confirmación' },
    { status: 'confirmed', label: 'Confirmada', color: '#3B82F6', description: 'Reserva confirmada y lista' },
    { status: 'check_in', label: 'Check-in', color: '#10B981', description: 'Huésped en la habitación' },
    { status: 'check_out', label: 'Check-out', color: '#6B7280', description: 'Huésped saliendo hoy' },
    { status: 'cancelled', label: 'Cancelada', color: '#EF4444', description: 'Reserva cancelada' },
    { status: 'no_show', label: 'No Show', color: '#8B5CF6', description: 'Huésped no se presentó' }
  ], [])

  // Calcular estadísticas de reservas
  const reservationStats = useMemo(() => {
    if (!rooms) return {
      totalReservations: 0,
      currentReservations: 0,
      futureReservations: 0,
      confirmedReservations: 0,
      pendingReservations: 0,
      cancelledReservations: 0,
      checkInsToday: 0,
      checkOutsToday: 0,
      totalRevenue: 0,
      averageStay: 0
    }

    let totalReservations = 0
    let currentReservations = 0
    let futureReservations = 0
    let confirmedReservations = 0
    let pendingReservations = 0
    let cancelledReservations = 0
    let checkInsToday = 0
    let checkOutsToday = 0
    let totalRevenue = 0
    let totalNights = 0
    const today = new Date()
    
    rooms.forEach(room => {
      // Reserva actual
      if (room.current_reservation) {
        const reservation = room.current_reservation
        totalReservations++
        currentReservations++
        
        if (reservation.status === 'confirmed' || reservation.status === 'check_in') {
          confirmedReservations++
        } else if (reservation.status === 'pending') {
          pendingReservations++
        } else if (reservation.status === 'cancelled') {
          cancelledReservations++
        }

        if (reservation.total_price) {
          totalRevenue += reservation.total_price
        }

        // Calcular noches
        const checkIn = parseISO(reservation.check_in)
        const checkOut = parseISO(reservation.check_out)
        const nights = Math.ceil((checkOut - checkIn) / (1000 * 60 * 60 * 24))
        totalNights += nights
      }

      // Reservas futuras
      if (room.future_reservations && room.future_reservations.length > 0) {
        room.future_reservations.forEach(reservation => {
          totalReservations++
          futureReservations++
          
          if (reservation.status === 'confirmed') {
            confirmedReservations++
          } else if (reservation.status === 'pending') {
            pendingReservations++
          } else if (reservation.status === 'cancelled') {
            cancelledReservations++
          }

          if (reservation.total_price) {
            totalRevenue += reservation.total_price
          }

          // Calcular noches
          const checkIn = parseISO(reservation.check_in)
          const checkOut = parseISO(reservation.check_out)
          const nights = Math.ceil((checkOut - checkIn) / (1000 * 60 * 60 * 24))
          totalNights += nights

          // Check-ins y check-outs de hoy
          if (isToday(checkIn)) {
            checkInsToday++
          }
          if (isToday(checkOut)) {
            checkOutsToday++
          }
        })
      }
    })

    return {
      totalReservations,
      currentReservations,
      futureReservations,
      confirmedReservations,
      pendingReservations,
      cancelledReservations,
      checkInsToday,
      checkOutsToday,
      totalRevenue,
      averageStay: totalReservations > 0 ? Math.round(totalNights / totalReservations) : 0
    }
  }, [rooms])

  // Convertir habitaciones a recursos para la vista de habitaciones
  const calendarResources = useMemo(() => {
    if (!rooms) return []
    
    return rooms.map(room => ({
      id: room.id.toString(),
      title: room.name || `HAB-${room.number || room.id}`,
      group: room.floor ? `Piso ${room.floor}` : 'Sin piso',
      extendedProps: {
        room: room,
        floor: room.floor,
        room_type: room.room_type,
        capacity: room.capacity
      }
    }))
  }, [rooms])

  // Convertir reservas a eventos del calendario (usando API de reservas directamente)
  const fullCalendarEvents = useMemo(() => {
    if (!reservations) return []
    
    
    const events = []
    
    reservations.forEach(reservation => {
        const startDate = parseISO(reservation.check_in)
        // Para FullCalendar con allDay, la fecha de fin debe ser el día después del último día
        const endDate = parseISO(reservation.check_out)
        endDate.setDate(endDate.getDate() + 1)
        
        const resourceId = String(
          (reservation.room && typeof reservation.room === 'object' ? reservation.room.id : reservation.room) ??
          reservation.room_id
        )

        events.push({
        id: `reservation-${reservation.id}`,
        title: `${reservation.guest_name}`,
          start: startDate,
          end: endDate,
          allDay: true,
          resourceId,
          backgroundColor: getStatusColor(reservation.status),
          borderColor: getStatusColor(reservation.status),
          textColor: '#FFFFFF',
          extendedProps: {
          room: reservation.room || { id: resourceId },
            reservation: reservation,
          type: 'reservation'
        }
      })
    })
    
    return events
  }, [reservations, getStatusColor])

  // Crear KPIs para el calendario de reservas
  const calendarKpis = useMemo(() => {
    if (!reservationStats) return []

    return [
      {
        title: 'Total Reservas',
        value: reservationStats.totalReservations,
        icon: CalendarIcon,
        color: "from-blue-500 to-blue-600",
        bgColor: "bg-blue-100",
        iconColor: "text-blue-600",
        change: "+2",
        changeType: "positive",
        subtitle: "En el período actual",
        showProgress: false
      },
      {
        title: 'Reservas Actuales',
        value: reservationStats.currentReservations,
        icon: CheckIcon,
        color: "from-green-500 to-green-600",
        bgColor: "bg-green-100",
        iconColor: "text-green-600",
        change: "+1",
        changeType: "positive",
        subtitle: "Hoy en el hotel",
        progressWidth: reservationStats.totalReservations > 0 ? `${Math.min((reservationStats.currentReservations / reservationStats.totalReservations) * 100, 100)}%` : '0%'
      },
      {
        title: 'Reservas Futuras',
        value: reservationStats.futureReservations,
        icon: CalendarIcon,
        color: "from-indigo-500 to-indigo-600",
        bgColor: "bg-indigo-100",
        iconColor: "text-indigo-600",
        change: "+3",
        changeType: "positive",
        subtitle: "Próximas reservas",
        progressWidth: reservationStats.totalReservations > 0 ? `${Math.min((reservationStats.futureReservations / reservationStats.totalReservations) * 100, 100)}%` : '0%'
      },
      {
        title: 'Confirmadas',
        value: reservationStats.confirmedReservations,
        icon: CheckIcon,
        color: "from-emerald-500 to-emerald-600",
        bgColor: "bg-emerald-100",
        iconColor: "text-emerald-600",
        change: "+2",
        changeType: "positive",
        subtitle: "Reservas confirmadas",
        progressWidth: reservationStats.totalReservations > 0 ? `${Math.min((reservationStats.confirmedReservations / reservationStats.totalReservations) * 100, 100)}%` : '0%'
      },
      {
        title: 'Pendientes',
        value: reservationStats.pendingReservations,
        icon: ExclamationTriangleIcon,
        color: "from-yellow-500 to-yellow-600",
        bgColor: "bg-yellow-100",
        iconColor: "text-yellow-600",
        change: "0",
        changeType: "neutral",
        subtitle: "Esperando confirmación",
        progressWidth: reservationStats.totalReservations > 0 ? `${Math.min((reservationStats.pendingReservations / reservationStats.totalReservations) * 100, 100)}%` : '0%'
      },
      {
        title: 'Check-ins Hoy',
        value: reservationStats.checkInsToday,
        icon: CheckinIcon,
        color: "from-green-500 to-green-600",
        bgColor: "bg-green-100",
        iconColor: "text-green-600",
        change: "+1",
        changeType: "positive",
        subtitle: "Llegadas de hoy",
        showProgress: false
      },
      {
        title: 'Check-outs Hoy',
        value: reservationStats.checkOutsToday,
        icon: CheckoutIcon,
        color: "from-orange-500 to-orange-600",
        bgColor: "bg-orange-100",
        iconColor: "text-orange-600",
        change: "-1",
        changeType: "negative",
        subtitle: "Salidas de hoy",
        showProgress: false
      },
      {
        title: 'Ingresos Totales',
        value: `$${reservationStats.totalRevenue.toLocaleString()}`,
        icon: CurrencyDollarIcon,
        color: "from-purple-500 to-purple-600",
        bgColor: "bg-purple-100",
        iconColor: "text-purple-600",
        change: "+15%",
        changeType: "positive",
        subtitle: "En el período actual",
        showProgress: false
      }
    ]
  }, [reservationStats])

  // Función para mostrar confirmación de drag & drop
  const showDragDropConfirmation = (guestName, oldDates, newDates) => {
    return new Promise((resolve) => {
      setAlertData({
        guestName,
        oldDates,
        newDates,
        type: 'dragDrop',
        resolve
      })
      setShowDragDropAlert(true)
    })
  }

  // Función para mostrar confirmación de resize
  const showResizeConfirmation = (guestName, oldDates, newDates) => {
    return new Promise((resolve) => {
      setAlertData({
        guestName,
        oldDates,
        newDates,
        type: 'resize',
        resolve
      })
      setShowResizeAlert(true)
    })
  }

  // Función para mostrar éxito
  const showSuccessAlert = (title, message) => {
    setAlertData({ title, message })
    setShowSuccessModal(true)
  }

  // Función para mostrar error
  const showErrorAlert = (title, message) => {
    setAlertData({ title, message })
    setShowErrorModal(true)
  }

  // Función para cerrar el modal con animación
  const closeEventModal = () => {
    setIsModalClosing(true)
    setTimeout(() => {
      setSelectedEvent(null)
      setIsModalClosing(false)
    }, 200) // Duración de la animación de salida
  }

  // Funciones de manejo para los modales de confirmación
  const handleDragDropConfirm = () => {
    if (alertData?.resolve) {
      alertData.resolve({ isConfirmed: true })
    }
    setShowDragDropAlert(false)
    setAlertData(null)
  }

  const handleDragDropCancel = () => {
    if (alertData?.resolve) {
      alertData.resolve({ isConfirmed: false })
    }
    setShowDragDropAlert(false)
    setAlertData(null)
  }

  const handleResizeConfirm = () => {
    if (alertData?.resolve) {
      alertData.resolve({ isConfirmed: true })
    }
    setShowResizeAlert(false)
    setAlertData(null)
  }

  const handleResizeCancel = () => {
    if (alertData?.resolve) {
      alertData.resolve({ isConfirmed: false })
    }
    setShowResizeAlert(false)
    setAlertData(null)
  }

  // Manejar clic en evento
  const handleEventClick = (clickInfo) => {
      setSelectedEvent(clickInfo.event)
    // Forzar re-render al hacer click para arreglar cualquier problema visual
    forceCalendarRender()
  }

  // Manejar clic en fecha vacía para crear nueva reserva
  const handleDateClick = (dateClickInfo) => {
    const clickedDate = startOfDay(dateClickInfo.date)
    const today = startOfDay(new Date())
    
    // Validar que no se pueda crear reserva en fechas pasadas (antes de hoy)
    if (clickedDate < today) {
      showErrorAlert(
        'Fecha Inválida',
        'No se pueden crear reservas en fechas pasadas. Solo se permiten fechas de hoy en adelante.'
      )
      return
    }
    
    // Para click individual, establecer rango mínimo de una noche
    // Si es hoy, check-in hoy y check-out mañana
    // Si es futuro, check-in en esa fecha y check-out al día siguiente
    const startDate = clickedDate
    const endDate = addDays(clickedDate, 1)
    
    // Guardar el rango de fechas con mínimo de una noche
    setSelectedDateRange({
      startDate: format(startDate, 'yyyy-MM-dd'),
      endDate: format(endDate, 'yyyy-MM-dd')
    })
    
    setShowModal(true)
    // Forzar re-render al hacer click para arreglar cualquier problema visual
    forceCalendarRender()
  }

  // Manejar selección de rango de fechas
  const handleSelect = (selectInfo) => {
    const startDate = startOfDay(selectInfo.start)
    const endDate = startOfDay(selectInfo.end)
    const today = startOfDay(new Date())
    
    // Validar que no se pueda crear reserva en fechas pasadas (antes de hoy)
    if (startDate < today || endDate < today) {
      showErrorAlert(
        'Fecha Inválida',
        'No se pueden crear reservas en fechas pasadas. Solo se permiten fechas de hoy en adelante.'
      )
      return
    }
    
    // FullCalendar excluye el día de fin en la selección, pero para reservas de hotel
    // necesitamos incluir ambos días. Restamos 1 día del endDate para obtener la fecha real de checkout
    const realEndDate = subDays(endDate, 1)
    
    // Guardar el rango de fechas seleccionado
    setSelectedDateRange({
      startDate: format(startDate, 'yyyy-MM-dd'),
      endDate: format(realEndDate, 'yyyy-MM-dd')
    })
    
    setShowModal(true)
  }

  // Función para validar si se puede mover una reserva
  // Esta lógica debería venir del backend, pero por ahora la mantenemos aquí
  const canMoveReservation = (reservation) => {
    const status = reservation.status
    
    // Estados que NO permiten movimiento
    const nonMovableStatuses = ['check_in', 'check_out', 'cancelled', 'no_show']
    
    if (nonMovableStatuses.includes(status)) {
      const statusMessages = {
        'check_in': 'No se puede mover una reserva con huésped en el hotel',
        'check_out': 'No se puede mover una reserva con huésped saliendo',
        'cancelled': 'No se puede mover una reserva cancelada',
        'no_show': 'No se puede mover una reserva de no show'
      }
      
      return {
        canMove: false,
        reason: statusMessages[status] || 'No se puede mover esta reserva'
      }
    }
    
    return { canMove: true, reason: null }
  }

  // Manejar drag & drop de eventos
  const handleEventDrop = async (dropInfo) => {
    const event = dropInfo.event
    const newStart = dropInfo.event.start
    const newEnd = dropInfo.event.end || newStart
    
    // Obtener datos del evento
    const eventData = event.extendedProps
    if (!eventData.reservation) {
      event.revert()
      return
    }
    
    // Validar si se puede mover la reserva según su estado
    const validation = canMoveReservation(eventData.reservation)
    if (!validation.canMove) {
      showErrorAlert(
        'Movimiento No Permitido', 
        validation.reason
      )
      event.revert()
      return
    }
    
    // Validar que no se pueda mover a fechas pasadas (antes de hoy)
    const today = startOfDay(new Date())
    const newStartDate = startOfDay(newStart)
    const newEndDate = startOfDay(newEnd)
    
    if (newStartDate < today || newEndDate < today) {
      showErrorAlert(
        'Fecha Inválida', 
        'No se puede mover una reserva a fechas pasadas. Solo se permiten fechas de hoy en adelante.'
      )
      event.revert()
      return
    }
    
    // Guardar las fechas originales para poder revertir
    const originalStart = parseISO(eventData.reservation.check_in)
    const originalEnd = parseISO(eventData.reservation.check_out)
    // Para FullCalendar, la fecha de fin debe ser el día después
    const originalEndForCalendar = new Date(originalEnd)
    originalEndForCalendar.setDate(originalEndForCalendar.getDate() + 1)
    
    // Calcular nuevas fechas
    const newCheckIn = format(newStart, 'yyyy-MM-dd')
    // Para FullCalendar, newEnd ya incluye el día extra, necesitamos restarlo para obtener la fecha real de checkout
    const newCheckOutReal = subDays(newEnd, 1)
    const newCheckOut = format(newCheckOutReal, 'yyyy-MM-dd')
    
    // Preparar fechas para mostrar (usar fechas reales sin +1)
    const oldDates = `${format(originalStart, 'dd/MM/yyyy')} - ${format(originalEnd, 'dd/MM/yyyy')}`
    const newDates = `${format(newStart, 'dd/MM/yyyy')} - ${format(newCheckOutReal, 'dd/MM/yyyy')}`
    
    // Mostrar confirmación con SweetAlert2
    const result = await showDragDropConfirmation(eventData.reservation.guest_name, oldDates, newDates)
    
    if (result.isConfirmed) {
      dragDropMutation({
        reservationId: eventData.reservation.id,
        newRoomId: eventData.room.id, // Por ahora mantener la misma habitación
        newStartDate: newCheckIn,
        newEndDate: newCheckOut,
        notes: `Movido desde ${oldDates}`
      }, {
        onSuccess: () => {
          refetch()
          showSuccessAlert('¡Éxito!', 'Reserva movida correctamente')
        },
        onError: (error) => {
          console.error('Error al mover reserva:', error)
          showErrorAlert('Error', 'No se pudo mover la reserva. Inténtalo de nuevo.')
          // Revertir el cambio visual usando las fechas correctas para FullCalendar
          event.setStart(originalStart)
          event.setEnd(originalEndForCalendar)
          // Forzar re-render del calendario para arreglar el layout
          forceCalendarRender()
        }
      })
    } else {
      // Revertir el cambio si el usuario cancela usando las fechas correctas para FullCalendar
      event.setStart(originalStart)
      event.setEnd(originalEndForCalendar)
      // Forzar re-render del calendario para arreglar el layout
      setTimeout(() => {
        if (calendarRef.current) {
          calendarRef.current.getApi().render()
        }
      }, 100)
    }
  }

  // Manejar resize de eventos
  const handleEventResize = async (resizeInfo) => {
    const event = resizeInfo.event
    const newStart = event.start
    const newEnd = event.end
    
    // Obtener datos del evento
    const eventData = event.extendedProps
    if (!eventData.reservation) {
      event.revert()
      return
    }
    
    // Validar si se puede redimensionar la reserva según su estado
    const validation = canMoveReservation(eventData.reservation)
    if (!validation.canMove) {
      showErrorAlert(
        'Redimensionado No Permitido', 
        validation.reason
      )
      event.revert()
      return
    }
    
    // Validar que no se pueda redimensionar a fechas pasadas (antes de hoy)
    const today = startOfDay(new Date())
    const newStartDate = startOfDay(newStart)
    const newEndDate = startOfDay(newEnd)
    
    if (newStartDate < today || newEndDate < today) {
      showErrorAlert(
        'Fecha Inválida', 
        'No se puede cambiar una reserva a fechas pasadas. Solo se permiten fechas de hoy en adelante.'
      )
      event.revert()
      return
    }
    
    // Guardar las fechas originales para poder revertir
    const originalStart = parseISO(eventData.reservation.check_in)
    const originalEnd = parseISO(eventData.reservation.check_out)
    // Para FullCalendar, la fecha de fin debe ser el día después
    const originalEndForCalendar = new Date(originalEnd)
    originalEndForCalendar.setDate(originalEndForCalendar.getDate() + 1)
    
    // Calcular nuevas fechas
    const newCheckIn = format(newStart, 'yyyy-MM-dd')
    // Para FullCalendar, newEnd ya incluye el día extra, necesitamos restarlo para obtener la fecha real de checkout
    const newCheckOutReal = subDays(newEnd, 1)
    const newCheckOut = format(newCheckOutReal, 'yyyy-MM-dd')
    
    // Preparar fechas para mostrar (usar fechas reales sin +1)
    const oldDates = `${format(originalStart, 'dd/MM/yyyy')} - ${format(originalEnd, 'dd/MM/yyyy')}`
    const newDates = `${format(newStart, 'dd/MM/yyyy')} - ${format(newCheckOutReal, 'dd/MM/yyyy')}`
    
    // Mostrar confirmación con SweetAlert2
    const result = await showResizeConfirmation(eventData.reservation.guest_name, oldDates, newDates)
    
    if (result.isConfirmed) {
      dragDropMutation({
        reservationId: eventData.reservation.id,
        newRoomId: eventData.room.id,
        newStartDate: newCheckIn,
        newEndDate: newCheckOut,
        notes: `Redimensionado desde ${oldDates}`
      }, {
        onSuccess: () => {
          refetch()
          showSuccessAlert('¡Éxito!', 'Fechas de reserva actualizadas correctamente')
        },
        onError: (error) => {
          console.error('Error al actualizar fechas:', error)
          showErrorAlert('Error', 'No se pudieron actualizar las fechas. Inténtalo de nuevo.')
          // Revertir el cambio visual usando las fechas correctas para FullCalendar
          event.setStart(originalStart)
          event.setEnd(originalEndForCalendar)
          // Forzar re-render del calendario para arreglar el layout
          forceCalendarRender()
        }
      })
    } else {
      // Revertir el cambio si el usuario cancela usando las fechas correctas para FullCalendar
      event.setStart(originalStart)
      event.setEnd(originalEndForCalendar)
      // Forzar re-render del calendario para arreglar el layout
      setTimeout(() => {
        if (calendarRef.current) {
          calendarRef.current.getApi().render()
        }
      }, 100)
    }
  }

  // Manejar selección múltiple de eventos
  const handleEventSelect = (selectInfo) => {
    const eventId = selectInfo.event.id
    setSelectedEvents(prev => {
      if (prev.includes(eventId)) {
        return prev.filter(id => id !== eventId)
      } else {
        return [...prev, eventId]
      }
    })
  }

  // Manejar cambio de vista
  const handleViewChange = (viewInfo) => {
    setCurrentView(viewInfo.view.type)
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('dashboard.reservations_management.title')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">Calendario de Reservas</h1>
        </div>
      </div>
      <ReservationsModal 
        isOpen={showModal} 
        onClose={() => {
          setShowModal(false)
          setSelectedDateRange(null)
        }} 
        onSuccess={refetch} 
        initialData={selectedDateRange ? {
          check_in: selectedDateRange.startDate,
          check_out: selectedDateRange.endDate
        } : null}
      />
      
      <ReservationsModal 
        isOpen={!!editReservation} 
        onClose={() => setEditReservation(null)} 
        isEdit={true} 
        reservation={editReservation} 
        onSuccess={refetch} 
      />
      <div className="space-y-4">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
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
          </div>
          
          <div className="flex items-center gap-3">
            <ToggleButton
              isOpen={showKpis}
              onToggle={() => setShowKpis(!showKpis)}
              openLabel="Ocultar KPIs"
              closedLabel="Mostrar KPIs"
              icon={EyeSlashIcon}
              closedIcon={EyeIcon}
            />

            <ToggleButton
              isOpen={showLegend}
              onToggle={() => setShowLegend(!showLegend)}
              openLabel="Ocultar Leyenda"
              closedLabel="Leyenda"
              icon={EyeSlashIcon}
              closedIcon={EyeIcon}
            />
          </div>
        </div>

        {/* KPIs con animación */}
        <div 
          className={`overflow-hidden transition-all duration-500 ease-in-out ${
            showKpis 
              ? 'max-h-96 opacity-100 transform translate-y-0' 
              : 'max-h-0 opacity-0 transform -translate-y-4'
          }`}
        >
          <div className={`transition-all duration-300 delay-75 ${
            showKpis ? 'opacity-100 transform translate-y-0' : 'opacity-0 transform -translate-y-2'
          }`}>
            <Kpis kpis={calendarKpis} loading={isPending} />
          </div>
        </div>

        {/* Leyenda de colores con animación */}
        <div 
          className={`overflow-hidden transition-all duration-500 ease-in-out ${
            showLegend 
              ? 'max-h-96 opacity-100 transform translate-y-0' 
              : 'max-h-0 opacity-0 transform -translate-y-4'
          }`}
        >
          <div className={`transition-all duration-300 delay-75 ${
            showLegend ? 'opacity-100 transform translate-y-0' : 'opacity-0 transform -translate-y-2'
          }`}>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <InfoIcon className="w-5 h-5 text-blue-600" />
                Leyenda de Colores
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {colorLegend.map((item) => (
                  <div key={item.status} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors duration-200">
                    <div 
                      className="w-4 h-4 rounded-full flex-shrink-0"
                      style={{ backgroundColor: item.color }}
                    ></div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900">{item.label}</div>
                      <div className="text-sm text-gray-600">{item.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 overflow-hidden">
        {isPending && (
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Cargando calendario...</span>
          </div>
        )}
        <FullCalendar
          key={forceRender}
          ref={calendarRef}
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin, resourceTimelinePlugin, resourceDayGridPlugin, scrollGridPlugin]}
          initialView={currentView}
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,resourceTimelineWeek'
          }}
          schedulerLicenseKey={'GPL-My-Project-Is-Open-Source'}
          // Configuración específica para vista de habitaciones
          {...(currentView === 'resourceTimelineWeek' && {
            slotDuration: { days: 1 },
            slotLabelInterval: { days: 1 },
            slotLabelFormat: [{ weekday: 'short', day: '2-digit', month: '2-digit' }],
            slotMinWidth: 100,
            stickyHeaderDates: true,
            nowIndicator: true,
            resources: calendarResources,
            resourceLabelText: "Habitaciones",
            resourceOrder: "title",
            resourceAreaWidth: "200px",
            resourceGroupField: 'group',
            resourceColumns: [
              {
                field: 'title',
                headerContent: 'Habitación'
              },
              {
                field: 'extendedProps.floor',
                headerContent: 'Piso'
              },
              {
                field: 'extendedProps.room_type',
                headerContent: 'Tipo'
              }
            ]
          })}
          // Configuración específica para otras vistas
          {...(currentView !== 'resourceTimelineWeek' && {
            nowIndicator: true
          })}
          events={fullCalendarEvents}
          eventClick={handleEventClick}
          dateClick={handleDateClick}
          selectable={true}
          selectMirror={true}
          select={handleSelect}
          selectOverlap={true}
          selectConstraint={{
            start: new Date().toISOString().split('T')[0], // Solo permitir selección desde hoy
            end: '2100-12-31' // Hasta el final de los tiempos
          }}
          selectAllow={(selectInfo) => {
            // Permitir selección sobre cualquier área, incluyendo eventos existentes
            const startDate = startOfDay(selectInfo.start)
            const endDate = startOfDay(selectInfo.end)
            const today = startOfDay(new Date())
            
            // Solo validar que no sean fechas pasadas (antes de hoy)
            return startDate >= today && endDate >= today
          }}
          dayMaxEvents={false} // Permitir ver todos los eventos, incluso en fechas pasadas
        editable={true}
        droppable={true}
        eventStartEditable={(event) => {
          // Validar fechas y estado de la reserva
          const eventStart = startOfDay(event.start)
          const eventEnd = startOfDay(event.end || event.start)
          const today = startOfDay(new Date())
          const eventData = event.extendedProps
          
          // No permitir fechas pasadas (antes de hoy)
          if (eventStart < today || eventEnd < today) return false
          
          // Validar estado de la reserva - esto previene que se inicie el drag
          if (eventData?.reservation) {
            const validation = canMoveReservation(eventData.reservation)
            return validation.canMove
          }
          
          return true
        }}
        eventDurationEditable={(event) => {
          // Validar fechas y estado de la reserva
          const eventStart = startOfDay(event.start)
          const eventEnd = startOfDay(event.end || event.start)
          const today = startOfDay(new Date())
          const eventData = event.extendedProps
          
          // No permitir fechas pasadas (antes de hoy)
          if (eventStart < today || eventEnd < today) return false
          
          // Validar estado de la reserva - esto previene que se inicie el resize
          if (eventData?.reservation) {
            const validation = canMoveReservation(eventData.reservation)
            return validation.canMove
          }
          
          return true
        }}
        eventAllow={(dropInfo, draggedEvent) => {
          // Validar fechas y estado de la reserva
          const eventStart = startOfDay(draggedEvent.start)
          const eventEnd = startOfDay(draggedEvent.end || draggedEvent.start)
          const today = startOfDay(new Date())
          const eventData = draggedEvent.extendedProps
          
          // No permitir fechas pasadas (antes de hoy)
          if (eventStart < today || eventEnd < today) return false
          
          // Validar estado de la reserva
          if (eventData?.reservation) {
            const validation = canMoveReservation(eventData.reservation)
            return validation.canMove
          }
          
          return true
        }}
          eventDrop={handleEventDrop}
          eventResize={handleEventResize}
          viewDidMount={handleViewChange}
          height="auto"
          locale={i18n.language === 'es' ? 'es' : 'en'}
          buttonText={{
            today: 'Hoy',
            month: 'Mes',
            week: 'Semana',
            day: 'Día',
            resourceTimelineWeek: 'Habitaciones'
          }}
          eventContent={(info) => {
            const r = info.event.extendedProps?.reservation
            const status = r?.status
            const guest = r?.guest_name || 'Reserva'
            return {
              domNodes: [(() => {
                const container = document.createElement('div')
                container.className = 'flex items-center gap-2'
                const title = document.createElement('div')
                title.className = 'text-xs font-semibold truncate'
                title.textContent = guest
                const badge = document.createElement('span')
                badge.className = 'text-[10px] px-1.5 py-0.5 rounded-md bg-white/20'
                badge.textContent = (status || '').replace('_',' ')
                container.appendChild(title)
                if (status) container.appendChild(badge)
                return container
              })()]
            }
          }}
          eventDisplay="block"
          dayMaxEvents={3}
          moreLinkClick="popover"
          dayCellClassNames={(dateInfo) => {
            const cellDate = startOfDay(dateInfo.date)
            const today = startOfDay(new Date())
            const classes = []
            
            // Marcar fechas pasadas (desde ayer para atrás)
            if (cellDate < today) {
              classes.push('fc-day-past')
            }
            
            return classes
          }}
          eventClassNames={(event) => {
            const isSelected = selectedEvents.includes(event.id)
            const classes = [
              isSelected ? 'event-selected' : '',
              'event-draggable'
            ]
            
            // Deshabilitar drag & drop para fechas pasadas (antes de hoy)
            const eventStart = startOfDay(event.start)
            const eventEnd = startOfDay(event.end || event.start)
            const today = startOfDay(new Date())
            if (eventStart < today || eventEnd < today) {
              classes.push('event-past-disabled')
            }
            
            // Deshabilitar drag & drop para reservas con estados que no permiten movimiento
            const eventData = event.extendedProps
            if (eventData?.reservation) {
              const validation = canMoveReservation(eventData.reservation)
              if (!validation.canMove) {
                classes.push('event-status-disabled')
              }
            }
            
            return classes
          }}
          eventDidMount={(info) => {
            const eventStart = startOfDay(info.event.start)
            const eventEnd = startOfDay(info.event.end || info.event.start)
            const today = startOfDay(new Date())
            const eventData = info.event.extendedProps
            
            if (eventStart < today || eventEnd < today) {
              // Fechas pasadas - no arrastrable pero clickeable para ver detalles
              info.el.style.cursor = 'pointer'
              info.el.title = `${info.event.title} - Reserva pasada (click para ver detalles)`
            } else if (eventData?.reservation) {
              // Validar estado de la reserva
              const validation = canMoveReservation(eventData.reservation)
              if (!validation.canMove) {
                // Estado que no permite movimiento
                info.el.style.cursor = 'not-allowed'
                info.el.title = `${info.event.title} - ${validation.reason}`
              } else {
                // Estado que permite movimiento
                info.el.style.cursor = 'move'
                info.el.title = `${info.event.title} - Arrastra para mover, redimensiona para cambiar fechas`
              }
            } else {
              // Fechas futuras - arrastrable por defecto
              info.el.style.cursor = 'move'
              info.el.title = `${info.event.title} - Arrastra para mover, redimensiona para cambiar fechas`
            }
          }}
        />
      </div>

      {/* Modal moderno para mostrar detalles del evento */}
      {selectedEvent && (
        <div className={`event-detail-modal ${isModalClosing ? 'closing' : ''}`}>
          <div className={`event-detail-modal-backdrop ${isModalClosing ? 'closing' : ''}`} onClick={closeEventModal}></div>
          <div className={`event-detail-modal-content ${isModalClosing ? 'closing' : ''}`}>
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
                  <p className="font-semibold text-gray-900">
                    {selectedEvent.extendedProps?.reservation?.room?.name || 
                     selectedEvent.extendedProps?.reservation?.room_name || 
                     selectedEvent.extendedProps?.room?.name || 
                     selectedEvent.extendedProps?.reservation?.room?.number ||
                     selectedEvent.extendedProps?.room?.number ||
                     'Sin habitación asignada'}
                  </p>
                  {(selectedEvent.extendedProps?.reservation?.room?.floor || selectedEvent.extendedProps?.room?.floor) && (
                    <p className="text-xs text-gray-500">
                      Piso {selectedEvent.extendedProps?.reservation?.room?.floor || selectedEvent.extendedProps?.room?.floor}
                    </p>
                  )}
                </div>
              </div>
              
              {selectedEvent.extendedProps?.reservation && (
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-green-600 font-bold text-sm">👤</span>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Huésped</p>
                    <p className="font-semibold text-gray-900">{selectedEvent.extendedProps.reservation.guest_name || 'N/A'}</p>
                    {selectedEvent.extendedProps.reservation.guests_count && (
                      <p className="text-xs text-gray-500">{selectedEvent.extendedProps.reservation.guests_count} huéspedes</p>
                    )}
                </div>
              </div>
              )}

              {selectedEvent.extendedProps?.reservation?.id && (
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                  <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                    <span className="text-purple-600 font-bold text-sm">#</span>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">N° de Reserva</p>
                    <p className="font-semibold text-gray-900">N° {selectedEvent.extendedProps.reservation.id}</p>
                  </div>
                </div>
              )}
              
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
              
              {selectedEvent.extendedProps?.reservation?.total_price && (
                <div className="p-3 bg-gray-50 rounded-xl">
                  <p className="text-sm text-gray-500">Precio Total</p>
                  <p className="font-semibold text-gray-900 text-lg">
                    ${selectedEvent.extendedProps.reservation.total_price.toLocaleString()}
                  </p>
                </div>
              )}
              
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <span className="text-purple-600 font-bold text-sm">📊</span>
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-500">Estado</p>
                  <p className="font-semibold text-gray-900 capitalize">
                    {selectedEvent.extendedProps?.reservation?.status || selectedEvent.extendedProps?.event_type || 'N/A'}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">Tipo</p>
                  <p className="font-semibold text-gray-900">
                    {selectedEvent.extendedProps?.reservation ? 'Reserva' : selectedEvent.extendedProps?.event_type || 'Evento'}
                  </p>
                </div>
              </div>
              
              {/* Mensaje informativo sobre edición */}
              {selectedEvent.extendedProps?.reservation && selectedEvent.extendedProps.reservation.status !== 'pending' && (
                <div className="flex items-center gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl">
                  <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center">
                    <span className="text-amber-600 font-bold text-sm">ℹ️</span>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-amber-800">
                      Reserva no editable
                    </p>
                    <p className="text-xs text-amber-700">
                      Solo se pueden editar reservas en estado "Pendiente". Esta reserva está en estado "{selectedEvent.extendedProps.reservation.status}".
                    </p>
                  </div>
                </div>
              )}
            </div>
            <div className="flex justify-end gap-3 mt-8">
              <Button 
                variant='danger'
                onClick={closeEventModal}
              >
                Cerrar
              </Button>
              {selectedEvent.extendedProps?.reservation && selectedEvent.extendedProps.reservation.status === 'pending' && (
              <Button 
                variant='success'
                onClick={() => {
                    setEditReservation(selectedEvent.extendedProps.reservation)
                    closeEventModal()
                }}
              >
                Editar Reserva
              </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modales de confirmación y alertas */}
      <AlertSwal
        isOpen={showDragDropAlert}
        onClose={handleDragDropCancel}
        onConfirm={handleDragDropConfirm}
        confirmLoading={false}
        title="¿Mover Reserva?"
        description={
          alertData ? (
            <div className="text-left space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center">
                  <span className="text-amber-600 font-bold text-sm">⚠️</span>
                </div>
                <div>
                  <p className="font-semibold text-gray-900">Confirmar Movimiento</p>
                  <p className="text-sm text-gray-600">Esta acción cambiará las fechas de la reserva</p>
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-1">Huésped:</p>
                  <p className="text-lg font-semibold text-gray-900">{alertData.guestName}</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-1">Fechas actuales:</p>
                    <p className="font-semibold text-red-600 bg-red-50 px-3 py-2 rounded-md">{alertData.oldDates}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-1">Nuevas fechas:</p>
                    <p className="font-semibold text-green-600 bg-green-50 px-3 py-2 rounded-md">{alertData.newDates}</p>
                  </div>
                </div>
              </div>
            </div>
          ) : ''
        }
        confirmText="Sí, mover reserva"
        cancelText="Cancelar"
        tone="warning"
      />

      <AlertSwal
        isOpen={showResizeAlert}
        onClose={handleResizeCancel}
        onConfirm={handleResizeConfirm}
        confirmLoading={false}
        title="¿Cambiar Fechas?"
        description={
          alertData ? (
            <div className="text-left space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 font-bold text-sm">⏰</span>
                </div>
                <div>
                  <p className="font-semibold text-gray-900">Confirmar Cambio de Fechas</p>
                  <p className="text-sm text-gray-600">Esta acción modificará la duración de la reserva</p>
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-1">Huésped:</p>
                  <p className="text-lg font-semibold text-gray-900">{alertData.guestName}</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-1">Fechas actuales:</p>
                    <p className="font-semibold text-red-600 bg-red-50 px-3 py-2 rounded-md">{alertData.oldDates}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-1">Nuevas fechas:</p>
                    <p className="font-semibold text-green-600 bg-green-50 px-3 py-2 rounded-md">{alertData.newDates}</p>
                  </div>
                </div>
              </div>
            </div>
          ) : ''
        }
        confirmText="Sí, cambiar fechas"
        cancelText="Cancelar"
        tone="info"
      />

      <AlertSwal
        isOpen={showSuccessModal}
        onClose={() => setShowSuccessModal(false)}
        onConfirm={() => setShowSuccessModal(false)}
        confirmLoading={false}
        title={alertData?.title || "Éxito"}
        description={alertData?.message || ""}
        confirmText="OK"
        cancelText=""
        tone="success"
      />

      <AlertSwal
        isOpen={showErrorModal}
        onClose={() => setShowErrorModal(false)}
        onConfirm={() => setShowErrorModal(false)}
        confirmLoading={false}
        title={alertData?.title || "Error"}
        description={alertData?.message || ""}
        confirmText="OK"
        cancelText=""
        tone="danger"
      />
    </div>
  )
}

export default ReservationsCalendar