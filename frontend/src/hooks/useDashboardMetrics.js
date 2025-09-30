import { useState, useEffect } from 'react'
import { useAction } from './useAction'
import { useList } from './useList'

/**
 * Hook personalizado para obtener métricas del dashboard
 * @param {number} hotelId - ID del hotel (opcional, null para vista global)
 * @param {string} date - Fecha en formato YYYY-MM-DD (opcional, por defecto hoy)
 * @returns {Object} Objeto con métricas y estado de carga
 */
export const useDashboardMetrics = (hotelId = null, date = null) => {
  const [metrics, setMetrics] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  // Debug: Log para verificar parámetros
  console.log('useDashboardMetrics Debug:', {
    hotelId,
    date,
    params: { 
      ...(hotelId && { hotel_id: hotelId }),
      date: date || new Date().toISOString().split('T')[0]
    }
  })

  // Solo obtener el resumen del dashboard para evitar bucles infinitos
  const { 
    results: summary, 
    isPending: summaryLoading, 
    refetch: refetchSummary 
  } = useAction({
    resource: 'dashboard',
    action: 'summary',
    params: { 
      ...(hotelId && { hotel_id: hotelId }),
      date: (date || new Date().toISOString().split('T')[0])
    },
    enabled: true
  })

  // Debug: Log para verificar respuesta
  console.log('useDashboardMetrics Summary:', {
    summary,
    summaryLoading,
    error: summary?.error
  })

  // Procesar métricas cuando cambien los datos
  useEffect(() => {
    if (summary) {
      setMetrics({
        summary,
        trends: [],
        occupancyByType: {},
        revenueAnalysis: null
      })
    }
  }, [summary])

  // Función para refrescar métricas
  const refreshMetrics = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      await refetchSummary()
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return {
    metrics,
    isLoading: summaryLoading || isLoading,
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
