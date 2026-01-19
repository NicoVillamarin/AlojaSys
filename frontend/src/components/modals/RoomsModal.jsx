import { Formik } from 'formik'
import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
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
  const { t } = useTranslation()
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
    max_capacity: room?.max_capacity ?? '',
    base_price: room?.base_price != null ? String(room.base_price) : '0',
    // Solo lectura: el precio OTA se gestiona en Smoobu (channel manager) y se publica a OTAs.
    // No lo enviamos en el payload de creación/edición de habitación.
    ota_price: room?.ota_price != null ? String(room.ota_price) : '',
    status: room?.status ?? 'available',
    description: room?.description ?? '',
  }

  const validationSchema = Yup.object().shape({
    hotel: Yup.string().required(t('rooms_modal.hotel_required')),
    name: Yup.string().required(t('rooms_modal.name_required')),
    number: Yup.string().required(t('rooms_modal.number_required')),
    floor: Yup.string().required(t('rooms_modal.floor_required')),
    room_type: Yup.string().required(t('rooms_modal.type_required')),
    capacity: Yup.number()
    .transform((v, o) => (o === '' ? undefined : v))
    .typeError(t('rooms_modal.capacity_number'))
    .integer(t('rooms_modal.capacity_integer'))
    .min(1, t('rooms_modal.capacity_min'))
    .required(t('rooms_modal.capacity_required')),
    max_capacity: Yup.number()
    .transform((v, o) => (o === '' ? undefined : v))
    .typeError(t('rooms_modal.max_capacity_number'))
    .integer(t('rooms_modal.max_capacity_integer'))
    .min(1, t('rooms_modal.max_capacity_min'))
    .required(t('rooms_modal.max_capacity_required')),
    base_price: Yup.number()
    .transform((val, original) => (original === '' ? undefined : val))
    .typeError(t('rooms_modal.base_price_number'))
    .moreThan(0, t('rooms_modal.base_price_more_than'))
    .required(t('rooms_modal.base_price_required')),
    status: Yup.string().required(t('rooms_modal.status_required')),
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
          max_capacity: values.max_capacity ? Number(values.max_capacity) : undefined,
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
          title={isEdit ? t('rooms_modal.edit_room') : t('rooms_modal.create_room')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('rooms_modal.save_changes') : t('rooms_modal.create')}
          cancelText={t('rooms_modal.cancel')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='lg'
        >
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5'>
            <SelectAsync
              title={`${t('rooms_modal.hotel')} *`}
              name='hotel'
              resource='hotels'
              placeholder={t('rooms_modal.hotel_placeholder')}
              getOptionLabel={(h) => h?.name}
              getOptionValue={(h) => h?.id}
            />
            <InputText title={`${t('rooms_modal.name')} *`} name='name' placeholder={t('rooms_modal.name_placeholder')} />
            <InputText title={`${t('rooms_modal.number')} *`} name='number' placeholder={t('rooms_modal.number_placeholder')} />
            <InputText title={`${t('rooms_modal.floor')} *`} name='floor' placeholder={t('rooms_modal.floor_placeholder')} />
            <SelectBasic
              title={`${t('rooms_modal.type')} *`}
              name='room_type'
              placeholder={t('rooms_modal.type_placeholder')}
              options={[
                { value: 'single', label: t('rooms_modal.room_types.single') },
                { value: 'double', label: t('rooms_modal.room_types.double') },
                { value: 'triple', label: t('rooms_modal.room_types.triple') },
                { value: 'suite', label: t('rooms_modal.room_types.suite') },
              ]}
            />
            <InputText title={`${t('rooms_modal.capacity')} *`} name='capacity' placeholder={t('rooms_modal.capacity_placeholder')} />
            <InputText title={`${t('rooms_modal.max_capacity')} *`} name='max_capacity' placeholder={t('rooms_modal.max_capacity_placeholder')} />
            <InputText title={`${t('rooms_modal.base_price')} *`} name='base_price' placeholder={t('rooms_modal.base_price_placeholder')} />
            <InputText
              title={t('rooms_modal.ota_price')}
              name='ota_price'
              placeholder={t('rooms_modal.ota_price_placeholder')}
              disabled
              inputClassName='bg-gray-100 text-gray-500 cursor-not-allowed'
              statusMessage={t('rooms_modal.ota_price_help')}
              statusType='info'
            />
            <SelectBasic
              title={`${t('rooms_modal.status')} *`}
              name='status'
              options={[
                { value: 'available', label: t('rooms_modal.statuses.available') },
                { value: 'occupied', label: t('rooms_modal.statuses.occupied') },
                { value: 'maintenance', label: t('rooms_modal.statuses.maintenance') },
                { value: 'out_of_service', label: t('rooms_modal.statuses.out_of_service') },
                { value: 'reserved', label: t('rooms_modal.statuses.reserved') },
              ]}
            />
            <div className='lg:col-span-2'>
              <InputTextTarea title={t('rooms_modal.description')} name='description' placeholder={t('rooms_modal.description_placeholder')} rows={3} />
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default RoomsModal