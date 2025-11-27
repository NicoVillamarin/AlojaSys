import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAction } from 'src/hooks/useAction'
import { useList } from 'src/hooks/useList'
import usePeriod from 'src/hooks/usePeriod'
import { useDashboardMetrics, useGlobalDashboardMetrics } from 'src/hooks/useDashboardMetrics'
import { useMe } from 'src/hooks/useMe'
import { usePermissions, useHasAnyPermission } from 'src/hooks/usePermissions'
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
import Tooltip from 'src/components/Tooltip'

const Dashboard = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { data: me } = useMe()
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()
  
  // Verificar permisos
  const hasViewDashboard = usePermissions("dashboard.view_dashboardmetrics")
  const hasReception = useHasAnyPermission(["reservations.view_reservation", "reservations.add_reservation", "reservations.change_reservation"])
  const hasViewReservations = usePermissions("reservations.view_reservation")
  const hasViewCalendar = usePermissions("calendar.view_calendarview")
  const hasViewRooms = usePermissions("rooms.view_room")
  const hasViewOTAs = usePermissions("otas.view_otaconfig")
  const hasAnyHistory = useHasAnyPermission(["reservations.view_reservation", "payments.view_payment", "payments.view_refund"])
  const hasAnyFinancial = useHasAnyPermission(["payments.view_refund", "payments.view_refundvoucher", "invoicing.view_invoice", "invoicing.view_receipt", "payments.view_bankreconciliation"])
  const hasAnySettings = useHasAnyPermission([
    "enterprises.view_enterprise",
    "otas.view_otaconfig",
    "rooms.view_room",
    "core.view_hotel",
    "users.view_userprofile",
    "auth.view_group",
    "locations.view_country",
    "locations.view_state",
    "locations.view_city",
    "rates.view_rateplan",
    "rates.view_raterule",
    "rates.view_promorule",
    "rates.view_taxrule",
    "payments.view_paymentpolicy",
    "payments.view_cancellationpolicy",
    "payments.view_refundpolicy"
  ])
  
  // Verificar si es solo personal de limpieza
  const isOnlyHousekeepingStaff = React.useMemo(() => {
    if (!me || !me.profile) return false
    const isHKStaff = me.profile.is_housekeeping_staff === true
    if (!isHKStaff) return false
    
    // Si es personal de limpieza, verificar si tiene otros permisos importantes
    const hasOtherPermissions = 
      hasViewDashboard || 
      hasReception || 
      hasViewReservations || 
      hasViewCalendar || 
      hasViewRooms || 
      hasViewOTAs ||
      hasAnyHistory ||
      hasAnyFinancial ||
      hasAnySettings
    
    // Si es personal de limpieza pero NO tiene otros permisos, es "solo" personal de limpieza
    return !hasOtherPermissions
  }, [me, hasViewDashboard, hasReception, hasViewReservations, hasViewCalendar, hasViewRooms, hasViewOTAs, hasAnyHistory, hasAnyFinancial, hasAnySettings])
  
  // Si el usuario solo tiene 1 hotel, iniciamos directamente en ese hotel
  const [selectedHotel, setSelectedHotel] = useState(hasSingleHotel ? singleHotelId : null) // null = todos los hoteles
  const [activeTab, setActiveTab] = useState(hasSingleHotel ? singleHotelId?.toString() : 'global') // global o hotel_id
  const [revenueMetric, setRevenueMetric] = useState('gross') // 'gross' | 'net'
  // Modo de vista: simple/avanzado (persistido)
  const [viewMode, setViewMode] = useState(() => {
    try { return localStorage.getItem('dashboard_view_mode') || 'simple' } catch { return 'simple' }
  })
  const showAdvanced = viewMode === 'advanced'
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

  // Obtener reservas globales para gráficos (incluir reservas que se solapen con el período)
  const {
    results: globalReservations,
    isPending: globalReservationsLoading,
    hasNextPage: hasNextReservations,
    fetchNextPage: fetchNextReservations
  } = useList({
    resource: 'reservations',
    params: {
      // Incluir reservas que se solapen con el período (check_in <= end AND check_out >= start)
      check_in__lte: dateRange.end,
      check_out__gte: dateRange.start,
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

  // Obtener datos filtrados (hotel específico) - incluir reservas que se solapen con el período
  const { results: filteredReservations, isPending: filteredReservationsLoading } = useList({
    resource: 'reservations',
    params: {
      hotel: selectedHotel,
      // Incluir reservas que se solapen con el período (check_in <= end AND check_out >= start)
      check_in__lte: dateRange.end,
      check_out__gte: dateRange.start,
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
    enabled: true,
    refetchInterval: 30000, // Auto-refresh cada 30 segundos
    refetchIntervalInBackground: true,
    staleTime: 15000
  })

  // Salidas de HOY desde API de reservas
  const { results: departuresToday, isPending: departuresTodayLoading } = useList({
    resource: 'reservations',
    params: {
      ...(activeTab !== 'global' && selectedHotel ? { hotel: selectedHotel } : {}),
      check_out: todayISO,
      page_size: 1000
    },
    enabled: true,
    refetchInterval: 30000, // Auto-refresh cada 30 segundos
    refetchIntervalInBackground: true,
    staleTime: 15000
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
    enabled: true,
    refetchInterval: 30000, // Auto-refresh cada 30 segundos
    refetchIntervalInBackground: true,
    staleTime: 15000
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
  if (futureReservations && futureReservations.length > 0) {
    const statusCount = futureReservations.reduce((acc, r) => {
      acc[r.status] = (acc[r.status] || 0) + 1
      return acc
    }, {})
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
  // Siempre usar rango de fechas cuando está disponible (incluyendo períodos predefinidos)
  // Los períodos como "current-month", "last-month", "7-days", etc. tienen dateRange.start y dateRange.end
  const hasDateRange = dateRange.start && dateRange.end
  const {
    metrics: dashboardMetrics,
    isLoading: dashboardLoading,
    error: dashboardError,
    refreshMetrics: refreshDashboardMetrics
  } = useDashboardMetrics(
    selectedHotel,
    hasDateRange ? null : dateRange.end,  // date solo si no hay rango (fecha única - caso raro)
    hasDateRange ? dateRange.start : null, // start_date cuando hay rango
    hasDateRange ? dateRange.end : null   // end_date cuando hay rango
  )
  
  // Obtener reservas específicas para gráficos:
  // - Para ingresos: filtradas por check_in dentro del rango
  // - Para tendencias: el gráfico filtra por created_at en el frontend
  const { results: chartReservations, isPending: chartReservationsLoading } = useList({
    resource: 'reservations',
    params: {
      ...(activeTab !== 'global' && selectedHotel ? { hotel: selectedHotel } : {}),
      // Para ingresos, necesitamos reservas con check_in dentro del rango
      ...(hasDateRange ? {
        check_in__gte: dateRange.start,
        check_in__lte: dateRange.end
      } : {}),
      page_size: 1000
    },
    enabled: true
  })
  
  // Obtener reservas para el gráfico de tendencias (filtradas por created_at dentro del rango)
  // Usamos un rango más amplio y filtramos en el frontend porque created_at puede tener hora
  const { results: trendsReservations, isPending: trendsReservationsLoading } = useList({
    resource: 'reservations',
    params: {
      ...(activeTab !== 'global' && selectedHotel ? { hotel: selectedHotel } : {}),
      // Para tendencias, obtener reservas con created_at en un rango amplio
      // El gráfico filtrará por fecha exacta en el frontend
      ...(hasDateRange ? {
        created_at__gte: `${dateRange.start}T00:00:00`,
        created_at__lte: `${dateRange.end}T23:59:59`
      } : {}),
      page_size: 1000
    },
    enabled: true
  })

  // Auto-refresh de datos críticos cada 30 segundos (sin isLoading por ahora)
  useEffect(() => {
    const interval = setInterval(() => {
      // Solo refrescar si hay datos
      if (dashboardMetrics || globalSummary || hotelSummary) {
        refreshDashboardMetrics()
      }
    }, 30000) // 30 segundos

    return () => clearInterval(interval)
  }, [dashboardMetrics, globalSummary, hotelSummary, refreshDashboardMetrics])

  // Persistir modo de vista
  useEffect(() => {
    try { localStorage.setItem('dashboard_view_mode', viewMode) } catch {}
  }, [viewMode])

  // Redirigir a housekeeping si es solo personal de limpieza (después de todos los hooks)
  useEffect(() => {
    if (isOnlyHousekeepingStaff) {
      navigate('/housekeeping', { replace: true })
    }
  }, [isOnlyHousekeepingStaff, navigate])
  
  // Si es solo personal de limpieza, no renderizar nada (se redirige)
  if (isOnlyHousekeepingStaff) {
    return null
  }

  // Datos actuales según el tab activo
  // Para gráficos, usar chartReservations que están filtradas por el período correcto
  // Para otras cosas (tablas, etc.), usar futureReservations sin filtro de fecha
  const reservations = chartReservations || (activeTab === 'global' ? futureReservations : filteredFutureReservations)
  const rooms = activeTab === 'global' ? globalRooms : filteredRooms
  const reservationsLoading = chartReservationsLoading || (activeTab === 'global' ? futureReservationsLoading : filteredFutureReservationsLoading)
  const roomsLoading = activeTab === 'global' ? globalRoomsLoading : filteredRoomsLoading

  // Función para calcular habitaciones ocupadas desde las reservas
  const calculateRoomOccupancy = () => {
    const today = new Date().toISOString().split('T')[0]
    
    // Obtener todas las reservas que están actualmente ocupadas (check_in <= hoy < check_out)
    const occupiedReservations = (reservations || []).filter(reservation => {
      const checkIn = reservation.check_in
      const checkOut = reservation.check_out
      return checkIn <= today && checkOut > today && reservation.status === 'check_in'
    })
    
    // Obtener habitaciones totales (asumiendo que tenemos datos de habitaciones)
    const totalRooms = rooms?.length || 0
    
    const occupiedRooms = occupiedReservations.length
    const availableRooms = Math.max(0, totalRooms - occupiedRooms)
    const occupancyRate = totalRooms > 0 ? Math.round((occupiedRooms / totalRooms) * 100) : 0

    return {
      totalRooms,
      occupiedRooms,
      availableRooms,
      occupancyRate
    }
  }

  // Calcular ocupación de habitaciones
  const roomOccupancy = calculateRoomOccupancy()

  // Función para filtrar reservas realmente futuras (check_in >= hoy)
  const getFutureReservations = (reservations) => {
    if (!reservations) return []
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    return reservations.filter(reservation => {
      const checkInDate = new Date(reservation.check_in)
      return checkInDate >= today
    })
  }

  // Reservas futuras según el tab activo (filtrar correctamente)
  const allReservations = activeTab === 'global' ? futureReservations : filteredFutureReservations
  const futureReservationsData = getFutureReservations(allReservations)
  const futureReservationsDataLoading = activeTab === 'global' ? futureReservationsLoading : filteredFutureReservationsLoading

  // Calcular estado de carga después de que todas las variables estén declaradas
  const isLoading = (activeTab === 'global' ? (globalSummaryLoading || globalReservationsLoading || globalRoomsLoading) : summaryLoading) || reservationsLoading || roomsLoading || futureReservationsDataLoading || dashboardLoading

  // Cargar todas las páginas de reservas globales para gráficos
  useEffect(() => {
    if (activeTab === 'global' && hasNextReservations && !globalReservationsLoading) {
      fetchNextReservations()
    }
  }, [activeTab, hasNextReservations, globalReservationsLoading, fetchNextReservations])

  // Cargar todas las páginas de habitaciones globales para gráficos
  useEffect(() => {
    if (activeTab === 'global' && hasNextRooms && !globalRoomsLoading) {
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
        label: t('dashboard.global_view'),
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
      const departuresAllowed = ['check_out'] // Solo las que ya salieron
      const arrivalsFiltered = (arrivalsToday || []).filter(r => arrivalsAllowed.includes(r.status))
      const departuresFiltered = (departuresToday || []).filter(r => departuresAllowed.includes(r.status))
      const inHouseFiltered = (inHouseToday || []).filter(r => r.status === 'check_in')
      const arrivalsCount = arrivalsFiltered.length
      const departuresCount = departuresFiltered.length
      const currentGuestsCount = inHouseFiltered.reduce((sum, r) => sum + (parseInt(r.guests || 0, 10)), 0)
      // Usar datos calculados desde reservas si hay datos disponibles
      // Solo usar cálculo local en vista GLOBAL; en vista de hotel confiamos en el backend
      const useCalculatedData = (activeTab === 'global') && roomOccupancy.totalRooms > 0
      
      metrics = {
        totalRooms: useCalculatedData ? roomOccupancy.totalRooms : (dashboardSummary.total_rooms || 0),
        occupiedRooms: useCalculatedData ? roomOccupancy.occupiedRooms : (dashboardSummary.occupied_rooms || 0),
        availableRooms: useCalculatedData ? roomOccupancy.availableRooms : (dashboardSummary.available_rooms || 0),
        maintenanceRooms: dashboardSummary.maintenance_rooms || 0,
        outOfServiceRooms: dashboardSummary.out_of_service_rooms || 0,
        arrivalsToday: arrivalsCount,
        departuresToday: departuresCount,
        currentGuests: currentGuestsCount,
        futureReservations: futureConfirmedCount,
        futureRevenue: futureRevenue,
        totalRevenue: parseFloat(dashboardSummary.total_revenue) || 0,
        occupancyRate: useCalculatedData ? roomOccupancy.occupancyRate : (parseFloat(dashboardSummary.occupancy_rate) || 0),
        averageRoomRate: parseFloat(dashboardSummary.average_room_rate) || 0,
        totalGuests: dashboardSummary.total_guests || 0,
        guestsExpectedToday: dashboardSummary.guests_expected_today || 0,
        guestsDepartingToday: departuresCount,
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
      const departuresAllowedH = ['check_out'] // Solo las que ya salieron
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
        guestsDepartingToday: departuresCountH,
        pendingReservations: pendingHotel,
        confirmedReservations: confirmedHotel,
        cancelledReservations: cancelledHotel
      }
    } else {
      // Fallback a métricas globales del summary API
      metrics = getGlobalMetrics()
      if (!metrics) return []
    }

    const subtitle = activeTab === 'global' ? t('dashboard.kpis.in_all_hotels') : t('dashboard.kpis.in_hotel')
    const revenueSubtitle = activeTab === 'global' ? t('dashboard.kpis.total_revenue_subtitle') : t('dashboard.kpis.hotel_revenue_subtitle')

    return [
      {
        title: t('dashboard.kpis.total_rooms'),
        value: metrics.totalRooms,
        icon: HomeIcon,
        color: "from-blue-500 to-blue-600",
        bgColor: "bg-blue-50",
        iconColor: "text-blue-600",
        subtitle: subtitle,
        showProgress: false
      },
      {
        title: t('dashboard.kpis.occupied_rooms'),
        value: metrics.occupiedRooms,
        icon: PleopleOccupatedIcon,
        color: "from-emerald-500 to-emerald-600",
        bgColor: "bg-emerald-50",
        iconColor: "text-emerald-600",
        subtitle: t('dashboard.kpis.of_total', { total: metrics.totalRooms }),
        progressWidth: `${metrics.occupancyRate}%`
      },
      {
        title: t('dashboard.kpis.available_rooms'),
        value: metrics.availableRooms,
        icon: HomeIcon,
        color: "from-cyan-500 to-cyan-600",
        bgColor: "bg-cyan-50",
        iconColor: "text-cyan-600",
        subtitle: t('dashboard.kpis.of_total', { total: metrics.totalRooms }),
        showProgress: false
      },
      {
        title: t('dashboard.kpis.occupancy_rate'),
        value: `${metrics.occupancyRate}%`,
        icon: ChartBarIcon,
        color: "from-purple-500 to-purple-600",
        bgColor: "bg-purple-50",
        iconColor: "text-purple-600",
        subtitle: t('dashboard.kpis.average_current'),
        progressWidth: `${metrics.occupancyRate}%`
      },
      {
        title: t('dashboard.kpis.current_guests'),
        value: metrics.currentGuests,
        icon: PleopleOccupatedIcon,
        color: "from-orange-500 to-orange-600",
        bgColor: "bg-orange-50",
        iconColor: "text-orange-600",
        subtitle: subtitle,
        showProgress: false
      },
      {
        title: t('dashboard.kpis.arrivals_today'),
        value: metrics.arrivalsToday,
        icon: CheckinIcon,
        color: "from-green-500 to-green-600",
        bgColor: "bg-green-50",
        iconColor: "text-green-600",
        subtitle: t('dashboard.kpis.reservations'),
        showProgress: false
      },
      {
        title: t('dashboard.kpis.departures_today'),
        value: metrics.departuresToday,
        icon: CheckoutIcon,
        color: "from-red-500 to-red-600",
        bgColor: "bg-red-50",
        iconColor: "text-red-600",
        subtitle: t('dashboard.kpis.reservations'),
        showProgress: false
      },
      {
        title: t('dashboard.kpis.to_confirm'),
        value: metrics.pendingReservations,
        icon: CheckCircleIcon,
        color: "from-amber-500 to-amber-600",
        bgColor: "bg-amber-50",
        iconColor: "text-amber-600",
        subtitle: t('dashboard.kpis.pending'),
        showProgress: false
      },
      {
        title: t('dashboard.kpis.confirmed'),
        value: metrics.confirmedReservations,
        icon: CheckCircleIcon,
        color: "from-blue-500 to-blue-600",
        bgColor: "bg-blue-50",
        iconColor: "text-blue-600",
        subtitle: t('dashboard.kpis.total_count'),
        showProgress: false
      },
      {
        title: t('dashboard.kpis.cancelled'),
        value: metrics.cancelledReservations,
        icon: CheckCircleIcon,
        color: "from-slate-500 to-slate-600",
        bgColor: "bg-slate-50",
        iconColor: "text-slate-600",
        subtitle: t('dashboard.kpis.total_count'),
        showProgress: false
      },
      {
        title: t('dashboard.kpis.total_revenue'),
        value: `$${getTotalRevenue().toLocaleString()}`,
        icon: CurrencyDollarIcon,
        color: "from-emerald-500 to-emerald-600",
        bgColor: "bg-emerald-50",
        iconColor: "text-emerald-600",
        subtitle: revenueSubtitle,
        showProgress: false
      },
      {
        title: t('dashboard.kpis.future_reservations'),
        value: metrics.futureReservations,
        icon: CheckCircleIcon,
        color: "from-indigo-500 to-indigo-600",
        bgColor: "bg-indigo-50",
        iconColor: "text-indigo-600",
        subtitle: t('dashboard.kpis.confirmed'),
        showProgress: false
      },
      {
        title: t('dashboard.kpis.future_revenue'),
        value: `$${metrics.futureRevenue?.toLocaleString() || '0'}`,
        icon: CurrencyDollarIcon,
        color: "from-cyan-500 to-cyan-600",
        bgColor: "bg-cyan-50",
        iconColor: "text-cyan-600",
        subtitle: t('dashboard.kpis.to_confirm_revenue'),
        showProgress: false
      },
      // KPIs adicionales del dashboard (solo si están disponibles y en modo avanzado)
      ...(showAdvanced && metrics.averageRoomRate ? [{
        title: t('dashboard.kpis.average_rate'),
        value: `$${metrics.averageRoomRate?.toLocaleString() || '0'}`,
        icon: CurrencyDollarIcon,
        color: "from-indigo-500 to-indigo-600",
        bgColor: "bg-indigo-50",
        iconColor: "text-indigo-600",
        subtitle: t('dashboard.kpis.per_room'),
        showProgress: false
      }] : []),
      ...(metrics.guestsExpectedToday ? [{
        title: t('dashboard.kpis.expected_guests'),
        value: metrics.guestsExpectedToday,
        icon: CheckinIcon,
        color: "from-teal-500 to-teal-600",
        bgColor: "bg-teal-50",
        iconColor: "text-teal-600",
        subtitle: t('dashboard.kpis.today'),
        showProgress: false
      }] : []),
      ...(showAdvanced && dashboardMetrics?.summary?.revpar !== undefined ? [{
        title: (
          <>
            {t('dashboard.kpis.revpar')}
            <Tooltip content={t('dashboard.kpis_help.revpar')}>
              <span className="ml-1 cursor-help">ℹ️</span>
            </Tooltip>
          </>
        ),
        value: `$${parseFloat(dashboardMetrics.summary.revpar || 0).toLocaleString()}`,
        icon: CurrencyDollarIcon,
        color: "from-purple-500 to-purple-600",
        bgColor: "bg-purple-50",
        iconColor: "text-purple-600",
        subtitle: t('dashboard.kpis.per_available_room'),
        showProgress: false
      }] : []),
      ...(showAdvanced && dashboardMetrics?.summary?.avg_length_of_stay_days !== undefined ? [{
        title: (
          <>
            {t('dashboard.kpis.avg_los')}
            <Tooltip content={t('dashboard.kpis_help.avg_los')}>
              <span className="ml-1 cursor-help">ℹ️</span>
            </Tooltip>
          </>
        ),
        value: `${parseFloat(dashboardMetrics.summary.avg_length_of_stay_days || 0).toFixed(2)} ${t('dashboard.kpis.days')}`,
        icon: BedAvailableIcon,
        color: "from-teal-500 to-teal-600",
        bgColor: "bg-teal-50",
        iconColor: "text-teal-600",
        subtitle: t('dashboard.kpis.in_house'),
        showProgress: false
      }] : []),
      ...(showAdvanced && dashboardMetrics?.summary?.lead_time_avg_days !== undefined ? [{
        title: (
          <>
            {t('dashboard.kpis.lead_time_avg')}
            <Tooltip content={t('dashboard.kpis_help.lead_time_avg')}>
              <span className="ml-1 cursor-help">ℹ️</span>
            </Tooltip>
          </>
        ),
        value: `${parseFloat(dashboardMetrics.summary.lead_time_avg_days || 0).toFixed(2)} ${t('dashboard.kpis.days')}`,
        icon: ChartBarIcon,
        color: "from-sky-500 to-sky-600",
        bgColor: "bg-sky-50",
        iconColor: "text-sky-600",
        subtitle: t('dashboard.kpis.for_today_arrivals'),
        showProgress: false
      }] : []),
      ...(showAdvanced && dashboardMetrics?.summary?.pickup_today !== undefined ? [{
        title: (
          <>
            {t('dashboard.kpis.pickup_today')}
            <Tooltip content={t('dashboard.kpis_help.pickup')}>
              <span className="ml-1 cursor-help">ℹ️</span>
            </Tooltip>
          </>
        ),
        value: dashboardMetrics.summary.pickup_today,
        icon: CheckCircleIcon,
        color: "from-emerald-500 to-emerald-600",
        bgColor: "bg-emerald-50",
        iconColor: "text-emerald-600",
        subtitle: t('dashboard.kpis.new_bookings'),
        showProgress: false
      }] : []),
      ...(showAdvanced && dashboardMetrics?.summary?.pickup_7d !== undefined ? [{
        title: (
          <>
            {t('dashboard.kpis.pickup_7d')}
            <Tooltip content={t('dashboard.kpis_help.pickup_7d')}>
              <span className="ml-1 cursor-help">ℹ️</span>
            </Tooltip>
          </>
        ),
        value: dashboardMetrics.summary.pickup_7d,
        icon: CheckCircleIcon,
        color: "from-amber-500 to-amber-600",
        bgColor: "bg-amber-50",
        iconColor: "text-amber-600",
        subtitle: t('dashboard.kpis.new_bookings_last_7d'),
        showProgress: false
      }] : []),
      ...(showAdvanced && dashboardMetrics?.summary?.otb_next_30d_nights !== undefined ? [{
        title: (
          <>
            {t('dashboard.kpis.otb_30d_nights')}
            <Tooltip content={t('dashboard.kpis_help.otb_30d')}>
              <span className="ml-1 cursor-help">ℹ️</span>
            </Tooltip>
          </>
        ),
        value: dashboardMetrics.summary.otb_next_30d_nights,
        icon: BedAvailableIcon,
        color: "from-indigo-500 to-indigo-600",
        bgColor: "bg-indigo-50",
        iconColor: "text-indigo-600",
        subtitle: t('dashboard.kpis.room_nights'),
        showProgress: false
      }] : []),
      ...(showAdvanced && dashboardMetrics?.summary?.otb_next_30d_revenue !== undefined ? [{
        title: (
          <>
            {t('dashboard.kpis.otb_30d_revenue')}
            <Tooltip content={t('dashboard.kpis_help.otb_30d_revenue')}>
              <span className="ml-1 cursor-help">ℹ️</span>
            </Tooltip>
          </>
        ),
        value: `$${parseFloat(dashboardMetrics.summary.otb_next_30d_revenue || 0).toLocaleString()}`,
        icon: CurrencyDollarIcon,
        color: "from-emerald-500 to-emerald-600",
        bgColor: "bg-emerald-50",
        iconColor: "text-emerald-600",
        subtitle: t('dashboard.kpis.next_30_days'),
        showProgress: false
      }] : []),
      ...(showAdvanced && dashboardMetrics?.summary?.cancellation_rate_30d !== undefined ? [{
        title: (
          <>
            {t('dashboard.kpis.cancellation_rate_30d')}
            <Tooltip content={t('dashboard.kpis_help.cancellation_rate_30d')}>
              <span className="ml-1 cursor-help">ℹ️</span>
            </Tooltip>
          </>
        ),
        value: `${parseFloat(dashboardMetrics.summary.cancellation_rate_30d || 0).toFixed(2)}%`,
        icon: WrenchScrewdriverIcon,
        color: "from-rose-500 to-rose-600",
        bgColor: "bg-rose-50",
        iconColor: "text-rose-600",
        subtitle: t('dashboard.kpis.last_30_days'),
        showProgress: false
      }] : [])
    ]
  }

  // Función auxiliar para calcular ingresos totales (usado en KPIs)
  const getTotalRevenue = () => {
    if (!reservations || reservations.length === 0) return 0
    return reservations.reduce((sum, res) => sum + (parseFloat(res.total_price) || 0), 0)
  }

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
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-white">
      {/* Header */}
      <div className="sticky top-0 z-30 bg-white/80 backdrop-blur border-b border-gray-200 px-6 py-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <p className="text-gray-600 mt-1 text-xl font-bold">
              {activeTab === 'global'
                ? t('dashboard.global_view')
                : selectedHotel && hotelSummary?.hotel?.name
                  ? `${hotelSummary.hotel.name} - ${hotelSummary.hotel.city}`
                  : t('dashboard.selected_hotel')
              }
            </p>
            <p className="text-sm text-gray-500 mt-1">
              📅 {t('dashboard.period')}: {dateRange.label}
            </p>
          </div>

          {/* Controles del Dashboard - Agrupados y organizados */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Grupo 1: Período y Actualización */}
            <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
              <PeriodSelector
                selectedPeriod={selectedPeriod}
                onPeriodChange={handlePeriodChange}
                className="flex-shrink-0"
              />
              <div className="h-4 w-px bg-gray-300"></div>
              <button
                onClick={refreshDashboardMetrics}
                className="px-3 py-1.5 bg-white text-gray-700 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-medium border border-gray-300 transition-colors flex items-center gap-1.5"
                title={t('dashboard.error_loading_metrics')}
              >
                <span className="text-base">🔄</span>
                <span>{t('dashboard.update_now')}</span>
              </button>
              {isLoading && (
                <>
                  <div className="h-4 w-px bg-gray-300"></div>
                  <div className="text-xs text-blue-600 font-medium flex items-center gap-1">
                    <span className="animate-spin">⏳</span>
                    <span>{t('dashboard.updating')}</span>
                  </div>
                </>
              )}
            </div>

            {/* Grupo 2: Modo de vista */}
            <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
              <span className="text-xs font-medium text-gray-600">{t('dashboard.view_mode')}:</span>
              <div className="inline-flex rounded-md shadow-sm" role="group">
                <button
                  type="button"
                  onClick={() => setViewMode('simple')}
                  className={`px-3 py-1 text-xs font-medium border transition-all ${
                    viewMode === 'simple'
                      ? 'bg-white text-gray-900 border-gray-300 shadow-sm'
                      : 'bg-transparent text-gray-600 border-transparent hover:text-gray-900'
                  } rounded-l-md`}
                >
                  {t('dashboard.simple_mode')}
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode('advanced')}
                  className={`px-3 py-1 text-xs font-medium border border-l-0 transition-all ${
                    viewMode === 'advanced'
                      ? 'bg-white text-gray-900 border-gray-300 shadow-sm'
                      : 'bg-transparent text-gray-600 border-transparent hover:text-gray-900'
                  } rounded-r-md`}
                >
                  {t('dashboard.advanced_mode')}
                </button>
              </div>
            </div>

            {/* Badge de auto-update (solo cuando no está cargando) */}
            {!isLoading && (
              <div className="text-xs text-blue-700 bg-blue-50 px-3 py-1.5 rounded-md border border-blue-200 font-medium">
                {t('dashboard.auto_update')}
              </div>
            )}

            {/* Inputs de fecha personalizada (solo cuando se selecciona "Personalizado") */}
            {selectedPeriod === 'custom' && (
              <div className="flex gap-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
                <input
                  type="date"
                  value={customStartDate}
                  onChange={(e) => handleCustomDateChange(e.target.value, customEndDate)}
                  className="px-3 py-1.5 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white"
                  placeholder="Desde"
                />
                <input
                  type="date"
                  value={customEndDate}
                  onChange={(e) => handleCustomDateChange(customStartDate, e.target.value)}
                  className="px-3 py-1.5 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white"
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
            <h2 className="text-xl font-semibold text-gray-700">{t('dashboard.main_metrics')}</h2>
            {dashboardError && (
              <div className="text-sm text-red-600 bg-red-50 px-3 py-1 rounded-lg">
                ⚠️ {t('dashboard.error_loading_metrics')}
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

        {/* Gráficos */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Gráfico de línea de tiempo de reservas */}
          <div className="bg-white/80 backdrop-blur rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
            <ReservationsTimelineChart
              key={`timeline-${selectedPeriod}-${dateRange.start}-${dateRange.end}`}
              reservations={trendsReservations || reservations}
              dateRange={dateRange}
              isLoading={trendsReservationsLoading || dashboardLoading}
              selectedPeriod={selectedPeriod}
              trends={dashboardMetrics?.trends}
            />
          </div>

          {/* Gráfico de ocupación por tipo de habitación */}
          <div className="bg-white/80 backdrop-blur rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
            <RoomTypeOccupancyChart
              rooms={rooms}
              dateRange={dateRange}
              isLoading={isLoading}
            />
          </div>
        </div>

        {/* Gráfico de reservas futuras */}
        {futureReservationsData && futureReservationsData.length > 0 && (
          <div className="bg-white/80 backdrop-blur rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
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
        <div className="bg-white/80 backdrop-blur rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-700">
              <CurrencyDollarIcon className="w-5 h-5 text-emerald-600" /> {t('dashboard.revenue')}
            </h2>
            <div className="inline-flex rounded-lg bg-gray-100 p-0.5" role="group">
              <button
                type="button"
                onClick={() => setRevenueMetric('gross')}
                className={`px-3 py-1 text-sm font-medium rounded-l-md transition-colors ${revenueMetric === 'gross' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'}`}
              >
                {t('dashboard.gross')}
              </button>
              <button
                type="button"
                onClick={() => setRevenueMetric('net')}
                className={`px-3 py-1 text-sm font-medium rounded-r-md transition-colors ${revenueMetric === 'net' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'}`}
              >
                {t('dashboard.net')}
              </button>
            </div>
          </div>
          <RevenueChart
            key={`revenue-${selectedPeriod}-${dateRange.start}-${dateRange.end}-${revenueMetric}`}
            reservations={chartReservations || reservations}
            dateRange={dateRange}
            isLoading={chartReservationsLoading || dashboardLoading}
            selectedPeriod={selectedPeriod}
            revenueAnalysis={dashboardMetrics?.revenueAnalysis}
            metric={revenueMetric}
          />
        </div>
        {/* Tablas de reservas */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Tabla de reservas actuales (check-in) */}
          {((activeTab !== 'global' && selectedHotel && hotelSummary?.current_reservations) || (activeTab === 'global' && globalSummary?.current_reservations)) && (
            <div className="bg-white/80 backdrop-blur rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
              <h2 className="text-xl font-semibold text-gray-700 mb-4">
                {activeTab === 'global' ? t('dashboard.current_checkins') : t('dashboard.hotel_checkins')}
              </h2>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {activeTab === 'global' && (
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          {t('dashboard.hotel')}
                        </th>
                      )}
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('dashboard.guest')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('dashboard.room')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('dashboard.check_out')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('dashboard.total')}
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
                            {reservation.guest_name || t('dashboard.no_name')}
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
            <div className="bg-white/80 backdrop-blur rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
              <h2 className="text-xl font-semibold text-gray-700 mb-4">
                {activeTab === 'global' ? t('dashboard.future_reservations_global') : t('dashboard.future_reservations_hotel')}
              </h2>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {activeTab === 'global' && (
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          {t('dashboard.hotel')}
                        </th>
                      )}
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('dashboard.guest')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('dashboard.room')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('dashboard.check_in')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('dashboard.check_out')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('dashboard.total')}
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
                          {reservation.guests_data?.[0]?.name || t('dashboard.no_name')}
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