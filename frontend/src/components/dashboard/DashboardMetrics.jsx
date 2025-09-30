import React from 'react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import SpinnerLoading from '../SpinnerLoading'

const DashboardMetrics = ({ 
  metrics, 
  isLoading, 
  error, 
  onRefresh,
  showRefreshButton = true 
}) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <SpinnerLoading />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">
              Error al cargar métricas
            </h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error}</p>
            </div>
            {showRefreshButton && (
              <div className="mt-4">
                <button
                  onClick={onRefresh}
                  className="bg-red-100 text-red-800 px-3 py-2 rounded-md text-sm font-medium hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  Reintentar
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-lg">No hay métricas disponibles</p>
      </div>
    )
  }

  const { summary, trends, occupancyByType, revenueAnalysis } = metrics

  return (
    <div className="space-y-6">
      {/* Header con botón de actualización */}
      {showRefreshButton && (
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">
            Métricas del Dashboard
          </h2>
          <button
            onClick={onRefresh}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Actualizar Métricas
          </button>
        </div>
      )}

      {/* Resumen de métricas principales */}
      {summary && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-700 mb-4">
            Resumen del {format(new Date(summary.date), 'dd MMMM yyyy', { locale: es })}
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Habitaciones */}
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v2H8V5z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-blue-600">Habitaciones</p>
                  <p className="text-2xl font-bold text-blue-900">
                    {summary.occupied_rooms} / {summary.total_rooms}
                  </p>
                  <p className="text-sm text-blue-600">
                    {summary.occupancy_rate}% ocupación
                  </p>
                </div>
              </div>
            </div>

            {/* Huéspedes */}
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-green-600">Huéspedes</p>
                  <p className="text-2xl font-bold text-green-900">
                    {summary.guests_checked_in}
                  </p>
                  <p className="text-sm text-green-600">
                    {summary.guests_expected_today} esperados hoy
                  </p>
                </div>
              </div>
            </div>

            {/* Check-ins/Check-outs */}
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-8 w-8 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-purple-600">Movimientos</p>
                  <p className="text-2xl font-bold text-purple-900">
                    {summary.check_in_today} / {summary.check_out_today}
                  </p>
                  <p className="text-sm text-purple-600">
                    Check-in / Check-out
                  </p>
                </div>
              </div>
            </div>

            {/* Ingresos */}
            <div className="bg-emerald-50 rounded-lg p-4">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-8 w-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-emerald-600">Ingresos</p>
                  <p className="text-2xl font-bold text-emerald-900">
                    ${summary.total_revenue?.toLocaleString() || '0'}
                  </p>
                  <p className="text-sm text-emerald-600">
                    ${summary.average_room_rate?.toLocaleString() || '0'} promedio
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Ocupación por tipo de habitación */}
      {occupancyByType && Object.keys(occupancyByType).length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-700 mb-4">
            Ocupación por Tipo de Habitación
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(occupancyByType).map(([type, data]) => (
              <div key={type} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 capitalize">
                      {type === 'single' ? 'Single' : 
                       type === 'double' ? 'Doble' : 
                       type === 'triple' ? 'Triple' : 
                       type === 'suite' ? 'Suite' : type}
                    </p>
                    <p className="text-2xl font-bold text-gray-900">
                      {data.occupied} / {data.total}
                    </p>
                    <p className="text-sm text-gray-500">
                      {data.total > 0 ? Math.round((data.occupied / data.total) * 100) : 0}% ocupado
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">Disponibles</p>
                    <p className="text-lg font-semibold text-green-600">
                      {data.available}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Análisis de ingresos */}
      {revenueAnalysis && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-700 mb-4">
            Análisis de Ingresos
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <p className="text-sm font-medium text-gray-600">Ingresos Totales</p>
              <p className="text-3xl font-bold text-emerald-600">
                ${revenueAnalysis.revenue?.total?.toLocaleString() || '0'}
              </p>
              <p className="text-sm text-gray-500">
                {revenueAnalysis.period?.days || 0} días
              </p>
            </div>
            
            <div className="text-center">
              <p className="text-sm font-medium text-gray-600">Promedio Diario</p>
              <p className="text-3xl font-bold text-blue-600">
                ${revenueAnalysis.revenue?.average_daily?.toLocaleString() || '0'}
              </p>
              <p className="text-sm text-gray-500">
                por día
              </p>
            </div>
            
            <div className="text-center">
              <p className="text-sm font-medium text-gray-600">Tarifa Promedio</p>
              <p className="text-3xl font-bold text-purple-600">
                ${revenueAnalysis.revenue?.average_room_rate?.toLocaleString() || '0'}
              </p>
              <p className="text-sm text-gray-500">
                por habitación
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tendencias */}
      {trends && trends.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-700 mb-4">
            Tendencias (Últimos 30 días)
          </h3>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fecha
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ocupación
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ingresos
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tarifa Promedio
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Huéspedes
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {trends.slice(0, 10).map((trend, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {format(new Date(trend.date), 'dd/MM/yyyy', { locale: es })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {trend.occupancy_rate}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ${trend.total_revenue?.toLocaleString() || '0'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ${trend.average_room_rate?.toLocaleString() || '0'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {trend.total_guests}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default DashboardMetrics
