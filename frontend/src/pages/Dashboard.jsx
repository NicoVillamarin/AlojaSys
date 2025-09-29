import React, { useState, useEffect } from 'react'
import Chart from 'react-apexcharts'
import { useAction } from 'src/hooks/useAction'
import { useList } from 'src/hooks/useList'
import Kpis from 'src/components/Kpis'
import SpinnerLoading from 'src/components/SpinnerLoading'
import Tabs from 'src/components/Tabs'
import HomeIcon from 'src/assets/icons/HomeIcon'
import UsersIcon from 'src/assets/icons/UsersIcon'
import ChartBarIcon from 'src/assets/icons/ChartBarIcon'
import CurrencyDollarIcon from 'src/assets/icons/CurrencyDollarIcon'
import CheckinIcon from 'src/assets/icons/CheckinIcon'
import CheckoutIcon from 'src/assets/icons/CheckoutIcon'
import BedAvailableIcon from 'src/assets/icons/BedAvailableIcon'
import PleopleOccupatedIcon from 'src/assets/icons/PleopleOccupatedIcon'
import WrenchScrewdriverIcon from 'src/assets/icons/WrenchScrewdriverIcon'
import HotelIcon from 'src/assets/icons/HotelIcon'
import GlobalIcon from 'src/assets/icons/GlobalIcon'

