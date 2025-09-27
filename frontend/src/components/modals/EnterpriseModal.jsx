import { Formik } from 'formik'
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
    name: Yup.string().required('Nombre es requerido'),
    email: Yup.string().email('Email inválido').nullable(),
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
          title={isEdit ? 'Editar empresa' : 'Crear empresa'}
          onSubmit={handleSubmit}
          submitText={isEdit ? 'Guardar cambios' : 'Crear'}
          cancelText='Cancelar'
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='lg'
        >
          <div className='grid grid-cols-1 md:grid-cols-2 gap-5'>
            <InputText title='Nombre *' name='name' placeholder='AlojaSys S.A.' autoFocus />
            <InputText title='Razón social' name='legal_name' placeholder='AlojaSys Sociedad Anónima' />
            <InputText title='CUIT/CUIL' name='tax_id' placeholder='20-12345678-9' />
            <InputText title='Email' name='email' placeholder='contacto@empresa.com' />
            <InputText title='Teléfono' name='phone' placeholder='+54 11 1234-5678' />
            <InputText title='Dirección' name='address' placeholder='Av. Siempre Viva 123' />
            <SelectAsync
              title='País'
              name='country'
              resource='countries'
              placeholder='Buscar país…'
              getOptionLabel={(c) => c?.name}
              getOptionValue={(c) => c?.id}
              onValueChange={() => { setFieldValue('state', ''); setFieldValue('city', '') }}
            />
            <SelectAsync
              title='Provincia/Estado'
              name='state'
              resource='states'
              placeholder='Buscar provincia…'
              extraParams={{ country: values.country || undefined }}
              getOptionLabel={(s) => s?.name}
              getOptionValue={(s) => s?.id}
              onValueChange={() => { setFieldValue('city', '') }}
            />
            <SelectAsync
              title='Ciudad'
              name='city'
              resource='cities'
              placeholder='Buscar ciudad…'
              extraParams={{ state: values.state || undefined, country: values.country || undefined }}
              getOptionLabel={(c) => c?.name}
              getOptionValue={(c) => c?.id}
            />
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
                <span className='text-sm text-aloja-gray-800/80'>Habilitada</span>
              </label>
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default EnterpriseModal