import React, { useState, useEffect } from 'react'
import { reconciliationService } from 'src/services/reconciliationService'
import SpinnerLoading from 'src/components/SpinnerLoading'
import Badge from 'src/components/Badge'
import Filter from '../Filter'
import { t } from 'i18next'

const ReconciliationList = ({ hotelId, onSelectReconciliation }) => {
  const [reconciliations, setReconciliations] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    status: '',
    dateFrom: '',
    dateTo: ''
  })

  // Función para mapear estados del backend a variantes de Badge
  const getStatusVariant = (status) => {
    switch (status) {
      case 'pending':
        return 'warning'
      case 'processing':
        return 'info'
      case 'completed':
        return 'success'
      case 'failed':
        return 'error'
      case 'manual_review':
        return 'warning'
      default:
        return 'default'
    }
  }

  // Función para mapear estados del backend a etiquetas en español
  const getStatusLabel = (status) => {
    switch (status) {
      case 'pending':
        return 'Pendiente'
      case 'processing':
        return 'Procesando'
      case 'completed':
        return 'Completada'
      case 'failed':
        return 'Fallida'
      case 'manual_review':
        return 'Revisión Manual'
      default:
        return status
    }
  }

  useEffect(() => {
    loadReconciliations()
  }, [hotelId, filters])

  const loadReconciliations = async () => {
    try {
      setLoading(true)
      // La API lista general no requiere hotel_id; filtros opcionales
      const params = { ...filters }
      const response = await reconciliationService.getReconciliations(params)
      setReconciliations(response.results || response)
    } catch (error) {
      console.error('Error cargando conciliaciones:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (e) => {
    const { name, value } = e.target
    setFilters(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const clearFilters = () => {
    setFilters({
      status: '',
      dateFrom: '',
      dateTo: ''
    })
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-8">
        <SpinnerLoading />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filtros */}
        <Filter title={t('filter.search_filters')}>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Estado
            </label>
            <select
              name="status"
              value={filters.status}
              onChange={handleFilterChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos</option>
              <option value="pending">Pendiente</option>
              <option value="processing">Procesando</option>
              <option value="completed">Completada</option>
              <option value="failed">Fallida</option>
              <option value="manual_review">Revisión Manual</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Fecha Desde
            </label>
            <input
              type="date"
              name="dateFrom"
              value={filters.dateFrom}
              onChange={handleFilterChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Fecha Hasta
            </label>
            <input
              type="date"
              name="dateTo"
              value={filters.dateTo}
              onChange={handleFilterChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div className="flex items-end">
            <button
              onClick={clearFilters}
              className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Limpiar Filtros
            </button>
          </div>
        </div>
        </Filter>
      

      {/* Lista de Conciliaciones */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Conciliaciones Bancarias ({reconciliations.length})
          </h3>
        </div>
        
        {reconciliations.length === 0 ? (
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No hay conciliaciones</h3>
            <p className="mt-1 text-sm text-gray-500">Sube un archivo CSV para comenzar.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {reconciliations.map((reconciliation) => (
              <div
                key={reconciliation.id}
                className="px-6 py-4 hover:bg-gray-50 cursor-pointer"
                onClick={() => onSelectReconciliation(reconciliation)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3">
                      <h4 className="text-sm font-medium text-gray-900 truncate">
                        Conciliación {reconciliation.id}
                      </h4>
                      <Badge
                        variant={getStatusVariant(reconciliation.status)}
                        className="text-xs"
                      >
                        {getStatusLabel(reconciliation.status)}
                      </Badge>
                    </div>
                    
                    <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                      <span>Fecha: {new Date(reconciliation.reconciliation_date).toLocaleDateString('es-ES')}</span>
                      <span>Archivo: {reconciliation.csv_filename}</span>
                      <span>Transacciones: {reconciliation.total_transactions}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {reconciliation.matched_transactions} / {reconciliation.total_transactions} matches
                      </div>
                      <div className="text-xs text-gray-500">
                        {reconciliation.match_percentage}% de coincidencia
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {reconciliation.needs_manual_review && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                          Revisión Manual
                        </span>
                      )}
                      
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ReconciliationList

