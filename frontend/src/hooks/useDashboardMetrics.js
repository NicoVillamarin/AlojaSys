import { useState, useEffect } from 'react'
import { useAction } from './useAction'
import { useList } from './useList'

/**
 * Hook personalizado para obtener métricas del dashboard
 * @param {number} hotelId - ID del hotel (opcional, null para vista global)
 * @param {string} date - Fecha en formato YYYY-MM-DD (opcional, por defecto hoy)
 * @returns {Object} Objeto con métricas y estado de carga
 */
export const useDashboardMetrics = (hotelId = null, date = null, startDate = null, endDate = null) => {
  const [metrics, setMetrics] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)


  // Solo obtener el resumen del dashboard con auto-refresh
  // Si hay startDate y endDate, usar rango de fechas; si no, usar date única
  const summaryParams = {
    ...(hotelId && { hotel_id: hotelId })
  }
  
  if (startDate && endDate) {
    summaryParams.start_date = startDate
    summaryParams.end_date = endDate
  } else {
    summaryParams.date = (date || new Date().toISOString().split('T')[0])
  }
  
  const { 
    results: summary, 
    isPending: summaryLoading, 
    refetch: refetchSummary 
  } = useAction({
    resource: 'dashboard',
    action: 'summary',
    params: summaryParams,
    enabled: true,
    refetchInterval: 30000, // Auto-refresh cada 30 segundos
    refetchIntervalInBackground: true, // Continuar refrescando aunque la pestaña no esté activa
    staleTime: 15000 // Considerar datos obsoletos después de 15 segundos
  })

  // Tendencias del dashboard (por rango con fallback a últimos 30 días)
  const trendsParams = {
    ...(hotelId && { hotel_id: hotelId }),
    ...(startDate && endDate ? { start_date: startDate, end_date: endDate } : {})
  }
  
  const { results: trends, isPending: trendsLoading, refetch: refetchTrends } = useAction({
    resource: 'dashboard',
    action: 'trends',
    params: trendsParams,
    enabled: true,
    refetchInterval: 60000, // Auto-refresh cada 60 segundos (menos frecuente que summary)
    refetchIntervalInBackground: true,
    staleTime: 30000
  })

  // Ocupación por tipo (por fecha)
  const { results: occupancyByType, isPending: occupancyLoading, refetch: refetchOccupancy } = useAction({
    resource: 'dashboard',
    action: 'occupancy-by-room-type',
    params: {
      ...(hotelId && { hotel_id: hotelId }),
      date: (date || new Date().toISOString().split('T')[0])
    },
    enabled: true,
    refetchInterval: 60000, // Auto-refresh cada 60 segundos
    refetchIntervalInBackground: true,
    staleTime: 30000
  })

  // Análisis de ingresos (por rango)
  const { results: revenueAnalysis, isPending: revenueLoading, refetch: refetchRevenue } = useAction({
    resource: 'dashboard',
    action: 'revenue-analysis',
    params: {
      ...(hotelId && { hotel_id: hotelId }),
      ...(startDate && endDate ? { start_date: startDate, end_date: endDate } : {})
    },
    enabled: true,
    refetchInterval: 60000, // Auto-refresh cada 60 segundos
    refetchIntervalInBackground: true,
    staleTime: 30000
  })

  // Debug: Log para verificar respuesta

  // Procesar métricas cuando cambien los datos
  useEffect(() => {
    if (summary) {
      setMetrics({
        summary,
        trends: trends || [],
        occupancyByType: occupancyByType || {},
        revenueAnalysis: revenueAnalysis || null
      })
    }
  }, [summary, trends, occupancyByType, revenueAnalysis])

  // Función para refrescar métricas
  const refreshMetrics = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      await Promise.all([
        refetchSummary(),
        refetchTrends?.(),
        refetchOccupancy?.(),
        refetchRevenue?.()
      ])
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return {
    metrics,
    isLoading: summaryLoading || trendsLoading || occupancyLoading || revenueLoading || isLoading,
    error,
    refreshMetrics,
    refetchSummary
  }
}

/**
 * Hook para obtener métricas globales (todos los hoteles)
 * @param {string} date - Fecha en formato YYYY-MM-DD (opcional, por defecto hoy)
 * @returns {Object} Objeto con métricas globales y estado de carga
 */
export const useGlobalDashboardMetrics = (date = null) => {
  const [globalMetrics, setGlobalMetrics] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  // Obtener resumen global
  const { 
    results: globalSummary, 
    isPending: globalSummaryLoading, 
    refetch: refetchGlobalSummary 
  } = useAction({
    resource: 'status',
    action: 'global-summary',
    params: {},
    enabled: true
  })

  // Obtener hoteles para métricas individuales
  const { 
    results: hotels, 
    isPending: hotelsLoading 
  } = useAction({
    resource: 'hotels',
    action: 'list',
    params: { page_size: 100 },
    enabled: true
  })

  // Procesar métricas globales
  useEffect(() => {
    if (globalSummary && hotels) {
      setGlobalMetrics({
        globalSummary,
        hotels: hotels.results || hotels,
        totalHotels: hotels.count || hotels.length || 0
      })
    }
  }, [globalSummary, hotels])

  // Estado de carga general
  const loading = globalSummaryLoading || hotelsLoading

  // Función para refrescar métricas globales
  const refreshGlobalMetrics = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      await refetchGlobalSummary()
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return {
    globalMetrics,
    isLoading: loading || isLoading,
    error,
    refreshGlobalMetrics,
    refetchGlobalSummary
  }
}

export default useDashboardMetrics
