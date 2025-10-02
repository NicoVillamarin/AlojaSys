import React, { useState, useEffect } from 'react'
import { useAction } from 'src/hooks/useAction'
import { useList } from 'src/hooks/useList'
import usePeriod from 'src/hooks/usePeriod'
import { useDashboardMetrics, useGlobalDashboardMetrics } from 'src/hooks/useDashboardMetrics'
import Kpis from 'src/components/Kpis'
import SpinnerLoading from 'src/components/SpinnerLoading'
import Tabs from 'src/components/Tabs'
import PeriodSelector from 'src/components/PeriodSelector'
import { 
  ReservationsTimelineChart, 
  RoomTypeOccupancyChart, 
  RevenueChart, 
  FutureReservationsChart 
} from 'src/components/charts'
import HomeIcon from 'src/assets/icons/HomeIcon'
import UsersIcon from 'src/assets/icons/UsersIcon'
import ChartBarIcon from 'src/assets/icons/ChartBarIcon'
import CurrencyDollarIcon from 'src/assets/icons/CurrencyDollarIcon'
import CheckinIcon from 'src/assets/icons/CheckinIcon'
import CheckoutIcon from 'src/assets/icons/CheckoutIcon'
import CheckCircleIcon from 'src/assets/icons/CheckCircleIcon'
import BedAvailableIcon from 'src/assets/icons/BedAvailableIcon'
import PleopleOccupatedIcon from 'src/assets/icons/PleopleOccupatedIcon'
import WrenchScrewdriverIcon from 'src/assets/icons/WrenchScrewdriverIcon'
import HotelIcon from 'src/assets/icons/HotelIcon'
import GlobalIcon from 'src/assets/icons/GlobalIcon'
import { format, parseISO } from 'date-fns'
import { getStatusLabel } from './utils'
import { useUserHotels } from 'src/hooks/useUserHotels'

