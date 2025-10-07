import { Formik } from 'formik'
import * as Yup from 'yup'
import { useEffect, useState, useRef } from 'react'
import { format, parseISO, isValid } from 'date-fns'
import { es } from 'date-fns/locale'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
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

/**
 * ReservationsModal: crear/editar reserva
 * Props:
 * - isOpen: boolean
 * - onClose: () => void
 * - isEdit?: boolean
 * - reservation?: objeto reserva existente (para editar)
 * - onSuccess?: (data) => void (se llama al crear/editar OK)
 */
const ReservationsModal = ({ isOpen, onClose, onSuccess, isEdit = false, reservation }) => {
  const [modalKey, setModalKey] = useState(0)
  const [activeTab, setActiveTab] = useState('basic')
  const formikRef = useRef(null)
  
  // Hook para obtener hoteles del usuario logueado
  const { hotelIdsString, isSuperuser } = useUserHotels()

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
      console.error('Error formatting date:', error)
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
      console.error('Error calculating stay duration:', error)
      return 0
    }
  }

  const { mutate: createReservation, isPending: creating } = useCreate({
    resource: 'reservations',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const { mutate: updateReservation, isPending: updating } = useUpdate({
    resource: 'reservations',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

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

  // Debug: mostrar datos de la reserva
  if (isEdit && reservation) {
    console.log('Datos de la reserva para editar:', reservation)
    console.log('Datos del huésped principal extraídos:', primaryGuestData)
    console.log('Otros huéspedes extraídos:', otherGuestsData)
  }

  const initialValues = {
    hotel: reservation?.hotel ?? '',
    ...primaryGuestData,
    guests: reservation?.guests ?? 1,
    other_guests: otherGuestsData,
    check_in: reservation?.check_in ? reservation.check_in.split('T')[0] : '',
    check_out: reservation?.check_out ? reservation.check_out.split('T')[0] : '',
    room: reservation?.room ?? '',
    room_data: reservation?.room_data ?? null, // Información completa de la habitación
    status: reservation?.status ?? 'pending',
    notes: reservation?.notes ?? '',
    // Precargar canal y código de promoción para edición
    channel: reservation?.channel ?? '',
    promotion_code: reservation?.promotion_code ?? '',
  }

  // Reset modal key when opening for creation
  useEffect(() => {
    if (isOpen && !isEdit) {
      setModalKey(prev => prev + 1)
    }
  }, [isOpen, isEdit])

  // Cargar datos de la habitación cuando se edita
  useEffect(() => {
    if (isEdit && reservation?.room && !reservation?.room_data) {
      // Si tenemos el ID de la habitación pero no los datos completos,
      // podríamos hacer una llamada para obtener los datos de la habitación
      // Por ahora, asumimos que room_data viene del backend
      console.log('Reserva para editar - ID de habitación:', reservation.room)
    }
  }, [isEdit, reservation])

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

  const validationSchema = Yup.object({
    hotel: Yup.number().required('Hotel es requerido'),
    guests: Yup.number()
      .min(1, 'Debe ser al menos 1 huésped')
      .test('max-capacity', 'El número de huéspedes excede la capacidad máxima de la habitación', function (value) {
        const roomData = this.parent.room_data
        if (roomData && value > roomData.max_capacity) {
          return this.createError({
            message: `La habitación seleccionada tiene una capacidad máxima de ${roomData.max_capacity} huéspedes`
          })
        }
        return true
      })
      .required('Número de huéspedes es requerido'),
    check_in: Yup.date()
      .required('Check-in es requerido')
      .test('not-before-today', 'La fecha de check-in no puede ser anterior a hoy', function (value) {
        if (!value) return true
        const today = new Date()
        const checkInDate = new Date(value)
        
        // Establecer ambas fechas a medianoche para comparar solo la fecha
        today.setHours(0, 0, 0, 0)
        checkInDate.setHours(0, 0, 0, 0)
        
        return checkInDate >= today
      }),
    check_out: Yup.date()
      .required('Check-out es requerido')
      .test('is-after-checkin', 'Check-out debe ser posterior al check-in', function (value) {
        const { check_in } = this.parent
        if (!check_in || !value) return true
        
        const checkInDate = new Date(check_in)
        const checkOutDate = new Date(value)
        
        // Establecer ambas fechas a medianoche para comparar solo la fecha
        checkInDate.setHours(0, 0, 0, 0)
        checkOutDate.setHours(0, 0, 0, 0)
        
        return checkOutDate > checkInDate
      })
      .test('min-stay', 'La estadía mínima es de 1 noche', function (value) {
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
    room: Yup.number().required('Habitación es requerida'),
    // Validación del huésped principal
    guest_name: Yup.string().required('Nombre del huésped principal es requerido'),
    guest_email: Yup.string().email('Email inválido').required('Email del huésped principal es requerido'),
    guest_phone: Yup.string().required('Teléfono del huésped principal es requerido'),
    guest_document: Yup.string().required('Documento del huésped principal es requerido'),
    contact_address: Yup.string().required('Dirección del huésped principal es requerida'),
    // Validación de otros huéspedes
    other_guests: Yup.array().of(
      Yup.object({
        name: Yup.string().required('Nombre es requerido'),
        document: Yup.string().required('Documento es requerido'),
        email: Yup.string().email('Email inválido').required('Email es requerido'),
        phone: Yup.string().required('Teléfono es requerido'),
        address: Yup.string().required('Dirección es requerida'),
      })
    ),
  })

  const tabs = [
    { id: 'basic', label: 'Información Básica', icon: <CandelarClock /> },
    { id: 'guests', label: 'Huéspedes', icon: <PeopleIcon /> },
    { id: 'payment', label: 'Pago', icon: <WalletIcon /> },
    { id: 'review', label: 'Revisar', icon: <CheckIcon /> }
  ]

  // Helpers de pasos
  const getEffectiveGuests = (vals) => {
    const raw = vals?.guests
    if (raw === 0) return 0
    if (raw === '' || raw === null || raw === undefined) return 1
    const num = Number(raw)
    return Number.isNaN(num) ? 1 : num
  }

  const isBasicComplete = () => {
    const { values } = formikRef.current || { values: {} }
    const effGuests = getEffectiveGuests(values)
    return Boolean(values?.hotel && values?.room && values?.check_in && values?.check_out && effGuests >= 1)
  }

  const isGuestsComplete = () => {
    const { values } = formikRef.current || { values: {} }
    return Boolean(values?.guest_name && values?.guest_email && values?.guest_phone && values?.guest_document)
  }

  const getStepStatus = (stepId) => {
    switch (stepId) {
      case 'basic':
        return isBasicComplete()
      case 'guests':
        return isGuestsComplete()
      case 'payment':
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
      const values = formikRef.current.values

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
        check_in: values.check_in || undefined,
        check_out: values.check_out || undefined,
        channel: values.channel || undefined,
        notes: values.notes || undefined,
        status: values.status || 'pending',
        promotion_code: values.promotion_code || undefined,
      }

      if (isEdit && reservation?.id) {
        updateReservation({ id: reservation.id, body: payload })
      } else {
        createReservation(payload)
      }
    }

    return (
      <div className="w-full flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="danger" size="md" onClick={onClose}>Cancelar</Button>
          {currentIndex > 0 && (
            <Button variant="secondary" size="md" onClick={goToPreviousStep}>← Anterior</Button>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {tabs.map((tab, index) => {
            const isActive = tab.id === activeTab
            const isCompleted = getStepStatus(tab.id)
            const isAccessible = index === 0 || getStepStatus(tabs[index - 1].id)
            return (
              <div key={tab.id} className={`flex items-center space-x-2 ${!isAccessible ? 'opacity-50' : ''}`}>
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : isCompleted
                      ? 'bg-green-500 text-white'
                      : isAccessible
                      ? 'bg-gray-200 text-gray-600'
                      : 'bg-gray-100 text-gray-400'
                  }`}
                >
                  {isCompleted ? '✓' : index + 1}
                </div>
                {index < tabs.length - 1 && (
                  <div className={`w-8 h-0.5 ${isCompleted ? 'bg-green-500' : 'bg-gray-200'}`} />
                )}
              </div>
            )
          })}
        </div>

        <div className="flex items-center gap-2">
          {isLast ? (
            <Button
              variant="success"
              size="md"
              onClick={handleCreate}
              disabled={creating || updating || !(isBasicComplete() && isGuestsComplete())}
              loadingText={creating || updating ? 'Creando...' : undefined}
            >
              {isEdit ? 'Guardar cambios' : 'Crear reserva'}
            </Button>
          ) : (
            <Button variant="primary" size="md" disabled={!canNext} onClick={goToNextStep}>Siguiente →</Button>
          )}
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
      {({ values, setFieldValue, errors, touched }) => {
        // Guardar referencia a Formik para helpers del footer
        formikRef.current = { values, setFieldValue, errors, touched }

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
            <span>{isEdit ? 'Editar reserva' : 'Crear reserva'}</span>
            {values.check_in && values.check_out && (
              <div className="text-sm font-normal text-gray-600 mt-1">
                {(() => {
                  const duration = calculateStayDuration(values.check_in, values.check_out)
                  return `${formatDate(values.check_in, 'dd/MM/yyyy')} - ${formatDate(values.check_out, 'dd/MM/yyyy')} (${duration} ${duration === 1 ? 'noche' : 'noches'})`
                })()}
              </div>
            )}
          </div>
        )

        return (
          <ModalLayout
            isOpen={isOpen}
            onClose={onClose}
            title={titleNode}
            customFooter={<CustomFooter />}
            size='lg2'
          >
            <div className="space-y-6">
              <Tabs tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />

              {activeTab === 'basic' && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <SelectAsync
                      title='Hotel *'
                      name='hotel'
                      resource='hotels'
                      extraParams={!isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {}}
                      placeholder='Buscar hotel…'
                      getOptionLabel={(h) => h?.name}
                      getOptionValue={(h) => h?.id}
                      value={values.hotel}
                      onChange={(option) => setFieldValue('hotel', option?.value || null)}
                      error={touched.hotel && errors.hotel}
                    />

                    <InputText
                      title='Número de huéspedes *'
                      name='guests'
                      type='number'
                      min='1'
                      max={values.room_data?.max_capacity || 10}
                      placeholder='Ej: 2'
                      value={values.guests}
                      onChange={(e) => setFieldValue('guests', Number(e.target.value))}
                      error={touched.guests && errors.guests}
                    />

                    <InputText
                      title='Check-in *'
                      name='check_in'
                      type='date'
                      value={values.check_in}
                      onChange={(e) => setFieldValue('check_in', e.target.value)}
                      error={touched.check_in && errors.check_in}
                    />
                    <InputText
                      title='Check-out *'
                      name='check_out'
                      type='date'
                      value={values.check_out}
                      onChange={(e) => setFieldValue('check_out', e.target.value)}
                      error={touched.check_out && errors.check_out}
                    />

                    <SelectAsync
                      title='Habitación *'
                      name='room'
                      resource='rooms'
                      placeholder={
                        !values.hotel
                          ? 'Selecciona un hotel primero'
                          : values.guests
                            ? `Habitaciones para ${values.guests} huésped${values.guests > 1 ? 'es' : ''}…`
                            : 'Cargando disponibilidad…'
                      }
                      getOptionLabel={(r) => r?.name || `Habitación ${r?.id}`}
                      getOptionValue={(r) => r?.id}
                      extraParams={{
                        hotel: values.hotel || undefined,
                        min_capacity: getEffectiveGuests(values) || undefined,
                      }}
                      value={values.room}
                      onValueChange={(option) => {
                        setFieldValue('room', option?.id || null)
                        setFieldValue('room_data', option || null)
                      }}
                      error={touched.room && errors.room}
                      disabled={!values.hotel || getEffectiveGuests(values) === 0}
                    />
                  </div>

                  {values.check_in && values.check_out && (
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200 w-1/2 mx-auto">
                      <div className="flex items-center justify-center space-x-6">
                        <div className="text-center">
                          <div className="text-sm font-medium text-gray-600 mb-1">Check-in</div>
                          <div className="text-lg font-bold text-blue-600">{formatDate(values.check_in, 'EEE, dd MMM')}</div>
                          <div className="text-xs text-gray-500">{formatDate(values.check_in, 'yyyy')}</div>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-6 h-0.5 bg-blue-300"></div>
                          <div className="bg-blue-100 px-3 py-1 rounded-full">
                            <span className="text-blue-700 font-semibold text-sm">
                              {(() => {
                                const duration = calculateStayDuration(values.check_in, values.check_out)
                                return `${duration} ${duration === 1 ? 'noche' : 'noches'}`
                              })()}
                            </span>
                          </div>
                          <div className="w-6 h-0.5 bg-blue-300"></div>
                        </div>
                        <div className="text-center">
                          <div className="text-sm font-medium text-gray-600 mb-1">Check-out</div>
                          <div className="text-lg font-bold text-blue-600">{formatDate(values.check_out, 'EEE, dd MMM')}</div>
                          <div className="text-xs text-gray-500">{formatDate(values.check_out, 'yyyy')}</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {values.guests && values.hotel && (
                    <div className="text-sm text-blue-600 mt-1">💡 Se mostrarán solo habitaciones con capacidad para {values.guests} huésped{values.guests > 1 ? 'es' : ''} o más</div>
                  )}
                  {values.room_data && (
                    <div className="text-sm text-gray-600 mt-1">Capacidad máxima: {values.room_data.max_capacity} huéspedes</div>
                  )}
                  <div>
                    <InputText
                      title='Notas'
                      name='notes'
                      placeholder='Notas adicionales…'
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
        )
      }}
    </Formik>
  )
}

export default ReservationsModal