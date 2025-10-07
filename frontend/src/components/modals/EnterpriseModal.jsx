import { Formik } from 'formik'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'

/**
 * EnterpriseModal: crear/editar empresa
 */
const EnterpriseModal = ({ isOpen, onClose, isEdit = false, enterprise, onSuccess }) => {
  const { t } = useTranslation()
  const { mutate: createEnterprise, isPending: creating } = useCreate({
    resource: 'enterprises',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  const { mutate: updateEnterprise, isPending: updating } = useUpdate({
    resource: 'enterprises',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
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
          is_active: !!values.is_active,
        }
        if (isEdit && enterprise?.id) updateEnterprise({ id: enterprise.id, body: payload })
        else createEnterprise(payload)
      }}
    >
      {({ values, handleSubmit, setFieldValue }) => (
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
      )}
    </Formik>
  )
}

export default EnterpriseModal