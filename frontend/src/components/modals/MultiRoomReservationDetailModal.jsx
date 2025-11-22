import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import Badge from 'src/components/Badge'
import { format, parseISO, differenceInCalendarDays } from 'date-fns'
import { es } from 'date-fns/locale'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import { getStatusLabel } from 'src/pages/utils'

/**
 * MultiRoomReservationDetailModal
 * 
 * Modal de detalle para reservas multi-habitación.
 * Muestra información completa del grupo de reservas, incluyendo:
 * - Resumen general (hotel, fechas, total)
 * - Lista detallada de cada habitación con sus huéspedes
 * - Totales agregados
 */
const MultiRoomReservationDetailModal = ({ isOpen, onClose, groupCode, groupReservations }) => {
  const { t } = useTranslation()
  const [reservations, setReservations] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!isOpen || !groupCode) return

    const loadReservations = async () => {
      setLoading(true)
      setError(null)
      try {
        const base = getApiURL() || ''
        // Si ya tenemos las reservas pasadas como prop, usarlas
        if (groupReservations && Array.isArray(groupReservations) && groupReservations.length > 0) {
          setReservations(groupReservations)
        } else {
          // Si no, buscar por group_code
          const response = await fetchWithAuth(`${base}/api/reservations/?group_code=${groupCode}`, {
            method: 'GET'
          })
          const results = response.results || response || []
          setReservations(results)
        }
      } catch (err) {
        setError(err.message || 'Error cargando reservas')
        console.error('Error loading multi-room reservations:', err)
      } finally {
        setLoading(false)
      }
    }

    loadReservations()
  }, [isOpen, groupCode, groupReservations])

  const formatDate = (dateString, formatStr = 'dd/MM/yyyy') => {
    if (!dateString) return '-'
    try {
      const date = dateString.includes('T') ? parseISO(dateString) : new Date(dateString + 'T00:00:00')
      return format(date, formatStr, { locale: es })
    } catch {
      return dateString
    }
  }

  const formatCurrency = (amount) => {
    if (!amount) return '$0.00'
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount)
  }

  const calculateStayDuration = (checkIn, checkOut) => {
    if (!checkIn || !checkOut) return 0
    try {
      const ci = checkIn.includes('T') ? parseISO(checkIn) : new Date(checkIn + 'T00:00:00')
      const co = checkOut.includes('T') ? parseISO(checkOut) : new Date(checkOut + 'T00:00:00')
      return differenceInCalendarDays(co, ci)
    } catch {
      return 0
    }
  }

  if (!isOpen) return null

  // Calcular totales
  const totalPrice = reservations.reduce((sum, r) => sum + (parseFloat(r.total_price) || 0), 0)
  const totalGuests = reservations.reduce((sum, r) => sum + (parseInt(r.guests) || 0), 0)
  const firstReservation = reservations[0] || {}
  const checkIn = firstReservation.check_in
  const checkOut = firstReservation.check_out
  const nights = calculateStayDuration(checkIn, checkOut)

  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={onClose}
      title={`Reserva Multi-habitación ${groupCode ? `· Grupo ${groupCode}` : ''}`}
      size="lg2"
    >
      <div className="space-y-6">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">{t('common.loading', 'Cargando...')}</span>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {!loading && !error && reservations.length > 0 && (
          <>
            {/* Resumen general */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Resumen de la reserva
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">Hotel</label>
                  <p className="text-lg font-semibold text-gray-900 mt-1">
                    {firstReservation.hotel_name || '-'}
                  </p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-600">Código de grupo</label>
                  <p className="text-lg font-semibold text-gray-900 mt-1 font-mono">
                    {groupCode || '-'}
                  </p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-600">Check-in</label>
                  <p className="text-lg font-semibold text-gray-900 mt-1">
                    {formatDate(checkIn, 'EEEE, dd MMM yyyy')}
                  </p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-600">Check-out</label>
                  <p className="text-lg font-semibold text-gray-900 mt-1">
                    {formatDate(checkOut, 'EEEE, dd MMM yyyy')}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4 border-t border-blue-200">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{reservations.length}</div>
                  <div className="text-sm text-gray-600">Habitaciones</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{totalGuests}</div>
                  <div className="text-sm text-gray-600">Huéspedes</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{nights}</div>
                  <div className="text-sm text-gray-600">{nights === 1 ? 'Noche' : 'Noches'}</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{formatCurrency(totalPrice)}</div>
                  <div className="text-sm text-gray-600">Total</div>
                </div>
              </div>
            </div>

            {/* Estado general */}
            {firstReservation.status && (
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700">Estado general:</label>
                <Badge variant={`reservation-${firstReservation.status}`} size="md">
                  {getStatusLabel(firstReservation.status, t)}
                </Badge>
              </div>
            )}

            {/* Detalle por habitación */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Habitaciones ({reservations.length})
              </h3>
              
              <div className="space-y-4">
                {reservations.map((reservation, index) => {
                  const primaryGuest = reservation.guests_data?.find(g => g.is_primary) || reservation.guests_data?.[0] || {}
                  const otherGuests = reservation.guests_data?.filter(g => !g.is_primary) || []
                  
                  return (
                    <div
                      key={reservation.id || index}
                      className="bg-white border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                              <span className="text-blue-600 font-bold text-lg">#{index + 1}</span>
                            </div>
                            <div>
                              <h4 className="text-lg font-semibold text-gray-900">
                                {reservation.room_name || `Habitación ${index + 1}`}
                              </h4>
                              <p className="text-sm text-gray-600">
                                Reserva #{reservation.id}
                              </p>
                            </div>
                          </div>
                        </div>
                        
                        <div className="text-right">
                          <div className="text-xl font-bold text-gray-900 mb-1">
                            {formatCurrency(reservation.total_price)}
                          </div>
                          <Badge variant={`reservation-${reservation.status}`} size="sm">
                            {getStatusLabel(reservation.status, t)}
                          </Badge>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <label className="text-xs font-medium text-gray-500">Huéspedes</label>
                          <p className="text-sm text-gray-900 mt-1">
                            {reservation.guests || 0} {reservation.guests === 1 ? 'huésped' : 'huéspedes'}
                          </p>
                        </div>
                        
                        <div>
                          <label className="text-xs font-medium text-gray-500">Duración</label>
                          <p className="text-sm text-gray-900 mt-1">
                            {calculateStayDuration(reservation.check_in, reservation.check_out)} {calculateStayDuration(reservation.check_in, reservation.check_out) === 1 ? 'noche' : 'noches'}
                          </p>
                        </div>
                      </div>

                      {/* Huésped principal */}
                      {primaryGuest.name && (
                        <div className="bg-gray-50 rounded-lg p-3 mb-3">
                          <label className="text-xs font-medium text-gray-500 mb-1 block">
                            Huésped principal
                          </label>
                          <div className="space-y-1">
                            <p className="text-sm font-semibold text-gray-900">{primaryGuest.name}</p>
                            {primaryGuest.email && (
                              <p className="text-xs text-gray-600">{primaryGuest.email}</p>
                            )}
                            {primaryGuest.phone && (
                              <p className="text-xs text-gray-600">{primaryGuest.phone}</p>
                            )}
                            {primaryGuest.document && (
                              <p className="text-xs text-gray-600">Doc: {primaryGuest.document}</p>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Otros huéspedes */}
                      {otherGuests.length > 0 && (
                        <div className="bg-gray-50 rounded-lg p-3">
                          <label className="text-xs font-medium text-gray-500 mb-2 block">
                            Otros huéspedes ({otherGuests.length})
                          </label>
                          <div className="space-y-2">
                            {otherGuests.map((guest, gIdx) => (
                              <div key={gIdx} className="border-l-2 border-blue-200 pl-2">
                                <p className="text-sm font-medium text-gray-900">{guest.name}</p>
                                {guest.email && (
                                  <p className="text-xs text-gray-600">{guest.email}</p>
                                )}
                                {guest.document && (
                                  <p className="text-xs text-gray-600">Doc: {guest.document}</p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Notas de la habitación */}
                      {reservation.notes && (
                        <div className="mt-3 pt-3 border-t border-gray-100">
                          <label className="text-xs font-medium text-gray-500">Notas</label>
                          <p className="text-sm text-gray-700 mt-1 whitespace-pre-wrap">{reservation.notes}</p>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Notas generales */}
            {firstReservation.notes && (
              <div className="bg-gray-50 rounded-lg p-4">
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  Notas generales
                </label>
                <p className="text-sm text-gray-900 whitespace-pre-wrap">{firstReservation.notes}</p>
              </div>
            )}
          </>
        )}

        {!loading && !error && reservations.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h4 className="text-lg font-medium text-gray-900 mb-2">
              No se encontraron reservas
            </h4>
            <p className="text-gray-600">
              No se pudieron cargar las reservas del grupo.
            </p>
          </div>
        )}
      </div>
    </ModalLayout>
  )
}

export default MultiRoomReservationDetailModal