const Dashboard = () => {
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()
  
  // Si el usuario solo tiene 1 hotel, iniciamos directamente en ese hotel
  const [selectedHotel, setSelectedHotel] = useState(hasSingleHotel ? singleHotelId : null) // null = todos los hoteles
  const [activeTab, setActiveTab] = useState(hasSingleHotel ? singleHotelId?.toString() : 'global') // global o hotel_id
  const [revenueMetric, setRevenueMetric] = useState('gross') // 'gross' | 'net'
  // Usar el hook de período personalizado
  const { 
    selectedPeriod, 
    dateRange, 
    handlePeriodChange, 
    handleCustomDateChange,
    customStartDate,
    customEndDate
  } = usePeriod('current-month')

  // Obtener hoteles disponibles (filtrados por usuario si no es superuser)
  const { results: hotels, isPending: hotelsLoading } = useList({
    resource: 'hotels',
    params: {
      page_size: 100,
      ...(!isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {})
    }
  })

  // Obtener resumen del hotel seleccionado (solo si hay uno seleccionado)
  const { results: hotelSummary, isPending: summaryLoading, refetch: refetchSummary } = useAction({
    resource: 'status',
    action: 'summary',
    params: { hotel: selectedHotel },
    enabled: !!selectedHotel && activeTab !== 'global'
  })

  // Obtener resumen global usando la nueva API
  const { results: globalSummary, isPending: globalSummaryLoading } = useAction({
    resource: 'status',
    action: 'global-summary',
    params: {},
    enabled: activeTab === 'global'
  })

  // Obtener reservas globales para gráficos
  const { 
    results: globalReservations, 
    isPending: globalReservationsLoading,
    hasNextPage: hasNextReservations,
    fetchNextPage: fetchNextReservations
  } = useList({
    resource: 'reservations',
    params: { 
      check_in__gte: dateRange.start,
      check_in__lte: dateRange.end,
      page_size: 1000
    },
    enabled: activeTab === 'global'
  })

  // Obtener habitaciones globales para gráficos
  const { 
    results: globalRooms, 
    isPending: globalRoomsLoading,
    hasNextPage: hasNextRooms,
    fetchNextPage: fetchNextRooms
  } = useList({
    resource: 'rooms',
    params: { page_size: 1000 },
    enabled: activeTab === 'global'
  })

  // Obtener datos filtrados (hotel específico)
  const { results: filteredReservations, isPending: filteredReservationsLoading } = useList({
    resource: 'reservations',
    params: { 
      hotel: selectedHotel,
      check_in__gte: dateRange.start,
      check_in__lte: dateRange.end,
      page_size: 1000
    },
    enabled: activeTab !== 'global' && !!selectedHotel
  })

  const { results: filteredRooms, isPending: filteredRoomsLoading } = useList({
    resource: 'rooms',
    params: { 
      hotel: selectedHotel,
      page_size: 1000
    },
    enabled: activeTab !== 'global' && !!selectedHotel
  })

  // Fecha de hoy para KPIs directos de reservas
  const todayISO = new Date().toISOString().split('T')[0]

  // Llegadas de HOY desde API de reservas
  const { results: arrivalsToday, isPending: arrivalsTodayLoading } = useList({
    resource: 'reservations',
    params: {
      ...(activeTab !== 'global' && selectedHotel ? { hotel: selectedHotel } : {}),
      check_in: todayISO,
      page_size: 1000
    },
    enabled: true
  })

  // Salidas de HOY desde API de reservas
  const { results: departuresToday, isPending: departuresTodayLoading } = useList({
    resource: 'reservations',
    params: {
      ...(activeTab !== 'global' && selectedHotel ? { hotel: selectedHotel } : {}),
      check_out: todayISO,
      page_size: 1000
    },
    enabled: true
  })

  // In-house de HOY (check_in <= hoy y check_out > hoy)
  const { results: inHouseToday, isPending: inHouseTodayLoading } = useList({
    resource: 'reservations',
    params: {
      ...(activeTab !== 'global' && selectedHotel ? { hotel: selectedHotel } : {}),
      check_in__lte: todayISO,
      check_out__gt: todayISO,
      page_size: 1000
    },
    enabled: true
  })

  // Obtener resúmenes de todos los hoteles para datos globales
  const { results: allHotelsSummary, isPending: allHotelsLoading } = useList({
    resource: 'hotels',
    params: { page_size: 100 },
    enabled: activeTab === 'global'
  })

  // Calcular fecha de mañana (reservas futuras = desde mañana en adelante)
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  const tomorrowStr = tomorrow.toISOString().split('T')[0]

  // Obtener TODAS las reservas pending y confirmed (el filtro de fecha se hará en el frontend)
  const { 
    results: futureReservations, 
    isPending: futureReservationsLoading 
  } = useList({
    resource: 'reservations',
    params: { 
      page_size: 1000,
      ordering: 'check_in' // Ordenar por fecha de check-in
    },
    enabled: true // Siempre habilitado para métricas globales
  })
  
  // Debug: Ver todas las reservas recibidas
  console.log('📦 Total reservas recibidas del backend:', futureReservations?.length || 0)
  if (futureReservations && futureReservations.length > 0) {
    const statusCount = futureReservations.reduce((acc, r) => {
      acc[r.status] = (acc[r.status] || 0) + 1
      return acc
    }, {})
    console.log('Estados de reservas:', statusCount)
  }

  // Obtener reservas por hotel (el filtro de fecha se hará en el frontend)
  const { 
    results: filteredFutureReservations, 
    isPending: filteredFutureReservationsLoading 
  } = useList({
    resource: 'reservations',
    params: { 
      hotel: selectedHotel,
      page_size: 1000,
      ordering: 'check_in'
    },
    enabled: activeTab !== 'global' && !!selectedHotel
  })

  // Hook del dashboard con métricas detalladas (funciona para global y hotel específico)
  const {
    metrics: dashboardMetrics,
    isLoading: dashboardLoading,
    error: dashboardError,
    refreshMetrics: refreshDashboardMetrics
  } = useDashboardMetrics(
    selectedHotel,
    dateRange.end,            // date para summary
    dateRange.start,          // start_date para trends/revenue
    dateRange.end             // end_date para trends/revenue
  )

  // Debug: Log para verificar parámetros
  console.log('Dashboard Debug:', {
    selectedHotel,
    dateRange,
    dashboardMetrics,
    dashboardLoading,
    dashboardError
  })

  // Datos actuales según el tab activo
  const reservations = activeTab === 'global' ? globalReservations : filteredReservations
  const rooms = activeTab === 'global' ? globalRooms : filteredRooms
  const reservationsLoading = activeTab === 'global' ? globalReservationsLoading : filteredReservationsLoading
  const roomsLoading = activeTab === 'global' ? globalRoomsLoading : filteredRoomsLoading
  
  // Reservas futuras según el tab activo
  const futureReservationsData = activeTab === 'global' ? futureReservations : filteredFutureReservations
  const futureReservationsDataLoading = activeTab === 'global' ? futureReservationsLoading : filteredFutureReservationsLoading

  // Cargar todas las páginas de reservas globales para gráficos
  useEffect(() => {
    if (activeTab === 'global' && hasNextReservations && !globalReservationsLoading) {
      console.log('Cargando siguiente página de reservas globales...')
      fetchNextReservations()
    }
  }, [activeTab, hasNextReservations, globalReservationsLoading, fetchNextReservations])

  // Cargar todas las páginas de habitaciones globales para gráficos
  useEffect(() => {
    if (activeTab === 'global' && hasNextRooms && !globalRoomsLoading) {
      console.log('Cargando siguiente página de habitaciones globales...')
      fetchNextRooms()
    }
  }, [activeTab, hasNextRooms, globalRoomsLoading, fetchNextRooms])


  // Función para cambiar de tab
  const handleTabChange = (tabId) => {
    setActiveTab(tabId)
    if (tabId === 'global') {
      setSelectedHotel(null)
    } else {
      setSelectedHotel(Number(tabId))
    }
  }

  // Crear tabs dinámicamente según permisos del usuario
  const getTabs = () => {
    if (!hotels) return []

    // Si el usuario solo tiene 1 hotel, solo mostrar ese hotel (sin vista global)
    if (hasSingleHotel && !isSuperuser) {
      return hotels.map(hotel => ({
        id: hotel.id.toString(),
        label: hotel.name,
        icon: <HotelIcon />
      }))
    }

    // Si tiene múltiples hoteles o es superuser, mostrar vista global + hoteles
    const tabs = [
      {
        id: 'global',
        label: 'Vista Global',
        icon: <GlobalIcon />
      },
      ...hotels.map(hotel => ({
        id: hotel.id.toString(),
        label: hotel.name,
        icon: <HotelIcon />
      }))
    ]

    return tabs
  }

  // Obtener métricas globales del summary API
  const getGlobalMetrics = () => {
    if (!globalSummary) return null

    // Calcular reservas futuras confirmadas
    const futureConfirmedCount = futureReservationsData?.length || 0
    const futureRevenue = futureReservationsData?.reduce((sum, res) => sum + (parseFloat(res.total_price) || 0), 0) || 0

    return {
      totalRooms: globalSummary.rooms?.total || 0,
      occupiedRooms: globalSummary.rooms?.occupied || 0,
      availableRooms: globalSummary.rooms?.available || 0,
      maintenanceRooms: globalSummary.rooms?.maintenance || 0,
      outOfServiceRooms: globalSummary.rooms?.out_of_service || 0,
      arrivalsToday: globalSummary.today?.arrivals || 0,
      departuresToday: globalSummary.today?.departures || 0,
      currentGuests: globalSummary.rooms?.current_guests || 0,
      futureReservations: futureConfirmedCount,
      futureRevenue: futureRevenue,
      totalRevenue: 0, // Se puede calcular si es necesario
      occupancyRate: globalSummary.rooms?.total > 0 ? 
        Math.round((globalSummary.rooms.occupied / globalSummary.rooms.total) * 100) : 0
    }
  }

  // Procesar datos para KPIs
  const getKPIs = () => {
    let metrics

    // Priorizar métricas del dashboard si están disponibles
    if (dashboardMetrics?.summary) {
      // Usar métricas del dashboard (funciona para global y hotel específico)
      const dashboardSummary = dashboardMetrics.summary
      const futureConfirmedCount = futureReservationsData?.length || 0
      const futureRevenue = futureReservationsData?.reduce((sum, res) => sum + (parseFloat(res.total_price) || 0), 0) || 0
      
      // Contar estados desde el listado de reservas del período (para no depender del summary)
      const baseReservations = (activeTab === 'global' ? globalReservations : filteredReservations) || []
      const pendingReservations = (baseReservations || []).filter(r => r.status === 'pending').length
      const confirmedReservations = (baseReservations || []).filter(r => r.status === 'confirmed').length
      const cancelledReservations = (baseReservations || []).filter(r => r.status === 'cancelled').length

      // KPIs de HOY desde API reservas
      const arrivalsAllowed = ['pending', 'confirmed', 'check_in']
      const departuresAllowed = ['check_in', 'check_out']
      const arrivalsFiltered = (arrivalsToday || []).filter(r => arrivalsAllowed.includes(r.status))
      const departuresFiltered = (departuresToday || []).filter(r => departuresAllowed.includes(r.status))
      const inHouseFiltered = (inHouseToday || []).filter(r => r.status === 'check_in')
      const arrivalsCount = arrivalsFiltered.length
      const departuresCount = departuresFiltered.length
      const currentGuestsCount = inHouseFiltered.reduce((sum, r) => sum + (parseInt(r.guests || 0, 10)), 0)

      metrics = {
        totalRooms: dashboardSummary.total_rooms || 0,
        occupiedRooms: dashboardSummary.occupied_rooms || 0,
        availableRooms: dashboardSummary.available_rooms || 0,
        maintenanceRooms: dashboardSummary.maintenance_rooms || 0,
        outOfServiceRooms: dashboardSummary.out_of_service_rooms || 0,
        arrivalsToday: arrivalsCount,
        departuresToday: departuresCount,
        currentGuests: currentGuestsCount,
        futureReservations: futureConfirmedCount,
        futureRevenue: futureRevenue,
        totalRevenue: parseFloat(dashboardSummary.total_revenue) || 0,
        occupancyRate: parseFloat(dashboardSummary.occupancy_rate) || 0,
        averageRoomRate: parseFloat(dashboardSummary.average_room_rate) || 0,
        totalGuests: dashboardSummary.total_guests || 0,
        guestsExpectedToday: dashboardSummary.guests_expected_today || 0,
        guestsDepartingToday: dashboardSummary.guests_departing_today || 0,
        pendingReservations,
        confirmedReservations,
        cancelledReservations
      }
    } else if (activeTab !== 'global' && selectedHotel && hotelSummary) {
      // Fallback a métricas del summary API para hotel específico
      const futureConfirmedCount = futureReservationsData?.length || 0
      const futureRevenue = futureReservationsData?.reduce((sum, res) => sum + (parseFloat(res.total_price) || 0), 0) || 0
      
      const baseReservationsHotel = filteredReservations || []
      const pendingHotel = (baseReservationsHotel || []).filter(r => r.status === 'pending').length
      const confirmedHotel = (baseReservationsHotel || []).filter(r => r.status === 'confirmed').length
      const cancelledHotel = (baseReservationsHotel || []).filter(r => r.status === 'cancelled').length

      const arrivalsAllowedH = ['pending', 'confirmed', 'check_in']
      const departuresAllowedH = ['check_in', 'check_out']
      const arrivalsFilteredH = (arrivalsToday || []).filter(r => arrivalsAllowedH.includes(r.status))
      const departuresFilteredH = (departuresToday || []).filter(r => departuresAllowedH.includes(r.status))
      const inHouseFilteredH = (inHouseToday || []).filter(r => r.status === 'check_in')
      const arrivalsCountH = arrivalsFilteredH.length
      const departuresCountH = departuresFilteredH.length
      const currentGuestsCountH = inHouseFilteredH.reduce((sum, r) => sum + (parseInt(r.guests || 0, 10)), 0)

      metrics = {
        totalRooms: hotelSummary.rooms?.total || 0,
        occupiedRooms: hotelSummary.rooms?.occupied || 0,
        availableRooms: hotelSummary.rooms?.available || 0,
        maintenanceRooms: hotelSummary.rooms?.maintenance || 0,
        outOfServiceRooms: hotelSummary.rooms?.out_of_service || 0,
        arrivalsToday: arrivalsCountH,
        departuresToday: departuresCountH,
        currentGuests: currentGuestsCountH,
        futureReservations: futureConfirmedCount,
        futureRevenue: futureRevenue,
        totalRevenue: 0, // Se calculará por separado
        occupancyRate: hotelSummary.rooms?.total > 0 ? 
          Math.round((hotelSummary.rooms.occupied / hotelSummary.rooms.total) * 100) : 0,
        pendingReservations: pendingHotel,
        confirmedReservations: confirmedHotel,
        cancelledReservations: cancelledHotel
      }
    } else {
      // Fallback a métricas globales del summary API
      metrics = getGlobalMetrics()
      if (!metrics) return []
    }

    const subtitle = activeTab === 'global' ? "en todos los hoteles" : "en el hotel"
    const revenueSubtitle = activeTab === 'global' ? "totales" : "del hotel"

    return [
      {
        title: "Habitaciones Totales",
        value: metrics.totalRooms,
        icon: HomeIcon,
        color: "from-blue-500 to-blue-600",
        bgColor: "bg-blue-50",
        iconColor: "text-blue-600",
        subtitle: subtitle,
        showProgress: false
      },
      {
        title: "Habitaciones Ocupadas",
        value: metrics.occupiedRooms,
        icon: PleopleOccupatedIcon,
        color: "from-emerald-500 to-emerald-600",
        bgColor: "bg-emerald-50",
        iconColor: "text-emerald-600",
        subtitle: `de ${metrics.totalRooms} totales`,
        progressWidth: `${metrics.occupancyRate}%`
      },
      {
        title: "Tasa de Ocupación",
        value: `${metrics.occupancyRate}%`,
        icon: ChartBarIcon,
        color: "from-purple-500 to-purple-600",
        bgColor: "bg-purple-50",
        iconColor: "text-purple-600",
        subtitle: "promedio actual",
        progressWidth: `${metrics.occupancyRate}%`
      },
      {
        title: "Huéspedes Actuales",
        value: metrics.currentGuests,
        icon: PleopleOccupatedIcon,
        color: "from-orange-500 to-orange-600",
        bgColor: "bg-orange-50",
        iconColor: "text-orange-600",
        subtitle: subtitle,
        showProgress: false
      },
      {
        title: "Llegadas Hoy",
        value: metrics.arrivalsToday,
        icon: CheckinIcon,
        color: "from-green-500 to-green-600",
        bgColor: "bg-green-50",
        iconColor: "text-green-600",
        subtitle: "reservas",
        showProgress: false
      },
      {
        title: "Salidas Hoy",
        value: metrics.departuresToday,
        icon: CheckoutIcon,
        color: "from-red-500 to-red-600",
        bgColor: "bg-red-50",
        iconColor: "text-red-600",
        subtitle: "reservas",
        showProgress: false
      },
      {
        title: "A Confirmar",
        value: metrics.pendingReservations,
        icon: CheckCircleIcon,
        color: "from-amber-500 to-amber-600",
        bgColor: "bg-amber-50",
        iconColor: "text-amber-600",
        subtitle: "pendientes",
        showProgress: false
      },
      {
        title: "Confirmadas",
        value: metrics.confirmedReservations,
        icon: CheckCircleIcon,
        color: "from-blue-500 to-blue-600",
        bgColor: "bg-blue-50",
        iconColor: "text-blue-600",
        subtitle: "totales",
        showProgress: false
      },
      {
        title: "Canceladas",
        value: metrics.cancelledReservations,
        icon: CheckCircleIcon,
        color: "from-slate-500 to-slate-600",
        bgColor: "bg-slate-50",
        iconColor: "text-slate-600",
        subtitle: "totales",
        showProgress: false
      },
      {
        title: "Ingresos Totales",
        value: `$${getTotalRevenue().toLocaleString()}`,
        icon: CurrencyDollarIcon,
        color: "from-emerald-500 to-emerald-600",
        bgColor: "bg-emerald-50",
        iconColor: "text-emerald-600",
        subtitle: revenueSubtitle,
        showProgress: false
      },
      {
        title: "Reservas Futuras",
        value: metrics.futureReservations,
        icon: CheckCircleIcon,
        color: "from-indigo-500 to-indigo-600",
        bgColor: "bg-indigo-50",
        iconColor: "text-indigo-600",
        subtitle: "confirmadas",
        showProgress: false
      },
      {
        title: "Ingresos Futuros",
        value: `$${metrics.futureRevenue?.toLocaleString() || '0'}`,
        icon: CurrencyDollarIcon,
        color: "from-cyan-500 to-cyan-600",
        bgColor: "bg-cyan-50",
        iconColor: "text-cyan-600",
        subtitle: "por confirmar",
        showProgress: false
      },
      // KPIs adicionales del dashboard (solo si están disponibles)
      ...(metrics.averageRoomRate ? [{
        title: "Tarifa Promedio",
        value: `$${metrics.averageRoomRate?.toLocaleString() || '0'}`,
        icon: CurrencyDollarIcon,
        color: "from-indigo-500 to-indigo-600",
        bgColor: "bg-indigo-50",
        iconColor: "text-indigo-600",
        subtitle: "por habitación",
        showProgress: false
      }] : []),
      ...(metrics.totalGuests ? [{
        title: "Total Huéspedes",
        value: metrics.totalGuests,
        icon: UsersIcon,
        color: "from-pink-500 to-pink-600",
        bgColor: "bg-pink-50",
        iconColor: "text-pink-600",
        subtitle: "en el sistema",
        showProgress: false
      }] : []),
      ...(metrics.guestsExpectedToday ? [{
        title: "Huéspedes Esperados",
        value: metrics.guestsExpectedToday,
        icon: CheckinIcon,
        color: "from-teal-500 to-teal-600",
        bgColor: "bg-teal-50",
        iconColor: "text-teal-600",
        subtitle: "hoy",
        showProgress: false
      }] : []),
      ...(metrics.guestsDepartingToday ? [{
        title: "Huéspedes Partiendo",
        value: metrics.guestsDepartingToday,
        icon: CheckoutIcon,
        color: "from-rose-500 to-rose-600",
        bgColor: "bg-rose-50",
        iconColor: "text-rose-600",
        subtitle: "hoy",
        showProgress: false
      }] : [])
    ]
  }

  // Función auxiliar para calcular ingresos totales (usado en KPIs)
  const getTotalRevenue = () => {
    if (!reservations || reservations.length === 0) return 0
    return reservations.reduce((sum, res) => sum + (parseFloat(res.total_price) || 0), 0)
  }


  const isLoading = (activeTab === 'global' ? (globalSummaryLoading || globalReservationsLoading || globalRoomsLoading) : summaryLoading) || reservationsLoading || roomsLoading || futureReservationsDataLoading || dashboardLoading

  if (hotelsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <SpinnerLoading />
      </div>
    )
  }

  if (!hotels || hotels.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-lg">No hay hoteles disponibles</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <p className="text-gray-600 mt-1 text-xl font-bold">
              {activeTab === 'global' 
                ? 'Vista Global - Todos los Hoteles'
                : selectedHotel && hotelSummary?.hotel?.name 
                  ? `${hotelSummary.hotel.name} - ${hotelSummary.hotel.city}` 
                  : 'Hotel seleccionado'
              }
            </p>
            <p className="text-sm text-gray-500 mt-1">
              📅 Período: {dateRange.label}
            </p>
          </div>
          
          {/* Selector de Período */}
          <div className="flex gap-2">
            <PeriodSelector
              selectedPeriod={selectedPeriod}
              onPeriodChange={handlePeriodChange}
              className="flex-shrink-0"
            />
            
            {/* Botón para refrescar métricas del dashboard */}
            {dashboardMetrics && (
              <button
                onClick={refreshDashboardMetrics}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-medium"
                title="Actualizar métricas del dashboard"
              >
                🔄 Actualizar
              </button>
            )}
            
            {/* Inputs de fecha personalizada (solo cuando se selecciona "Personalizado") */}
            {selectedPeriod === 'custom' && (
              <div className="flex gap-2">
                <input
                  type="date"
                  value={customStartDate}
                  onChange={(e) => handleCustomDateChange(e.target.value, customEndDate)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  placeholder="Desde"
                />
                <input
                  type="date"
                  value={customEndDate}
                  onChange={(e) => handleCustomDateChange(customStartDate, e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  placeholder="Hasta"
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tabs de Hoteles */}
      <div className="bg-white border-b border-gray-200">
        <Tabs
          tabs={getTabs()}
          activeTab={activeTab}
          onTabChange={handleTabChange}
          className="px-6"
        />
      </div>

      {/* Contenido del Dashboard */}
      <div className="p-6 space-y-6">

      {/* KPIs */}
      <div className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-700">Métricas Principales</h2>
          {dashboardError && (
            <div className="text-sm text-red-600 bg-red-50 px-3 py-1 rounded-lg">
              ⚠️ Error cargando métricas del dashboard
            </div>
          )}
        </div>
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <SpinnerLoading />
          </div>
        ) : (
            <Kpis kpis={getKPIs()} />
        )}
      </div>

      {/* Información adicional del dashboard */}
      {dashboardMetrics?.summary && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-700 mb-4">
            Información Detallada del Dashboard
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm font-medium text-blue-600">Habitaciones en Mantenimiento</p>
              <p className="text-2xl font-bold text-blue-900">
                {dashboardMetrics.summary.maintenance_rooms || 0}
              </p>
            </div>
            
            <div className="bg-red-50 rounded-lg p-4">
              <p className="text-sm font-medium text-red-600">Fuera de Servicio</p>
              <p className="text-2xl font-bold text-red-900">
                {dashboardMetrics.summary.out_of_service_rooms || 0}
              </p>
            </div>
            
            <div className="bg-yellow-50 rounded-lg p-4">
              <p className="text-sm font-medium text-yellow-600">Reservadas</p>
              <p className="text-2xl font-bold text-yellow-900">
                {dashboardMetrics.summary.reserved_rooms || 0}
              </p>
            </div>
            
            <div className="bg-purple-50 rounded-lg p-4">
              <p className="text-sm font-medium text-purple-600">No Shows Hoy</p>
              <p className="text-2xl font-bold text-purple-900">
                {dashboardMetrics.summary.no_show_today || 0}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Gráficos */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Gráfico de línea de tiempo de reservas */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <ReservationsTimelineChart
            key={`timeline-${selectedPeriod}-${dateRange.start}-${dateRange.end}`}
            reservations={reservations}
            dateRange={dateRange}
            isLoading={isLoading}
            selectedPeriod={selectedPeriod}
            trends={dashboardMetrics?.trends}
          />
        </div>

        {/* Gráfico de ocupación por tipo de habitación */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <RoomTypeOccupancyChart
            rooms={rooms}
            dateRange={dateRange}
            isLoading={isLoading}
          />
        </div>
      </div>

      {/* Gráfico de reservas futuras */}
      {futureReservationsData && futureReservationsData.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <FutureReservationsChart
            key={`future-${selectedPeriod}-${dateRange.start}-${dateRange.end}`}
            futureReservations={futureReservationsData}
            dateRange={dateRange}
            isLoading={isLoading}
            selectedPeriod={selectedPeriod}
          />
        </div>
      )}

      {/* Gráfico de ingresos */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-700">Ingresos</h2>
          <div className="inline-flex rounded-md shadow-sm" role="group">
            <button
              type="button"
              onClick={() => setRevenueMetric('gross')}
              className={`px-3 py-1.5 text-sm font-medium border border-gray-200 ${revenueMetric === 'gross' ? 'bg-emerald-600 text-white' : 'bg-white text-gray-700'} rounded-l-md`}
            >
              Bruto
            </button>
            <button
              type="button"
              onClick={() => setRevenueMetric('net')}
              className={`px-3 py-1.5 text-sm font-medium border border-gray-200 border-l-0 ${revenueMetric === 'net' ? 'bg-emerald-600 text-white' : 'bg-white text-gray-700'} rounded-r-md`}
            >
              Neto
            </button>
          </div>
        </div>
        <RevenueChart
          key={`revenue-${selectedPeriod}-${dateRange.start}-${dateRange.end}-${revenueMetric}`}
          reservations={reservations}
          dateRange={dateRange}
          isLoading={isLoading}
          selectedPeriod={selectedPeriod}
          revenueAnalysis={dashboardMetrics?.revenueAnalysis}
          metric={revenueMetric}
        />
      </div>

      {/* Tablas de reservas */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Tabla de reservas actuales (check-in) */}
        {((activeTab !== 'global' && selectedHotel && hotelSummary?.current_reservations) || (activeTab === 'global' && globalSummary?.current_reservations)) && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-xl font-semibold text-gray-700 mb-4">
              {activeTab === 'global' ? 'Check-ins Actuales' : 'Check-ins del Hotel'}
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {activeTab === 'global' && (
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Hotel
                      </th>
                    )}
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Huésped
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Habitación
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Check-out
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {(() => {
                    const currentReservations = activeTab === 'global'
                      ? globalSummary?.current_reservations || []
                      : hotelSummary?.current_reservations || []
                    
                    return currentReservations.map((reservation, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        {activeTab === 'global' && (
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {reservation.hotel_name || 'N/A'}
                          </td>
                        )}
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {reservation.guest_name || 'Sin nombre'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {reservation.room || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {format(parseISO(reservation.check_out), "dd/MM/yyyy")}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          ${reservation.total_price?.toLocaleString() || '0'}
                        </td>
                      </tr>
                    ))
                  })()}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tabla de reservas confirmadas futuras */}
        {futureReservationsData && futureReservationsData.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-xl font-semibold text-gray-700 mb-4">
              {activeTab === 'global' ? 'Reservas Confirmadas Futuras' : 'Reservas Futuras del Hotel'}
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {activeTab === 'global' && (
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Hotel
                      </th>
                    )}
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Huésped
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Habitación
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Check-in
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Check-out
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {futureReservationsData.map((reservation, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      {activeTab === 'global' && (
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {reservation.hotel_name || 'N/A'}
                        </td>
                      )}
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {reservation.guests_data?.[0]?.name || 'Sin nombre'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {reservation.room_name || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {format(parseISO(reservation.check_in), "dd/MM/yyyy")}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {format(parseISO(reservation.check_out), "dd/MM/yyyy")}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${reservation.total_price?.toLocaleString() || '0'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
      </div>
    </div>
  )
}

export default Dashboard