const Dashboard = () => {
  const [selectedHotel, setSelectedHotel] = useState(null) // null = todos los hoteles
  // Configurar fechas del mes actual
  const getCurrentMonthRange = () => {
    const now = new Date()
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0)
    
    return {
      start: firstDay.toISOString().split('T')[0],
      end: lastDay.toISOString().split('T')[0],
      monthName: now.toLocaleString('es-ES', { month: 'long', year: 'numeric' })
    }
  }

  const [dateRange, setDateRange] = useState(getCurrentMonthRange())
  const [selectedPeriod, setSelectedPeriod] = useState('current-month') // current-month, last-month, custom
  const [activeTab, setActiveTab] = useState('global') // global o hotel_id

  // Obtener hoteles disponibles
  const { results: hotels, isPending: hotelsLoading } = useList({
    resource: 'hotels',
    params: { page_size: 100 }
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

  // Obtener resúmenes de todos los hoteles para datos globales
  const { results: allHotelsSummary, isPending: allHotelsLoading } = useList({
    resource: 'hotels',
    params: { page_size: 100 },
    enabled: activeTab === 'global'
  })

  // Datos actuales según el tab activo
  const reservations = activeTab === 'global' ? globalReservations : filteredReservations
  const rooms = activeTab === 'global' ? globalRooms : filteredRooms
  const reservationsLoading = activeTab === 'global' ? globalReservationsLoading : filteredReservationsLoading
  const roomsLoading = activeTab === 'global' ? globalRoomsLoading : filteredRoomsLoading

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

  // Función para cambiar el período
  const handlePeriodChange = (period) => {
    setSelectedPeriod(period)
    
    if (period === 'current-month') {
      setDateRange(getCurrentMonthRange())
    } else if (period === 'last-month') {
      const now = new Date()
      const firstDayLastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
      const lastDayLastMonth = new Date(now.getFullYear(), now.getMonth(), 0)
      
      setDateRange({
        start: firstDayLastMonth.toISOString().split('T')[0],
        end: lastDayLastMonth.toISOString().split('T')[0],
        monthName: firstDayLastMonth.toLocaleString('es-ES', { month: 'long', year: 'numeric' })
      })
    }
    // Para 'custom' no cambiamos las fechas, el usuario las seleccionará manualmente
  }

  // Función para cambiar de tab
  const handleTabChange = (tabId) => {
    setActiveTab(tabId)
    if (tabId === 'global') {
      setSelectedHotel(null)
    } else {
      setSelectedHotel(Number(tabId))
    }
  }

  // Crear tabs dinámicamente
  const getTabs = () => {
    if (!hotels) return []

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

    return {
      totalRooms: globalSummary.rooms?.total || 0,
      occupiedRooms: globalSummary.rooms?.occupied || 0,
      availableRooms: globalSummary.rooms?.available || 0,
      maintenanceRooms: globalSummary.rooms?.maintenance || 0,
      outOfServiceRooms: globalSummary.rooms?.out_of_service || 0,
      arrivalsToday: globalSummary.today?.arrivals || 0,
      departuresToday: globalSummary.today?.departures || 0,
      currentGuests: globalSummary.rooms?.current_guests || 0,
      totalRevenue: 0, // Se puede calcular si es necesario
      occupancyRate: globalSummary.rooms?.total > 0 ? 
        Math.round((globalSummary.rooms.occupied / globalSummary.rooms.total) * 100) : 0
    }
  }

  // Procesar datos para KPIs
  const getKPIs = () => {
    let metrics

    if (activeTab !== 'global' && selectedHotel && hotelSummary) {
      // Datos de hotel específico
      metrics = {
        totalRooms: hotelSummary.rooms?.total || 0,
        occupiedRooms: hotelSummary.rooms?.occupied || 0,
        availableRooms: hotelSummary.rooms?.available || 0,
        maintenanceRooms: hotelSummary.rooms?.maintenance || 0,
        outOfServiceRooms: hotelSummary.rooms?.out_of_service || 0,
        arrivalsToday: hotelSummary.today?.arrivals || 0,
        departuresToday: hotelSummary.today?.departures || 0,
        currentGuests: hotelSummary.rooms?.current_guests || 0,
        totalRevenue: 0, // Se calculará por separado
        occupancyRate: hotelSummary.rooms?.total > 0 ? 
          Math.round((hotelSummary.rooms.occupied / hotelSummary.rooms.total) * 100) : 0
      }
    } else {
      // Datos globales
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
      }
    ]
  }

  // Procesar datos para gráfico de línea de tiempo de reservas
  const getReservationsTimelineData = () => {
    if (!reservations) return { series: [], categories: [] }

    // Agrupar reservas por fecha
    const reservationsByDate = {}
    reservations.forEach(reservation => {
      const date = reservation.check_in
      if (!reservationsByDate[date]) {
        reservationsByDate[date] = 0
      }
      reservationsByDate[date]++
    })

    // Crear arrays para el gráfico
    const dates = Object.keys(reservationsByDate).sort()
    const counts = dates.map(date => reservationsByDate[date])

    return {
      series: [{
        name: 'Reservas',
        data: counts
      }],
      categories: dates
    }
  }

  // Procesar datos para gráfico de ocupación por tipo de habitación
  const getRoomTypeOccupancyData = () => {
    if (!rooms) return { series: [], labels: [] }

    const roomTypes = {}
    rooms.forEach(room => {
      const type = room.room_type
      if (!roomTypes[type]) {
        roomTypes[type] = { total: 0, occupied: 0 }
      }
      roomTypes[type].total++
      if (room.status === 'occupied') {
        roomTypes[type].occupied++
      }
    })

    const labels = Object.keys(roomTypes)
    const occupiedData = labels.map(type => roomTypes[type].occupied)
    const totalData = labels.map(type => roomTypes[type].total)

    return {
      series: [
        {
          name: 'Ocupadas',
          data: occupiedData
        },
        {
          name: 'Disponibles',
          data: totalData.map((total, index) => total - occupiedData[index])
        }
      ],
      labels: labels.map(type => {
        const typeNames = {
          'single': 'Individual',
          'double': 'Doble',
          'triple': 'Triple',
          'suite': 'Suite'
        }
        return typeNames[type] || type
      })
    }
  }

  // Procesar datos para gráfico de ingresos
  const getRevenueData = () => {
    if (!reservations) return { series: [], categories: [] }

    // Agrupar por mes
    const revenueByMonth = {}
    reservations.forEach(reservation => {
      const date = new Date(reservation.check_in)
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      if (!revenueByMonth[monthKey]) {
        revenueByMonth[monthKey] = 0
      }
      revenueByMonth[monthKey] += parseFloat(reservation.total_price || 0)
    })

    const months = Object.keys(revenueByMonth).sort()
    const revenues = months.map(month => revenueByMonth[month])

    return {
      series: [{
        name: 'Ingresos',
        data: revenues
      }],
      categories: months
    }
  }

  // Configuración de gráficos
  const timelineOptions = {
    chart: {
      type: 'line',
      height: 350,
      toolbar: { show: true },
      zoom: { enabled: true }
    },
    stroke: {
      curve: 'smooth',
      width: 3
    },
    colors: ['#3B82F6'],
    xaxis: {
      categories: getReservationsTimelineData().categories,
      title: { text: 'Fecha' }
    },
    yaxis: {
      title: { text: 'Número de Reservas' }
    },
    tooltip: {
      y: {
        formatter: (val) => `${val} reservas`
      }
    },
    title: {
      text: `Tendencia de Reservas - ${dateRange.monthName}`,
      align: 'left',
      style: { fontSize: '16px', fontWeight: 'bold' }
    }
  }

  const roomTypeOptions = {
    chart: {
      type: 'bar',
      height: 350,
      stacked: true,
      toolbar: { show: true }
    },
    colors: ['#10B981', '#E5E7EB'],
    xaxis: {
      categories: getRoomTypeOccupancyData().labels
    },
    yaxis: {
      title: { text: 'Número de Habitaciones' }
    },
    legend: {
      position: 'top'
    },
    title: {
      text: `Ocupación por Tipo de Habitación - ${dateRange.monthName}`,
      align: 'left',
      style: { fontSize: '16px', fontWeight: 'bold' }
    }
  }

  const revenueOptions = {
    chart: {
      type: 'area',
      height: 350,
      toolbar: { show: true },
      zoom: { enabled: true }
    },
    colors: ['#8B5CF6'],
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.7,
        opacityTo: 0.3
      }
    },
    xaxis: {
      categories: getRevenueData().categories,
      title: { text: 'Mes' }
    },
    yaxis: {
      title: { text: 'Ingresos ($)' },
      labels: {
        formatter: (val) => `$${val.toLocaleString()}`
      }
    },
    tooltip: {
      y: {
        formatter: (val) => `$${val.toLocaleString()}`
      }
    },
    title: {
      text: `Ingresos - ${dateRange.monthName}`,
      align: 'left',
      style: { fontSize: '16px', fontWeight: 'bold' }
    }
  }

  const isLoading = (activeTab === 'global' ? (globalSummaryLoading || globalReservationsLoading || globalRoomsLoading) : summaryLoading) || reservationsLoading || roomsLoading

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
              📅 Período: {dateRange.monthName}
            </p>
          </div>
          
          {/* Selector de Período */}
          <div className="flex gap-2">
            <select
              value={selectedPeriod}
              onChange={(e) => handlePeriodChange(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="current-month">📅 Mes Actual</option>
              <option value="last-month">📅 Mes Anterior</option>
              <option value="custom">📅 Personalizado</option>
            </select>
            
            {/* Inputs de fecha personalizada (solo cuando se selecciona "Personalizado") */}
            {selectedPeriod === 'custom' && (
              <div className="flex gap-2">
                <input
                  type="date"
                  value={dateRange.start}
                  onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  placeholder="Desde"
                />
                <input
                  type="date"
                  value={dateRange.end}
                  onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
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
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Métricas Principales</h2>
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
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-80">
              <SpinnerLoading />
            </div>
          ) : (
            <Chart
              options={timelineOptions}
              series={getReservationsTimelineData().series}
              type="line"
              height={350}
            />
          )}
        </div>

        {/* Gráfico de ocupación por tipo de habitación */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-80">
              <SpinnerLoading />
            </div>
          ) : (
            <Chart
              options={roomTypeOptions}
              series={getRoomTypeOccupancyData().series}
              type="bar"
              height={350}
            />
          )}
        </div>
      </div>

      {/* Gráfico de ingresos */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-80">
            <SpinnerLoading />
          </div>
        ) : (
          <Chart
            options={revenueOptions}
            series={getRevenueData().series}
            type="area"
            height={350}
          />
        )}
      </div>

      {/* Tabla de reservas actuales */}
      {((activeTab !== 'global' && selectedHotel && hotelSummary?.current_reservations) || (activeTab === 'global' && globalSummary?.current_reservations)) && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">
            {activeTab === 'global' ? 'Reservas Actuales - Todos los Hoteles' : 'Reservas Actuales del Hotel'}
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
                    Estado
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
                        {reservation.check_in}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {reservation.check_out}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          reservation.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                          reservation.status === 'check_in' ? 'bg-blue-100 text-blue-800' :
                          reservation.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {reservation.status}
                        </span>
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
      </div>
    </div>
  )
}

export default Dashboard