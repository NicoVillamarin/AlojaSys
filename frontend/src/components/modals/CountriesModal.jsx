import { Formik } from 'formik'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'

const CountriesModal = ({ isOpen, onClose, isEdit = false, country, onSuccess }) => {
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
    name: Yup.string().required('Nombre es requerido'),
    code2: Yup.string().length(2, 'Debe tener 2 caracteres').required('ISO2 es requerido'),
    code3: Yup.string().length(3, 'Debe tener 3 caracteres').nullable().transform((v, o) => (o === '' ? null : v)),
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
          title={isEdit ? 'Editar país' : 'Crear país'}
          onSubmit={handleSubmit}
          submitText={isEdit ? 'Guardar cambios' : 'Crear'}
          cancelText='Cancelar'
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='md'
        >
          <div className='grid grid-cols-1 md:grid-cols-2 gap-5'>
            <InputText title='Nombre *' name='name' placeholder='Argentina' autoFocus />
            <InputText title='ISO2 *' name='code2' placeholder='AR' />
            <InputText title='ISO3' name='code3' placeholder='ARG' />
            <InputText title='Tel. país' name='phone_code' placeholder='+54' />
            <InputText title='Moneda' name='currency_code' placeholder='ARS' />
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default CountriesModal
