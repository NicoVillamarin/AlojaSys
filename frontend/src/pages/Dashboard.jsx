import React, { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAction } from 'src/hooks/useAction'
import { useList } from 'src/hooks/useList'
import usePeriod from 'src/hooks/usePeriod'
import { useDashboardMetrics } from 'src/hooks/useDashboardMetrics'
import { useMe } from 'src/hooks/useMe'
import { usePermissions, useHasAnyPermission } from 'src/hooks/usePermissions'
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
import { useUserHotels } from 'src/hooks/useUserHotels'
import Tooltip from 'src/components/Tooltip'
import HelpTooltip from 'src/components/HelpTooltip'
import { usePlanFeatures } from 'src/hooks/usePlanFeatures'

const Dashboard = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { data: me } = useMe()
  const { housekeepingEnabled } = usePlanFeatures()
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

    // Si el módulo no está habilitado por plan, no redirigir (evita pantalla vacía)
    if (!housekeepingEnabled) return false
    
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
  }, [me, housekeepingEnabled, hasViewDashboard, hasReception, hasViewReservations, hasViewCalendar, hasViewRooms, hasViewOTAs, hasAnyHistory, hasAnyFinancial, hasAnySettings])
  
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

  // Fecha de HOY (operación)
  const todayISO = new Date().toISOString().split('T')[0]

  // Inventario de habitaciones (counts confiables vía DRF count; no depende de métricas cacheadas)
  const { count: totalRoomsCount, isPending: totalRoomsLoading } = useList({
    resource: 'rooms',
    params: {
      ...(activeTab !== 'global' && selectedHotel ? { hotel: selectedHotel } : {}),
      page_size: 1
    },
    enabled: true
  })

  const { count: maintenanceRoomsCount } = useList({
    resource: 'rooms',
    params: {
      ...(activeTab !== 'global' && selectedHotel ? { hotel: selectedHotel } : {}),
      status: 'maintenance',
      page_size: 1
    },
    enabled: true
  })

  const { count: outOfServiceRoomsCount } = useList({
    resource: 'rooms',
    params: {
      ...(activeTab !== 'global' && selectedHotel ? { hotel: selectedHotel } : {}),
      status: 'out_of_service',
      page_size: 1
    },
    enabled: true
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
  
  // Tendencia de reservas: usamos reservas creadas en el período (fallback si el backend no expone "pickup" por día)
  const { results: reservationsCreatedInPeriod, isPending: reservationsCreatedLoading } = useList({
    resource: 'reservations',
    params: {
      ...(activeTab !== 'global' && selectedHotel ? { hotel: selectedHotel } : {}),
      ...(hasDateRange ? {
        created_at__gte: `${dateRange.start}T00:00:00`,
        created_at__lte: `${dateRange.end}T23:59:59`
      } : {}),
      page_size: 1000
    },
    enabled: Boolean(hasDateRange)
  })

  // Reservas futuras (próximos 30 días) para gráfico/tabla informativa
  const end30 = new Date()
  end30.setDate(end30.getDate() + 30)
  const end30ISO = end30.toISOString().split('T')[0]

  const { results: futureReservations, isPending: futureReservationsLoading } = useList({
    resource: 'reservations',
    params: {
      ...(activeTab !== 'global' && selectedHotel ? { hotel: selectedHotel } : {}),
      check_in__gte: todayISO,
      check_in__lte: end30ISO,
      ordering: 'check_in',
      page_size: 1000
    },
    enabled: true
  })

  // Operación HOY (en vivo desde reservas; no depende de métricas cacheadas)
  const { results: arrivalsTodayReservations, isPending: arrivalsTodayLoading, refetch: refetchArrivalsToday } = useList({
    resource: 'reservations',
    params: {
      ...(activeTab !== 'global' && selectedHotel ? { hotel: selectedHotel } : {}),
      check_in: todayISO,
      page_size: 1000
    },
    enabled: true
  })

  const { results: departuresTodayReservations, isPending: departuresTodayLoading, refetch: refetchDeparturesToday } = useList({
    resource: 'reservations',
    params: {
      ...(activeTab !== 'global' && selectedHotel ? { hotel: selectedHotel } : {}),
      check_out: todayISO,
      page_size: 1000
    },
    enabled: true
  })

  const { results: inHouseReservations, isPending: inHouseLoading, refetch: refetchInHouse } = useList({
    resource: 'reservations',
    params: {
      ...(activeTab !== 'global' && selectedHotel ? { hotel: selectedHotel } : {}),
      check_in__lte: todayISO,
      check_out__gt: todayISO,
      page_size: 1000
    },
    enabled: true
  })

  // Auto-refresh de datos críticos cada 30 segundos (sin isLoading por ahora)
  useEffect(() => {
    const interval = setInterval(() => {
      // Solo refrescar si hay datos
      refreshDashboardMetrics()
      refetchArrivalsToday?.()
      refetchDeparturesToday?.()
      refetchInHouse?.()
    }, 30000) // 30 segundos

    return () => clearInterval(interval)
  }, [refreshDashboardMetrics, refetchArrivalsToday, refetchDeparturesToday, refetchInHouse])

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

  // Reservas futuras (solo estados operativos, evitar canceladas)
  const futureReservationsData = useMemo(() => {
    const allowed = new Set(['pending', 'confirmed'])
    return (futureReservations || []).filter(r => allowed.has(r.status))
  }, [futureReservations])

  // Loading consolidado
  const isLoading = hotelsLoading || dashboardLoading || futureReservationsLoading || totalRoomsLoading || arrivalsTodayLoading || departuresTodayLoading || inHouseLoading

  // Derivados “operación hoy” desde reservas (en vivo)
  const operational = useMemo(() => {
    const arrivalAllowed = new Set(['pending', 'confirmed', 'check_in', 'early_check_in'])
    const departureAllowed = new Set(['check_in', 'check_out'])
    const inHouseAllowed = new Set(['check_in', 'early_check_in'])

    const arrivals = (arrivalsTodayReservations || []).filter(r => arrivalAllowed.has(r.status))
    const departures = (departuresTodayReservations || []).filter(r => departureAllowed.has(r.status))
    const inhouse = (inHouseReservations || []).filter(r => inHouseAllowed.has(r.status))

    const occupiedRooms = inhouse.length
    const currentGuests = inhouse.reduce((sum, r) => sum + (parseInt(r.guests || 0, 10) || 0), 0)

    return {
      arrivalsCount: arrivals.length,
      departuresCount: departures.length,
      occupiedRooms,
      currentGuests,
      inhouseReservations: inhouse
    }
  }, [arrivalsTodayReservations, departuresTodayReservations, inHouseReservations])


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

  // (Antes existía un getKPIs basado en `status.*`; se removió porque esos endpoints no exponen rooms/today)

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

  // Helpers visuales (UI)
  const formatMoney = (value) => {
    const n = Number(value || 0)
    return `$${n.toLocaleString()}`
  }

  const MetricCard = ({ title, value, subtitle, icon: Icon, tone = 'brand', progress = null }) => {
    // Paleta AlojaSys (ver `documents/Esquma.txt`)
    // - Navy: #0A304A
    // - Dorado: #D4AF37
    // - Base: blanco / grises claros
    const tones = {
      brand: {
        ring: 'ring-slate-200',
        hoverRing: 'hover:ring-[#0A304A]/25',
        glow: 'from-[#0A304A]/[0.07] via-transparent to-transparent',
        iconBg: 'bg-[#0A304A]/5',
        iconText: 'text-[#0A304A]',
        progressFill: 'bg-[#0A304A]/70',
      },
      accent: {
        ring: 'ring-slate-200',
        hoverRing: 'hover:ring-[#D4AF37]/45',
        glow: 'from-[#D4AF37]/[0.10] via-transparent to-transparent',
        iconBg: 'bg-[#D4AF37]/15',
        iconText: 'text-[#0A304A]',
        progressFill: 'bg-[#0A304A]/70',
      },
      neutral: {
        ring: 'ring-slate-200',
        hoverRing: 'hover:ring-[#0A304A]/20',
        glow: 'from-slate-200/40 via-transparent to-transparent',
        iconBg: 'bg-slate-100',
        iconText: 'text-[#0A304A]',
        progressFill: 'bg-[#0A304A]/70',
      }
    }
    const c = tones[tone] || tones.brand

    return (
      <div
        className={`group relative overflow-hidden rounded-2xl bg-gradient-to-br from-white via-white to-slate-50 shadow-sm ring-1 ${c.ring} ${c.hoverRing} p-4 transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-lg`}
      >
        {/* Glow sutil de marca */}
        <div className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${c.glow}`} />

        {/* Fondo atmosférico (sutil, paleta AlojaSys) */}
        <div className="pointer-events-none absolute -top-10 -right-12 h-28 w-28 rounded-full bg-[#D4AF37]/[0.14] blur-2xl transition-transform duration-500 ease-out group-hover:scale-110" />
        <div className="pointer-events-none absolute -bottom-12 -left-10 h-32 w-32 rounded-full bg-[#0A304A]/[0.10] blur-2xl transition-transform duration-500 ease-out group-hover:scale-110" />

        {/* Borde de acento (muy sutil) */}
        <div className="pointer-events-none absolute left-0 top-0 h-full w-1 bg-gradient-to-b from-[#0A304A]/25 via-[#0A304A]/10 to-transparent" />

        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="text-xs font-semibold text-slate-600 tracking-wide uppercase truncate">
              {title}
            </div>
            <div className="mt-2 text-2xl font-semibold text-slate-900 leading-none">
              {value}
            </div>
            {subtitle && (
              <div className="mt-2 text-xs text-slate-600 leading-snug">
                {subtitle}
              </div>
            )}
          </div>
          {Icon && (
            <div className={`shrink-0 rounded-xl ${c.iconBg} p-2.5 ring-1 ring-black/5 transition-all duration-300 ease-out group-hover:shadow-sm group-hover:scale-[1.03]`}>
              <div className="transition-transform duration-300 ease-out group-hover:-rotate-3">
                <Icon className={`w-5 h-5 ${c.iconText}`} />
              </div>
            </div>
          )}
        </div>

        {progress != null && (
          <div className="mt-3">
            <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
              <div
                className={`h-full rounded-full ${c.progressFill} transition-all duration-700 ease-out`}
                style={{ width: `${Math.max(0, Math.min(progress, 100))}%` }}
              />
            </div>
          </div>
        )}

        {/* Brillo/shine muy sutil en hover */}
        <div className="pointer-events-none absolute -inset-y-10 -left-24 w-24 rotate-12 bg-white/40 blur-xl opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      </div>
    )
  }

  const periodRevenue = revenueMetric === 'net'
    ? (dashboardMetrics?.revenueAnalysis?.revenue?.net_total ?? dashboardMetrics?.summary?.total_revenue ?? 0)
    : (dashboardMetrics?.revenueAnalysis?.revenue?.total ?? dashboardMetrics?.summary?.total_revenue ?? 0)

  // Cobros (caja) del período: por fecha de pago, no por fecha de estadía
  const cashPeriod = revenueMetric === 'net'
    ? (dashboardMetrics?.revenueAnalysis?.cash?.net_collected ?? dashboardMetrics?.summary?.cash_net_collected ?? 0)
    : (dashboardMetrics?.revenueAnalysis?.cash?.gross_collected ?? dashboardMetrics?.summary?.cash_gross_collected ?? 0)
  const cashRefundsPeriod = (dashboardMetrics?.revenueAnalysis?.cash?.refunds ?? dashboardMetrics?.summary?.cash_refunds ?? 0)

  // Tooltips de ayuda (abreviaciones / KPIs financieros) - texto claro para cliente final
  const insightHelpText = {
    revpar:
      `RevPAR (Revenue Per Available Room)\n` +
      `Ingresos por habitación disponible.\n` +
      `Se calcula como: Ingresos del período ÷ Habitaciones disponibles.\n` +
      `Sirve para medir performance combinando tarifa y ocupación.`,
    adr:
      `Tarifa Promedio (ADR - Average Daily Rate)\n` +
      `Promedio de ingreso por habitación ocupada.\n` +
      `Se calcula como: Ingresos del período ÷ Habitaciones ocupadas.`,
    pickup:
      `Pickup\n` +
      `Reservas nuevas creadas en el período indicado.\n` +
      `Ej: “Pickup hoy” = reservas creadas hoy (para fechas futuras o desde hoy).`,
    otb:
      `OTB (On The Books)\n` +
      `Reservas “en cartera” ya confirmadas para los próximos días.\n` +
      `Ayuda a ver lo que ya está vendido hacia adelante (noches/ingresos).`,
    cancelRate:
      `Tasa de cancelación (30 días)\n` +
      `% de reservas canceladas en los últimos 30 días.\n` +
      `Útil para detectar problemas de política, pricing o canales.`
  }

  const insights = [
    {
      label: t('dashboard.kpis.revpar'),
      value: dashboardMetrics?.summary?.revpar !== undefined
        ? formatMoney(dashboardMetrics.summary.revpar)
        : '—',
      help: insightHelpText.revpar
    },
    {
      label: t('dashboard.kpis.average_rate'),
      value: dashboardMetrics?.summary?.average_room_rate !== undefined
        ? formatMoney(dashboardMetrics.summary.average_room_rate)
        : '—',
      help: insightHelpText.adr
    },
    {
      label: t('dashboard.kpis.pickup_today'),
      value: dashboardMetrics?.summary?.pickup_today ?? '—',
      help: insightHelpText.pickup
    },
    {
      label: t('dashboard.kpis.pickup_7d'),
      value: dashboardMetrics?.summary?.pickup_7d ?? '—',
      help: insightHelpText.pickup
    },
    {
      label: t('dashboard.kpis.otb_30d_nights'),
      value: dashboardMetrics?.summary?.otb_next_30d_nights ?? '—',
      help: insightHelpText.otb
    },
    {
      label: t('dashboard.kpis.otb_30d_revenue'),
      value: dashboardMetrics?.summary?.otb_next_30d_revenue !== undefined
        ? formatMoney(dashboardMetrics.summary.otb_next_30d_revenue)
        : '—',
      help: insightHelpText.otb
    },
    {
      label: t('dashboard.kpis.cancellation_rate_30d'),
      value: dashboardMetrics?.summary?.cancellation_rate_30d !== undefined
        ? `${parseFloat(dashboardMetrics.summary.cancellation_rate_30d || 0).toFixed(2)}%`
        : '—',
      help: insightHelpText.cancelRate
    }
  ]

  // Métricas principales (UI) - pocas, claras y sin truncar
  const futureCountK = futureReservationsData?.length || 0
  const futureRevenueK = futureReservationsData?.reduce((sum, res) => sum + (parseFloat(res.total_price) || 0), 0) || 0

  const mainCards = [
    {
      title: t('dashboard.kpis.total_rooms_short', 'Hab. totales'),
      value: totalRoomsCount || 0,
      subtitle: activeTab === 'global' ? t('dashboard.kpis.in_all_hotels') : t('dashboard.kpis.in_hotel'),
      icon: HomeIcon,
      tone: 'brand'
    },
    {
      title: t('dashboard.kpis.occupied_rooms_short', 'Ocupadas'),
      value: operational.occupiedRooms,
      subtitle: t('dashboard.kpis.of_total', { total: totalRoomsCount || 0 }),
      icon: PleopleOccupatedIcon,
      tone: 'brand',
      progress: (totalRoomsCount || 0) > 0 ? Math.round((operational.occupiedRooms / (totalRoomsCount || 1)) * 100) : 0
    },
    {
      title: t('dashboard.kpis.available_rooms_short', 'Disponibles'),
      value: Math.max(0, (totalRoomsCount || 0) - operational.occupiedRooms - (maintenanceRoomsCount || 0) - (outOfServiceRoomsCount || 0)),
      subtitle: t('dashboard.kpis.of_total', { total: totalRoomsCount || 0 }),
      icon: HomeIcon,
      tone: 'neutral'
    },
    {
      title: t('dashboard.kpis.occupancy_rate_short', 'Ocupación'),
      value: `${(totalRoomsCount || 0) > 0 ? Math.round((operational.occupiedRooms / (totalRoomsCount || 1)) * 100) : 0}%`,
      subtitle: t('dashboard.kpis.average_current'),
      icon: ChartBarIcon,
      tone: 'neutral',
      progress: (totalRoomsCount || 0) > 0 ? Math.round((operational.occupiedRooms / (totalRoomsCount || 1)) * 100) : 0
    },
    {
      title: t('dashboard.kpis.arrivals_today_short', 'Check-in hoy'),
      value: operational.arrivalsCount,
      subtitle: t('dashboard.kpis.today'),
      icon: CheckinIcon,
      tone: 'brand'
    },
    {
      title: t('dashboard.kpis.departures_today_short', 'Check-out hoy'),
      value: operational.departuresCount,
      subtitle: t('dashboard.kpis.today'),
      icon: CheckoutIcon,
      tone: 'brand'
    },
    {
      title: t('dashboard.kpis.current_guests_short', 'Huéspedes'),
      value: operational.currentGuests,
      subtitle: t('dashboard.kpis.today'),
      icon: PleopleOccupatedIcon,
      tone: 'accent'
    },
    {
      title: t('dashboard.kpis.future_reservations_short', 'Reservas (30d)'),
      value: futureCountK,
      subtitle: t('dashboard.kpis.next_30_days', 'Próximos 30 días'),
      icon: CheckCircleIcon,
      tone: 'neutral'
    },
    {
      title: t('dashboard.kpis.future_revenue_short', 'Ingresos (30d)'),
      value: formatMoney(futureRevenueK),
      subtitle: t('dashboard.kpis.next_30_days', 'Próximos 30 días'),
      icon: CurrencyDollarIcon,
      tone: 'accent'
    }
  ]

  const advancedOpsCards = showAdvanced ? [
    {
      title: t('dashboard.kpis.maintenance_rooms_short', 'Mantenimiento'),
      value: maintenanceRoomsK,
      subtitle: t('dashboard.kpis.today'),
      icon: WrenchScrewdriverIcon,
      tone: 'neutral'
    },
    {
      title: t('dashboard.kpis.out_of_service_rooms_short', 'Fuera de servicio'),
      value: outOfServiceRoomsK,
      subtitle: t('dashboard.kpis.today'),
      icon: WrenchScrewdriverIcon,
      tone: 'neutral'
    }
  ] : []

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-white">
      {/* Hero Header */}
      <div className="relative overflow-hidden border-b border-slate-200 bg-white">
        <div className="pointer-events-none absolute inset-0">
          {/* Paleta AlojaSys (sutil): Navy #0A304A, Dorado #D4AF37 */}
          <div className="absolute -top-24 -left-24 h-64 w-64 rounded-full bg-[#0A304A]/[0.10] blur-3xl"></div>
          <div className="absolute -top-16 right-0 h-72 w-72 rounded-full bg-[#D4AF37]/[0.16] blur-3xl"></div>
          <div className="absolute bottom-0 left-1/2 h-64 w-64 -translate-x-1/2 rounded-full bg-[#0A304A]/[0.08] blur-3xl"></div>
        </div>

        <div className="relative px-6 py-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-3 py-1 text-xs font-medium text-slate-600">
                <span className="h-2 w-2 rounded-full bg-[#D4AF37]"></span>
                {t('dashboard.period')}: <span className="text-slate-900">{dateRange.label}</span>
              </div>
              <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
                {activeTab === 'global'
                  ? t('dashboard.global_view')
                  : (() => {
                    const h = (hotels || []).find(x => x.id === selectedHotel)
                    return h ? `${h.name}${h.city ? ` - ${h.city}` : ''}` : t('dashboard.selected_hotel')
                  })()
                }
              </h1>
              <p className="text-sm text-slate-600">
                {t('dashboard.main_metrics')} · {t('dashboard.auto_update')}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {/* Período */}
              <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white/80 px-3 py-2 shadow-sm">
                <PeriodSelector
                  selectedPeriod={selectedPeriod}
                  onPeriodChange={handlePeriodChange}
                  className="flex-shrink-0"
                />
                <div className="h-5 w-px bg-slate-200"></div>
                <button
                  onClick={refreshDashboardMetrics}
                  className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-[#0A304A]/30"
                  title={t('dashboard.update_now')}
                >
                  <span className={isLoading ? 'animate-spin' : ''}>⟳</span>
                  {t('dashboard.update_now')}
                </button>
              </div>

              {/* Modo */}
              <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white/80 px-3 py-2 shadow-sm">
                <span className="text-xs font-medium text-slate-600">{t('dashboard.view_mode')}:</span>
                <div className="inline-flex rounded-lg bg-slate-100 p-0.5" role="group">
                  <button
                    type="button"
                    onClick={() => setViewMode('simple')}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition ${
                      viewMode === 'simple' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {t('dashboard.simple_mode')}
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode('advanced')}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition ${
                      viewMode === 'advanced' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {t('dashboard.advanced_mode')}
                  </button>
                </div>
              </div>

              {/* Custom dates */}
              {selectedPeriod === 'custom' && (
                <div className="flex gap-2 rounded-xl border border-slate-200 bg-white/80 px-3 py-2 shadow-sm">
                  <input
                    type="date"
                    value={customStartDate}
                    onChange={(e) => handleCustomDateChange(e.target.value, customEndDate)}
                    className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm focus:ring-2 focus:ring-[#0A304A]/30"
                    placeholder="Desde"
                  />
                  <input
                    type="date"
                    value={customEndDate}
                    onChange={(e) => handleCustomDateChange(customStartDate, e.target.value)}
                    className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm focus:ring-2 focus:ring-[#0A304A]/30"
                    placeholder="Hasta"
                  />
                </div>
              )}
            </div>
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

        {/* Overview */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* KPIs (main) */}
          <div className="xl:col-span-2 rounded-3xl border border-slate-200 bg-white/80 backdrop-blur shadow-sm">
            <div className="flex items-start justify-between gap-4 px-6 py-5 border-b border-slate-100">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">{t('dashboard.main_metrics')}</h2>
                <p className="text-sm text-slate-600">
                  {t('dashboard.period')}: <span className="text-slate-900">{dateRange.label}</span>
                </p>
              </div>
              {dashboardError && (
                <div className="text-sm text-rose-700 bg-rose-50 px-3 py-1.5 rounded-lg border border-rose-200">
                  {t('dashboard.error_loading_metrics')}
                </div>
              )}
            </div>
            <div className="p-6">
              {isLoading ? (
                <div className="flex items-center justify-center h-32">
                  <SpinnerLoading />
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {mainCards.slice(0, 6).map((c) => (
                      <MetricCard
                        key={c.title}
                        title={c.title}
                        value={c.value}
                        subtitle={c.subtitle}
                        icon={c.icon}
                        tone={c.tone}
                        progress={c.progress}
                      />
                    ))}
                  </div>

                  <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {mainCards.slice(6).map((c) => (
                      <MetricCard
                        key={c.title}
                        title={c.title}
                        value={c.value}
                        subtitle={c.subtitle}
                        icon={c.icon}
                        tone={c.tone}
                        progress={c.progress}
                      />
                    ))}
                    {advancedOpsCards.map((c) => (
                      <MetricCard
                        key={c.title}
                        title={c.title}
                        value={c.value}
                        subtitle={c.subtitle}
                        icon={c.icon}
                        tone={c.tone}
                        progress={c.progress}
                      />
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Insights */}
          <div className="rounded-3xl border border-slate-200 bg-white/80 backdrop-blur shadow-sm overflow-hidden">
            <div className="px-6 py-5 border-b border-slate-100">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900">{t('dashboard.revenue')}</h3>
                <div className="inline-flex rounded-lg bg-slate-100 p-0.5" role="group">
                  <button
                    type="button"
                    onClick={() => setRevenueMetric('gross')}
                    className={`px-3 py-1 text-xs font-semibold rounded-md transition ${
                      revenueMetric === 'gross' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {t('dashboard.gross')}
                  </button>
                  <button
                    type="button"
                    onClick={() => setRevenueMetric('net')}
                    className={`px-3 py-1 text-xs font-semibold rounded-md transition ${
                      revenueMetric === 'net' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {t('dashboard.net')}
                  </button>
                </div>
              </div>
              <div className="mt-3 rounded-2xl bg-gradient-to-br from-emerald-50 to-cyan-50 border border-emerald-100 px-4 py-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-xs font-medium text-slate-600">
                      {t('dashboard.revenue_accrual', 'Ingresos (estadía)')}
                    </div>
                    <div className="mt-1 text-2xl font-semibold text-slate-900">{formatMoney(periodRevenue)}</div>
                  </div>
                  <HelpTooltip
                    text={
                      `Ingresos (estadía) = devengado por noches dentro del período.\n` +
                      `No incluye cobros de reservas futuras si la estadía todavía no ocurre.\n\n` +
                      `Cobros (caja) = pagos cobrados dentro del período, aunque la estadía sea futura.`
                    }
                    className="shrink-0"
                  />
                </div>

                <div className="mt-3 pt-3 border-t border-emerald-100">
                  <div className="text-xs font-medium text-slate-600">
                    {t('dashboard.cash_collections', 'Cobros (caja)')}
                  </div>
                  <div className="mt-1 text-xl font-semibold text-slate-900">{formatMoney(cashPeriod)}</div>
                  {Number(cashRefundsPeriod || 0) > 0 && (
                    <div className="mt-1 text-xs text-slate-600">
                      {t('dashboard.refunds', 'Devoluciones')}: <span className="text-slate-900">{formatMoney(cashRefundsPeriod)}</span>
                    </div>
                  )}
                </div>
                <div className="mt-1 text-xs text-slate-600">
                  {t('dashboard.period')}: <span className="text-slate-900">{dateRange.label}</span>
                </div>
              </div>
            </div>

            <div className="p-6">
              <div className="grid grid-cols-2 gap-3">
                {insights.map((item) => (
                  <div
                    key={item.label}
                    className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-gradient-to-br from-white via-white to-slate-50 p-4 shadow-sm transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-md hover:ring-1 hover:ring-[#0A304A]/20"
                  >
                    {/* Fondo atmosférico sutil */}
                    <div className="pointer-events-none absolute -top-8 -right-10 h-24 w-24 rounded-full bg-[#D4AF37]/[0.14] blur-2xl transition-transform duration-500 ease-out group-hover:scale-110" />
                    <div className="pointer-events-none absolute -bottom-10 -left-8 h-28 w-28 rounded-full bg-[#0A304A]/[0.10] blur-2xl transition-transform duration-500 ease-out group-hover:scale-110" />
                    <div className="pointer-events-none absolute left-0 top-0 h-full w-1 bg-gradient-to-b from-[#0A304A]/20 via-[#0A304A]/10 to-transparent" />

                    <div className="relative flex items-center justify-between gap-2">
                      <div className="text-xs font-semibold text-slate-700 truncate">{item.label}</div>
                      <HelpTooltip
                        text={item.help}
                        className="ml-2"
                      />
                    </div>
                    <div className="relative mt-1 text-lg font-semibold text-slate-900">{item.value}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Gráficos */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Gráfico de línea de tiempo de reservas */}
          <div className="bg-white/80 backdrop-blur rounded-3xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
            <ReservationsTimelineChart
              key={`timeline-${selectedPeriod}-${dateRange.start}-${dateRange.end}`}
              reservations={reservationsCreatedInPeriod}
              dateRange={dateRange}
              isLoading={reservationsCreatedLoading || dashboardLoading}
              selectedPeriod={selectedPeriod}
              trends={dashboardMetrics?.trends}
            />
          </div>

          {/* Gráfico de ocupación por tipo de habitación */}
          <div className="bg-white/80 backdrop-blur rounded-3xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
            <RoomTypeOccupancyChart
              rooms={[]}
              dateRange={dateRange}
              isLoading={isLoading}
              occupancyByType={dashboardMetrics?.occupancyByType}
            />
          </div>
        </div>

        {/* Gráfico de ingresos */}
        <div className="bg-white/80 backdrop-blur rounded-3xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
              <CurrencyDollarIcon className="w-5 h-5 text-emerald-600" /> {t('dashboard.revenue')}
            </h2>
            <div className="text-xs text-slate-600">
              {t('dashboard.period')}: <span className="text-slate-900">{dateRange.label}</span>
            </div>
          </div>
          <RevenueChart
            key={`revenue-${selectedPeriod}-${dateRange.start}-${dateRange.end}-${revenueMetric}`}
            reservations={[]}
            dateRange={dateRange}
            isLoading={dashboardLoading}
            selectedPeriod={selectedPeriod}
            revenueAnalysis={dashboardMetrics?.revenueAnalysis}
            metric={revenueMetric}
          />
        </div>

        {/* Gráfico de reservas futuras */}
        {futureReservationsData && futureReservationsData.length > 0 && (
          <div className="bg-white/80 backdrop-blur rounded-3xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
            <FutureReservationsChart
              key={`future-${selectedPeriod}-${dateRange.start}-${dateRange.end}`}
              futureReservations={futureReservationsData}
              dateRange={dateRange}
              isLoading={isLoading}
              selectedPeriod={selectedPeriod}
            />
          </div>
        )}

        {/* Tablas de reservas */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Tabla de huéspedes in-house (hoy) */}
          {operational.inhouseReservations && operational.inhouseReservations.length > 0 && (
            <div className="bg-white/80 backdrop-blur rounded-3xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">
                {t('dashboard.current_checkins')}
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
                    {operational.inhouseReservations.map((reservation, index) => (
                      <tr key={reservation.id ?? index} className="hover:bg-gray-50">
                        {activeTab === 'global' && (
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {reservation.hotel_name || 'N/A'}
                          </td>
                        )}
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {reservation.guests_data?.[0]?.name || reservation.guest_name || t('dashboard.no_name')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {reservation.room_name || reservation.room || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {reservation.check_out ? format(parseISO(reservation.check_out), "dd/MM/yyyy") : '—'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          ${reservation.total_price?.toLocaleString?.() || reservation.total_price || '0'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tabla de reservas confirmadas futuras */}
          {futureReservationsData && futureReservationsData.length > 0 && (
            <div className="bg-white/80 backdrop-blur rounded-3xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">
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