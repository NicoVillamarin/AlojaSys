import { useEffect, useState } from 'react'
import { Formik, FieldArray } from 'formik'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import SelectBasic from 'src/components/selects/SelectBasic'
import SelectStandalone from 'src/components/selects/SelectStandalone'
import DatePickedRange from 'src/components/DatePickedRange'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import Button from 'src/components/Button'

const RulesRateModal = ({ isOpen, onClose, isEdit = false, row, onSuccess }) => {
  const { mutate: createRow, isPending: creating } = useCreate({
    resource: 'rates/rate-rules',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  const { mutate: updateRow, isPending: updating } = useUpdate({
    resource: 'rates/rate-rules',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const [choices, setChoices] = useState({ room_types: [], price_modes: [], channels: [] })
  useEffect(() => {
    const load = async () => {
      const url = `${getApiURL()}/api/rates/choices/`
      const json = await fetchWithAuth(url, { method: 'GET' })
      setChoices({
        room_types: json?.room_types || [],
        price_modes: json?.price_modes || [],
        channels: json?.channels || [],
      })
    }
    if (isOpen) load()
  }, [isOpen])

  const initialValues = {
    plan: isEdit ? (row?.plan ?? '') : '',
    name: isEdit ? (row?.name ?? '') : '',
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
    price_mode: isEdit ? (row?.price_mode ?? (choices.price_modes?.[0]?.value || 'absolute')) : (choices.price_modes?.[0]?.value || 'absolute'),
    base_amount: isEdit ? (row?.base_amount != null ? String(row.base_amount) : '') : '',
    extra_guest_fee_amount: isEdit ? (row?.extra_guest_fee_amount != null ? String(row.extra_guest_fee_amount) : '') : '',
    min_stay: isEdit ? (row?.min_stay != null ? String(row.min_stay) : '') : '',
    max_stay: isEdit ? (row?.max_stay != null ? String(row.max_stay) : '') : '',
    closed: isEdit ? (row?.closed ?? false) : false,
    closed_to_arrival: isEdit ? (row?.closed_to_arrival ?? false) : false,
    closed_to_departure: isEdit ? (row?.closed_to_departure ?? false) : false,
    occupancy_prices: isEdit ? (row?.occupancy_prices || []) : [],
    use_weekdays: true,
  }

  const validationSchema = Yup.object().shape({
    plan: Yup.number().typeError('Plan requerido').required('Plan requerido'),
    start_date: Yup.string().required('Inicio requerido'),
    end_date: Yup.string().required('Fin requerido')
      .test('dates-order', 'Fin debe ser >= Inicio', function (end) {
        const { start_date } = this.parent
        if (!start_date || !end) return true
        return new Date(end) >= new Date(start_date)
      }),
    priority: Yup.number().typeError('Debe ser número').required('Requerido'),
    price_mode: Yup.string().required('Requerido'),
    min_stay: Yup.mixed().test('min-nonnegative', 'Mín noches >= 0', (v) => v === '' || Number(v) >= 0),
    max_stay: Yup.mixed().test('max-positive', 'Máx noches > 0', (v) => v === '' || Number(v) > 0)
      .test('max>=min', 'Máx debe ser >= Mín', function (max) {
        const { min_stay } = this.parent
        if (max === '' || min_stay === '') return true
        return Number(max) >= Number(min_stay)
      }),
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
          plan: values.plan ? Number(values.plan) : undefined,
          name: values.name || undefined,
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
          price_mode: values.price_mode || undefined,
          base_amount: values.base_amount !== '' ? values.base_amount : null,
          extra_guest_fee_amount: values.extra_guest_fee_amount !== '' ? values.extra_guest_fee_amount : null,
          min_stay: values.min_stay !== '' ? Number(values.min_stay) : null,
          max_stay: values.max_stay !== '' ? Number(values.max_stay) : null,
          closed: !!values.closed,
          closed_to_arrival: !!values.closed_to_arrival,
          closed_to_departure: !!values.closed_to_departure,
          occupancy_prices: (values.occupancy_prices || []).map((o) => ({
            occupancy: Number(o.occupancy),
            price: o.price,
          })),
        }
        if (isEdit && row?.id) updateRow({ id: row.id, body: payload })
        else createRow(payload)
      }}
    >
      {({ handleSubmit, values, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? 'Editar regla' : 'Crear regla'}
          onSubmit={handleSubmit}
          submitText={isEdit ? 'Guardar cambios' : 'Crear'}
          cancelText='Cancelar'
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='lg'
        >
          <div className='grid grid-cols-1 md:grid-cols-2 gap-5'>
            <SelectAsync
              title='Plan *'
              name='plan'
              resource='rates/rate-plans'
              placeholder='Buscar plan…'
              getOptionLabel={(p) => `${p?.name} (#${p?.id})`}
              getOptionValue={(p) => p?.id}
            />
            <InputText title='Nombre' name='name' placeholder='Temporada alta' />
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
              title='Modo de precio *'
              value={values.price_mode ? choices.price_modes.find(p => p.value === values.price_mode) || { value: values.price_mode, label: values.price_mode } : null}
              onChange={(v) => setFieldValue('price_mode', v?.value || v || '')}
              options={choices.price_modes}
              isClearable={false}
              getOptionLabel={(o) => o.label}
              getOptionValue={(o) => o.value}
            />
            <InputText title='Base/Delta' name='base_amount' placeholder='100.00 o +20.00' />
            <InputText title='Extra huésped' name='extra_guest_fee_amount' placeholder='15.00' />

            <InputText title='Mín noches' name='min_stay' placeholder='2' />
            <InputText title='Máx noches' name='max_stay' placeholder='30' />

            <label className='flex items-center gap-2 text-sm'>
              <input type='checkbox' checked={!!values.closed} onChange={(e)=>setFieldValue('closed', e.target.checked)} />
              Cerrado (no vendible)
            </label>
            <label className='flex items-center gap-2 text-sm'>
              <input type='checkbox' checked={!!values.closed_to_arrival} onChange={(e)=>setFieldValue('closed_to_arrival', e.target.checked)} />
              CTA (cerrado a llegada)
            </label>
            <label className='flex items-center gap-2 text-sm'>
              <input type='checkbox' checked={!!values.closed_to_departure} onChange={(e)=>setFieldValue('closed_to_departure', e.target.checked)} />
              CTD (cerrado a salida)
            </label>

            <div className='col-span-2'>
              <div className='flex items-center justify-between mb-2'>
                <div className='font-medium'>Precios por ocupación</div>
                <Button size='sm' onClick={() => setFieldValue('occupancy_prices', [...(values.occupancy_prices||[]), { occupancy: 2, price: '0.00' }])}>
                  Agregar
                </Button>
              </div>
              <FieldArray
                name='occupancy_prices'
                render={(arrayHelpers) => (
                  <div className='space-y-2'>
                    {(values.occupancy_prices || []).map((item, idx) => (
                      <div className='grid grid-cols-6 gap-2 items-center' key={idx}>
                        <div className='col-span-2'>
                          <InputText title='Ocupación' name={`occupancy_prices[${idx}].occupancy`} placeholder='2' />
                        </div>
                        <div className='col-span-3'>
                          <InputText title='Precio' name={`occupancy_prices[${idx}].price`} placeholder='120.00' />
                        </div>
                        <div className='col-span-1'>
                          <Button variant='secondary' size='sm' onClick={() => arrayHelpers.remove(idx)}>Quitar</Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              />
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default RulesRateModal