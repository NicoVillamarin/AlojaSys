import React, { useState } from 'react'
import { useDashboardMetrics, useGlobalDashboardMetrics } from '../hooks/useDashboardMetrics'
import DashboardMetrics from '../components/dashboard/DashboardMetrics'
import SpinnerLoading from '../components/SpinnerLoading'

const DashboardMetricsPage = () => {
  const [selectedHotel, setSelectedHotel] = useState(null)
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [viewMode, setViewMode] = useState('hotel') // 'hotel' o 'global'

  // Hook para métricas de hotel específico
  const {
    metrics: hotelMetrics,
    isLoading: hotelLoading,
    error: hotelError,
    refreshMetrics: refreshHotelMetrics
  } = useDashboardMetrics(selectedHotel, selectedDate)

  // Hook para métricas globales
  const {
    globalMetrics,
    isLoading: globalLoading,
    error: globalError,
    refreshGlobalMetrics
  } = useGlobalDashboardMetrics(selectedDate)

  // Obtener hoteles disponibles
  const { results: hotels, isPending: hotelsLoading } = useAction({
    resource: 'hotels',
    params: { page_size: 100 }
  })

  const handleHotelChange = (hotelId) => {
    setSelectedHotel(hotelId)
    setViewMode('hotel')
  }

  const handleDateChange = (date) => {
    setSelectedDate(date)
  }

  const handleViewModeChange = (mode) => {
    setViewMode(mode)
    if (mode === 'global') {
      setSelectedHotel(null)
    }
  }

  if (hotelsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <SpinnerLoading />
      </div>
    )
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Métricas del Dashboard
            </h1>
            <p className="text-gray-600 mt-1">
              Análisis detallado de métricas del hotel
            </p>
          </div>
          
          {/* Controles */}
          <div className="flex gap-4">
            {/* Selector de modo de vista */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => handleViewModeChange('hotel')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'hotel'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Hotel Específico
              </button>
              <button
                onClick={() => handleViewModeChange('global')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'global'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Vista Global
              </button>
            </div>

            {/* Selector de hotel (solo en modo hotel) */}
            {viewMode === 'hotel' && (
              <select
                value={selectedHotel || ''}
                onChange={(e) => handleHotelChange(e.target.value ? Number(e.target.value) : null)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Seleccionar hotel...</option>
                {hotels?.map(hotel => (
                  <option key={hotel.id} value={hotel.id}>
                    {hotel.name}
                  </option>
                ))}
              </select>
            )}

            {/* Selector de fecha */}
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => handleDateChange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Contenido */}
      <div className="p-6">
        {viewMode === 'hotel' ? (
          <DashboardMetrics
            metrics={hotelMetrics}
            isLoading={hotelLoading}
            error={hotelError}
            onRefresh={refreshHotelMetrics}
          />
        ) : (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-xl font-semibold text-gray-700 mb-4">
                Vista Global - Todos los Hoteles
              </h2>
              <p className="text-gray-600">
                Las métricas globales se muestran en la página principal del Dashboard.
                Aquí puedes ver métricas detalladas de hoteles específicos.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default DashboardMetricsPage
