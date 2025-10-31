import { Formik } from 'formik'
import * as Yup from 'yup'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import SelectStandalone from 'src/components/selects/SelectStandalone'
import InputText from 'src/components/inputs/InputText'
import Checkbox from 'src/components/Checkbox'
import { useList } from 'src/hooks/useList'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'

export default function OtaRoomTypeMappingModal({ isOpen, onClose, isEdit = false, mapping, defaultHotelId, onSuccess }) {
  const { t } = useTranslation()
  const { results: hotels } = useList({ resource: 'hotels' })

  const { mutate: createItem, isPending: creating } = useCreate({ resource: 'otas/room-type-mappings', onSuccess: (d) => { onSuccess && onSuccess(d); onClose && onClose() } })
  const { mutate: updateItem, isPending: updating } = useUpdate({ resource: 'otas/room-type-mappings', onSuccess: (d) => { onSuccess && onSuccess(d); onClose && onClose() } })

  const initialValues = {
    hotel: mapping?.hotel ?? defaultHotelId ?? '',
    provider: mapping?.provider ?? 'booking',
    room_type_code: mapping?.room_type_code ?? '',
    provider_code: mapping?.provider_code ?? '',
    name: mapping?.name ?? '',
    is_active: mapping?.is_active ?? true,
  }

  const validationSchema = Yup.object().shape({
    hotel: Yup.number().required(t('common.required')),
    provider: Yup.string().required(t('common.required')),
    room_type_code: Yup.string().required(t('common.required')),
    provider_code: Yup.string().required(t('common.required')),
  })

  return (
    <Formik enableReinitialize initialValues={initialValues} validationSchema={validationSchema} onSubmit={(values) => {
      const payload = { ...values, hotel: values.hotel ? Number(values.hotel) : undefined }
      if (isEdit && mapping?.id) updateItem({ id: mapping.id, body: payload })
      else createItem(payload)
    }}>
      {({ handleSubmit, values, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('ota.room_types.edit_title') : t('ota.room_types.create_title')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('common.save_changes') : t('common.create')}
          cancelText={t('common.cancel')}
          size="md"
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5">
            <SelectStandalone
              title={t('ota.room_types.hotel')}
              options={hotels}
              placeholder={t('ota.filters.hotel_placeholder')}
              value={hotels.find(h => String(h.id) === String(values.hotel)) || null}
              onChange={(opt) => setFieldValue('hotel', opt ? opt.id : '')}
              getOptionLabel={(h) => h?.name}
              getOptionValue={(h) => h?.id}
            />

            <div>
              <label className="block text-sm font-medium text-aloja-navy mb-1">{t('ota.room_types.provider')} *</label>
              <select className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full" value={values.provider} onChange={(e) => setFieldValue('provider', e.target.value)}>
                <option value="booking">Booking</option>
                <option value="airbnb">Airbnb</option>
              </select>
            </div>

            <InputText title={t('ota.room_types.room_type_code')} name="room_type_code" placeholder="DOUBLE" />
            <InputText title={t('ota.room_types.provider_code')} name="provider_code" placeholder="STD_DBL" />
            <div className="lg:col-span-2">
              <InputText title={t('ota.room_types.name')} name="name" placeholder="Doble Estándar (opcional)" />
            </div>
            <div className="lg:col-span-2">
              <Checkbox checked={!!values.is_active} onChange={(v) => setFieldValue('is_active', v)} label={t('ota.room_types.is_active')} />
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}


