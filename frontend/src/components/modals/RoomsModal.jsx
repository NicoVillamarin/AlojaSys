import { Formik } from 'formik'
import React, { useEffect, useState } from 'react'
import ModalLayout from 'src/layouts/ModalLayout'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import InputText from 'src/components/inputs/InputText'
import InputTextTarea from 'src/components/inputs/InputTextTarea'
import SelectBasic from 'src/components/selects/SelectBasic'
import SelectAsync from 'src/components/selects/SelectAsync'
import * as Yup from 'yup'


/**
 * RoomsModal: crear/editar habitación
 * Props:
 * - isOpen: boolean
 * - onClose: () => void
 * - isEdit?: boolean
 * - room?: objeto habitación existente (para editar)
 * - onSuccess?: (data) => void (se llama al crear/editar OK)
 */
const RoomsModal = ({ isOpen, onClose, isEdit = false, room, onSuccess }) => {
  const { mutate: createRoom, isPending: creating } = useCreate({
    resource: 'rooms',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
      onClose && onClose()
    },
  })

  const { mutate: updateRoom, isPending: updating } = useUpdate({
    resource: 'rooms',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
      onClose && onClose()
    },
  })

  const initialValues = {
    hotel: room?.hotel ?? '',
    hotel_name: room?.hotel_name ?? '',
    name: room?.name ?? '',
    number: room?.number ?? '',
    floor: room?.floor ?? '',
    room_type: room?.room_type ?? '',
    capacity: room?.capacity ?? '',
    base_price: room?.base_price != null ? String(room.base_price) : '0',
    status: room?.status ?? 'available',
    description: room?.description ?? '',
  }

  const validationSchema = Yup.object().shape({
    hotel: Yup.string().required('Hotel es requerido'),
    name: Yup.string().required('Nombre es requerido'),
    number: Yup.string().required('Número es requerido'),
    floor: Yup.string().required('Piso es requerido'),
    room_type: Yup.string().required('Tipo es requerido'),
    capacity: Yup.number()
    .transform((v, o) => (o === '' ? undefined : v))
    .typeError('Capacidad debe ser un número')
    .integer('Capacidad debe ser un entero')
    .min(1, 'Capacidad debe ser al menos 1')
    .required('Capacidad es requerido'),
    base_price: Yup.number()
    .transform((val, original) => (original === '' ? undefined : val))
    .typeError('Precio base debe ser un número')
    .moreThan(0, 'Precio base debe ser mayor a 0')
    .required('Precio base es requerido'),
    status: Yup.string().required('Estado es requerido'),
  })

  const [instanceKey, setInstanceKey] = useState(0)
  useEffect(() => {
    if (isOpen && !isEdit) {
      setInstanceKey((k) => k + 1)
    }
  }, [isOpen, isEdit])

  return (
    <Formik
      key={isEdit ? `edit-${room?.id ?? 'new'}` : `create-${instanceKey}`}
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          hotel: values.hotel ? Number(values.hotel) : undefined,
          name: values.name || undefined,
          number: values.number !== '' ? Number(values.number) : undefined,
          floor: values.floor !== '' ? Number(values.floor) : undefined,
          room_type: values.room_type || undefined,
          capacity: values.capacity ? Number(values.capacity) : undefined,
          base_price: values.base_price ? Number(values.base_price) : undefined,
          status: values.status || undefined,
          description: values.description || undefined,
        }
        if (isEdit && room?.id) {
          updateRoom({ id: room.id, body: payload })
        } else {
          createRoom(payload)
        }
      }}
    >
      {({ values, handleChange, handleSubmit }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? 'Editar habitación' : 'Crear habitación'}
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
            />
            <InputText title='Nombre *' name='name' placeholder='Suite 101' />
            <InputText title='Número *' name='number' placeholder='101' />
            <InputText title='Piso *' name='floor' placeholder='1' />
            <SelectBasic
              title='Tipo *'
              name='room_type'
              placeholder='Seleccionar tipo'
              options={[
                { value: 'single', label: 'Single' },
                { value: 'double', label: 'Doble' },
                { value: 'triple', label: 'Triple' },
                { value: 'suite', label: 'Suite' },
              ]}
            />
            <InputText title='Capacidad *' name='capacity' placeholder='2' />
            <InputText title='Precio base *' name='base_price' placeholder='100.00' />
            <SelectBasic
              title='Estado *'
              name='status'
              options={[
                { value: 'available', label: 'Disponible' },
                { value: 'occupied', label: 'Ocupada' },
                { value: 'maintenance', label: 'Mantenimiento' },
                { value: 'out_of_service', label: 'Fuera de servicio' },
                { value: 'reserved', label: 'Reservada' },
              ]}
            />
            <div className='md:col-span-2'>
              <InputTextTarea title='Descripción' name='description' placeholder='Notas internas…' rows={3} />
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default RoomsModal