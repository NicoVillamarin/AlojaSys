import { Formik } from 'formik'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'

const CountriesModal = ({ isOpen, onClose, isEdit = false, country, onSuccess }) => {
  const { t } = useTranslation()
  const { mutate: createCountry, isPending: creating } = useCreate({
    resource: 'countries',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  const { mutate: updateCountry, isPending: updating } = useUpdate({
    resource: 'countries',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const initialValues = {
    name: country?.name ?? '',
    code2: country?.code2 ?? '',
    code3: country?.code3 ?? '',
    phone_code: country?.phone_code ?? '',
    currency_code: country?.currency_code ?? '',
  }

  const validationSchema = Yup.object().shape({
    name: Yup.string().required(t('countries_modal.name_required')),
    code2: Yup.string().length(2, t('countries_modal.iso2_length')).required(t('countries_modal.iso2_required')),
    code3: Yup.string().length(3, t('countries_modal.iso3_length')).nullable().transform((v, o) => (o === '' ? null : v)),
  })

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          name: values.name || undefined,
          code2: values.code2 ? values.code2.toUpperCase() : undefined,
          code3: values.code3 ? values.code3.toUpperCase() : undefined,
          phone_code: values.phone_code || undefined,
          currency_code: values.currency_code ? values.currency_code.toUpperCase() : undefined,
        }
        if (isEdit && country?.id) updateCountry({ id: country.id, body: payload })
        else createCountry(payload)
      }}
    >
      {({ handleSubmit }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('countries_modal.edit_country') : t('countries_modal.create_country')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('countries_modal.save_changes') : t('countries_modal.create')}
          cancelText={t('countries_modal.cancel')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='md'
        >
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5'>
            <InputText title={`${t('countries_modal.name')} *`} name='name' placeholder={t('countries_modal.name_placeholder')} autoFocus />
            <InputText title={`${t('countries_modal.iso2')} *`} name='code2' placeholder={t('countries_modal.iso2_placeholder')} />
            <InputText title={t('countries_modal.iso3')} name='code3' placeholder={t('countries_modal.iso3_placeholder')} />
            <InputText title={t('countries_modal.phone_code')} name='phone_code' placeholder={t('countries_modal.phone_code_placeholder')} />
            <InputText title={t('countries_modal.currency_code')} name='currency_code' placeholder={t('countries_modal.currency_code_placeholder')} />
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default CountriesModal
