import { Formik } from 'formik'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import SelectBasic from 'src/components/selects/SelectBasic'

const PlansRateModal = ({ isOpen, onClose, isEdit = false, row, onSuccess }) => {
    const { mutate: createRow, isPending: creating } = useCreate({
        resource: 'rates/rate-plans',
        onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
    })
    const { mutate: updateRow, isPending: updating } = useUpdate({
        resource: 'rates/rate-plans',
        onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
    })

    const initialValues = {
        hotel: row?.hotel ?? '',
        name: row?.name ?? '',
        code: row?.code ?? '',
        is_active: row?.is_active ?? true,
        priority: row?.priority != null ? String(row.priority) : '100',
    }

    const validationSchema = Yup.object().shape({
        hotel: Yup.number().typeError('Hotel requerido').required('Hotel requerido'),
        name: Yup.string().required('Nombre requerido'),
        code: Yup.string().required('Código requerido'),
        priority: Yup.number().typeError('Debe ser número').required('Requerido'),
    })

    return (
        <Formik
            enableReinitialize
            initialValues={initialValues}
            validationSchema={validationSchema}
            onSubmit={(values) => {
                const payload = {
                    hotel: values.hotel ? Number(values.hotel) : undefined,
                    name: values.name || undefined,
                    code: values.code || undefined,
                    is_active: Boolean(values.is_active),
                    priority: values.priority !== '' ? Number(values.priority) : undefined,
                }
                if (isEdit && row?.id) updateRow({ id: row.id, body: payload })
                else createRow(payload)
            }}
        >
            {({ handleSubmit, values, setFieldValue }) => (
                <ModalLayout
                    isOpen={isOpen}
                    onClose={onClose}
                    title={isEdit ? 'Editar plan' : 'Crear plan'}
                    onSubmit={handleSubmit}
                    submitText={isEdit ? 'Guardar cambios' : 'Crear'}
                    cancelText='Cancelar'
                    submitDisabled={creating || updating}
                    submitLoading={creating || updating}
                    size='md'
                >
                    <div className='grid grid-cols-1 md:grid-cols-2 gap-5'>
                        <SelectAsync
                            title='Hotel *'
                            name='hotel'
                            resource='hotels'
                            placeholder='Buscar hotel…'
                            getOptionLabel={(h) => h?.name}
                            getOptionValue={(h) => h?.id}
                        />
                        <InputText title='Nombre *' name='name' placeholder='BAR' />
                        <InputText title='Código *' name='code' placeholder='BAR' />
                        <InputText title='Prioridad *' name='priority' placeholder='100' />
                        <div className='md:col-span-2'>
                            <label className='text-xs text-aloja-gray-800/70'>Activo</label>
                            <label htmlFor='is_active' className='flex items-center gap-2 cursor-pointer'>
                                <input
                                    id='is_active'
                                    name='is_active'
                                    type='checkbox'
                                    className='rounded border-gray-300'
                                    checked={!!values.is_active}
                                    onChange={(e) => setFieldValue('is_active', e.target.checked)}
                                />
                                <span className='text-sm text-aloja-gray-800/80'>Habilitado para operar</span>
                            </label>
                        </div>
                    </div>
                </ModalLayout>
            )}
        </Formik>
    )
}

export default PlansRateModal