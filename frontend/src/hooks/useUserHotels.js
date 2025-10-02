import { useMemo } from 'react'
import { useAuthStore } from 'src/stores/useAuthStore'

/**
 * Hook para obtener los hoteles asignados al usuario logueado.
 * 
 * @returns {Object} Información de los hoteles del usuario
 * @returns {Array} hotels - Array de objetos hotel con {id, name, city, timezone}
 * @returns {Array} hotelIds - Array de IDs de hoteles (para filtros)
 * @returns {string} hotelIdsString - IDs separados por coma (para query params)
 * @returns {boolean} hasMultipleHotels - Si el usuario tiene más de un hotel
 * @returns {boolean} hasSingleHotel - Si el usuario tiene exactamente un hotel
 * @returns {number|null} singleHotelId - ID del único hotel (si solo tiene uno)
 * @returns {boolean} isSuperuser - Si el usuario es superusuario (ve todos los hoteles)
 */
export const useUserHotels = () => {
  const { user } = useAuthStore()

  return useMemo(() => {
    // Si no hay usuario logueado
    if (!user) {
      return {
        hotels: [],
        hotelIds: [],
        hotelIdsString: '',
        hasMultipleHotels: false,
        hasSingleHotel: false,
        singleHotelId: null,
        isSuperuser: false,
      }
    }

    // Si es superuser, puede ver todos los hoteles (no filtrar)
    const isSuperuser = user.is_superuser || false

    // Obtener hoteles del usuario
    const hotels = user.hotels || []
    const hotelIds = user.hotel_ids || []

    return {
      hotels,
      hotelIds,
      hotelIdsString: hotelIds.join(','),
      hasMultipleHotels: hotelIds.length > 1,
      hasSingleHotel: hotelIds.length === 1,
      singleHotelId: hotelIds.length === 1 ? hotelIds[0] : null,
      isSuperuser,
    }
  }, [user])
}

