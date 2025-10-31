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

export default function OtaRatePlanMappingModal({ isOpen, onClose, isEdit = false, mapping, defaultHotelId, onSuccess }) {
  const { t } = useTranslation()
  const { results: hotels } = useList({ resource: 'hotels' })

  const { mutate: createItem, isPending: creating } = useCreate({ resource: 'otas/rate-plan-mappings', onSuccess: (d) => { onSuccess && onSuccess(d); onClose && onClose() } })
  const { mutate: updateItem, isPending: updating } = useUpdate({ resource: 'otas/rate-plan-mappings', onSuccess: (d) => { onSuccess && onSuccess(d); onClose && onClose() } })

  const initialValues = {
    hotel: mapping?.hotel ?? defaultHotelId ?? '',
    provider: mapping?.provider ?? 'booking',
    rate_plan_code: mapping?.rate_plan_code ?? '',
    provider_code: mapping?.provider_code ?? '',
    currency: mapping?.currency ?? 'ARS',
    is_active: mapping?.is_active ?? true,
  }

  const validationSchema = Yup.object().shape({
    hotel: Yup.number().required(t('common.required')),
    provider: Yup.string().required(t('common.required')),
    rate_plan_code: Yup.string().required(t('common.required')),
    provider_code: Yup.string().required(t('common.required')),
    currency: Yup.string().required(t('common.required')),
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
          title={isEdit ? t('ota.rate_plans.edit_title') : t('ota.rate_plans.create_title')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('common.save_changes') : t('common.create')}
          cancelText={t('common.cancel')}
          size="md"
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5">
            <SelectStandalone
              title={t('ota.rate_plans.hotel')}
              options={hotels}
              placeholder={t('ota.filters.hotel_placeholder')}
              value={hotels.find(h => String(h.id) === String(values.hotel)) || null}
              onChange={(opt) => setFieldValue('hotel', opt ? opt.id : '')}
              getOptionLabel={(h) => h?.name}
              getOptionValue={(h) => h?.id}
            />

            <div>
              <label className="block text-sm font-medium text-aloja-navy mb-1">{t('ota.rate_plans.provider')} *</label>
              <select className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full" value={values.provider} onChange={(e) => setFieldValue('provider', e.target.value)}>
                <option value="booking">Booking</option>
                <option value="airbnb">Airbnb</option>
              </select>
            </div>

            <InputText title={t('ota.rate_plans.rate_plan_code')} name="rate_plan_code" placeholder="STANDARD" />
            <InputText title={t('ota.rate_plans.provider_code')} name="provider_code" placeholder="STD_NONREF" />
            <InputText title={t('ota.rate_plans.currency')} name="currency" placeholder="ARS" />
            <div className="lg:col-span-2">
              <Checkbox checked={!!values.is_active} onChange={(v) => setFieldValue('is_active', v)} label={t('ota.rate_plans.is_active')} />
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}


