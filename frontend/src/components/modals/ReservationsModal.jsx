import { Formik } from 'formik'
import * as Yup from 'yup'
import { useEffect, useState, useRef, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { format, parseISO, isValid, startOfDay, isAfter, isBefore, isSameDay, subDays, addDays } from 'date-fns'
import { es } from 'date-fns/locale'
import ModalLayout from 'src/layouts/ModalLayout'
import AlertSwal from 'src/components/AlertSwal'
import InputText from 'src/components/inputs/InputText'
import LabelsContainer from 'src/components/inputs/LabelsContainer'
import SelectAsync from 'src/components/selects/SelectAsync'
import DatePickedRange from 'src/components/DatePickedRange'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import Tabs from 'src/components/Tabs'
import CancelIcon from 'src/assets/icons/CancelIcon'
import PeopleIcon from 'src/assets/icons/PeopleIcon'
import WalletIcon from 'src/assets/icons/WalletIcon'
import CheckCircleIcon from 'src/assets/icons/CheckCircleIcon'
import CandelarClock from 'src/assets/icons/CandelarClock'
import CheckIcon from 'src/assets/icons/CheckIcon'
import Button from 'src/components/Button'
import GuestInformation from '../reservations/GuestInformation'
import PaymentInformation from '../reservations/PaymentInformation'
import ReviewReservation from '../reservations/ReviewReservation'
import { useMe } from 'src/hooks/useMe'
import { useUserHotels } from 'src/hooks/useUserHotels'
import PaymentModal from 'src/components/modals/PaymentModal'

/**
 * ReservationsModal: crear/editar reserva
 * Props:
 * - isOpen: boolean
 * - onClose: () => void
 * - isEdit?: boolean
 * - reservation?: objeto reserva existente (para editar)
 * - onSuccess?: (data) => void (se llama al crear/editar OK)
 * - initialData?: objeto con datos iniciales (ej: { check_in: '2025-01-15', check_out: '2025-01-17' })
 */
const ReservationsModal = ({ isOpen, onClose, onSuccess, isEdit = false, reservation, initialData, lockHotel = false, lockRoom = false }) => {
  const { t } = useTranslation()
  const [modalKey, setModalKey] = useState(0)
  const [activeTab, setActiveTab] = useState('basic')
  const formikRef = useRef(null)
  
  // Hook para obtener hoteles del usuario logueado
  const { hotelIdsString, isSuperuser } = useUserHotels()
  const [payOpen, setPayOpen] = useState(false)
  const [payInfo, setPayInfo] = useState(null)
  const roomNameCollator = useMemo(() => new Intl.Collator('es', { numeric: true, sensitivity: 'base' }), [])

  const getRoomDisplayName = (room) => {
    return (
      room?.name ??
      room?.number ??
      room?.room_number ??
      room?.code ??
      (room?.id != null ? t('reservations_modal.room_name', { id: room.id }) : '')
    )
  }

  const getRoomTypeLabel = (room) => {
    return (
      room?.room_type_alias ??
      room?.room_type_name ??
      room?.room_type_display ??
      room?.room_type?.name ??
      room?.room_type ??
      room?.type?.name ??
      room?.type
    )
  }

  const getRoomOptionLabel = (room) => {
    const name = getRoomDisplayName(room)
    const type = getRoomTypeLabel(room)
    if (name && type) return `${name} - ${type}`
    return name || (room?.id != null ? t('reservations_modal.room_name', { id: room.id }) : '')
  }

  // Función helper para formatear fechas correctamente
  const formatDate = (dateString, formatStr = 'dd MMM') => {
    if (!dateString) return ''
    try {
      // Si es una fecha en formato ISO, usar parseISO
      if (dateString.includes('T') || dateString.includes('Z')) {
        const parsed = parseISO(dateString)
        return isValid(parsed) ? format(parsed, formatStr, { locale: es }) : ''
      }
      // Si es una fecha en formato YYYY-MM-DD, crear Date directamente
      const date = new Date(dateString + 'T00:00:00')
      return isValid(date) ? format(date, formatStr, { locale: es }) : ''
    } catch (error) {
      return ''
    }
  }

  // Función para calcular duración de estadía
  const calculateStayDuration = (checkIn, checkOut) => {
    if (!checkIn || !checkOut) return 0
    try {
      const checkInDate = checkIn.includes('T') ? parseISO(checkIn) : new Date(checkIn + 'T00:00:00')
      const checkOutDate = checkOut.includes('T') ? parseISO(checkOut) : new Date(checkOut + 'T00:00:00')
      
      if (!isValid(checkInDate) || !isValid(checkOutDate)) return 0
      
      const diffTime = checkOutDate - checkInDate
      return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    } catch (error) {
      return 0
    }
  }

  // Función para extraer fechas ocupadas de los datos de la habitación
  // Retorna: { reservationRanges: [], occupiedNights: [], arrivalDays: [] }
  // - reservationRanges: rangos completos de reservas [check_in, check_out] para visualización
  // - occupiedNights: noches ocupadas (check_in hasta check_out, sin incluir check_out) para lógica
  // - arrivalDays: días que son check-in de reservas existentes (para permitir back-to-back)
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

  const { mutate: createReservation, isPending: creating } = useCreate({
    resource: 'reservations',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
    onError: (error) => {
      // Si el error está relacionado con fechas, limpiar el input
      const errorMsg = error?.message || ''
      if (errorMsg.toLowerCase().includes('fecha') || 
          errorMsg.toLowerCase().includes('reserva') || 
          errorMsg.toLowerCase().includes('ocupada') ||
          errorMsg.toLowerCase().includes('conflicto')) {
        if (formikRef.current) {
          const { setFieldValue } = formikRef.current
          setFieldValue('date_range', { startDate: '', endDate: '' })
          setFieldValue('check_in', '')
          setFieldValue('check_out', '')
        }
      }
    },
  })

  const { mutate: updateReservation, isPending: updating } = useUpdate({
    resource: 'reservations',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
    onError: (error) => {
      // Si el error está relacionado con fechas, limpiar el input
      const errorMsg = error?.message || ''
      if (errorMsg.toLowerCase().includes('fecha') || 
          errorMsg.toLowerCase().includes('reserva') || 
          errorMsg.toLowerCase().includes('ocupada') ||
          errorMsg.toLowerCase().includes('conflicto')) {
        if (formikRef.current) {
          const { setFieldValue } = formikRef.current
          setFieldValue('date_range', { startDate: '', endDate: '' })
          setFieldValue('check_in', '')
          setFieldValue('check_out', '')
        }
      }
    },
  })

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

  // Función para extraer datos del huésped principal
  const getPrimaryGuestData = (reservation) => {
    if (!reservation?.guests_data || !Array.isArray(reservation.guests_data)) {
      return {
        guest_name: '',
        guest_email: '',
        guest_phone: '',
        guest_document: '',
        contact_address: ''
      }
    }

    const primaryGuest = reservation.guests_data.find(guest => guest.is_primary === true)
    if (!primaryGuest) {
      // Si no hay huésped principal marcado, tomar el primero
      const firstGuest = reservation.guests_data[0] || {}
      return {
        guest_name: firstGuest.name || '',
        guest_email: firstGuest.email || '',
        guest_phone: firstGuest.phone || '',
        guest_document: firstGuest.document || '',
        contact_address: firstGuest.address || ''
      }
    }

    return {
      guest_name: primaryGuest.name || '',
      guest_email: primaryGuest.email || '',
      guest_phone: primaryGuest.phone || '',
      guest_document: primaryGuest.document || '',
      contact_address: primaryGuest.address || ''
    }
  }

  // Función para extraer otros huéspedes
  const getOtherGuestsData = (reservation) => {
    if (!reservation?.guests_data || !Array.isArray(reservation.guests_data)) {
      return []
    }

    return reservation.guests_data
      .filter(guest => guest.is_primary !== true)
      .map(guest => ({
        name: guest.name || '',
        email: guest.email || '',
        phone: guest.phone || '',
        document: guest.document || '',
        address: guest.address || ''
      }))
  }

  const primaryGuestData = getPrimaryGuestData(reservation)
  const otherGuestsData = getOtherGuestsData(reservation)

  const initialValues = {
    hotel: reservation?.hotel ?? '',
    ...primaryGuestData,
    guests: reservation?.guests ?? 1,
    other_guests: otherGuestsData,
    // Campos individuales para compatibilidad
    check_in: reservation?.check_in ? reservation.check_in.split('T')[0] : (initialData?.check_in ?? ''),
    check_out: reservation?.check_out ? reservation.check_out.split('T')[0] : (initialData?.check_out ?? ''),
    // Campo unificado para el rango de fechas
    date_range: {
      startDate: reservation?.check_in ? reservation.check_in.split('T')[0] : (initialData?.check_in ?? ''),
      endDate: reservation?.check_out ? reservation.check_out.split('T')[0] : (initialData?.check_out ?? ''),
    },
    room: reservation?.room ?? '',
    room_data: reservation?.room_data ?? null, // Información completa de la habitación
    status: reservation?.status ?? 'pending',
    notes: reservation?.notes ?? '',
    // Canal siempre DIRECT para reservas creadas desde el sistema
    // Si la reserva tiene external_id (viene de OTA), el backend lo maneja automáticamente
    channel: reservation?.external_id ? reservation?.channel ?? 'direct' : 'direct',
    promotion_code: reservation?.promotion_code ?? '',
    voucher_code: reservation?.voucher_code ?? '',
    price_source: reservation?.price_source ?? 'primary',
  }

  // Reset modal key when opening for creation
  useEffect(() => {
    if (isOpen && !isEdit) {
      setModalKey(prev => prev + 1)
    }
  }, [isOpen, isEdit])

  // Limpiar selección de habitación cuando cambie el hotel
  useEffect(() => {
    if (formikRef.current) {
      const { values, setFieldValue } = formikRef.current

      // Si cambió el hotel, limpiar habitación
      if (values.hotel !== (reservation?.hotel ?? '')) {
        setFieldValue('room', '')
        setFieldValue('room_data', null)
      }
    }
  }, [reservation?.hotel])

  // Estado para rastrear el número de huéspedes anterior
  const [previousGuests, setPreviousGuests] = useState(null)
  const [dateAlertOpen, setDateAlertOpen] = useState(false)
  const [dateAlertMsg, setDateAlertMsg] = useState('')

  const validationSchema = Yup.object({
    hotel: Yup.number().required(t('reservations_modal.hotel_required')),
    guests: Yup.number()
      .min(1, t('reservations_modal.guests_min'))
      .test('max-capacity', t('reservations_modal.guests_max_capacity'), function (value) {
        const roomData = this.parent.room_data
        if (roomData && value > roomData.max_capacity) {
          return this.createError({
            message: t('reservations_modal.guests_max_capacity_msg', { max: roomData.max_capacity })
          })
        }
        return true
      })
      .required(t('reservations_modal.guests_required')),
    // Validación del rango de fechas
    date_range: Yup.object({
      startDate: Yup.date()
        .required(t('reservations_modal.check_in_required'))
        .test('not-before-today', t('reservations_modal.check_in_not_before_today'), function (value) {
          if (!value) return true
          const today = startOfDay(new Date())
          const checkInDate = startOfDay(new Date(value))
          
          // Permitir fechas de hoy en adelante (no bloquear hoy)
          return isAfter(checkInDate, today) || isSameDay(checkInDate, today)
        }),
      endDate: Yup.date()
        .required(t('reservations_modal.check_out_required'))
        .test('is-after-checkin', t('reservations_modal.check_out_after_checkin'), function (value) {
          const { startDate } = this.parent
          if (!startDate || !value) return true
          
          const checkInDate = new Date(startDate)
          const checkOutDate = new Date(value)
          
          // Establecer ambas fechas a medianoche para comparar solo la fecha
          checkInDate.setHours(0, 0, 0, 0)
          checkOutDate.setHours(0, 0, 0, 0)
          
          return checkOutDate > checkInDate
        })
        .test('min-stay', t('reservations_modal.min_stay'), function (value) {
          const { startDate } = this.parent
          if (!startDate || !value) return true
          
          const checkInDate = new Date(startDate)
          const checkOutDate = new Date(value)
          
          // Establecer ambas fechas a medianoche para comparar solo la fecha
          checkInDate.setHours(0, 0, 0, 0)
          checkOutDate.setHours(0, 0, 0, 0)
          
          const diffTime = checkOutDate - checkInDate
          const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
          return diffDays >= 1
        }),
    }),
    // Mantener validaciones individuales para compatibilidad
    check_in: Yup.date()
      .required(t('reservations_modal.check_in_required'))
      .test('not-before-today', t('reservations_modal.check_in_not_before_today'), function (value) {
        if (!value) return true
        const today = startOfDay(new Date())
        const checkInDate = startOfDay(new Date(value))
        
        // Permitir fechas de hoy en adelante (no bloquear hoy)
        return isAfter(checkInDate, today) || isSameDay(checkInDate, today)
      }),
    check_out: Yup.date()
      .required(t('reservations_modal.check_out_required'))
      .test('is-after-checkin', t('reservations_modal.check_out_after_checkin'), function (value) {
        const { check_in } = this.parent
        if (!check_in || !value) return true
        
        const checkInDate = new Date(check_in)
        const checkOutDate = new Date(value)
        
        // Establecer ambas fechas a medianoche para comparar solo la fecha
        checkInDate.setHours(0, 0, 0, 0)
        checkOutDate.setHours(0, 0, 0, 0)
        
        return checkOutDate > checkInDate
      })
      .test('min-stay', t('reservations_modal.min_stay'), function (value) {
        const { check_in } = this.parent
        if (!check_in || !value) return true
        
        const checkInDate = new Date(check_in)
        const checkOutDate = new Date(value)
        
        // Establecer ambas fechas a medianoche para comparar solo la fecha
        checkInDate.setHours(0, 0, 0, 0)
        checkOutDate.setHours(0, 0, 0, 0)
        
        const diffTime = checkOutDate - checkInDate
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
        return diffDays >= 1
      }),
    room: Yup.number().required(t('reservations_modal.room_required')),
    // Validación del huésped principal
    guest_name: Yup.string()
      .trim()
      .min(2, t('reservations_modal.guest_name_required'))
      .matches(/^[\p{L}\p{M}.'\- ]+$/u, t('reservations_modal.guest_name_required'))
      .required(t('reservations_modal.guest_name_required')),
    guest_email: Yup.string().email(t('reservations_modal.guest_email_invalid')).required(t('reservations_modal.guest_email_required')),
    guest_phone: Yup.string()
      .trim()
      .matches(/^[0-9()+\-.\s]{6,20}$/, t('reservations_modal.guest_phone_required'))
      .required(t('reservations_modal.guest_phone_required')),
    guest_document: Yup.string()
      .trim()
      .matches(/^\d{6,15}$/, t('reservations_modal.guest_document_required'))
      .required(t('reservations_modal.guest_document_required')),
    contact_address: Yup.string()
      .trim()
      .min(5, t('reservations_modal.contact_address_required'))
      .required(t('reservations_modal.contact_address_required')),
    // Validación de otros huéspedes
    other_guests: Yup.array().of(
      Yup.object({
        name: Yup.string()
          .trim()
          .min(2, t('reservations_modal.other_guests_name_required'))
          .matches(/^[\p{L}\p{M}.'\- ]+$/u, t('reservations_modal.other_guests_name_required'))
          .required(t('reservations_modal.other_guests_name_required')),
        document: Yup.string()
          .trim()
          .matches(/^\d{6,15}$/, t('reservations_modal.other_guests_document_required'))
          .required(t('reservations_modal.other_guests_document_required')),
        email: Yup.string().email(t('reservations_modal.other_guests_email_invalid')).required(t('reservations_modal.other_guests_email_required')),
        phone: Yup.string()
          .trim()
          .matches(/^[0-9()+\-.\s]{6,20}$/, t('reservations_modal.other_guests_phone_required'))
          .required(t('reservations_modal.other_guests_phone_required')),
        address: Yup.string()
          .trim()
          .min(5, t('reservations_modal.other_guests_address_required'))
          .required(t('reservations_modal.other_guests_address_required')),
      })
    ),
  })

  // Función para verificar si hay reservas existentes en la habitación
  const hasExistingReservations = (roomData) => {
    if (!roomData) return false
    return !!(roomData.current_reservation || (roomData.future_reservations && roomData.future_reservations.length > 0))
  }

  // Tabs dinámicos basados en si hay reservas existentes
  const getTabs = () => {
    const baseTabs = [
      { id: 'basic', label: t('reservations_modal.basic_info'), icon: <CandelarClock /> },
      { id: 'guests', label: t('reservations_modal.guests'), icon: <PeopleIcon /> },
      { id: 'payment', label: t('reservations_modal.payment'), icon: <WalletIcon /> },
      { id: 'review', label: t('reservations_modal.review'), icon: <CheckIcon /> }
    ]

    // Si hay reservas existentes, agregar el tab de reservas al inicio
    if (hasExistingReservations(reservation?.room_data)) {
      return [
        { id: 'existing', label: 'Reservas Existentes', icon: <CheckCircleIcon /> },
        ...baseTabs
      ]
    }

    return baseTabs
  }

  const tabs = getTabs()

  // Helpers de pasos
  const getEffectiveGuests = (vals) => {
    const raw = vals?.guests
    if (raw === 0) return 0
    if (raw === '' || raw === null || raw === undefined) return 1
    const num = Number(raw)
    return Number.isNaN(num) ? 1 : num
  }

  const hasDatesSelected = (vals) => {
    const checkIn = vals?.date_range?.startDate || vals?.check_in
    const checkOut = vals?.date_range?.endDate || vals?.check_out
    return Boolean(checkIn && checkOut)
  }

  const isBasicComplete = () => {
    const { values } = formikRef.current || { values: {} }
    const effGuests = getEffectiveGuests(values)
    // Verificar tanto el rango de fechas como los campos individuales para compatibilidad
    const hasDateRange = values?.date_range?.startDate && values?.date_range?.endDate
    const hasIndividualDates = values?.check_in && values?.check_out
    return Boolean(values?.hotel && values?.room && (hasDateRange || hasIndividualDates) && effGuests >= 1)
  }

  const isGuestsComplete = () => {
    const { values } = formikRef.current || { values: {} }
    return Boolean(values?.guest_name && values?.guest_email && values?.guest_phone && values?.guest_document)
  }

  const getStepStatus = (stepId) => {
    const currentIndex = tabs.findIndex(t => t.id === activeTab)
    const stepIndex = tabs.findIndex(t => t.id === stepId)
    
    // Solo marcar como completado si el paso actual es posterior al paso que se está evaluando
    // o si es el paso actual y está completo
    if (stepIndex > currentIndex) {
      return false // Pasos futuros no pueden estar completados
    }
    
    switch (stepId) {
      case 'existing':
        return true // El tab de reservas existentes siempre está "completo" (solo muestra información)
      case 'basic':
        return isBasicComplete()
      case 'guests':
        return isGuestsComplete()
      case 'payment':
        // El paso de pago solo se completa cuando se ha completado la información básica
        // y se ha llenado la información de pago (por ahora solo verificamos básico)
        return isBasicComplete()
      case 'review':
        return isBasicComplete() && isGuestsComplete()
      default:
        return false
    }
  }

  const canProceedToNext = () => {
    const currentIndex = tabs.findIndex(t => t.id === activeTab)
    if (currentIndex === -1 || currentIndex >= tabs.length - 1) return false
    return getStepStatus(tabs[currentIndex].id)
  }

  const goToNextStep = () => {
    const idx = tabs.findIndex(t => t.id === activeTab)
    if (idx < tabs.length - 1) setActiveTab(tabs[idx + 1].id)
  }

  const goToPreviousStep = () => {
    const idx = tabs.findIndex(t => t.id === activeTab)
    if (idx > 0) setActiveTab(tabs[idx - 1].id)
  }

  // Footer personalizado con stepper y acciones
  const CustomFooter = () => {
    const currentIndex = tabs.findIndex(t => t.id === activeTab)
    const isLast = currentIndex === tabs.length - 1
    const canNext = canProceedToNext()

    const handleCreate = () => {
      if (!formikRef.current) return
      const { values, setFieldValue } = formikRef.current

      // Validar conflictos de fechas antes de enviar
      const checkIn = values.date_range?.startDate || values.check_in
      const checkOut = values.date_range?.endDate || values.check_out
      
      if (checkIn && checkOut && values.room_data) {
        const hasConflict = validateDateConflict(checkIn, checkOut, values.room_data)
        if (hasConflict) {
          // Limpiar las fechas y mostrar alerta
          setFieldValue('date_range', { startDate: '', endDate: '' })
          setFieldValue('check_in', '')
          setFieldValue('check_out', '')
          setDateAlertMsg('La habitación ya tiene reservas en alguna(s) de las noches seleccionadas. Por favor elegí otro rango.')
          setDateAlertOpen(true)
          return // No enviar la reserva
        }
      }

      const guestsData = []
      if (values.guest_name) {
        guestsData.push({
          name: values.guest_name,
          email: values.guest_email || '',
          phone: values.guest_phone || '',
          document: values.guest_document || '',
          address: values.contact_address || '',
          is_primary: true,
        })
      }
      if (values.other_guests && values.other_guests.length > 0) {
        values.other_guests.forEach((guest) => {
          if (guest.name) {
            guestsData.push({
              name: guest.name,
              email: guest.email || '',
              phone: guest.phone || '',
              document: guest.document || '',
              address: guest.address || '',
              is_primary: false,
            })
          }
        })
      }

      const payload = {
        hotel: values.hotel ? Number(values.hotel) : undefined,
        room: values.room ? Number(values.room) : undefined,
        guests: values.guests ? Number(values.guests) : 1,
        guests_data: guestsData,
        check_in: checkIn || undefined,
        check_out: checkOut || undefined,
        // No enviar channel, el backend lo normaliza automáticamente a DIRECT para reservas sin external_id
        notes: values.notes || undefined,
        status: values.status || 'pending',
        promotion_code: values.promotion_code || undefined,
        voucher_code: values.voucher_code || undefined,
        price_source: values.price_source || 'primary',
      }

      if (isEdit && reservation?.id) {
        updateReservation({ id: reservation.id, body: payload })
      } else {
        createReservation(payload)
      }
    }

    return (
      <div className="w-full flex flex-col gap-4">
        {/* Stepper arriba */}
        <div className="flex items-center justify-center space-x-1 sm:space-x-2">
          {tabs.map((tab, index) => {
            const isActive = tab.id === activeTab
            const isCompleted = getStepStatus(tab.id)
            const isAccessible = index === 0 || getStepStatus(tabs[index - 1].id)
            const isPrevious = index < tabs.findIndex(t => t.id === activeTab)
            
            return (
              <div key={tab.id} className={`flex items-center space-x-1 sm:space-x-2 ${!isAccessible ? 'opacity-50' : ''}`}>
                <div
                  className={`w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center text-xs sm:text-sm font-semibold transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : isCompleted && isPrevious
                      ? 'bg-green-500 text-white'
                      : isAccessible
                      ? 'bg-gray-200 text-gray-600'
                      : 'bg-gray-100 text-gray-400'
                  }`}
                >
                  {isCompleted && isPrevious ? '✓' : index + 1}
                </div>
                {index < tabs.length - 1 && (
                  <div className={`w-4 sm:w-8 h-0.5 ${isCompleted && isPrevious ? 'bg-green-500' : 'bg-gray-200'}`} />
                )}
              </div>
            )
          })}
        </div>

        {/* Botones de acción abajo, juntos horizontalmente */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Button variant="danger" size="sm lg:size-md" onClick={onClose}>{t('reservations_modal.cancel')}</Button>
            {currentIndex > 0 && (
              <Button variant="secondary" size="sm lg:size-md" onClick={goToPreviousStep}>{t('reservations_modal.previous')}</Button>
            )}
          </div>

          <div className="flex items-center gap-2">
            {isLast ? (
              <Button
                variant="success"
                size="sm lg:size-md"
                onClick={handleCreate}
                disabled={creating || updating || !(isBasicComplete() && isGuestsComplete())}
                loadingText={creating || updating ? t('reservations_modal.creating') : undefined}
              >
                {isEdit ? t('reservations_modal.save_changes') : t('reservations_modal.create_reservation_btn')}
              </Button>
            ) : (
              <Button variant="primary" size="sm lg:size-md" disabled={!canNext} onClick={goToNextStep}>{t('reservations_modal.next')}</Button>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <Formik
      key={isEdit ? `edit-${reservation?.id ?? 'new'}` : `create-${modalKey}`}
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={() => { }}
    >
      {({ values, setFieldValue, setFieldTouched, errors, touched }) => {
        // Guardar referencia a Formik para helpers del footer
        formikRef.current = { values, setFieldValue, setFieldTouched, errors, touched }

        // Extraer fechas ocupadas de los datos de la habitación
        const { reservationRanges, occupiedNights, arrivalDays } = getOccupiedDates(values.room_data)
        
        // Preparar lista de reservas para el panel lateral
        const reservationsList = useMemo(() => {
          if (!values.room_data) return []
          
          const list = []
          const occupyingStatuses = ['confirmed', 'check_in', 'pending']
          
          // Agregar reserva actual si existe
          if (values.room_data.current_reservation) {
            const res = values.room_data.current_reservation
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
          if (values.room_data.future_reservations && Array.isArray(values.room_data.future_reservations)) {
            values.room_data.future_reservations.forEach(res => {
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
        }, [values.room_data])
        
        
        if (values.room_data) {
          
          // Mostrar qué reservas se están considerando
          const allReservations = [
            ...(values.room_data.current_reservation ? [values.room_data.current_reservation] : []),
            ...(values.room_data.future_reservations || [])
          ]
          const occupyingReservations = allReservations.filter(r => 
            ['confirmed', 'check_in', 'pending'].includes(r.status)
          )
        }

        // Limpiar habitación si cambió el número de huéspedes y la habitación actual no tiene capacidad suficiente
        if (values.guests !== previousGuests) {
          setPreviousGuests(values.guests)
          if (values.guests && values.room_data && values.guests > values.room_data.max_capacity) {
            setFieldValue('room', '')
            setFieldValue('room_data', null)
          }
        }

        const titleNode = (
          <div className="flex flex-col">
            <span className="text-base sm:text-lg">
              {isEdit ? t('reservations_modal.edit_reservation') : t('reservations_modal.create_reservation')}
            </span>
            {(() => {
              // Usar el rango de fechas si está disponible, sino usar los campos individuales
              const checkIn = values.date_range?.startDate || values.check_in
              const checkOut = values.date_range?.endDate || values.check_out
              
              if (checkIn && checkOut) {
                const duration = calculateStayDuration(checkIn, checkOut)
                return (
                  <div className="text-xs sm:text-sm font-normal text-gray-600 mt-1">
                    {`${formatDate(checkIn, 'dd/MM/yyyy')} - ${formatDate(checkOut, 'dd/MM/yyyy')} (${duration} ${duration === 1 ? t('reservations_modal.night') : t('reservations_modal.nights')})`}
                  </div>
                )
              }
              return null
            })()}
          </div>
        )

        return (
          <>
          <ModalLayout
            isOpen={isOpen}
            onClose={onClose}
            title={titleNode}
            customFooter={<CustomFooter />}
            size='lg2'
          >
            <div className="space-y-4 sm:space-y-6">
              {/* Banner de pago por canal para reservas OTA editadas */}
              {isEdit && reservation?.paid_by === 'ota' && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div>
                      <div className="text-emerald-900 font-semibold">
                        Pagada por {reservation.channel_display || reservation.channel || 'canal'}
                      </div>
                      <div className="text-emerald-800 text-sm mt-1">
                        Este pago pertenece al canal y no se modifica al editar. Si cambian fechas/precio,
                        podés conciliar la <strong>diferencia</strong> desde aquí.
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-sm text-emerald-900 font-medium">
                        Diferencia actual: {new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(parseFloat(reservation?.balance_due || 0))}
                      </div>
                      {parseFloat(reservation?.balance_due || 0) > 0 && (
                        <button
                          type="button"
                          onClick={() => {
                            setPayInfo({
                              balance_due: reservation.balance_due,
                              total_paid: reservation.total_paid,
                              total_reservation: reservation.total_price,
                              payment_required_at: 'check_in'
                            })
                            setPayOpen(true)
                          }}
                          className="px-3 py-1.5 rounded-md bg-emerald-600 text-white text-sm hover:bg-emerald-700"
                        >
                          Cobrar diferencia
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )}
              <Tabs tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />

              {activeTab === 'existing' && (
                <div className="space-y-6">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-blue-900 mb-2">
                      Reservas de la Habitación {reservation?.room_data?.name || reservation?.room_data?.number}
                    </h3>
                    <p className="text-sm text-blue-700">
                      Esta habitación tiene reservas existentes. Revisa los detalles antes de crear una nueva reserva.
                    </p>
                  </div>

                  {/* Reserva Actual */}
                  {reservation?.room_data?.current_reservation && (
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-md font-semibold text-gray-900 flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                          Reserva Actual
                        </h4>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          reservation.room_data.current_reservation.status === 'check_in' 
                            ? 'bg-amber-100 text-amber-800' 
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {reservation.room_data.current_reservation.status === 'check_in' ? 'Ocupada' : 'Confirmada'}
                        </span>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-gray-600">Huésped</p>
                          <p className="font-medium">{reservation.room_data.current_reservation.guest_name || 'No especificado'}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">N° de Reserva</p>
                          <p className="font-medium">#{reservation.room_data.current_reservation.id}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Check-in</p>
                          <p className="font-medium">{formatDate(reservation.room_data.current_reservation.check_in, 'dd MMM yyyy')}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Check-out</p>
                          <p className="font-medium">{formatDate(reservation.room_data.current_reservation.check_out, 'dd MMM yyyy')}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Reservas Futuras */}
                  {reservation?.room_data?.future_reservations && reservation.room_data.future_reservations.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-md font-semibold text-gray-900 flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                        Reservas Futuras ({reservation.room_data.future_reservations.length})
                      </h4>
                      {reservation.room_data.future_reservations.map((res, index) => (
                        <div key={res.id || index} className="bg-white border border-gray-200 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <h5 className="font-medium text-gray-900">Reserva #{res.id}</h5>
                            <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {res.status === 'confirmed' ? 'Confirmada' : res.status}
                            </span>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <p className="text-sm text-gray-600">Huésped</p>
                              <p className="font-medium">{res.guest_name || 'No especificado'}</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600">Check-in</p>
                              <p className="font-medium">{formatDate(res.check_in, 'dd MMM yyyy')}</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600">Check-out</p>
                              <p className="font-medium">{formatDate(res.check_out, 'dd MMM yyyy')}</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600">Duración</p>
                              <p className="font-medium">
                                {calculateStayDuration(res.check_in, res.check_out)} noche(s)
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Información de la Habitación */}
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <h4 className="text-md font-semibold text-gray-900 mb-3">Información de la Habitación</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-600">Número</p>
                        <p className="font-medium">{reservation?.room_data?.name || reservation?.room_data?.number}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Tipo</p>
                        <p className="font-medium">{reservation?.room_data?.room_type || 'No especificado'}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Capacidad</p>
                        <p className="font-medium">{reservation?.room_data?.capacity || 'No especificado'}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Piso</p>
                        <p className="font-medium">{reservation?.room_data?.floor || 'No especificado'}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'basic' && (
                <>
                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                    <div>
                      <SelectAsync
                        title={`${t('reservations_modal.hotel')} *`}
                        name='hotel'
                        resource='hotels'
                        extraParams={!isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {}}
                        placeholder={t('common.search_placeholder')}
                        getOptionLabel={(h) => h?.name}
                        getOptionValue={(h) => h?.id}
                        disabled={lockHotel}
                        isClearable={!lockHotel}
                        onValueChange={() => {
                          // Limpiar habitación cuando cambia el hotel.
                          // Importante: NO limpiar fechas, porque pueden venir preseleccionadas
                          // desde el calendario (y se deben mantener visibles en el modal).
                          setFieldValue('room', '')
                          setFieldValue('room_data', null)
                          setFieldTouched('room', false, false)
                        }}
                        error={touched.hotel && errors.hotel}
                      />
                    </div>

                    {/* 2. Fechas de estadía */}
                    <div>
                      <DatePickedRange
                        label="Fechas de estadía *"
                        startDate={values.date_range?.startDate || values.check_in}
                        endDate={values.date_range?.endDate || values.check_out}
                        minDate={format(new Date(), 'yyyy-MM-dd')}
                        reservationsList={reservationsList}
                        occupiedNights={occupiedNights}
                        onChange={(startDate, endDate) => {
                          // Normalizar: si el usuario selecciona un solo día (start=end),
                          // interpretarlo como 1 noche (check_out = check_in + 1 día).
                          let normalizedStart = startDate
                          let normalizedEnd = endDate
                          if (normalizedStart && normalizedEnd && normalizedStart === normalizedEnd) {
                            try {
                              normalizedEnd = format(addDays(parseISO(normalizedStart), 1), 'yyyy-MM-dd')
                            } catch (e) {
                              // fallback defensivo: mantener lo recibido
                              normalizedEnd = endDate
                            }
                          }
                          // Actualizar tanto el rango como los campos individuales para compatibilidad
                          setFieldValue('date_range', { startDate: normalizedStart, endDate: normalizedEnd })
                          setFieldValue('check_in', normalizedStart)
                          setFieldValue('check_out', normalizedEnd)
                          // Limpiar habitación cuando cambian las fechas (solo si NO está fijada)
                          if (!lockRoom) {
                            setFieldValue('room', '')
                            setFieldValue('room_data', null)
                            setFieldTouched('room', false, false)
                          }
                        }}
                        onApply={(startISO, endISO) => {
                          try {
                            if (!startISO || !endISO) return
                            // Normalizar también en "Aplicar" por seguridad
                            let normalizedStartISO = startISO
                            let normalizedEndISO = endISO
                            if (normalizedStartISO === normalizedEndISO) {
                              normalizedEndISO = format(addDays(parseISO(normalizedStartISO), 1), 'yyyy-MM-dd')
                              setFieldValue('date_range', { startDate: normalizedStartISO, endDate: normalizedEndISO })
                              setFieldValue('check_in', normalizedStartISO)
                              setFieldValue('check_out', normalizedEndISO)
                            }

                            const start = new Date(normalizedStartISO + 'T00:00:00')
                            const end = new Date(normalizedEndISO + 'T00:00:00')
                            // Chequear noches en [start, end)
                            let conflict = false
                            const occupiedSet = new Set(occupiedNights || [])
                            const iter = new Date(start)
                            while (iter < end) {
                              const iso = format(iter, 'yyyy-MM-dd')
                              if (occupiedSet.has(iso)) {
                                conflict = true
                                break
                              }
                              iter.setDate(iter.getDate() + 1)
                            }
                            if (conflict) {
                              setFieldValue('date_range', { startDate: '', endDate: '' })
                              setFieldValue('check_in', '')
                              setFieldValue('check_out', '')
                              setDateAlertMsg('La habitación ya tiene reservas en alguna(s) de las noches seleccionadas. Por favor elegí otro rango.')
                              setDateAlertOpen(true)
                              return false
                            }
                          } catch (e) {}
                          return true
                        }}
                        placeholder="Check-in — Check-out"
                        inputClassName="w-full"
                        containerClassName=""
                        disabled={!values.hotel}
                      />
                      <div className="text-xs text-gray-500 mt-1">
                        💡 La primera fecha es el <strong>check-in</strong> y la segunda el <strong>check-out</strong>
                        {values.room && occupiedNights.length > 0 && (
                          <span className="text-red-600 ml-2">🚫 {occupiedNights.length} noche(s) ocupada(s)</span>
                        )}
                      </div>
                    </div>

                    {/* 3. Cantidad de huéspedes */}
                    <div>
                      <InputText
                        title={`${t('reservations_modal.guests_number')} *`}
                        name='guests'
                        type='number'
                        min='1'
                        max={values.room_data?.max_capacity || 10}
                        placeholder='Ej: 2'
                        value={values.guests}
                        onChange={(e) => {
                          const raw = Number(e.target.value)
                          const maxCap = values.room_data?.max_capacity
                          const newGuests = lockRoom && maxCap ? Math.min(raw, maxCap) : raw
                          setFieldValue('guests', newGuests)
                          // Si NO está fijada la habitación, y excede capacidad, limpiar selección
                          if (!lockRoom && values.room_data && newGuests > values.room_data.max_capacity) {
                            setFieldValue('room', '')
                            setFieldValue('room_data', null)
                            setFieldTouched('room', false, false)
                          }
                        }}
                        error={touched.guests && errors.guests}
                        disabled={!values.hotel || !hasDatesSelected(values)}
                      />
                      {!hasDatesSelected(values) ? (
                        <div className="text-xs text-gray-500 mt-1">
                          Primero seleccioná las fechas de estadía.
                        </div>
                      ) : null}
                    </div>

                    {/* 4. Habitación */}
                    <div>
                      {lockRoom ? (
                        <LabelsContainer title={`${t('reservations_modal.room')} *`}>
                          <div className="w-full border border-gray-200 rounded-md px-3 py-2 bg-gray-100 text-gray-500 cursor-not-allowed">
                            {values.room_data ? getRoomOptionLabel(values.room_data) : (values.room ? `#${values.room}` : '—')}
                          </div>
                        </LabelsContainer>
                      ) : (
                        <SelectAsync
                          title={`${t('reservations_modal.room')} *`}
                          name='room'
                          resource='rooms'
                          placeholder={
                            !values.hotel
                              ? t('reservations_modal.room_placeholder_no_hotel')
                              : !hasDatesSelected(values)
                              ? 'Primero seleccioná las fechas de estadía'
                              : !getEffectiveGuests(values) || getEffectiveGuests(values) === 0
                              ? 'Primero ingresá la cantidad de huéspedes'
                              : t('reservations_modal.room_placeholder_with_guests', { 
                                  guests: values.guests, 
                                  plural: values.guests > 1 ? 'es' : '' 
                                })
                          }
                          transformOptions={(opts) => {
                            const sorted = Array.isArray(opts) ? [...opts] : []
                            sorted.sort((a, b) => roomNameCollator.compare(getRoomDisplayName(a), getRoomDisplayName(b)))
                            return sorted
                          }}
                          getOptionLabel={(r) => getRoomOptionLabel(r)}
                          getOptionValue={(r) => r?.id}
                          extraParams={{
                            hotel: values.hotel || undefined,
                            min_capacity: getEffectiveGuests(values) || undefined,
                            check_in: values.date_range?.startDate || values.check_in || undefined,
                            check_out: values.date_range?.endDate || values.check_out || undefined,
                          }}
                          onValueChange={(option) => {
                            setFieldValue('room', option?.id || null)
                            setFieldValue('room_data', option || null)
                          }}
                          error={touched.room && errors.room}
                          disabled={!values.hotel || !hasDatesSelected(values) || getEffectiveGuests(values) === 0}
                        />
                      )}
                      {values.guests && values.hotel && (
                        <div className="text-xs text-blue-600 mt-1">
                          💡 {t('reservations_modal.capacity_filter_info', { 
                            guests: values.guests, 
                            plural: values.guests > 1 ? 'es' : '' 
                          })}
                        </div>
                      )}
                      {values.room_data && (
                        <div className="text-xs text-gray-600 mt-1">
                          {t('reservations_modal.capacity_info', { max: values.room_data.max_capacity })}
                        </div>
                      )}
                    </div>
                  </div>

                  {(() => {
                    // Usar el rango de fechas si está disponible, sino usar los campos individuales
                    const checkIn = values.date_range?.startDate || values.check_in
                    const checkOut = values.date_range?.endDate || values.check_out
                    
                    if (checkIn && checkOut) {
                      return (
                        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-3 sm:p-4 rounded-lg border border-blue-200 w-full sm:w-3/4 lg:w-1/2 mx-auto">
                          <div className="flex flex-col sm:flex-row items-center justify-center space-y-3 sm:space-y-0 sm:space-x-6">
                            <div className="text-center">
                              <div className="text-xs sm:text-sm font-medium text-gray-600 mb-1">{t('reservations_modal.check_in')}</div>
                              <div className="text-base sm:text-lg font-bold text-blue-600">{formatDate(checkIn, 'EEE, dd MMM')}</div>
                              <div className="text-xs text-gray-500">{formatDate(checkIn, 'yyyy')}</div>
                            </div>
                            <div className="flex items-center space-x-2 sm:space-x-3">
                              <div className="w-4 sm:w-6 h-0.5 bg-blue-300"></div>
                              <div className="bg-blue-100 px-2 sm:px-3 py-1 rounded-full">
                                <span className="text-blue-700 font-semibold text-xs sm:text-sm">
                                  {(() => {
                                    const duration = calculateStayDuration(checkIn, checkOut)
                                    return `${duration} ${duration === 1 ? t('reservations_modal.night') : t('reservations_modal.nights')}`
                                  })()}
                                </span>
                              </div>
                              <div className="w-4 sm:w-6 h-0.5 bg-blue-300"></div>
                            </div>
                            <div className="text-center">
                              <div className="text-xs sm:text-sm font-medium text-gray-600 mb-1">{t('reservations_modal.check_out')}</div>
                              <div className="text-base sm:text-lg font-bold text-blue-600">{formatDate(checkOut, 'EEE, dd MMM')}</div>
                              <div className="text-xs text-gray-500">{formatDate(checkOut, 'yyyy')}</div>
                            </div>
                          </div>
                        </div>
                      )
                    }
                    return null
                  })()}

                  <div>
                    <InputText
                      title={t('reservations_modal.notes')}
                      name='notes'
                      placeholder={t('reservations_modal.notes_placeholder')}
                      multiline
                      rows={3}
                      value={values.notes}
                      onChange={(e) => setFieldValue('notes', e.target.value)}
                      error={touched.notes && errors.notes}
                    />
                  </div>
                </>
              )}

              {activeTab === 'guests' && <GuestInformation />}
              {activeTab === 'payment' && <PaymentInformation />}
              {activeTab === 'review' && <ReviewReservation />}
            </div>
          </ModalLayout>
          <AlertSwal
            isOpen={dateAlertOpen}
            onClose={() => setDateAlertOpen(false)}
            onConfirm={() => setDateAlertOpen(false)}
            title="Rango no disponible"
            description={dateAlertMsg || 'Las fechas seleccionadas se superponen con reservas existentes.'}
            confirmText="Entendido"
            cancelText="Cerrar"
            tone="warning"
          />
          {/* Modal de pago de diferencia */}
          {isEdit && reservation?.id && (
            <PaymentModal
              isOpen={payOpen}
              reservationId={reservation.id}
              balanceInfo={payInfo}
              onClose={() => { setPayOpen(false); setPayInfo(null); }}
              onPaid={() => { setPayOpen(false); setPayInfo(null); onSuccess && onSuccess(); }}
            />
          )}
          </>
        )
      }}
    </Formik>
  )
}

export default ReservationsModal