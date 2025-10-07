import { Formik } from 'formik'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'

const CitiesModal = ({ isOpen, onClose, isEdit = false, city, onSuccess }) => {
  const { t } = useTranslation()
  const { mutate: createCity, isPending: creating } = useCreate({
    resource: 'cities',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  const { mutate: updateCity, isPending: updating } = useUpdate({
    resource: 'cities',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const initialValues = {
    state: city?.state ?? '',
    name: city?.name ?? '',
    postal_code: city?.postal_code ?? '',
    lat: city?.lat != null ? String(city.lat) : '',
    lng: city?.lng != null ? String(city.lng) : '',
  }

  const validationSchema = Yup.object().shape({
    state: Yup.string().required(t('cities_modal.state_required')),
    name: Yup.string().required(t('cities_modal.name_required')),
    lat: Yup.number().transform((v, o) => (o === '' ? undefined : v)).typeError(t('cities_modal.lat_number')).nullable(),
    lng: Yup.number().transform((v, o) => (o === '' ? undefined : v)).typeError(t('cities_modal.lng_number')).nullable(),
  })

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          state: values.state ? Number(values.state) : undefined,
          name: values.name || undefined,
          postal_code: values.postal_code || undefined,
          lat: values.lat !== '' ? Number(values.lat) : undefined,
          lng: values.lng !== '' ? Number(values.lng) : undefined,
        }
        if (isEdit && city?.id) updateCity({ id: city.id, body: payload })
        else createCity(payload)
      }}
    >
      {({ handleSubmit }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('cities_modal.edit_city') : t('cities_modal.create_city')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('cities_modal.save_changes') : t('cities_modal.create')}
          cancelText={t('cities_modal.cancel')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='md'
        >
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5'>
            <SelectAsync
              title={`${t('cities_modal.state')} *`}
              name='state'
              resource='states'
              placeholder={t('cities_modal.state_placeholder')}
              getOptionLabel={(s) => `${s?.name} (${s?.country_code2})`}
              getOptionValue={(s) => s?.id}
            />
            <InputText title={`${t('cities_modal.name')} *`} name='name' placeholder={t('cities_modal.name_placeholder')} />
            <InputText title={t('cities_modal.postal_code')} name='postal_code' placeholder={t('cities_modal.postal_code_placeholder')} />
            <InputText title={t('cities_modal.lat')} name='lat' placeholder={t('cities_modal.lat_placeholder')} />
            <InputText title={t('cities_modal.lng')} name='lng' placeholder={t('cities_modal.lng_placeholder')} />
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default CitiesModal