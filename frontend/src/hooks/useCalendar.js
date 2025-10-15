import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useUserHotels } from './useUserHotels'
import fetchWithAuth from '../services/fetchWithAuth'
import { getApiParams, getApiURL } from '../services/utils'

/**
 * Hook para obtener eventos del calendario
 * @param {Object} options - Opciones de configuración
 * @param {string} options.hotel - ID del hotel
 * @param {string} options.startDate - Fecha de inicio (YYYY-MM-DD)
 * @param {string} options.endDate - Fecha de fin (YYYY-MM-DD)
 * @param {boolean} options.includeMaintenance - Incluir mantenimiento
 * @param {boolean} options.includeBlocks - Incluir bloqueos
 * @param {string} options.viewType - Tipo de vista (month, week, day, rooms)
 */
export const useCalendarEvents = (options = {}) => {
  const { singleHotelId } = useUserHotels()
  
  const {
    hotel = singleHotelId,
    startDate,
    endDate,
    includeMaintenance = true,
    includeBlocks = true,
    viewType = 'month',
    enabled = true
  } = options

  const { data, isError, isPending, refetch, isRefetching } = useQuery({
    queryKey: ['calendar-events', { hotel, startDate, endDate, includeMaintenance, includeBlocks, viewType }],
    queryFn: async () => {
      if (!hotel || !startDate || !endDate) return []
      
      const params = {
        hotel,
        start_date: startDate,
        end_date: endDate,
        include_maintenance: includeMaintenance,
        include_blocks: includeBlocks,
        view_type: viewType
      }
      
      const base = getApiURL() || ""
      const url = `${base}/api/calendar/events/calendar_events/?${getApiParams(params)}`
      
      return await fetchWithAuth(url, { method: "GET" })
    },
    enabled: enabled && !!hotel && !!startDate && !!endDate
  })

  return {
    events: data || [],
    isPending,
    isError,
    isRefetching,
    refetch
  }
}

/**
 * Hook para obtener estadísticas del calendario
 */
export const useCalendarStats = (options = {}) => {
  const { singleHotelId } = useUserHotels()
  
  const {
    hotel = singleHotelId,
    startDate,
    endDate,
    enabled = true
  } = options

  const { data, isError, isPending, refetch } = useQuery({
    queryKey: ['calendar-stats', { hotel, startDate, endDate }],
    queryFn: async () => {
      if (!hotel || !startDate || !endDate) return null
      
      const params = {
        hotel,
        start_date: startDate,
        end_date: endDate
      }
      
      const base = getApiURL() || ""
      const url = `${base}/api/calendar/events/stats/?${getApiParams(params)}`
      
      return await fetchWithAuth(url, { method: "GET" })
    },
    enabled: enabled && !!hotel && !!startDate && !!endDate
  })

  return {
    stats: data,
    isPending,
    isError,
    refetch
  }
}

/**
 * Hook para obtener vista de habitaciones
 */
export const useCalendarRoomsView = (options = {}) => {
  const { singleHotelId } = useUserHotels()
  
  const {
    hotel = singleHotelId,
    startDate,
    endDate,
    enabled = true
  } = options

  const { data, isError, isPending, refetch } = useQuery({
    queryKey: ['calendar-rooms-view', { hotel, startDate, endDate }],
    queryFn: async () => {
      if (!hotel || !startDate || !endDate) return null
      
      const params = {
        hotel,
        start_date: startDate,
        end_date: endDate
      }
      
      const base = getApiURL() || ""
      const url = `${base}/api/calendar/events/rooms_view/?${getApiParams(params)}`
      
      return await fetchWithAuth(url, { method: "GET" })
    },
    enabled: enabled && !!hotel && !!startDate && !!endDate
  })

  return {
    roomsData: data,
    isPending,
    isError,
    refetch
  }
}

/**
 * Hook para obtener matriz de disponibilidad
 */
export const useCalendarAvailability = (options = {}) => {
  const { singleHotelId } = useUserHotels()
  
  const {
    hotel = singleHotelId,
    startDate,
    endDate,
    enabled = true
  } = options

  const { data, isError, isPending, refetch } = useQuery({
    queryKey: ['calendar-availability', { hotel, startDate, endDate }],
    queryFn: async () => {
      if (!hotel || !startDate || !endDate) return null
      
      const params = {
        hotel,
        start_date: startDate,
        end_date: endDate
      }
      
      const base = getApiURL() || ""
      const url = `${base}/api/calendar/availability-matrix/?${getApiParams(params)}`
      
      return await fetchWithAuth(url, { method: "GET" })
    },
    enabled: enabled && !!hotel && !!startDate && !!endDate
  })

  return {
    availability: data,
    isPending,
    isError,
    refetch
  }
}

/**
 * Hook para acciones masivas en el calendario
 */
export const useCalendarBulkAction = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ action, reservationIds, notes = '' }) => {
      const base = getApiURL() || ""
      const url = `${base}/api/calendar/events/bulk_action/`
      
      return await fetchWithAuth(url, {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action,
          reservation_ids: reservationIds,
          notes
        })
      })
    },
    onSuccess: () => {
      // Invalidar queries relacionadas
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] })
      queryClient.invalidateQueries({ queryKey: ['calendar-stats'] })
      queryClient.invalidateQueries({ queryKey: ['calendar-rooms-view'] })
      queryClient.invalidateQueries({ queryKey: ['calendar-availability'] })
    }
  })
}

/**
 * Hook para drag & drop de reservas
 */
export const useCalendarDragDrop = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ reservationId, newRoomId, newStartDate, newEndDate, notes = '' }) => {
      const base = getApiURL() || ""
      const url = `${base}/api/calendar/events/drag_drop/`
      
      return await fetchWithAuth(url, {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reservation_id: reservationId,
          new_room_id: newRoomId,
          new_start_date: newStartDate,
          new_end_date: newEndDate,
          notes
        })
      })
    },
    onSuccess: () => {
      // Invalidar queries relacionadas
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] })
      queryClient.invalidateQueries({ queryKey: ['calendar-stats'] })
      queryClient.invalidateQueries({ queryKey: ['calendar-rooms-view'] })
      queryClient.invalidateQueries({ queryKey: ['calendar-availability'] })
    }
  })
}
