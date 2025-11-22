import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Formik } from 'formik'
import * as Yup from 'yup'
import { format, differenceInCalendarDays, startOfDay, isAfter, isBefore, isSameDay } from 'date-fns'
import { es } from 'date-fns/locale'
import ModalLayout from 'src/layouts/ModalLayout'
import AlertSwal from 'src/components/AlertSwal'
import SelectAsync from 'src/components/selects/SelectAsync'
import DatePickedRange from 'src/components/DatePickedRange'
import InputText from 'src/components/inputs/InputText'
import Button from 'src/components/Button'
import Tabs from 'src/components/Tabs'
import CandelarClock from 'src/assets/icons/CandelarClock'
import WalletIcon from 'src/assets/icons/WalletIcon'
import CheckIcon from 'src/assets/icons/CheckIcon'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import { useUserHotels } from 'src/hooks/useUserHotels'
import PaymentInformationMultiRoom from 'src/components/reservations/PaymentInformationMultiRoom'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'

/**
 * MultiRoomReservationsModal
 *
 * Modal para crear reservas multi-habitación usando el endpoint
 * POST /api/reservations/multi-room/
 *
 * Estructura similar a ReservationsModal:
 * - Tab "Básico": hotel, fechas, notas y habitaciones
 * - Tab "Pago": códigos de promo/voucher + resumen estimado
 * - Tab "Revisar": resumen final antes de crear
 */

const buildGuestsDataFromRoom = (room) => {
  const guestsData = []
  if (room.guest_name) {
    guestsData.push({
      name: room.guest_name,
      email: room.guest_email || '',
      phone: room.guest_phone || '',
      document: room.guest_document || '',
      address: room.guest_address || '',
      is_primary: true,
    })
  }
  return guestsData
}

