import { Formik } from 'formik'
import React from 'react'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'

/**
 * HotelsModal: crear/editar hotel
 */
const HotelsModal = ({ isOpen, onClose, isEdit = false, hotel, onSuccess }) => {
  const { mutate: createHotel, isPending: creating } = useCreate({
    resource: 'hotels',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  const { mutate: updateHotel, isPending: updating } = useUpdate({
    resource: 'hotels',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const initialValues = {
    name: hotel?.name ?? '',
    legal_name: hotel?.legal_name ?? '',
    tax_id: hotel?.tax_id ?? '',
    email: hotel?.email ?? '',
    phone: hotel?.phone ?? '',
    address: hotel?.address ?? '',
    country: hotel?.country ?? '',
    state: hotel?.state ?? '',
    city: hotel?.city ?? '',
    check_in_time: (hotel?.check_in_time ?? '15:00').slice(0, 5),
    check_out_time: (hotel?.check_out_time ?? '11:00').slice(0, 5),
    is_active: hotel?.is_active ?? true,
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
          check_in_time: values.check_in_time || undefined,
          check_out_time: values.check_out_time || undefined,
          is_active: values.is_active,
        }
        if (isEdit && hotel?.id) updateHotel({ id: hotel.id, body: payload })
        else createHotel(payload)
      }}
    >
      {({ values, handleChange, handleSubmit, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? 'Editar hotel' : 'Crear hotel'}
          onSubmit={handleSubmit}
          submitText={isEdit ? 'Guardar cambios' : 'Crear'}
          cancelText='Cancelar'
          submitDisabled={creating || updating}
          size='lg'
        >
          <div className='grid grid-cols-1 md:grid-cols-2 gap-5'>
            <InputText title='Nombre *' name='name' placeholder='Hotel Central' autoFocus />
            <InputText title='Razón social' name='legal_name' placeholder='Hotel Central S.A.' />
            <InputText title='CUIT/CUIL' name='tax_id' placeholder='20-12345678-9' />
            <InputText title='Email' name='email' placeholder='contacto@hotel.com' />
            <InputText title='Teléfono' name='phone' placeholder='+54 11 1234-5678' />
            <InputText title='Dirección' name='address' placeholder='Av. Siempre Viva 123' />
            <SelectAsync
              title='País'
              name='country'
              resource='countries'
              placeholder='Buscar país…'
              getOptionLabel={(c) => c?.name}
              getOptionValue={(c) => c?.id}
              onValueChange={() => {
                // al cambiar país, limpiar state y city
                setFieldValue('state', '')
                setFieldValue('city', '')
              }}
            />
            <SelectAsync
              title='Provincia/Estado'
              name='state'
              resource='states'
              placeholder='Buscar provincia…'
              extraParams={{ country: values.country || undefined }}
              getOptionLabel={(s) => s?.name}
              getOptionValue={(s) => s?.id}
              onValueChange={() => {
                // al cambiar state, limpiar city
                setFieldValue('city', '')
              }}
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
            <InputText title='Check-in' name='check_in_time' type='time' />
            <InputText title='Check-out' name='check_out_time' type='time' />
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

export default HotelsModal