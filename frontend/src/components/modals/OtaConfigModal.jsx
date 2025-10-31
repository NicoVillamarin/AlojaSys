import { Formik } from 'formik'
import * as Yup from 'yup'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import SelectAsync from 'src/components/selects/SelectAsync'
import InputText from 'src/components/inputs/InputText'
import InputTextTarea from 'src/components/inputs/InputTextTarea'
import Checkbox from 'src/components/Checkbox'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'

const PROVIDER_OPTIONS = [
  { value: 'ical', label: 'iCal' },
  { value: 'booking', label: 'Booking' },
  { value: 'airbnb', label: 'Airbnb' },
  { value: 'expedia', label: 'Expedia' },
  { value: 'other', label: 'Otro' },
]

export default function OtaConfigModal({ isOpen, onClose, isEdit = false, config, onSuccess }) {
  const { t } = useTranslation()

  const { mutate: createItem, isPending: creating } = useCreate({
    resource: 'otas/configs',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  const { mutate: updateItem, isPending: updating } = useUpdate({
    resource: 'otas/configs',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const initialValues = {
    hotel: config?.hotel ?? '',
    provider: config?.provider ?? 'ical',
    label: config?.label ?? '',
    is_active: config?.is_active ?? true,
    ical_out_token: config?.ical_out_token ?? '',
    credentials: config?.credentials ? JSON.stringify(config.credentials, null, 2) : '',
    // Booking specific
    booking_hotel_id: config?.booking_hotel_id ?? '',
    booking_client_id: config?.booking_client_id ?? '',
    booking_client_secret: config?.booking_client_secret ?? '',
    booking_base_url: config?.booking_base_url ?? '',
    booking_mode: config?.booking_mode ?? 'test',
    // Airbnb specific
    airbnb_account_id: config?.airbnb_account_id ?? '',
    airbnb_client_id: config?.airbnb_client_id ?? '',
    airbnb_client_secret: config?.airbnb_client_secret ?? '',
    airbnb_base_url: config?.airbnb_base_url ?? '',
    airbnb_mode: config?.airbnb_mode ?? 'test',
  }

  const validationSchema = Yup.object().shape({
    hotel: Yup.number().required(t('common.required')),
    provider: Yup.string().required(t('common.required')),
    label: Yup.string().max(120, t('common.max_chars', { count: 120 })).nullable(),
    ical_out_token: Yup.string().max(64, t('common.max_chars', { count: 64 })).nullable(),
    credentials: Yup.string().test('is-json', t('common.invalid_json'), (val) => {
      if (!val) return true
      try { JSON.parse(val) } catch { return false }
      return true
    }),
    // Booking: si provider es booking, validar mínimos
    booking_hotel_id: Yup.string().when('provider', {
      is: 'booking',
      then: (s) => s.required(t('common.required')),
      otherwise: (s) => s.nullable(),
    }),
    booking_mode: Yup.string().oneOf(['test', 'prod']).nullable(),
    // Airbnb
    airbnb_account_id: Yup.string().when('provider', {
      is: 'airbnb',
      then: (s) => s.required(t('common.required')),
      otherwise: (s) => s.nullable(),
    }),
    airbnb_mode: Yup.string().oneOf(['test', 'prod']).nullable(),
  })

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          hotel: values.hotel ? Number(values.hotel) : undefined,
          provider: values.provider || undefined,
          label: values.label || undefined,
          is_active: !!values.is_active,
          ical_out_token: values.ical_out_token || undefined,
              credentials: values.credentials ? JSON.parse(values.credentials) : {},
              // Booking
              booking_hotel_id: values.booking_hotel_id || undefined,
              booking_client_id: values.booking_client_id || undefined,
              booking_client_secret: values.booking_client_secret || undefined,
              booking_base_url: values.booking_base_url || undefined,
              booking_mode: values.booking_mode || undefined,
              // Airbnb
              airbnb_account_id: values.airbnb_account_id || undefined,
              airbnb_client_id: values.airbnb_client_id || undefined,
              airbnb_client_secret: values.airbnb_client_secret || undefined,
              airbnb_base_url: values.airbnb_base_url || undefined,
              airbnb_mode: values.airbnb_mode || undefined,
        }
        if (isEdit && config?.id) updateItem({ id: config.id, body: payload })
        else createItem(payload)
      }}
    >
      {({ handleSubmit, values, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('ota.config.edit_title') : t('ota.config.create_title')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('reservations_modal.save_changes') : t('common.create')}
          cancelText={t('common.cancel')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size="md"
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5">
            <SelectAsync
              title={`${t('ota.config.hotel')} *`}
              name="hotel"
              resource="hotels"
              placeholder={t('ota.config.hotel_placeholder')}
              getOptionLabel={(h) => h?.name}
              getOptionValue={(h) => h?.id}
              value={values.hotel}
            />

            <div>
              <label className="block text-sm font-medium text-aloja-navy mb-1">{t('ota.config.provider')} *</label>
              <select
                className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-full"
                value={values.provider}
                onChange={(e) => setFieldValue('provider', e.target.value)}
              >
                {PROVIDER_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>

            <InputText title={t('ota.config.label')} name="label" placeholder={t('ota.config.label_placeholder')} />
            <InputText title={t('ota.config.ical_token')} name="ical_out_token" placeholder={t('ota.config.ical_token_placeholder')} />

            {values.provider === 'booking' && (
              <>
                <InputText title={t('ota.config.booking_hotel_id')} name="booking_hotel_id" placeholder="e.g. 123456" />
                <InputText title={t('ota.config.booking_client_id')} name="booking_client_id" placeholder="client id" autoComplete="off" />
                <InputText title={t('ota.config.booking_client_secret')} name="booking_client_secret" placeholder="client secret" type="password" autoComplete="new-password" />
                <InputText title={t('ota.config.booking_base_url')} name="booking_base_url" placeholder="https://connectivity-sandbox.booking.com" />
                <div>
                  <label className="block text-sm font-medium text-aloja-navy mb-1">{t('ota.config.booking_mode')}</label>
                  <select
                    className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-full"
                    value={values.booking_mode}
                    onChange={(e) => setFieldValue('booking_mode', e.target.value)}
                  >
                    <option value="test">{t('ota.config.booking_mode_test')}</option>
                    <option value="prod">{t('ota.config.booking_mode_prod')}</option>
                  </select>
                </div>
              </>
            )}

            {values.provider === 'airbnb' && (
              <>
                <InputText title={t('ota.config.airbnb_account_id')} name="airbnb_account_id" placeholder="e.g. test-account" />
                <InputText title={t('ota.config.airbnb_client_id')} name="airbnb_client_id" placeholder="client id" autoComplete="off" />
                <InputText title={t('ota.config.airbnb_client_secret')} name="airbnb_client_secret" placeholder="client secret" type="password" autoComplete="new-password" />
                <InputText title={t('ota.config.airbnb_base_url')} name="airbnb_base_url" placeholder="https://httpbin.org" />
                <div>
                  <label className="block text-sm font-medium text-aloja-navy mb-1">{t('ota.config.airbnb_mode')}</label>
                  <select
                    className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-full"
                    value={values.airbnb_mode}
                    onChange={(e) => setFieldValue('airbnb_mode', e.target.value)}
                  >
                    <option value="test">{t('ota.config.booking_mode_test')}</option>
                    <option value="prod">{t('ota.config.booking_mode_prod')}</option>
                  </select>
                </div>
              </>
            )}

            <div className="lg:col-span-2">
              <InputTextTarea title={t('ota.config.credentials')} name="credentials" placeholder={t('ota.config.credentials_placeholder')} />
            </div>

            <div className="lg:col-span-2">
              <Checkbox
                checked={!!values.is_active}
                onChange={(v) => setFieldValue('is_active', v)}
                label={t('ota.config.is_active')}
              />
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}