const MultiRoomReservationsModal = ({ isOpen, onClose, onSuccess, isEdit = false, groupCode, groupReservations = [] }) => {
  const { t } = useTranslation()
  const { hotelIdsString, isSuperuser } = useUserHotels()
  const [alert, setAlert] = useState({ open: false, title: '', description: '' })
  const [summaryData, setSummaryData] = useState(null)
  const [activeTab, setActiveTab] = useState('basic')
  const [dateAlertOpen, setDateAlertOpen] = useState(false)
  const [dateAlertMsg, setDateAlertMsg] = useState('')

  const { mutate: createMultiReservation, isPending: creating } = useCreate({
    resource: 'reservations/multi-room',
    onSuccess: (data) => {
      const reservations = data?.reservations || data?.data?.reservations || []
      const totalPrice = reservations.reduce((sum, res) => sum + (parseFloat(res.total_price) || 0), 0)
      const totalGuests = reservations.reduce((sum, res) => sum + (parseInt(res.guests) || 0), 0)

      setSummaryData({
        group_code: data?.group_code || data?.data?.group_code,
        reservations,
        total_price: totalPrice,
        total_guests: totalGuests,
        count: reservations.length,
      })
    },
  })

  // Función para extraer datos del huésped principal de una reserva
  const getPrimaryGuestFromReservation = (reservation) => {
    if (!reservation?.guests_data || !Array.isArray(reservation.guests_data)) {
      return {
        guest_name: reservation?.guest_name || '',
        guest_email: reservation?.guest_email || '',
        guest_phone: reservation?.guest_phone || '',
        guest_document: reservation?.guest_document || '',
        guest_address: reservation?.guest_address || '',
      }
    }
    const primaryGuest = reservation.guests_data.find(g => g.is_primary === true) || reservation.guests_data[0] || {}
    return {
      guest_name: primaryGuest.name || reservation?.guest_name || '',
      guest_email: primaryGuest.email || reservation?.guest_email || '',
      guest_phone: primaryGuest.phone || reservation?.guest_phone || '',
      guest_document: primaryGuest.document || reservation?.guest_document || '',
      guest_address: primaryGuest.address || reservation?.guest_address || '',
    }
  }

  // Construir initialValues desde groupReservations si está en modo edición
  const buildInitialValues = () => {
    if (isEdit && groupReservations && groupReservations.length > 0) {
      const firstReservation = groupReservations[0]
      return {
        hotel: firstReservation.hotel || '',
        date_range: {
          startDate: firstReservation.check_in ? firstReservation.check_in.split('T')[0] : '',
          endDate: firstReservation.check_out ? firstReservation.check_out.split('T')[0] : '',
        },
        notes: firstReservation.notes || '',
        promotion_code: firstReservation.promotion_code || '',
        voucher_code: firstReservation.voucher_code || '',
        rooms: groupReservations.map((res) => {
          const guestData = getPrimaryGuestFromReservation(res)
          return {
            room: res.room || '',
            room_data: res.room_data || null,
            guests: res.guests || 1,
            guest_name: guestData.guest_name,
            guest_email: guestData.guest_email,
            guest_phone: guestData.guest_phone,
            guest_document: guestData.guest_document,
            guest_address: guestData.guest_address,
            notes: res.notes || '',
            reservation_id: res.id, // Guardar el ID para actualizar
          }
        }),
      }
    }
    
    // Valores por defecto para creación
    return {
      hotel: '',
      date_range: {
        startDate: '',
        endDate: '',
      },
      notes: '',
      promotion_code: '',
      voucher_code: '',
      rooms: [
        {
          room: '',
          room_data: null,
          guests: 1,
          guest_name: '',
          guest_email: '',
          guest_phone: '',
          guest_document: '',
          guest_address: '',
          notes: '',
        },
      ],
    }
  }

  const initialValues = buildInitialValues()

  const validationSchema = Yup.object({
    hotel: Yup.number().required('El hotel es obligatorio'),
    date_range: Yup.object({
      startDate: Yup.date().required('El check-in es obligatorio'),
      endDate: Yup.date()
        .required('El check-out es obligatorio')
        .test('is-after-checkin', 'El check-out debe ser posterior al check-in', function (value) {
          const { startDate } = this.parent
          if (!startDate || !value) return true
          const ci = new Date(startDate)
          const co = new Date(value)
          ci.setHours(0, 0, 0, 0)
          co.setHours(0, 0, 0, 0)
          return co > ci
        }),
    }),
    rooms: Yup.array()
      .of(
        Yup.object({
          room: Yup.number().required('La habitación es obligatoria'),
          guests: Yup.number().min(1, 'Debe haber al menos 1 huésped').required('La cantidad de huéspedes es obligatoria'),
          guest_name: Yup.string().required('El nombre del huésped principal es obligatorio'),
        })
      )
      .min(1, 'Agrega al menos una habitación')
      .test('no-duplicate-rooms', 'No se puede seleccionar la misma habitación dos veces', function (rooms) {
        if (!rooms || rooms.length === 0) return true
        const roomIds = rooms.map(r => r.room).filter(Boolean)
        const uniqueIds = new Set(roomIds)
        return uniqueIds.size === roomIds.length
      }),
  })

  const formatDate = (dateString, formatStr = 'dd MMM') => {
    if (!dateString) return ''
    try {
      const date = new Date(dateString + 'T00:00:00')
      return format(date, formatStr, { locale: es })
    } catch {
      return ''
    }
  }

  const calculateStayDuration = (checkIn, checkOut) => {
    if (!checkIn || !checkOut) return 0
    try {
      const ci = new Date(checkIn + 'T00:00:00')
      const co = new Date(checkOut + 'T00:00:00')
      return differenceInCalendarDays(co, ci)
    } catch {
      return 0
    }
  }

  // Función para extraer fechas ocupadas de los datos de la habitación
  // Similar a ReservationsModal.jsx
  const getOccupiedDates = (roomData) => {
    if (!roomData) return { reservationRanges: [], occupiedNights: [], arrivalDays: [] }
    
    const reservationRanges = []
    const occupiedNights = new Set()
    const arrivalDays = new Set()
    
    // Estados que SÍ ocupan la habitación (en minúsculas como vienen del backend)
    const occupyingStatuses = ['confirmed', 'check_in', 'pending']
    
    // Función helper para agregar una reserva
    const addReservation = (checkIn, checkOut) => {
      const startDate = new Date(checkIn)
      const endDate = new Date(checkOut)
      
      // Agregar rango completo para visualización (check_in hasta check_out inclusive)
      reservationRanges.push({
        check_in: checkIn,
        check_out: checkOut,
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0]
      })
      
      // Agregar el día de check-in como "llegada"
      arrivalDays.add(startDate.toISOString().split('T')[0])
      
      // Agregar todas las noches entre check_in y check_out (SIN incluir check_out)
      // Esto permite back-to-back: si hay reserva 13→14, el 13 es "llegada" pero el 14 está libre
      let currentDate = new Date(startDate)
      while (currentDate < endDate) {
        occupiedNights.add(currentDate.toISOString().split('T')[0])
        currentDate.setDate(currentDate.getDate() + 1)
      }
    }
    
    // Agregar reserva actual si existe y está ocupando
    if (roomData.current_reservation) {
      const { check_in, check_out, status } = roomData.current_reservation
      if (check_in && check_out && occupyingStatuses.includes(status)) {
        addReservation(check_in, check_out)
      }
    }
    
    // Agregar reservas futuras que estén ocupando
    if (roomData.future_reservations && Array.isArray(roomData.future_reservations)) {
      roomData.future_reservations.forEach(reservation => {
        const { check_in, check_out, status } = reservation
        if (check_in && check_out && occupyingStatuses.includes(status)) {
          addReservation(check_in, check_out)
        }
      })
    }
    
    return {
      reservationRanges,
      occupiedNights: Array.from(occupiedNights).sort(),
      arrivalDays: Array.from(arrivalDays).sort()
    }
  }

  // Función para validar conflictos de fechas antes de enviar
  const validateDateConflict = (checkIn, checkOut, roomData) => {
    if (!checkIn || !checkOut || !roomData) return false
    
    const { occupiedNights } = getOccupiedDates(roomData)
    const occupiedSet = new Set(occupiedNights || [])
    const start = new Date(checkIn + 'T00:00:00')
    const end = new Date(checkOut + 'T00:00:00')
    const iter = new Date(start)
    
    while (iter < end) {
      const iso = format(iter, 'yyyy-MM-dd')
      if (occupiedSet.has(iso)) {
        return true // Hay conflicto
      }
      iter.setDate(iter.getDate() + 1)
    }
    return false // No hay conflicto
  }

  const handleSubmit = (values, setFieldValue) => {
    const checkIn = values.date_range?.startDate
    const checkOut = values.date_range?.endDate
    if (!checkIn || !checkOut) {
      setAlert({
        open: true,
        title: 'Fechas incompletas',
        description: 'Seleccioná un rango de fechas válido para la estadía.',
      })
      return
    }

    const validRooms = (values.rooms || []).filter((r) => r.room)
    if (!validRooms.length) {
      setAlert({
        open: true,
        title: 'Sin habitaciones',
        description: 'Agregá al menos una habitación a la reserva.',
      })
      return
    }

    // Validar conflictos de fechas para cada habitación
    const roomsWithConflicts = []
    for (const room of validRooms) {
      if (room.room_data) {
        const hasConflict = validateDateConflict(checkIn, checkOut, room.room_data)
        if (hasConflict) {
          const roomName = room.room_data?.name || room.room_data?.number || `Habitación ${room.room}`
          roomsWithConflicts.push(roomName)
        }
      }
    }

    if (roomsWithConflicts.length > 0) {
      setDateAlertMsg(
        `Las siguientes habitaciones ya tienen reservas en alguna(s) de las noches seleccionadas: ${roomsWithConflicts.join(', ')}. Por favor elegí otro rango de fechas o cambiá las habitaciones.`
      )
      setDateAlertOpen(true)
      return // No enviar la reserva
    }

    if (isEdit) {
      // Modo edición: actualizar cada reserva individualmente
      // Nota: Por ahora actualizamos cada reserva por separado
      // En el futuro se podría crear un endpoint específico para actualizar todo el grupo
      const updatePromises = validRooms.map(async (room) => {
        if (!room.reservation_id) {
          console.warn('Reserva sin ID, no se puede actualizar:', room)
          return null
        }
        
        const updatePayload = {
          hotel: values.hotel ? Number(values.hotel) : undefined,
          room: room.room ? Number(room.room) : undefined,
          guests: room.guests ? Number(room.guests) : 1,
          guests_data: buildGuestsDataFromRoom(room),
          check_in: checkIn,
          check_out: checkOut,
          notes: room.notes || values.notes || undefined,
          promotion_code: values.promotion_code || undefined,
          voucher_code: values.voucher_code || undefined,
        }
        
        try {
          const response = await fetchWithAuth(
            `${getApiURL()}/api/reservations/${room.reservation_id}/`,
            {
              method: 'PATCH',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(updatePayload),
            }
          )
          return response
        } catch (error) {
          console.error(`Error actualizando reserva ${room.reservation_id}:`, error)
          throw error
        }
      })
      
      Promise.all(updatePromises)
        .then(() => {
          onSuccess && onSuccess()
          onClose && onClose()
        })
        .catch((error) => {
          setAlert({
            open: true,
            title: 'Error al actualizar',
            description: `Hubo un error al actualizar las reservas: ${error.message || 'Error desconocido'}`,
          })
        })
    } else {
      // Modo creación: crear nuevas reservas multi-habitación
      const payload = {
        hotel: values.hotel ? Number(values.hotel) : undefined,
        check_in: checkIn,
        check_out: checkOut,
        notes: values.notes || undefined,
        promotion_code: values.promotion_code || undefined,
        voucher_code: values.voucher_code || undefined,
        rooms: validRooms.map((room) => ({
          room: room.room ? Number(room.room) : undefined,
          guests: room.guests ? Number(room.guests) : 1,
          guests_data: buildGuestsDataFromRoom(room),
          notes: room.notes || undefined,
        })),
      }

      createMultiReservation(payload)
    }
  }

  const titleNode = (values) => {
    const checkIn = values.date_range?.startDate
    const checkOut = values.date_range?.endDate
    const duration = calculateStayDuration(checkIn, checkOut)

    return (
      <div className="flex flex-col">
        <span className="text-base sm:text-lg">
          {isEdit 
            ? t('dashboard.reservations_management.edit_multi_room_title', 'Editar reserva multi-habitación')
            : t('dashboard.reservations_management.multi_room_title', 'Nueva reserva multi-habitación')}
        </span>
        {checkIn && checkOut && (
          <div className="text-xs sm:text-sm font-normal text-gray-600 mt-1">
            {`${formatDate(checkIn, 'dd/MM/yyyy')} - ${formatDate(checkOut, 'dd/MM/yyyy')} (${duration} ${
              duration === 1 ? t('reservations_modal.night', 'noche') : t('reservations_modal.nights', 'noches')
            })`}
          </div>
        )}
      </div>
    )
  }

  // Pantalla de resumen después de crear
  if (summaryData) {
    return (
      <ModalLayout
        isOpen={isOpen}
        onClose={() => {
          setSummaryData(null)
          onClose && onClose()
        }}
        title="Reserva multi-habitación creada"
        customFooter={
          <div className="flex items-center justify-end gap-2">
            <Button
              variant="primary"
              size="sm lg:size-md"
              onClick={() => {
                onSuccess && onSuccess(summaryData)
                setSummaryData(null)
                onClose && onClose()
              }}
            >
              Ver reservas
            </Button>
          </div>
        }
        size="lg2"
      >
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <h3 className="text-lg font-semibold text-green-900">
                Reserva multi-habitación creada exitosamente
              </h3>
            </div>
            <p className="text-sm text-green-800">
              Se crearon {summaryData.count} reserva(s) con el código de grupo:{' '}
              <strong>{summaryData.group_code}</strong>
            </p>
          </div>

          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 sm:p-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-4">Resumen de la reserva</h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
              <div className="text-center sm:text-left">
                <div className="text-xs text-gray-600 mb-1">Habitaciones</div>
                <div className="text-2xl font-bold text-blue-600">{summaryData.count}</div>
              </div>
              <div className="text-center sm:text-left">
                <div className="text-xs text-gray-600 mb-1">Total huéspedes</div>
                <div className="text-2xl font-bold text-blue-600">{summaryData.total_guests}</div>
              </div>
              <div className="text-center sm:text-left">
                <div className="text-xs text-gray-600 mb-1">Total de la reserva</div>
                <div className="text-2xl font-bold text-green-600">
                  {new Intl.NumberFormat('es-AR', {
                    style: 'currency',
                    currency: 'ARS',
                    minimumFractionDigits: 2,
                  }).format(summaryData.total_price)}
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-gray-700">Detalle por habitación</h4>
            {summaryData.reservations.map((res, idx) => (
              <div key={res.id || idx} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">
                      {res.room_name || `Habitación ${idx + 1}`}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      Huésped: {res.guest_name || 'Sin nombre'}
                    </div>
                    <div className="text-xs text-gray-600">
                      {res.guests || 0} huésped(es)
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-900">
                      {new Intl.NumberFormat('es-AR', {
                        style: 'currency',
                        currency: 'ARS',
                        minimumFractionDigits: 2,
                      }).format(parseFloat(res.total_price) || 0)}
                    </div>
                    <div className="text-xs text-gray-500">Reserva #{res.id}</div>
                  </div>
                </div>
                <div className="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-100">
                  {formatDate(res.check_in, 'dd MMM yyyy')} - {formatDate(res.check_out, 'dd MMM yyyy')}
                  {' • '}
                  {calculateStayDuration(res.check_in, res.check_out)}{' '}
                  {calculateStayDuration(res.check_in, res.check_out) === 1 ? 'noche' : 'noches'}
                </div>
              </div>
            ))}
          </div>
        </div>
      </ModalLayout>
    )
  }

  const tabs = [
    { id: 'basic', label: t('reservations_modal.basic_info', 'Información básica'), icon: <CandelarClock /> },
    { id: 'payment', label: t('reservations_modal.payment', 'Pago'), icon: <WalletIcon /> },
    { id: 'review', label: t('reservations_modal.review', 'Revisar'), icon: <CheckIcon /> },
  ]

  return (
    <>
      <Formik
        enableReinitialize
        initialValues={initialValues}
        validationSchema={validationSchema}
        onSubmit={handleSubmit}
      >
        {({ values, setFieldValue, errors, touched }) => {
          const nights = calculateStayDuration(values.date_range?.startDate, values.date_range?.endDate)
          const roomsSummary = {
            totalRooms: (values.rooms || []).filter((r) => r.room).length,
            totalGuests: (values.rooms || []).reduce((acc, r) => acc + (Number(r.guests) || 0), 0),
          }

          // Helpers de pasos similares a ReservationsModal.jsx
          const isBasicComplete = () => {
            const hasHotel = !!values.hotel
            const hasDates = !!(values.date_range?.startDate && values.date_range?.endDate)
            const hasRooms = (values.rooms || []).some((r) => r.room)
            return Boolean(hasHotel && hasDates && hasRooms)
          }

          const isPaymentComplete = () => {
            // Por ahora, consideramos completo pago si la info básica está completa
            return isBasicComplete()
          }

          const isReviewComplete = () => {
            return isBasicComplete()
          }

          const getStepStatus = (stepId) => {
            const currentIndex = tabs.findIndex((t) => t.id === activeTab)
            const stepIndex = tabs.findIndex((t) => t.id === stepId)

            if (stepIndex > currentIndex) {
              return false
            }

            switch (stepId) {
              case 'basic':
                return isBasicComplete()
              case 'payment':
                return isPaymentComplete()
              case 'review':
                return isReviewComplete()
              default:
                return false
            }
          }

          const canProceedToNext = () => {
            const currentIndex = tabs.findIndex((t) => t.id === activeTab)
            if (currentIndex === -1 || currentIndex >= tabs.length - 1) return false
            return getStepStatus(tabs[currentIndex].id)
          }

          const goToNextStep = () => {
            const idx = tabs.findIndex((t) => t.id === activeTab)
            if (idx < tabs.length - 1 && getStepStatus(tabs[idx].id)) {
              setActiveTab(tabs[idx + 1].id)
            }
          }

          const goToPreviousStep = () => {
            const idx = tabs.findIndex((t) => t.id === activeTab)
            if (idx > 0) setActiveTab(tabs[idx - 1].id)
          }

          const CustomFooter = () => {
            const currentIndex = tabs.findIndex((t) => t.id === activeTab)
            const isLast = currentIndex === tabs.length - 1
            const canNext = canProceedToNext()

            const handleCreate = () => {
              // Usamos el mismo handler que el submit principal
              handleSubmit(values, setFieldValue)
            }

            return (
              <div className="w-full flex flex-col gap-4">
                {/* Stepper arriba */}
                <div className="flex items-center justify-center space-x-1 sm:space-x-2">
                  {tabs.map((tab, index) => {
                    const isActive = tab.id === activeTab
                    const isCompleted = getStepStatus(tab.id)
                    const isPrevious = index < tabs.findIndex((t) => t.id === activeTab)

                    return (
                      <div
                        key={tab.id}
                        className={`flex items-center space-x-1 sm:space-x-2`}
                      >
                        <div
                          className={`w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center text-xs sm:text-sm font-semibold transition-colors ${
                            isActive
                              ? 'bg-blue-600 text-white'
                              : isCompleted && isPrevious
                              ? 'bg-green-500 text-white'
                              : 'bg-gray-200 text-gray-600'
                          }`}
                        >
                          {isCompleted && isPrevious ? '✓' : index + 1}
                        </div>
                        {index < tabs.length - 1 && (
                          <div
                            className={`w-4 sm:w-8 h-0.5 ${
                              isCompleted && isPrevious ? 'bg-green-500' : 'bg-gray-200'
                            }`}
                          />
                        )}
                      </div>
                    )
                  })}
                </div>

                {/* Botones de acción abajo */}
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Button
                      variant="danger"
                      size="sm lg:size-md"
                      onClick={onClose}
                    >
                      {t('reservations_modal.cancel', 'Cancelar')}
                    </Button>
                    {currentIndex > 0 && (
                      <Button
                        variant="secondary"
                        size="sm lg:size-md"
                        onClick={goToPreviousStep}
                      >
                        {t('reservations_modal.previous', 'Anterior')}
                      </Button>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {isLast ? (
                      <Button
                        variant="success"
                        size="sm lg:size-md"
                        onClick={handleCreate}
                        disabled={creating || !isReviewComplete()}
                      >
                        {creating
                          ? (isEdit ? t('reservations_modal.updating', 'Guardando…') : t('reservations_modal.creating', 'Creando…'))
                          : (isEdit ? t('reservations_modal.save_changes', 'Guardar cambios') : t(
                              'dashboard.reservations_management.create_multi_room_btn',
                              'Crear reserva'
                            ))}
                      </Button>
                    ) : (
                      <Button
                        variant="primary"
                        size="sm lg:size-md"
                        disabled={!canNext}
                        onClick={goToNextStep}
                      >
                        {t('reservations_modal.next', 'Siguiente')}
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            )
          }

          return (
            <ModalLayout
              isOpen={isOpen}
              onClose={onClose}
              title={titleNode(values)}
              customFooter={<CustomFooter />}
              size="lg2"
            >
              <div className="space-y-4 sm:space-y-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 sm:p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div>
                    <div className="text-xs text-blue-900/70 font-medium mb-0.5">
                      {t('dashboard.reservations_management.multi_room_summary', 'Resumen de la reserva')}
                    </div>
                    <div className="text-sm text-blue-900">
                      {roomsSummary.totalRooms > 0
                        ? `${roomsSummary.totalRooms} habitación(es), ${roomsSummary.totalGuests} huésped(es)`
                        : t('dashboard.reservations_management.multi_room_empty', 'Sin habitaciones agregadas aún')}
                    </div>
                  </div>
                  {nights > 0 && (
                    <div className="text-xs sm:text-sm text-blue-800">
                      {nights}{' '}
                      {nights === 1
                        ? t('reservations_modal.night', 'noche')
                        : t('reservations_modal.nights', 'noches')}
                    </div>
                  )}
                </div>

                <Tabs tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />

                {activeTab === 'basic' && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <SelectAsync
                          title={t('reservations_modal.hotel', 'Hotel') + ' *'}
                          name="hotel"
                          resource="hotels"
                          extraParams={!isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {}}
                          placeholder={t('common.search_placeholder', 'Buscar…')}
                          getOptionLabel={(h) => h?.name}
                          getOptionValue={(h) => h?.id}
                          value={values.hotel}
                          onChange={(option) => setFieldValue('hotel', option?.value || null)}
                          error={touched.hotel && errors.hotel}
                        />
                      </div>
                      <div className="md:col-span-2">
                        <DatePickedRange
                          label={t('reservations_modal.date_range_label', 'Fechas de estadía') + ' *'}
                          startDate={values.date_range?.startDate}
                          endDate={values.date_range?.endDate}
                          minDate={format(new Date(), 'yyyy-MM-dd')}
                          reservationsList={[]} // Para multi-habitación, no mostramos reservas en el calendario principal
                          occupiedNights={[]} // Para multi-habitación, no mostramos ocupaciones en el calendario principal
                          onChange={(startDate, endDate) => {
                            setFieldValue('date_range', { startDate, endDate })
                          }}
                          onApply={(startISO, endISO) => {
                            // Validar conflictos para todas las habitaciones seleccionadas
                            try {
                              if (!startISO || !endISO) return true
                              const start = new Date(startISO + 'T00:00:00')
                              const end = new Date(endISO + 'T00:00:00')
                              
                              const roomsWithConflicts = []
                              for (const room of values.rooms || []) {
                                if (room.room_data) {
                                  const { occupiedNights: roomOccupiedNights } = getOccupiedDates(room.room_data)
                                  const occupiedSet = new Set(roomOccupiedNights || [])
                                  const iter = new Date(start)
                                  let hasConflict = false
                                  
                                  while (iter < end) {
                                    const iso = format(iter, 'yyyy-MM-dd')
                                    if (occupiedSet.has(iso)) {
                                      hasConflict = true
                                      break
                                    }
                                    iter.setDate(iter.getDate() + 1)
                                  }
                                  
                                  if (hasConflict) {
                                    const roomName = room.room_data?.name || room.room_data?.number || `Habitación ${room.room}`
                                    roomsWithConflicts.push(roomName)
                                  }
                                }
                              }
                              
                              if (roomsWithConflicts.length > 0) {
                                setDateAlertMsg(
                                  `Las siguientes habitaciones ya tienen reservas en alguna(s) de las noches seleccionadas: ${roomsWithConflicts.join(', ')}. Por favor elegí otro rango de fechas.`
                                )
                                setDateAlertOpen(true)
                                return false // No cerrar el calendario
                              }
                            } catch (e) {
                              // Si algo falla, no bloquear
                            }
                            return true
                          }}
                          placeholder={t('reservations_modal.date_range_placeholder', 'Check-in — Check-out')}
                          inputClassName="w-full"
                          containerClassName=""
                        />
                        {touched.date_range && errors.date_range && (
                          <div className="text-xs text-red-600 mt-1">
                            {errors.date_range.startDate || errors.date_range.endDate}
                          </div>
                        )}
                        <div className="text-xs text-gray-500 mt-1">
                          💡 La primera fecha es el <strong>check-in</strong> y la segunda el <strong>check-out</strong>
                        </div>
                      </div>
                    </div>

                    <div>
                      <InputText
                        title={t('reservations_modal.notes', 'Notas generales')}
                        name="notes"
                        placeholder={t(
                          'dashboard.reservations_management.multi_room_notes_placeholder',
                          'Notas internas para la reserva (se aplican a todo el grupo)'
                        )}
                        multiline
                        rows={3}
                        value={values.notes}
                        onChange={(e) => setFieldValue('notes', e.target.value)}
                      />
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-semibold text-gray-900">
                          {t(
                            'dashboard.reservations_management.multi_room_rooms_title',
                            'Habitaciones del grupo'
                          )}
                        </h3>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => {
                            setFieldValue('rooms', [
                              ...(values.rooms || []),
                              {
                                room: '',
                                room_data: null,
                                guests: 1,
                                guest_name: '',
                                guest_email: '',
                                guest_phone: '',
                                guest_document: '',
                                guest_address: '',
                                notes: '',
                              },
                            ])
                          }}
                        >
                          {t(
                            'dashboard.reservations_management.multi_room_add_room',
                            'Agregar habitación'
                          )}
                        </Button>
                      </div>

                      {(values.rooms || []).map((room, index) => {
                        const roomErrors = errors.rooms && errors.rooms[index]
                        const roomTouched = touched.rooms && touched.rooms[index]
                        
                        // Obtener fechas ocupadas para esta habitación
                        const { occupiedNights, reservationRanges } = getOccupiedDates(room.room_data || null)
                        
                        // Preparar lista de reservas para el panel lateral del DatePickedRange
                        // (función normal, no hook, porque está dentro de un map)
                        const getReservationsList = (roomData) => {
                          if (!roomData) return []
                          
                          const list = []
                          const occupyingStatuses = ['confirmed', 'check_in', 'pending']
                          
                          // Agregar reserva actual si existe
                          if (roomData.current_reservation) {
                            const res = roomData.current_reservation
                            if (res.check_in && res.check_out && occupyingStatuses.includes(res.status)) {
                              list.push({
                                id: res.id,
                                check_in: res.check_in,
                                check_out: res.check_out,
                                guest_name: res.guest_name || null,
                                status: res.status
                              })
                            }
                          }
                          
                          // Agregar reservas futuras
                          if (roomData.future_reservations && Array.isArray(roomData.future_reservations)) {
                            roomData.future_reservations.forEach(res => {
                              if (res.check_in && res.check_out && occupyingStatuses.includes(res.status)) {
                                list.push({
                                  id: res.id,
                                  check_in: res.check_in,
                                  check_out: res.check_out,
                                  guest_name: res.guest_name || null,
                                  status: res.status
                                })
                              }
                            })
                          }
                          
                          // Ordenar por fecha de check-in
                          return list.sort((a, b) => {
                            const dateA = new Date(a.check_in)
                            const dateB = new Date(b.check_in)
                            return dateA - dateB
                          })
                        }
                        
                        const reservationsList = getReservationsList(room.room_data)
                        
                        return (
                          <div
                            key={index}
                            className="border border-gray-200 rounded-lg p-3 sm:p-4 space-y-3 bg-white"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <div className="text-sm font-medium text-gray-800">
                                {t(
                                  'dashboard.reservations_management.multi_room_room_label',
                                  'Habitación'
                                )}{' '}
                                #{index + 1}
                              </div>
                              {values.rooms.length > 1 && (
                                <button
                                  type="button"
                                  className="text-xs text-red-600 hover:underline"
                                  onClick={() => {
                                    const next = [...values.rooms]
                                    next.splice(index, 1)
                                    setFieldValue('rooms', next)
                                  }}
                                >
                                  {t('common.remove', 'Quitar')}
                                </button>
                              )}
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                              <div>
                                <SelectAsync
                                  title={t('reservations_modal.room', 'Habitación') + ' *'}
                                  name={`rooms[${index}].room`}
                                  resource="rooms"
                                  placeholder={
                                    !values.hotel
                                      ? t(
                                          'reservations_modal.room_placeholder_no_hotel',
                                          'Seleccioná un hotel primero'
                                        )
                                      : t(
                                          'reservations_modal.room_placeholder_loading',
                                          'Seleccioná una habitación'
                                        )
                                  }
                                  getOptionLabel={(r) =>
                                    r?.name || t('reservations_modal.room_name', { id: r?.id })
                                  }
                                  getOptionValue={(r) => r?.id}
                                  extraParams={{
                                    hotel: values.hotel || undefined,
                                  }}
                                  value={room.room}
                                  onValueChange={(option, value) => {
                                    const next = [...values.rooms]
                                    
                                    // Verificar si la habitación ya está seleccionada en otra entrada
                                    const roomId = value || option?.id
                                    if (roomId) {
                                      const isDuplicate = next.some((r, idx) => 
                                        idx !== index && r.room && Number(r.room) === Number(roomId)
                                      )
                                      
                                      if (isDuplicate) {
                                        setAlert({
                                          open: true,
                                          title: 'Habitación duplicada',
                                          description: 'Esta habitación ya está seleccionada en otra entrada del grupo. Por favor elegí una habitación diferente.',
                                        })
                                        return // No actualizar si es duplicada
                                      }
                                    }
                                    
                                    // Guardar tanto el ID como los datos completos de la habitación
                                    // option es el objeto completo de la habitación (con current_reservation, future_reservations, etc.)
                                    next[index].room = value || option?.id || ''
                                    next[index].room_data = option || null
                                    setFieldValue('rooms', next)
                                  }}
                                  error={roomTouched?.room && roomErrors?.room}
                                  disabled={!values.hotel}
                                />
                                {/* Error de habitación duplicada */}
                                {errors.rooms === 'No se puede seleccionar la misma habitación dos veces' && (
                                  <div className="text-xs text-red-600 mt-1">
                                    ⚠️ Esta habitación ya está seleccionada en otra entrada del grupo
                                  </div>
                                )}
                                {room.room_data && occupiedNights.length > 0 && (
                                  <div className="text-xs text-red-600 mt-1">
                                    🚫 {occupiedNights.length} noche(s) ocupada(s) en esta habitación
                                  </div>
                                )}
                              </div>
                              <div>
                                <InputText
                                  title={t(
                                    'reservations_modal.guests_number',
                                    'Cantidad de huéspedes'
                                  )}
                                  name={`rooms[${index}].guests`}
                                  type="number"
                                  min="1"
                                  placeholder="Ej: 2"
                                  value={room.guests}
                                  onChange={(e) => {
                                    const val = Number(e.target.value || '1')
                                    const next = [...values.rooms]
                                    next[index].guests = val
                                    setFieldValue('rooms', next)
                                  }}
                                  error={roomTouched?.guests && roomErrors?.guests}
                                />
                              </div>
                              <div>
                                <InputText
                                  title={t(
                                    'reservations_modal.guest_name',
                                    'Huésped principal'
                                  )}
                                  name={`rooms[${index}].guest_name`}
                                  placeholder="Nombre y apellido"
                                  value={room.guest_name}
                                  onChange={(e) => {
                                    const next = [...values.rooms]
                                    next[index].guest_name = e.target.value
                                    setFieldValue('rooms', next)
                                  }}
                                  error={roomTouched?.guest_name && roomErrors?.guest_name}
                                />
                              </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                              <div>
                                <InputText
                                  title={t('reservations_modal.guest_email', 'Email')}
                                  name={`rooms[${index}].guest_email`}
                                  type="email"
                                  placeholder="email@ejemplo.com"
                                  value={room.guest_email}
                                  onChange={(e) => {
                                    const next = [...values.rooms]
                                    next[index].guest_email = e.target.value
                                    setFieldValue('rooms', next)
                                  }}
                                />
                              </div>
                              <div>
                                <InputText
                                  title={t('reservations_modal.guest_phone', 'Teléfono')}
                                  name={`rooms[${index}].guest_phone`}
                                  placeholder="+54 9 ..."
                                  value={room.guest_phone}
                                  onChange={(e) => {
                                    const next = [...values.rooms]
                                    next[index].guest_phone = e.target.value
                                    setFieldValue('rooms', next)
                                  }}
                                />
                              </div>
                              <div>
                                <InputText
                                  title={t('reservations_modal.guest_document', 'Documento')}
                                  name={`rooms[${index}].guest_document`}
                                  placeholder="DNI / Pasaporte"
                                  value={room.guest_document}
                                  onChange={(e) => {
                                    const next = [...values.rooms]
                                    next[index].guest_document = e.target.value
                                    setFieldValue('rooms', next)
                                  }}
                                />
                              </div>
                            </div>

                            <div>
                              <InputText
                                title={t('reservations_modal.notes', 'Notas para la habitación')}
                                name={`rooms[${index}].notes`}
                                placeholder={t(
                                  'dashboard.reservations_management.multi_room_room_notes_placeholder',
                                  'Notas internas específicas para esta habitación'
                                )}
                                multiline
                                rows={2}
                                value={room.notes}
                                onChange={(e) => {
                                  const next = [...values.rooms]
                                  next[index].notes = e.target.value
                                  setFieldValue('rooms', next)
                                }}
                              />
                            </div>
                          </div>
                        )
                      })}

                      {touched.rooms && typeof errors.rooms === 'string' && (
                        <div className="text-xs text-red-600">{errors.rooms}</div>
                      )}
                    </div>
                  </div>
                )}

                {activeTab === 'payment' && <PaymentInformationMultiRoom />}

                {activeTab === 'review' && (
                  <div className="space-y-4">
                    <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-xl border border-green-200">
                      <h3 className="text-xl font-bold text-green-900 mb-4">Resumen de la reserva</h3>
                      <div className="space-y-4">
                        <div>
                          <p className="text-sm text-gray-600">Hotel</p>
                          <p className="font-medium">
                            {values.hotel ? `Hotel ID: ${values.hotel}` : 'No seleccionado'}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Fechas</p>
                          <p className="font-medium">
                            {values.date_range?.startDate && values.date_range?.endDate
                              ? `${formatDate(
                                  values.date_range.startDate,
                                  'dd/MM/yyyy'
                                )} - ${formatDate(
                                  values.date_range.endDate,
                                  'dd/MM/yyyy'
                                )} (${nights} ${nights === 1 ? 'noche' : 'noches'})`
                              : 'No seleccionadas'}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Habitaciones</p>
                          <p className="font-medium">
                            {roomsSummary.totalRooms} habitación(es), {roomsSummary.totalGuests} huésped(es)
                          </p>
                        </div>
                        {values.notes && (
                          <div>
                            <p className="text-sm text-gray-600">Notas</p>
                            <p className="font-medium">{values.notes}</p>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <h4 className="font-semibold text-gray-900 mb-3">Habitaciones del grupo</h4>
                      <div className="space-y-3">
                        {(values.rooms || [])
                          .filter((r) => r.room)
                          .map((room, idx) => {
                            const roomData = typeof room.room === 'object' ? room.room : null
                            return (
                              <div key={idx} className="border border-gray-200 rounded-lg p-3">
                                <div className="font-medium text-gray-900 mb-2">
                                  {roomData?.name || `Habitación ${idx + 1}`}
                                </div>
                                <div className="text-sm text-gray-600 space-y-1">
                                  <p>Huéspedes: {room.guests}</p>
                                  <p>Huésped principal: {room.guest_name || 'Sin nombre'}</p>
                                  {room.guest_email && <p>Email: {room.guest_email}</p>}
                                  {room.guest_phone && <p>Teléfono: {room.guest_phone}</p>}
                                  {room.notes && (
                                    <p className="text-xs text-gray-500">Notas: {room.notes}</p>
                                  )}
                                </div>
                              </div>
                            )
                          })}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ModalLayout>
          )
        }}
      </Formik>

      <AlertSwal
        isOpen={alert.open}
        onClose={() => setAlert((prev) => ({ ...prev, open: false }))}
        onConfirm={() => setAlert((prev) => ({ ...prev, open: false }))}
        title={alert.title || 'Error'}
        description={alert.description || 'Revisá los datos ingresados.'}
        confirmText="Entendido"
        cancelText=""
        tone="warning"
      />
      <AlertSwal
        isOpen={dateAlertOpen}
        onClose={() => setDateAlertOpen(false)}
        onConfirm={() => setDateAlertOpen(false)}
        title="Rango no disponible"
        description={dateAlertMsg || 'Las fechas seleccionadas se superponen con reservas existentes en alguna de las habitaciones.'}
        confirmText="Entendido"
        cancelText="Cerrar"
        tone="warning"
      />
    </>
  )
}

export default MultiRoomReservationsModal


