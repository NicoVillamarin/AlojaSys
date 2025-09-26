import { Formik } from 'formik'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'

const CitiesModal = ({ isOpen, onClose, isEdit = false, city, onSuccess }) => {
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
    state: Yup.string().required('Provincia/Estado es requerido'),
    name: Yup.string().required('Nombre es requerido'),
    lat: Yup.number().transform((v, o) => (o === '' ? undefined : v)).typeError('Lat debe ser número').nullable(),
    lng: Yup.number().transform((v, o) => (o === '' ? undefined : v)).typeError('Lng debe ser número').nullable(),
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
          title={isEdit ? 'Editar ciudad' : 'Crear ciudad'}
          onSubmit={handleSubmit}
          submitText={isEdit ? 'Guardar cambios' : 'Crear'}
          cancelText='Cancelar'
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='md'
        >
          <div className='grid grid-cols-1 md:grid-cols-2 gap-5'>
            <SelectAsync
              title='Provincia/Estado *'
              name='state'
              resource='states'
              placeholder='Buscar provincia…'
              getOptionLabel={(s) => `${s?.name} (${s?.country_code2})`}
              getOptionValue={(s) => s?.id}
            />
            <InputText title='Nombre *' name='name' placeholder='CABA' />
            <InputText title='CP' name='postal_code' placeholder='1000' />
            <InputText title='Lat' name='lat' placeholder='-34.6037' />
            <InputText title='Lng' name='lng' placeholder='-58.3816' />
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default CitiesModal