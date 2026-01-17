import { Formik } from 'formik'
import * as Yup from 'yup'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import SelectAsync from 'src/components/selects/SelectAsync'
import InputText from 'src/components/inputs/InputText'
import InputTextTarea from 'src/components/inputs/InputTextTarea'
import Checkbox from 'src/components/Checkbox'
import HelpTooltip from 'src/components/HelpTooltip'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'

const PROVIDER_OPTIONS = [
  { value: 'ical', label: 'iCal' },
  { value: 'google', label: 'Google Calendar' },
  { value: 'smoobu', label: 'Smoobu' },
  { value: 'booking', label: 'Booking' },
  { value: 'airbnb', label: 'Airbnb' },
  { value: 'expedia', label: 'Expedia' },
  { value: 'other', label: 'Otro' },
]

export default function OtaConfigModal({ isOpen, onClose, isEdit = false, config, onSuccess }) {
  const { t } = useTranslation()

  const labelWithHelp = (label, helpText) => (
    <span className="inline-flex items-center gap-1">
      <span>{label}</span>
      <HelpTooltip text={helpText} />
    </span>
  )

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
    // Smoobu specific (persistido en backend dentro de credentials)
    smoobu_api_key: '',
    smoobu_base_url: (config?.credentials?.base_url ?? ''),
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
    // Smoobu
    smoobu_api_key: Yup.string().when('provider', {
      is: 'smoobu',
      then: (s) => s.required(t('common.required')),
      otherwise: (s) => s.nullable(),
    }),
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
          // Smoobu (write-only; backend lo guarda en credentials)
          smoobu_api_key: values.smoobu_api_key || undefined,
          smoobu_base_url: values.smoobu_base_url || undefined,
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

            <InputText
              title={labelWithHelp(
                t('ota.config.label'),
                'Opcional. Útil para identificar esta conexión (ej: "Smoobu Principal").'
              )}
              name="label"
              placeholder={t('ota.config.label_placeholder')}
            />
            <InputText 
              title={labelWithHelp(
                t('ota.config.ical_token'),
                'Solo aplica para export iCal (.ics). Para Smoobu no hace falta.'
              )} 
              name="ical_out_token" 
              placeholder={t('ota.config.ical_token_placeholder')}
              statusMessage={isEdit && config?.ical_out_token_masked ? `Actual: ${config.ical_out_token_masked}` : undefined}
              statusType={isEdit && config?.ical_out_token_masked ? 'info' : undefined}
            />

            {values.provider === 'smoobu' && (
              <>
                <InputText
                  title={labelWithHelp(
                    'Smoobu API Key *',
                    'Se obtiene en Smoobu → Settings/Configuración → API. Se envía como header "Api-Key".'
                  )}
                  name="smoobu_api_key"
                  placeholder="Api-Key (desde Smoobu)"
                  type="password"
                  autoComplete="new-password"
                  statusMessage={isEdit && config?.smoobu_api_key_masked ? `Actual: ${config.smoobu_api_key_masked}` : undefined}
                  statusType={isEdit && config?.smoobu_api_key_masked ? 'info' : undefined}
                />
                <InputText
                  title={labelWithHelp(
                    'Smoobu Base URL (opcional)',
                    'Normalmente es https://login.smoobu.com. Solo cambiar si Smoobu lo indica.'
                  )}
                  name="smoobu_base_url"
                  placeholder="https://login.smoobu.com"
                  statusMessage={config?.verified ? t('common.verified') : undefined}
                  statusType={config?.verified ? 'success' : undefined}
                />
                <div className="lg:col-span-2">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-sm text-blue-800 font-medium mb-1">
                      Checklist Smoobu (para que funcione)
                    </p>
                    <ol className="text-xs text-blue-700 list-decimal list-inside space-y-1">
                      <li>
                        Cargar esta <b>API Key</b> y guardar.
                      </li>
                      <li>
                        En <b>Mapeos por Habitación</b>, crear un mapeo por cada habitación con el <b>Apartment ID</b> de Smoobu.
                      </li>
                      <li>
                        Configurar el webhook en Smoobu apuntando a:
                        <div className="mt-1 font-mono text-[11px] break-all">
                          /api/otas/webhooks/smoobu/?token=TU_TOKEN
                        </div>
                      </li>
                      <li>
                        El token <b>TU_TOKEN</b> se define en el backend con <span className="font-mono">SMOOBU_WEBHOOK_TOKEN</span>.
                      </li>
                    </ol>
                  </div>
                </div>
              </>
            )}

            {values.provider === 'booking' && (
              <>
                <InputText title={t('ota.config.booking_hotel_id')} name="booking_hotel_id" placeholder="e.g. 123456" />
                <InputText title={t('ota.config.booking_client_id')} name="booking_client_id" placeholder="client id" autoComplete="off" />
                <InputText 
                  title={t('ota.config.booking_client_secret')} 
                  name="booking_client_secret" 
                  placeholder="client secret" 
                  type="password" 
                  autoComplete="new-password"
                  statusMessage={isEdit && config?.booking_client_secret_masked ? `Actual: ${config.booking_client_secret_masked}` : undefined}
                  statusType={isEdit && config?.booking_client_secret_masked ? 'info' : undefined}
                />
                <InputText 
                  title={t('ota.config.booking_base_url')} 
                  name="booking_base_url" 
                  placeholder="https://connectivity-sandbox.booking.com"
                  statusMessage={config?.verified ? t('common.verified') : (config?.booking_base_url ? t('common.not_verified') : undefined)}
                  statusType={config?.verified ? 'success' : (config?.booking_base_url ? 'warning' : undefined)}
                />
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
                <InputText 
                  title={t('ota.config.airbnb_client_secret')} 
                  name="airbnb_client_secret" 
                  placeholder="client secret" 
                  type="password" 
                  autoComplete="new-password"
                  statusMessage={isEdit && config?.airbnb_client_secret_masked ? `Actual: ${config.airbnb_client_secret_masked}` : undefined}
                  statusType={isEdit && config?.airbnb_client_secret_masked ? 'info' : undefined}
                />
                <InputText 
                  title={t('ota.config.airbnb_base_url')} 
                  name="airbnb_base_url" 
                  placeholder="https://httpbin.org"
                  statusMessage={config?.verified ? t('common.verified') : (config?.airbnb_base_url ? t('common.not_verified') : undefined)}
                  statusType={config?.verified ? 'success' : (config?.airbnb_base_url ? 'warning' : undefined)}
                />
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

            {values.provider === 'google' && (
              <div className="lg:col-span-2">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-2">
                  <p className="text-sm text-blue-800 font-medium mb-1">📋 Instrucciones para Google Calendar:</p>
                  <ol className="text-xs text-blue-700 list-decimal list-inside space-y-1">
                    <li>Crea una Service Account en Google Cloud Console</li>
                    <li>Descarga el JSON de la Service Account</li>
                    <li>Comparte tu calendario con el email de la Service Account</li>
                    <li>Pega el JSON completo aquí en este formato:</li>
                  </ol>
                  <pre className="text-xs bg-blue-100 p-2 rounded mt-2 overflow-x-auto">
{`{
  "service_account_json": {
    "type": "service_account",
    "project_id": "...",
    "private_key": "...",
    "client_email": "...",
    ...
  }
}`}
                  </pre>
                </div>
              </div>
            )}

            <div className="lg:col-span-2">
              <InputTextTarea 
                title={
                  values.provider === 'google'
                    ? 'Credenciales JSON (Service Account)'
                    : values.provider === 'smoobu'
                      ? labelWithHelp(
                          'Opciones avanzadas (JSON)',
                          'Opcional. Útil para: {"blocked_channel_id":11, "dry_run":true}. La API key/base_url se cargan arriba.'
                        )
                      : t('ota.config.credentials')
                } 
                name="credentials" 
                placeholder={
                  values.provider === 'google'
                    ? 'Pega el JSON completo de la Service Account dentro de {"service_account_json": {...}}'
                    : values.provider === 'smoobu'
                      ? '{\n  "blocked_channel_id": 11,\n  "dry_run": false\n}'
                      : t('ota.config.credentials_placeholder')
                } 
              />
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


