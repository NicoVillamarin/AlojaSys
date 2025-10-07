import { Formik } from 'formik'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import SelectBasic from 'src/components/selects/SelectBasic'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import SelectStandalone from '../selects/SelectStandalone'
import { useEffect, useState } from 'react'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'

const TaxesRateModal = ({ isOpen, onClose, isEdit = false, row, onSuccess }) => {
  const { mutate: createRow, isPending: creating } = useCreate({
    resource: 'rates/tax-rules',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  const { mutate: updateRow, isPending: updating } = useUpdate({
    resource: 'rates/tax-rules',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  const [choices, setChoices] = useState({ channels: [], tax_amount_types: [], tax_scopes: [] })
  useEffect(() => {
    const load = async () => {
      const url = `${getApiURL()}/api/rates/choices/`
      const json = await fetchWithAuth(url, { method: 'GET' })
      setChoices({
        channels: json?.channels || [],
        tax_amount_types: json?.tax_amount_types || [],
        tax_scopes: json?.tax_scopes || [],
      })
    }
    if (isOpen) load()
  }, [isOpen])

  const initialValues = {
    hotel: row?.hotel ?? '',
    name: row?.name ?? '',
    channel: row?.channel ?? '',
    amount_type: row?.amount_type ?? 'percent',
    percent: row?.percent != null ? String(row.percent) : '',
    fixed_amount: row?.fixed_amount != null ? String(row.fixed_amount) : '',
    scope: row?.scope ?? 'per_night',
    priority: row?.priority != null ? String(row.priority) : '100',
    is_active: row?.is_active ?? true,
  }

  const validationSchema = Yup.object().shape({
    hotel: Yup.number().typeError('Hotel requerido').required('Hotel requerido'),
    name: Yup.string().required('Nombre requerido'),
    amount_type: Yup.string().required('Tipo requerido'),
    percent: Yup.number().typeError('Debe ser número')
      .when('amount_type', {
        is: 'percent',
        then: (schema) => schema.required('Requerido'),
        otherwise: (schema) => schema.notRequired(),
      }),
    fixed_amount: Yup.number().typeError('Debe ser número')
      .when('amount_type', {
        is: 'fixed',
        then: (schema) => schema.required('Requerido'),
        otherwise: (schema) => schema.notRequired(),
      }),
    scope: Yup.string().required('Alcance requerido'),
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
          channel: values.channel || null,
          amount_type: values.amount_type,
          percent: values.amount_type === 'percent' ? (values.percent !== '' ? values.percent : undefined) : 0,
          fixed_amount: values.amount_type === 'fixed' ? (values.fixed_amount !== '' ? values.fixed_amount : undefined) : 0,
          scope: values.scope,
          priority: values.priority !== '' ? Number(values.priority) : undefined,
          is_active: !!values.is_active,
        }
        if (isEdit && row?.id) updateRow({ id: row.id, body: payload })
        else createRow(payload)
      }}
    >
      {({ handleSubmit, values, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? 'Editar impuesto' : 'Crear impuesto'}
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
            <InputText title='Nombre *' name='name' placeholder='IVA' />
            <SelectStandalone
              title='Canal (opcional)'
              value={values.channel ? choices.channels.find(c => c.value === values.channel) || { value: values.channel, label: values.channel } : null}
              onChange={(v) => setFieldValue('channel', v?.value || v || '')}
              options={choices.channels}
              isClearable={true}
              getOptionLabel={(o) => o.label}
              getOptionValue={(o) => o.value}
            />
          <SelectStandalone
            title='Tipo de monto *'
            value={choices.tax_amount_types.find(t => t.value === values.amount_type) || { value: values.amount_type, label: values.amount_type }}
            onChange={(v) => setFieldValue('amount_type', v?.value || v)}
            options={choices.tax_amount_types}
            getOptionLabel={(o) => o.label}
            getOptionValue={(o) => o.value}
          />
          {values.amount_type === 'percent' ? (
            <InputText title='Porcentaje (%) *' name='percent' placeholder='21' />
          ) : (
            <InputText title='Monto fijo *' name='fixed_amount' placeholder='100.00' />
          )}
          <SelectStandalone
            title='Alcance *'
            value={choices.tax_scopes.find(s => s.value === values.scope) || { value: values.scope, label: values.scope }}
            onChange={(v) => setFieldValue('scope', v?.value || v)}
            options={choices.tax_scopes}
            getOptionLabel={(o) => o.label}
            getOptionValue={(o) => o.value}
          />
            <InputText title='Prioridad *' name='priority' placeholder='100' />
            <label className='flex items-center gap-2 text-sm'>
              <input type='checkbox' checked={!!values.is_active} onChange={(e)=>setFieldValue('is_active', e.target.checked)} />
              Activo
            </label>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default TaxesRateModal