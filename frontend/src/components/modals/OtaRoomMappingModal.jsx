import { Formik } from 'formik'
import * as Yup from 'yup'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import SelectAsync from 'src/components/selects/SelectAsync'
import InputText from 'src/components/inputs/InputText'
import Checkbox from 'src/components/Checkbox'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'

export default function OtaRoomMappingModal({ isOpen, onClose, isEdit = false, mapping, defaultHotelId, onSuccess }) {
  const { t } = useTranslation()

  const { mutate: createItem, isPending: creating } = useCreate({
    resource: 'otas/mappings',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  const { mutate: updateItem, isPending: updating } = useUpdate({
    resource: 'otas/mappings',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const initialValues = {
    hotel: mapping?.hotel ?? defaultHotelId ?? '',
    room: mapping?.room ?? '',
    provider: mapping?.provider ?? 'ical',
    external_id: mapping?.external_id ?? '',
    ical_in_url: mapping?.ical_in_url ?? '',
    sync_direction: mapping?.sync_direction ?? 'both',
    is_active: mapping?.is_active ?? true,
  }

  const validationSchema = Yup.object().shape({
    hotel: Yup.number().required(t('common.required')),
    room: Yup.number().required(t('common.required')),
    provider: Yup.string().required(t('common.required')),
    ical_in_url: Yup.string().url(t('common.invalid_url')).nullable(),
  })

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          hotel: values.hotel ? Number(values.hotel) : undefined,
          room: values.room ? Number(values.room) : undefined,
          provider: values.provider || undefined,
          external_id: values.external_id || undefined,
          ical_in_url: values.ical_in_url || undefined,
          sync_direction: values.sync_direction || 'both',
          is_active: !!values.is_active,
        }
        if (isEdit && mapping?.id) updateItem({ id: mapping.id, body: payload })
        else createItem(payload)
      }}
    >
      {({ handleSubmit, values, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('ota.mappings.edit_title') : t('ota.mappings.create_title')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('common.save_changes') : t('common.create')}
          cancelText={t('common.cancel')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size="md"
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5">
            <SelectAsync
              title={`${t('ota.mappings.hotel')} *`}
              name="hotel"
              resource="hotels"
              placeholder={t('ota.mappings.hotel_placeholder')}
              getOptionLabel={(h) => h?.name}
              getOptionValue={(h) => h?.id}
              value={values.hotel}
              onChange={(val) => { setFieldValue('hotel', val); setFieldValue('room', '') }}
            />

            <SelectAsync
              title={`${t('ota.mappings.room')} *`}
              name="room"
              resource="rooms"
              params={{ hotel: values.hotel || undefined }}
              placeholder={t('ota.mappings.room_placeholder')}
              getOptionLabel={(r) => r?.name || `#${r?.id}`}
              getOptionValue={(r) => r?.id}
              value={values.room}
            />

            <div>
              <label className="block text-sm font-medium text-aloja-navy mb-1">{t('ota.mappings.provider')} *</label>
              <select
                className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-full"
                value={values.provider}
                onChange={(e) => setFieldValue('provider', e.target.value)}
              >
                <option value="ical">iCal</option>
                <option value="booking">Booking</option>
                <option value="airbnb">Airbnb</option>
                <option value="expedia">Expedia</option>
                <option value="other">{t('common.other')}</option>
              </select>
            </div>

            <InputText title={t('ota.mappings.external_id')} name="external_id" placeholder={t('ota.mappings.external_id_placeholder')} />
            <div className="lg:col-span-2">
              <InputText title={t('ota.mappings.ical_in_url')} name="ical_in_url" placeholder={t('ota.mappings.ical_in_url_placeholder')} />
            </div>

            <div>
              <label className="block text-sm font-medium text-aloja-navy mb-1">{t('ota.mappings.sync_direction')}</label>
              <select
                className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-full"
                value={values.sync_direction}
                onChange={(e) => setFieldValue('sync_direction', e.target.value)}
              >
                <option value="both">{t('ota.mappings.sync_direction_both')}</option>
                <option value="import">{t('ota.mappings.sync_direction_import')}</option>
                <option value="export">{t('ota.mappings.sync_direction_export')}</option>
              </select>
            </div>

            <div className="lg:col-span-2">
              <Checkbox
                checked={!!values.is_active}
                onChange={(v) => setFieldValue('is_active', v)}
                label={t('ota.mappings.is_active')}
              />
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}


