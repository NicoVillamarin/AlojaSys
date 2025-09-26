import { Formik } from 'formik'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'

const StatesModal = ({ isOpen, onClose, isEdit = false, stateItem, onSuccess }) => {
  const { mutate: createState, isPending: creating } = useCreate({
    resource: 'states',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  const { mutate: updateState, isPending: updating } = useUpdate({
    resource: 'states',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const initialValues = {
    country: stateItem?.country ?? '',
    name: stateItem?.name ?? '',
    code: stateItem?.code ?? '',
  }

  const validationSchema = Yup.object().shape({
    country: Yup.string().required('País es requerido'),
    name: Yup.string().required('Nombre es requerido'),
  })

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          country: values.country ? Number(values.country) : undefined,
          name: values.name || undefined,
          code: values.code || undefined,
        }
        if (isEdit && stateItem?.id) updateState({ id: stateItem.id, body: payload })
        else createState(payload)
      }}
    >
      {({ handleSubmit }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? 'Editar provincia/estado' : 'Crear provincia/estado'}
          onSubmit={handleSubmit}
          submitText={isEdit ? 'Guardar cambios' : 'Crear'}
          cancelText='Cancelar'
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='md'
        >
          <div className='grid grid-cols-1 md:grid-cols-2 gap-5'>
            <SelectAsync
              title='País *'
              name='country'
              resource='countries'
              placeholder='Buscar país…'
              getOptionLabel={(c) => c?.name}
              getOptionValue={(c) => c?.id}
            />
            <InputText title='Nombre *' name='name' placeholder='Buenos Aires' />
            <InputText title='Código' name='code' placeholder='AR-B' />
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default StatesModal