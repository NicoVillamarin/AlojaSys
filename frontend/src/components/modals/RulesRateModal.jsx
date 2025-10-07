import { useEffect, useState } from 'react'
import { Formik, FieldArray } from 'formik'
import { useTranslation } from 'react-i18next'
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
  const { t } = useTranslation()
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
    plan: Yup.number().typeError(t('rules_rate_modal.plan_required')).required(t('rules_rate_modal.plan_required')),
    start_date: Yup.string().required(t('rules_rate_modal.start_date_required')),
    end_date: Yup.string().required(t('rules_rate_modal.end_date_required'))
      .test('dates-order', t('rules_rate_modal.end_date_order'), function (end) {
        const { start_date } = this.parent
        if (!start_date || !end) return true
        return new Date(end) >= new Date(start_date)
      }),
    priority: Yup.number().typeError(t('rules_rate_modal.priority_number')).required(t('rules_rate_modal.priority_required')),
    price_mode: Yup.string().required(t('rules_rate_modal.price_mode_required')),
    min_stay: Yup.mixed().test('min-nonnegative', t('rules_rate_modal.min_stay_nonnegative'), (v) => v === '' || Number(v) >= 0),
    max_stay: Yup.mixed().test('max-positive', t('rules_rate_modal.max_stay_positive'), (v) => v === '' || Number(v) > 0)
      .test('max>=min', t('rules_rate_modal.max_stay_gte_min'), function (max) {
        const { min_stay } = this.parent
        if (max === '' || min_stay === '') return true
        return Number(max) >= Number(min_stay)
      }),
  }).test('at-least-one-day', t('rules_rate_modal.at_least_one_day'), (values) => {
    if (!values.use_weekdays) return true
    return !!(values.apply_mon || values.apply_tue || values.apply_wed || values.apply_thu || values.apply_fri || values.apply_sat || values.apply_sun)
  }).test('xor-room-type', t('rules_rate_modal.xor_room_type'), (values) => {
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
          title={isEdit ? t('rules_rate_modal.edit_rule') : t('rules_rate_modal.create_rule')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('rules_rate_modal.save_changes') : t('rules_rate_modal.create')}
          cancelText={t('rules_rate_modal.cancel')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='lg'
        >
          <div className='grid grid-cols-1 xl:grid-cols-2 gap-4 lg:gap-5'>
            <SelectAsync
              title={`${t('rules_rate_modal.plan')} *`}
              name='plan'
              resource='rates/rate-plans'
              placeholder={t('rules_rate_modal.plan_placeholder')}
              getOptionLabel={(p) => `${p?.name} (#${p?.id})`}
              getOptionValue={(p) => p?.id}
            />
            <InputText title={t('rules_rate_modal.name')} name='name' placeholder={t('rules_rate_modal.name_placeholder')} />
            <div className='xl:col-span-2'>
              <DatePickedRange
                label={`${t('rules_rate_modal.date_range')} *`}
                startDate={values.start_date}
                endDate={values.end_date}
                onChange={(s, e) => { setFieldValue('start_date', s); setFieldValue('end_date', e) }}
              />
            </div>

            <div className='xl:col-span-2'>
              <div className='flex items-center justify-between mb-2'>
                <div className='text-sm font-medium text-gray-700'>{t('rules_rate_modal.weekdays')}</div>
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
                    {t('rules_rate_modal.apply_specific_days')}
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
                      }}>{t('rules_rate_modal.all')}</button>
                      <button type='button' className='text-xs text-gray-600 underline' onClick={() => {
                        setFieldValue('apply_mon', false)
                        setFieldValue('apply_tue', false)
                        setFieldValue('apply_wed', false)
                        setFieldValue('apply_thu', false)
                        setFieldValue('apply_fri', false)
                        setFieldValue('apply_sat', false)
                        setFieldValue('apply_sun', false)
                      }}>{t('rules_rate_modal.clear')}</button>
                    </div>
                  )}
                </div>
              </div>
              <div className={`grid grid-cols-4 sm:grid-cols-7 gap-2 ${!values.use_weekdays ? 'opacity-50 pointer-events-none' : ''}`}>
                {[
                  ['apply_mon', t('rules_rate_modal.days.mon')],['apply_tue', t('rules_rate_modal.days.tue')],['apply_wed', t('rules_rate_modal.days.wed')],['apply_thu', t('rules_rate_modal.days.thu')],['apply_fri', t('rules_rate_modal.days.fri')],['apply_sat', t('rules_rate_modal.days.sat')],['apply_sun', t('rules_rate_modal.days.sun')],
                ].map(([name,label]) => (
                  <button
                    key={name}
                    type='button'
                    onClick={() => setFieldValue(name, !values[name])}
                    className={`px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm border text-center ${values[name] ? 'bg-aloja-navy text-white border-aloja-navy' : 'bg-white text-gray-700 border-gray-300'}`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <SelectAsync
              title={t('rules_rate_modal.room')}
              name='target_room'
              resource='rooms'
              placeholder={t('rules_rate_modal.room_placeholder')}
              getOptionLabel={(r) => `${r?.name} (#${r?.id})`}
              getOptionValue={(r) => r?.id}
              isDisabled={!!values.target_room_type}
              onChange={(room) => setFieldValue('target_room', room?.id)}
            />
            <SelectStandalone
              title={t('rules_rate_modal.room_type')}
              value={values.target_room_type ? choices.room_types.find(r => r.value === values.target_room_type) || { value: values.target_room_type, label: values.target_room_type } : null}
              onChange={(v) => setFieldValue('target_room_type', v?.value || v || '')}
              options={choices.room_types}
              isDisabled={!!values.target_room}
              isClearable={true}
              getOptionLabel={(o) => o.label}
              getOptionValue={(o) => o.value}
            />
            <SelectStandalone
              title={t('rules_rate_modal.channel')}
              value={values.channel ? choices.channels.find(c => c.value === values.channel) || { value: values.channel, label: values.channel } : null}
              onChange={(v) => setFieldValue('channel', v?.value || v || '')}
              options={choices.channels}
              isClearable={true}
              getOptionLabel={(o) => o.label}
              getOptionValue={(o) => o.value}
            />
            <InputText title={`${t('rules_rate_modal.priority')} *`} name='priority' placeholder={t('rules_rate_modal.priority_placeholder')} />

            <SelectStandalone
              title={`${t('rules_rate_modal.price_mode')} *`}
              value={values.price_mode ? choices.price_modes.find(p => p.value === values.price_mode) || { value: values.price_mode, label: values.price_mode } : null}
              onChange={(v) => setFieldValue('price_mode', v?.value || v || '')}
              options={choices.price_modes}
              isClearable={false}
              getOptionLabel={(o) => o.label}
              getOptionValue={(o) => o.value}
            />
            <InputText title={t('rules_rate_modal.base_amount')} name='base_amount' placeholder={t('rules_rate_modal.base_amount_placeholder')} />
            <InputText title={t('rules_rate_modal.extra_guest_fee_amount')} name='extra_guest_fee_amount' placeholder={t('rules_rate_modal.extra_guest_fee_amount_placeholder')} />

            <InputText title={t('rules_rate_modal.min_stay')} name='min_stay' placeholder={t('rules_rate_modal.min_stay_placeholder')} />
            <InputText title={t('rules_rate_modal.max_stay')} name='max_stay' placeholder={t('rules_rate_modal.max_stay_placeholder')} />

            <label className='flex items-center gap-2 text-sm'>
              <input type='checkbox' checked={!!values.closed} onChange={(e)=>setFieldValue('closed', e.target.checked)} />
              {t('rules_rate_modal.closed')}
            </label>
            <label className='flex items-center gap-2 text-sm'>
              <input type='checkbox' checked={!!values.closed_to_arrival} onChange={(e)=>setFieldValue('closed_to_arrival', e.target.checked)} />
              {t('rules_rate_modal.closed_to_arrival')}
            </label>
            <label className='flex items-center gap-2 text-sm'>
              <input type='checkbox' checked={!!values.closed_to_departure} onChange={(e)=>setFieldValue('closed_to_departure', e.target.checked)} />
              {t('rules_rate_modal.closed_to_departure')}
            </label>

            <div className='xl:col-span-2'>
              <div className='flex items-center justify-between mb-2'>
                <div className='font-medium'>{t('rules_rate_modal.occupancy_prices')}</div>
                <Button size='sm' onClick={() => setFieldValue('occupancy_prices', [...(values.occupancy_prices||[]), { occupancy: 2, price: '0.00' }])}>
                  {t('rules_rate_modal.add')}
                </Button>
              </div>
              <FieldArray
                name='occupancy_prices'
                render={(arrayHelpers) => (
                  <div className='space-y-2'>
                    {(values.occupancy_prices || []).map((item, idx) => (
                      <div className='grid grid-cols-3 sm:grid-cols-6 gap-2 items-center' key={idx}>
                        <div className='col-span-2'>
                          <InputText title={t('rules_rate_modal.occupancy')} name={`occupancy_prices[${idx}].occupancy`} placeholder={t('rules_rate_modal.occupancy_placeholder')} />
                        </div>
                        <div className='col-span-3'>
                          <InputText title={t('rules_rate_modal.price')} name={`occupancy_prices[${idx}].price`} placeholder={t('rules_rate_modal.price_placeholder')} />
                        </div>
                        <div className='col-span-1'>
                          <Button variant='secondary' size='sm' onClick={() => arrayHelpers.remove(idx)}>{t('rules_rate_modal.remove')}</Button>
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