import { Formik } from 'formik'
import * as Yup from 'yup'
import { useEffect, useState, useRef } from 'react'
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
import GuestInformation from '../reservations/GuestInformation'
import PaymentInformation from '../reservations/PaymentInformation'
import ReviewReservation from '../reservations/ReviewReservation'

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
    check_in: Yup.date().required('Check-in es requerido'),
    check_out: Yup.date().required('Check-out es requerido'),
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


  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? 'Editar reserva' : 'Crear reserva'}
      onSubmit={() => {
        // Obtener los valores de Formik y enviar
        if (formikRef.current) {
          const values = formikRef.current.values

          // Preparar datos de huéspedes
          const guestsData = []

          // Agregar huésped principal
          if (values.guest_name) {
            guestsData.push({
              name: values.guest_name,
              email: values.guest_email || '',
              phone: values.guest_phone || '',
              document: values.guest_document || '',
              address: values.contact_address || '',
              is_primary: true
            })
          }

          // Agregar otros huéspedes
          if (values.other_guests && values.other_guests.length > 0) {
            values.other_guests.forEach(guest => {
              if (guest.name) {
                guestsData.push({
                  name: guest.name,
                  email: guest.email || '',
                  phone: guest.phone || '',
                  document: guest.document || '',
                  address: guest.address || '',
                  is_primary: false
                })
              }
            })
          }

          // Solo enviar los campos que existen en el backend
          const payload = {
            hotel: values.hotel ? Number(values.hotel) : undefined,
            room: values.room ? Number(values.room) : undefined,
            guests: values.guests ? Number(values.guests) : 1,
            guests_data: guestsData,
            check_in: values.check_in || undefined,
            check_out: values.check_out || undefined,
            notes: values.notes || undefined,
            status: values.status || 'pending',
          }

          console.log('Enviando payload:', payload)

          if (isEdit && reservation?.id) {
            updateReservation({ id: reservation.id, body: payload })
          } else {
            createReservation(payload)
          }
        }
      }}
      submitText={isEdit ? 'Guardar cambios' : 'Crear'}
      cancelText='Cancelar'
      submitDisabled={creating || updating}
      submitLoading={creating || updating}
      size='lg2'
    >
      <Formik
        key={isEdit ? `edit-${reservation?.id ?? 'new'}` : `create-${modalKey}`}
        enableReinitialize
        initialValues={initialValues}
        validationSchema={validationSchema}
        onSubmit={() => { }} // El submit se maneja en ModalLayout
      >
        {({ values, setFieldValue, errors, touched }) => {
          // Guardar referencia a Formik
          formikRef.current = { values, setFieldValue, errors, touched }

          // Limpiar habitación si cambió el número de huéspedes y la habitación actual no tiene capacidad suficiente
          if (values.guests !== previousGuests) {
            setPreviousGuests(values.guests)
            if (values.guests && values.room_data && values.guests > values.room_data.max_capacity) {
              setFieldValue('room', '')
              setFieldValue('room_data', null)
            }
          }

          return (
            <div className="space-y-6">
              {/* Pestañas */}
              <Tabs
                tabs={tabs}
                activeTab={activeTab}
                onTabChange={setActiveTab}
              />

              {activeTab === 'basic' && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* 1. Selección de Hotel */}
                    <SelectAsync
                      title='Hotel *'
                      name='hotel'
                      resource='hotels'
                      placeholder='Buscar hotel…'
                      getOptionLabel={(h) => h?.name}
                      getOptionValue={(h) => h?.id}
                      value={values.hotel}
                      onChange={(option) => setFieldValue('hotel', option?.value || null)}
                      error={touched.hotel && errors.hotel}
                    />
                    
                    {/* 2. Número de huéspedes */}
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
                    
                    {/* 3. Fechas de estadía */}
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
                    
                    {/* 4. Selección de habitación */}
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
                        min_capacity: values.guests || undefined
                      }}
                      value={values.room}
                      onValueChange={(option) => {
                        setFieldValue('room', option?.id || null)
                        setFieldValue('room_data', option || null)
                      }}
                      error={touched.room && errors.room}
                      disabled={!values.hotel || !values.guests}
                    />
                  </div>
                  
                  {/* Mensajes informativos */}
                  {values.guests && values.hotel && (
                    <div className="text-sm text-blue-600 mt-1">
                      💡 Se mostrarán solo habitaciones con capacidad para {values.guests} huésped{values.guests > 1 ? 'es' : ''} o más
                    </div>
                  )}
                  {values.room_data && (
                    <div className="text-sm text-gray-600 mt-1">
                      Capacidad máxima: {values.room_data.max_capacity} huéspedes
                    </div>
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

              {activeTab === 'guests' && (
                <GuestInformation />
              )}

              {activeTab === 'payment' && (
                <div className="text-center py-8 text-gray-500">
                  <PaymentInformation />
                </div>
              )}

              {activeTab === 'review' && (
                <div className="text-center py-8 text-gray-500">
                  <ReviewReservation />
                </div>
              )}
            </div>
          )
        }}
      </Formik>
    </ModalLayout>
  )
}

export default ReservationsModal