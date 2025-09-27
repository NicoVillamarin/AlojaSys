import { Formik } from 'formik'
import * as Yup from 'yup'
import { useEffect, useState } from 'react'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import { useAction } from 'src/hooks/useAction'

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
  
  const { mutate: createReservation, isPending: creating } = useCreate({
    resource: 'reservations',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const { mutate: updateReservation, isPending: updating } = useUpdate({
    resource: 'reservations',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const initialValues = {
    hotel: reservation?.hotel ?? '',
    hotel_name: reservation?.hotel_name ?? '',
    guest_name: reservation?.guest_name ?? '',
    guest_email: reservation?.guest_email ?? '',
    guests: reservation?.guests ?? 1,
    check_in: reservation?.check_in ? reservation.check_in.split('T')[0] : '',
    check_out: reservation?.check_out ? reservation.check_out.split('T')[0] : '',
    room: reservation?.room ?? '',
    room_name: reservation?.room_name ?? '',
    notes: reservation?.notes ?? '',
    status: reservation?.status ?? 'pending',
  }

  // Resetear el modal cada vez que se abre (solo para crear, no para editar)
  useEffect(() => {
    if (isOpen && !isEdit) {
      setModalKey(prev => prev + 1)
    }
  }, [isOpen, isEdit])

  const validationSchema = Yup.object().shape({
    hotel: Yup.string().required('Hotel es requerido'),
    guest_name: Yup.string().required('Nombre del huésped es requerido'),
    guests: Yup.number()
      .min(1, 'Debe haber al menos 1 huésped')
      .required('Número de huéspedes es requerido'),
    check_in: Yup.string().required('Check-in requerido'),
    check_out: Yup.string().required('Check-out requerido'),
    room: Yup.string().required('Habitación es requerida'),
  })

  return (
    <Formik
      key={isEdit ? `edit-${reservation?.id ?? 'new'}` : `create-${modalKey}`} // Resetear completamente el formulario
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          hotel: values.hotel ? Number(values.hotel) : undefined,
          room: values.room ? Number(values.room) : undefined,
          guest_name: values.guest_name || undefined,
          guest_email: values.guest_email || undefined,
          guests: values.guests ? Number(values.guests) : 1,
          check_in: values.check_in || undefined,
          check_out: values.check_out || undefined,
          notes: values.notes || undefined,
          status: values.status || 'pending',
        }
        
        if (isEdit && reservation?.id) {
          updateReservation({ id: reservation.id, body: payload })
        } else {
          createReservation(payload)
        }
      }}
    >
      {({ values, handleSubmit, setFieldValue }) => {
        const { results: availableRooms, isPending: loadingAvail } = useAction({
          resource: 'reservations',
          action: 'availability',
          params: { 
            hotel: values.hotel || undefined, 
            start: values.check_in || undefined, 
            end: values.check_out || undefined,
            modalKey: modalKey // Agregar key única para evitar caché
          },
          enabled: !!values.hotel && !!values.check_in && !!values.check_out,
        })

        // Obtener información de la habitación seleccionada
        const selectedRoom = availableRooms?.find(room => String(room.id) === String(values.room))
        const roomCapacity = selectedRoom?.capacity || 1
        const roomMaxCapacity = selectedRoom?.max_capacity || 1
        const extraFee = selectedRoom?.extra_guest_fee || 0


        // Validación dinámica para el número de huéspedes
        const validateGuests = (value) => {
          if (!value || value < 1) {
            return 'Debe haber al menos 1 huésped'
          }
          if (selectedRoom && value > roomMaxCapacity) {
            return `La habitación tiene una capacidad máxima de ${roomMaxCapacity} huéspedes`
          }
          return undefined
        }

        return (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? 'Editar reserva' : 'Crear reserva'}
          onSubmit={handleSubmit}
          submitText={isEdit ? 'Guardar cambios' : 'Crear'}
          cancelText='Cancelar'
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='lg'
        >
            <div className='grid grid-cols-1 md:grid-cols-2 gap-5'>
              <SelectAsync
                title='Hotel *'
                name='hotel'
                resource='hotels'
                placeholder='Buscar hotel…'
                getOptionLabel={(h) => h?.name}
                getOptionValue={(h) => h?.id}
                onValueChange={() => {
                  // Al cambiar de hotel, limpiar la habitación seleccionada y resetear huéspedes
                  setFieldValue('room', '')
                  setFieldValue('guests', 1)
                }}
              />
              <InputText title='Huésped *' name='guest_name' placeholder='Juan Pérez' />
              <InputText title='Email' name='guest_email' placeholder='juan@example.com' />

              <InputText title='Check-in *' name='check_in' type='date' />
              <InputText title='Check-out *' name='check_out' type='date' />
              <SelectAsync
                title='Habitación *'
                name='room'
                resource='rooms'
                placeholder={loadingAvail ? 'Cargando disponibilidad…' : 'Seleccionar habitación disponible…'}
                getOptionLabel={(r) => r?.name || r?.number || `#${r?.id}`}
                getOptionValue={(r) => r?.id}
                extraParams={{ hotel: values.hotel || undefined }}
                filterOption={(opt) => {
                  if (!availableRooms || !Array.isArray(availableRooms)) return true
                  return availableRooms.some((ar) => String(ar.id) === String(opt.value))
                }}
                onValueChange={(opt) => {
                  // Al seleccionar habitación, actualizar automáticamente el número de huéspedes
                  if (opt) {
                    // Buscar la habitación en availableRooms para obtener la capacidad máxima
                    const room = availableRooms?.find(r => String(r.id) === String(opt.id))
                    if (room?.max_capacity) {
                      setFieldValue('guests', room.max_capacity)
                    }
                  }
                }}
              />
              <InputText 
                title='Número de huéspedes *' 
                name='guests' 
                type='number' 
                min='1' 
                max={roomMaxCapacity}
                placeholder={`${roomMaxCapacity || 1}`}
                disabled={!values.room}
                validate={validateGuests}
              />
              <div className='md:col-span-2'>
                <InputText title='Notas' name='notes' placeholder='Observaciones…' />
              </div>
              
              {/* Información de capacidad de la habitación */}
              {values.room && selectedRoom && (
                <div className='md:col-span-2 bg-blue-50 border border-blue-200 rounded-lg p-4'>
                  <div className='text-sm text-blue-800'>
                    <div className='font-semibold mb-2'>Información de la habitación:</div>
                    <div className='space-y-1'>
                      <div>• Capacidad estándar: {roomCapacity} huésped{roomCapacity > 1 ? 'es' : ''}</div>
                      <div>• Capacidad máxima: {roomMaxCapacity} huésped{roomMaxCapacity > 1 ? 'es' : ''}</div>
                      {roomMaxCapacity > roomCapacity && (
                        <div className='text-orange-600'>
                          • Cargo extra por huésped adicional: ${extraFee}
                        </div>
                      )}
                      {values.guests > roomCapacity && values.guests <= roomMaxCapacity && (
                        <div className='text-orange-600 font-semibold'>
                          • Cargo extra total: ${(values.guests - roomCapacity) * extraFee}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ModalLayout>
        )
      }}
    </Formik>
  )
}

export default ReservationsModal