import { Formik } from 'formik'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import SelectBasic from 'src/components/selects/SelectBasic'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import { useQueryClient } from '@tanstack/react-query'

// Defaults por plan (deben reflejar backend/apps/enterprises/features.py)
const PLAN_DEFAULT_FEATURES = {
  basic: {
    afip: false,
    mercado_pago: false,
    whatsapp_bot: false,
    otas: false,
    housekeeping_advanced: false,
    bank_reconciliation: false,
  },
  medium: {
    afip: true,
    mercado_pago: true,
    whatsapp_bot: true,
    otas: false,
    housekeeping_advanced: false,
    bank_reconciliation: false,
  },
  full: {
    afip: true,
    mercado_pago: true,
    whatsapp_bot: true,
    otas: true,
    housekeeping_advanced: true,
    bank_reconciliation: true,
  },
  custom: {},
}

/**
 * EnterpriseModal: crear/editar empresa
 */
const EnterpriseModal = ({ isOpen, onClose, isEdit = false, enterprise, onSuccess }) => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const { mutate: createEnterprise, isPending: creating } = useCreate({
    resource: 'enterprises',
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['enterprises'] })
      onSuccess && onSuccess(data); onClose && onClose()
    },
  })
  const { mutate: updateEnterprise, isPending: updating } = useUpdate({
    resource: 'enterprises',
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['enterprises'] })
      onSuccess && onSuccess(data); onClose && onClose()
    },
  })

  const initialValues = {
    name: enterprise?.name ?? '',
    legal_name: enterprise?.legal_name ?? '',
    tax_id: enterprise?.tax_id ?? '',
    email: enterprise?.email ?? '',
    phone: enterprise?.phone ?? '',
    address: enterprise?.address ?? '',
    country: enterprise?.country ?? '',
    state: enterprise?.state ?? '',
    city: enterprise?.city ?? '',
    plan_type: enterprise?.plan_type ?? 'basic',
    enabled_features: enterprise?.enabled_features ?? {},
    is_active: enterprise?.is_active ?? true,
  }

  const validationSchema = Yup.object().shape({
    name: Yup.string().required(t('enterprise_modal.name_required')),
    email: Yup.string().email(t('enterprise_modal.email_invalid')).nullable(),
  })

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          name: values.name || undefined,
          legal_name: values.legal_name || undefined,
          tax_id: values.tax_id || undefined,
          email: values.email || undefined,
          phone: values.phone || undefined,
          address: values.address || undefined,
          country: values.country ? Number(values.country) : undefined,
          state: values.state ? Number(values.state) : undefined,
          city: values.city ? Number(values.city) : undefined,
          plan_type: values.plan_type || 'basic',
          // En planes no-custom, se limpian overrides para que mande el plan.
          enabled_features: values.plan_type === 'custom' ? (values.enabled_features || {}) : {},
          is_active: !!values.is_active,
        }
        if (isEdit && enterprise?.id) updateEnterprise({ id: enterprise.id, body: payload })
        else createEnterprise(payload)
      }}
    >
      {({ values, handleSubmit, setFieldValue }) => (
        (() => {
          const planKey = (values.plan_type || 'basic').toLowerCase()
          const effectiveFeatures =
            values.plan_type === 'custom'
              ? (values.enabled_features || {})
              : (PLAN_DEFAULT_FEATURES[planKey] || PLAN_DEFAULT_FEATURES.basic)

          return (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('enterprise_modal.edit_enterprise') : t('enterprise_modal.create_enterprise')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('enterprise_modal.save_changes') : t('enterprise_modal.create')}
          cancelText={t('enterprise_modal.cancel')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='lg'
        >
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5'>
            <InputText title={`${t('enterprise_modal.name')} *`} name='name' placeholder={t('enterprise_modal.name_placeholder')} autoFocus />
            <InputText title={t('enterprise_modal.legal_name')} name='legal_name' placeholder={t('enterprise_modal.legal_name_placeholder')} />
            <InputText title={t('enterprise_modal.tax_id')} name='tax_id' placeholder={t('enterprise_modal.tax_id_placeholder')} />
            <InputText title={t('enterprise_modal.email')} name='email' placeholder={t('enterprise_modal.email_placeholder')} />
            <InputText title={t('enterprise_modal.phone')} name='phone' placeholder={t('enterprise_modal.phone_placeholder')} />
            <InputText title={t('enterprise_modal.address')} name='address' placeholder={t('enterprise_modal.address_placeholder')} />
            <SelectAsync
              title={t('enterprise_modal.country')}
              name='country'
              resource='countries'
              placeholder={t('enterprise_modal.country_placeholder')}
              getOptionLabel={(c) => c?.name}
              getOptionValue={(c) => c?.id}
              onValueChange={() => { setFieldValue('state', ''); setFieldValue('city', '') }}
            />
            <SelectAsync
              title={t('enterprise_modal.state')}
              name='state'
              resource='states'
              placeholder={t('enterprise_modal.state_placeholder')}
              extraParams={{ country: values.country || undefined }}
              getOptionLabel={(s) => s?.name}
              getOptionValue={(s) => s?.id}
              onValueChange={() => { setFieldValue('city', '') }}
            />
            <SelectAsync
              title={t('enterprise_modal.city')}
              name='city'
              resource='cities'
              placeholder={t('enterprise_modal.city_placeholder')}
              extraParams={{ state: values.state || undefined, country: values.country || undefined }}
              getOptionLabel={(c) => c?.name}
              getOptionValue={(c) => c?.id}
            />

            <div className='md:col-span-2 border-t pt-3 mt-1 space-y-3'>
              <div>
                <SelectBasic
                  title={t('enterprise_modal.plan_type')}
                  name='plan_type'
                  options={[
                    { value: 'basic', label: t('enterprise_modal.plan_basic') },
                    { value: 'medium', label: t('enterprise_modal.plan_medium') },
                    { value: 'full', label: t('enterprise_modal.plan_full') },
                    { value: 'custom', label: t('enterprise_modal.plan_custom') },
                  ]}
                  placeholder={t('enterprise_modal.plan_type')}
                  isSearchable={false}
                  onChangeExtra={(newValue) => {
                    const newPlan = newValue
                    setFieldValue('plan_type', newPlan)
                    if (newPlan !== 'custom') {
                      // Al salir de custom, limpiamos overrides para usar solo defaults de backend
                      setFieldValue('enabled_features', {})
                    }
                  }}
                />
                <p className='mt-1 text-[11px] text-aloja-gray-800/70'>
                  {t('enterprise_modal.plan_help')}
                </p>
              </div>

              <div>
                <label className='block text-xs text-aloja-gray-800/70 mb-1'>
                  {t('enterprise_modal.features_title')}
                </label>
                <div className='grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm'>
                  <label className={`flex items-center gap-2 ${values.plan_type !== 'custom' ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}>
                    <input
                      type='checkbox'
                      disabled={values.plan_type !== 'custom'}
                      checked={!!effectiveFeatures?.afip}
                      onChange={(e) =>
                        setFieldValue('enabled_features', {
                          ...values.enabled_features,
                          afip: e.target.checked,
                        })
                      }
                    />
                    <span>{t('enterprise_modal.feature_afip')}</span>
                    <span className={`ml-auto text-[11px] font-medium ${effectiveFeatures?.afip ? 'text-emerald-200' : 'text-white/70'}`}>
                      {effectiveFeatures?.afip ? t('common.included', 'Incluido') : t('common.not_included', 'No incluido')}
                    </span>
                  </label>
                  <label className={`flex items-center gap-2 ${values.plan_type !== 'custom' ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}>
                    <input
                      type='checkbox'
                      disabled={values.plan_type !== 'custom'}
                      checked={!!effectiveFeatures?.mercado_pago}
                      onChange={(e) =>
                        setFieldValue('enabled_features', {
                          ...values.enabled_features,
                          mercado_pago: e.target.checked,
                        })
                      }
                    />
                    <span>{t('enterprise_modal.feature_mp')}</span>
                    <span className={`ml-auto text-[11px] font-medium ${effectiveFeatures?.mercado_pago ? 'text-emerald-200' : 'text-white/70'}`}>
                      {effectiveFeatures?.mercado_pago ? t('common.included', 'Incluido') : t('common.not_included', 'No incluido')}
                    </span>
                  </label>
                  <label className={`flex items-center gap-2 ${values.plan_type !== 'custom' ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}>
                    <input
                      type='checkbox'
                      disabled={values.plan_type !== 'custom'}
                      checked={!!effectiveFeatures?.whatsapp_bot}
                      onChange={(e) =>
                        setFieldValue('enabled_features', {
                          ...values.enabled_features,
                          whatsapp_bot: e.target.checked,
                        })
                      }
                    />
                    <span>{t('enterprise_modal.feature_whatsapp')}</span>
                    <span className={`ml-auto text-[11px] font-medium ${effectiveFeatures?.whatsapp_bot ? 'text-emerald-200' : 'text-white/70'}`}>
                      {effectiveFeatures?.whatsapp_bot ? t('common.included', 'Incluido') : t('common.not_included', 'No incluido')}
                    </span>
                  </label>
                  <label className={`flex items-center gap-2 ${values.plan_type !== 'custom' ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}>
                    <input
                      type='checkbox'
                      disabled={values.plan_type !== 'custom'}
                      checked={!!effectiveFeatures?.otas}
                      onChange={(e) =>
                        setFieldValue('enabled_features', {
                          ...values.enabled_features,
                          otas: e.target.checked,
                        })
                      }
                    />
                    <span>{t('enterprise_modal.feature_otas')}</span>
                    <span className={`ml-auto text-[11px] font-medium ${effectiveFeatures?.otas ? 'text-emerald-200' : 'text-white/70'}`}>
                      {effectiveFeatures?.otas ? t('common.included', 'Incluido') : t('common.not_included', 'No incluido')}
                    </span>
                  </label>
                  <label className={`flex items-center gap-2 ${values.plan_type !== 'custom' ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}>
                    <input
                      type='checkbox'
                      disabled={values.plan_type !== 'custom'}
                      checked={!!effectiveFeatures?.housekeeping_advanced}
                      onChange={(e) =>
                        setFieldValue('enabled_features', {
                          ...values.enabled_features,
                          housekeeping_advanced: e.target.checked,
                        })
                      }
                    />
                    <span>{t('enterprise_modal.feature_housekeeping')}</span>
                    <span className={`ml-auto text-[11px] font-medium ${effectiveFeatures?.housekeeping_advanced ? 'text-emerald-200' : 'text-white/70'}`}>
                      {effectiveFeatures?.housekeeping_advanced ? t('common.included', 'Incluido') : t('common.not_included', 'No incluido')}
                    </span>
                  </label>
                  <label className={`flex items-center gap-2 ${values.plan_type !== 'custom' ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}>
                    <input
                      type='checkbox'
                      disabled={values.plan_type !== 'custom'}
                      checked={!!effectiveFeatures?.bank_reconciliation}
                      onChange={(e) =>
                        setFieldValue('enabled_features', {
                          ...values.enabled_features,
                          bank_reconciliation: e.target.checked,
                        })
                      }
                    />
                    <span>{t('enterprise_modal.feature_bank_reconciliation')}</span>
                    <span className={`ml-auto text-[11px] font-medium ${effectiveFeatures?.bank_reconciliation ? 'text-emerald-200' : 'text-white/70'}`}>
                      {effectiveFeatures?.bank_reconciliation ? t('common.included', 'Incluido') : t('common.not_included', 'No incluido')}
                    </span>
                  </label>
                </div>
                {values.plan_type !== 'custom' && (
                  <p className='mt-1 text-[11px] text-aloja-gray-800/60'>
                    {t('enterprise_modal.features_readonly_info')}
                  </p>
                )}
              </div>
            </div>
            <div className='md:col-span-2'>
              <label className='text-xs text-aloja-gray-800/70'>{t('enterprise_modal.active')}</label>
              <label htmlFor='is_active' className='flex items-center gap-2 cursor-pointer'>
                <input
                  id='is_active'
                  name='is_active'
                  type='checkbox'
                  className='rounded border-gray-300'
                  checked={!!values.is_active}
                  onChange={(e) => setFieldValue('is_active', e.target.checked)}
                />
                <span className='text-sm text-aloja-gray-800/80'>{t('enterprise_modal.enabled')}</span>
              </label>
            </div>
          </div>
        </ModalLayout>
          )
        })()
      )}
    </Formik>
  )
}

export default EnterpriseModal