import { useEffect, useState } from 'react'
import { Formik } from 'formik'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import SelectBasic from 'src/components/selects/SelectBasic'
import DatePickedRange from 'src/components/DatePickedRange'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import SelectStandalone from '../selects/SelectStandalone'

const PromoRateModal = ({ isOpen, onClose, isEdit = false, row, onSuccess }) => {
  const { mutate: createRow, isPending: creating } = useCreate({
    resource: 'rates/promo-rules',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  const { mutate: updateRow, isPending: updating } = useUpdate({
    resource: 'rates/promo-rules',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const [choices, setChoices] = useState({ room_types: [], channels: [] })
  useEffect(() => {
    const load = async () => {
      const url = `${getApiURL()}/api/rates/choices/`
      const json = await fetchWithAuth(url, { method: 'GET' })
      setChoices({
        room_types: json?.room_types || [],
        channels: json?.channels || [],
      })
    }
    if (isOpen) load()
  }, [isOpen])

  const initialValues = {
    hotel: isEdit ? (row?.hotel ?? '') : '',
    plan: isEdit ? (row?.plan ?? '') : '',
    name: isEdit ? (row?.name ?? '') : '',
    code: isEdit ? (row?.code ?? '') : '',
    start_date: isEdit ? (row?.start_date ?? '') : '',
    end_date: isEdit ? (row?.end_date ?? '') : '',
    apply_mon: isEdit ? (row?.apply_mon ?? true) : true,
    apply_tue: isEdit ? (row?.apply_tue ?? true) : true,
    apply_wed: isEdit ? (row?.apply_wed ?? true) : true,
    apply_thu: isEdit ? (row?.apply_thu ?? true) : true,
    apply_fri: isEdit ? (row?.apply_fri ?? true) : true,
    apply_sat: isEdit ? (row?.apply_sat ?? true) : true,
    apply_sun: isEdit ? (row?.apply_sun ?? true) : true,
    target_room: isEdit ? (row?.target_room ?? '') : '',
    target_room_type: isEdit ? (row?.target_room_type ?? '') : '',
    channel: isEdit ? (row?.channel ?? '') : '',
    priority: isEdit ? (row?.priority != null ? String(row.priority) : '100') : '100',
    discount_type: isEdit ? (row?.discount_type ?? 'percent') : 'percent',
    discount_value: isEdit ? (row?.discount_value != null ? String(row.discount_value) : '') : '',
    scope: isEdit ? (row?.scope ?? 'per_night') : 'per_night',
    combinable: isEdit ? (row?.combinable ?? false) : false,
    is_active: isEdit ? (row?.is_active ?? true) : true,
    use_weekdays: true,
  }

  const validationSchema = Yup.object().shape({
    hotel: Yup.number().typeError('Hotel requerido').required('Hotel requerido'),
    name: Yup.string().required('Nombre requerido'),
    start_date: Yup.string().required('Inicio requerido'),
    end_date: Yup.string().required('Fin requerido')
      .test('dates-order', 'Fin debe ser >= Inicio', function (end) {
        const { start_date } = this.parent
        if (!start_date || !end) return true
        return new Date(end) >= new Date(start_date)
      }),
    discount_type: Yup.string().required('Tipo requerido'),
    discount_value: Yup.number().typeError('Debe ser número').required('Requerido')
      .test('percent-range', 'Si es porcentaje debe estar entre 0 y 100', function (value) {
        const { discount_type } = this.parent
        if (discount_type !== 'percent' || value == null || value === '') return true
        const n = Number(value)
        return n >= 0 && n <= 100
      }),
    priority: Yup.number().typeError('Debe ser número').required('Requerido'),
  }).test('at-least-one-day', 'Selecciona al menos un día de la semana', (values) => {
    if (!values.use_weekdays) return true
    return !!(values.apply_mon || values.apply_tue || values.apply_wed || values.apply_thu || values.apply_fri || values.apply_sat || values.apply_sun)
  }).test('xor-room-type', 'Elegí habitación o tipo de habitación (no ambos)', (values) => {
    const hasRoom = !!values.target_room
    const hasType = !!values.target_room_type
    return !(hasRoom && hasType)
  })

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          hotel: values.hotel ? Number(values.hotel) : undefined,
          plan: values.plan ? Number(values.plan) : null,
          name: values.name || undefined,
          code: values.code || null,
          start_date: values.start_date || undefined,
          end_date: values.end_date || undefined,
          apply_mon: !!values.apply_mon,
          apply_tue: !!values.apply_tue,
          apply_wed: !!values.apply_wed,
          apply_thu: !!values.apply_thu,
          apply_fri: !!values.apply_fri,
          apply_sat: !!values.apply_sat,
          apply_sun: !!values.apply_sun,
          target_room: values.target_room ? Number(values.target_room) : null,
          target_room_type: values.target_room_type || null,
          channel: values.channel || null,
          priority: values.priority !== '' ? Number(values.priority) : undefined,
          discount_type: values.discount_type,
          discount_value: values.discount_value !== '' ? values.discount_value : undefined,
          scope: values.scope || 'per_night',
          combinable: !!values.combinable,
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
          title={isEdit ? 'Editar promoción' : 'Crear promoción'}
          onSubmit={handleSubmit}
          submitText={isEdit ? 'Guardar cambios' : 'Crear'}
          cancelText='Cancelar'
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='lg'
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
            <SelectAsync
              title='Plan (opcional)'
              name='plan'
              resource='rates/rate-plans'
              placeholder='Buscar plan…'
              getOptionLabel={(p) => `${p?.name} (#${p?.id})`}
              getOptionValue={(p) => p?.id}
            />
            <InputText title='Nombre *' name='name' placeholder='BLACK FRIDAY' />
            <InputText title='Código (opcional)' name='code' placeholder='BLACK' />
            <DatePickedRange
              label='Rango de fechas *'
              startDate={values.start_date}
              endDate={values.end_date}
              onChange={(s, e) => { setFieldValue('start_date', s); setFieldValue('end_date', e) }}
            />

            <div className='col-span-2'>
              <div className='flex items-center justify-between mb-2'>
                <div className='text-sm font-medium text-gray-700'>Días de la semana</div>
                <div className='flex items-center gap-3'>
                  <label className='flex items-center gap-2 text-xs'>
                    <input
                      type='checkbox'
                      checked={!!values.use_weekdays}
                      onChange={(e) => {
                        const on = e.target.checked
                        setFieldValue('use_weekdays', on)
                        if (!on) {
                          setFieldValue('apply_mon', true)
                          setFieldValue('apply_tue', true)
                          setFieldValue('apply_wed', true)
                          setFieldValue('apply_thu', true)
                          setFieldValue('apply_fri', true)
                          setFieldValue('apply_sat', true)
                          setFieldValue('apply_sun', true)
                        }
                      }}
                    />
                    Aplicar solo ciertos días
                  </label>
                  {values.use_weekdays && (
                    <div className='flex gap-2'>
                      <button type='button' className='text-xs text-aloja-navy underline' onClick={() => {
                        setFieldValue('apply_mon', true)
                        setFieldValue('apply_tue', true)
                        setFieldValue('apply_wed', true)
                        setFieldValue('apply_thu', true)
                        setFieldValue('apply_fri', true)
                        setFieldValue('apply_sat', true)
                        setFieldValue('apply_sun', true)
                      }}>Todos</button>
                      <button type='button' className='text-xs text-gray-600 underline' onClick={() => {
                        setFieldValue('apply_mon', false)
                        setFieldValue('apply_tue', false)
                        setFieldValue('apply_wed', false)
                        setFieldValue('apply_thu', false)
                        setFieldValue('apply_fri', false)
                        setFieldValue('apply_sat', false)
                        setFieldValue('apply_sun', false)
                      }}>Limpiar</button>
                    </div>
                  )}
                </div>
              </div>
              <div className={`flex flex-wrap gap-2 ${!values.use_weekdays ? 'opacity-50 pointer-events-none' : ''}`}>
                {[
                  ['apply_mon','Lun'],['apply_tue','Mar'],['apply_wed','Mié'],['apply_thu','Jue'],['apply_fri','Vie'],['apply_sat','Sáb'],['apply_sun','Dom'],
                ].map(([name,label]) => (
                  <button
                    key={name}
                    type='button'
                    onClick={() => setFieldValue(name, !values[name])}
                    className={`px-3 py-1 rounded-full text-sm border ${values[name] ? 'bg-aloja-navy text-white border-aloja-navy' : 'bg-white text-gray-700 border-gray-300'}`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <SelectAsync
              title='Habitación (opcional)'
              name='target_room'
              resource='rooms'
              placeholder='Buscar habitación…'
              getOptionLabel={(r) => `${r?.name} (#${r?.id})`}
              getOptionValue={(r) => r?.id}
              isDisabled={!!values.target_room_type}
              onChange={(room) => setFieldValue('target_room', room?.id)}
            />
            <SelectStandalone
              title='Tipo de habitación (opcional)'
              value={values.target_room_type ? choices.room_types.find(r => r.value === values.target_room_type) || { value: values.target_room_type, label: values.target_room_type } : null}
              onChange={(v) => setFieldValue('target_room_type', v?.value || v || '')}
              options={choices.room_types}
              isDisabled={!!values.target_room}
              isClearable={true}
              getOptionLabel={(o) => o.label}
              getOptionValue={(o) => o.value}
            />
            <SelectStandalone
              title='Canal (opcional)'
              value={values.channel ? choices.channels.find(c => c.value === values.channel) || { value: values.channel, label: values.channel } : null}
              onChange={(v) => setFieldValue('channel', v?.value || v || '')}
              options={choices.channels}
              isClearable={true}
              getOptionLabel={(o) => o.label}
              getOptionValue={(o) => o.value}
            />

            <InputText title='Prioridad *' name='priority' placeholder='100' />
            <SelectStandalone
              title='Alcance *'
              value={{ value: values.scope, label: values.scope === 'per_night' ? 'Por noche' : 'Por reserva' }}
              onChange={(v) => setFieldValue('scope', v?.value || v)}
              options={[{ value:'per_night', label:'Por noche' }, { value:'per_reservation', label:'Por reserva' }]}
              getOptionLabel={(o) => o.label}
              getOptionValue={(o) => o.value}
            />
            <SelectStandalone
              title='Tipo de descuento *'
              value={values.discount_type ? { value: values.discount_type, label: values.discount_type === 'percent' ? 'Porcentaje' : 'Monto fijo' } : null}
              onChange={(v) => setFieldValue('discount_type', v?.value || v)}
              options={[{ value:'percent', label:'Porcentaje' }, { value:'fixed', label:'Monto fijo' }]}
              getOptionLabel={(o) => o.label}
              getOptionValue={(o) => o.value}
            />
            <InputText title='Valor *' name='discount_value' placeholder='10 (o 15.00 si fijo)' />

            <label className='flex items-center gap-2 text-sm'>
              <input type='checkbox' checked={!!values.combinable} onChange={(e)=>setFieldValue('combinable', e.target.checked)} />
              Combinable
            </label>
            <label className='flex items-center gap-2 text-sm'>
              <input type='checkbox' checked={!!values.is_active} onChange={(e)=>setFieldValue('is_active', e.target.checked)} />
              Activa
            </label>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default PromoRateModal