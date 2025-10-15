import React from 'react'
import { Formik } from 'formik'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectBasic from 'src/components/selects/SelectBasic'
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

  const timezoneOptions = React.useMemo(() => [
    { value: 'America/Argentina/Buenos_Aires', label: 'America/Argentina/Buenos_Aires' },
    { value: 'America/Bogota', label: 'America/Bogota' },
    { value: 'America/Mexico_City', label: 'America/Mexico_City' },
    { value: 'America/Lima', label: 'America/Lima' },
    { value: 'America/Santiago', label: 'America/Santiago' },
    { value: 'America/Montevideo', label: 'America/Montevideo' },
    { value: 'America/Sao_Paulo', label: 'America/Sao_Paulo' },
    { value: 'Atlantic/Canary', label: 'Atlantic/Canary' },
    { value: 'Europe/Madrid', label: 'Europe/Madrid' },
    { value: 'Europe/Lisbon', label: 'Europe/Lisbon' },
    { value: 'UTC', label: 'UTC' },
  ], [])

  const initialValues = {
    name: country?.name ?? '',
    code2: country?.code2 ?? '',
    code3: country?.code3 ?? '',
    phone_code: country?.phone_code ?? '',
    currency_code: country?.currency_code ?? '',
    timezone: country?.timezone ?? '',
    default_check_in_time: country?.default_check_in_time ?? '',
    default_check_out_time: country?.default_check_out_time ?? '',
  }

  const validationSchema = Yup.object().shape({
    name: Yup.string().required(t('countries_modal.name_required')),
    code2: Yup.string().length(2, t('countries_modal.iso2_length')).required(t('countries_modal.iso2_required')),
    code3: Yup.string().length(3, t('countries_modal.iso3_length')).nullable().transform((v, o) => (o === '' ? null : v)),
    timezone: Yup.string().nullable().transform((v, o) => (o === '' ? null : v)),
    default_check_in_time: Yup.string().matches(/^$|^\d{2}:\d{2}$/, t('countries_modal.time_format')).nullable().transform((v, o) => (o === '' ? null : v)),
    default_check_out_time: Yup.string().matches(/^$|^\d{2}:\d{2}$/, t('countries_modal.time_format')).nullable().transform((v, o) => (o === '' ? null : v)),
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
          timezone: values.timezone || undefined,
          default_check_in_time: values.default_check_in_time || undefined,
          default_check_out_time: values.default_check_out_time || undefined,
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
            <SelectBasic
              title={t('countries_modal.timezone')}
              name='timezone'
              placeholder='America/Argentina/Buenos_Aires'
              isClearable
              isSearchable
              options={timezoneOptions}
            />
            <InputText title={t('countries_modal.default_check_in_time')} name='default_check_in_time' placeholder='15:00' />
            <InputText title={t('countries_modal.default_check_out_time')} name='default_check_out_time' placeholder='11:00' />
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default CountriesModal
