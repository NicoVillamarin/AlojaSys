import React, { useEffect, useState } from 'react'
import { Formik } from 'formik'
import * as Yup from 'yup'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import SelectBasic from 'src/components/selects/SelectBasic'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import { useUserHotels } from 'src/hooks/useUserHotels'

const validationSchema = (t) => Yup.object().shape({
  hotel: Yup.number().required(t('housekeeping.validations.hotel_required')),
  room: Yup.number().required(t('housekeeping.validations.room_required')),
  task_type: Yup.string().oneOf(['checkout', 'daily', 'maintenance']).required(t('housekeeping.validations.type_required')),
  status: Yup.string().oneOf(['pending', 'in_progress', 'completed', 'cancelled']).required(),
  assigned_to_user: Yup.number().required(t('housekeeping.validations.assigned_to_user_required')),
  priority: Yup.number().min(0).optional(),
})

const HousekeepingModal = ({ isOpen, onClose, isEdit = false, task, onSuccess }) => {
  const { t } = useTranslation()
  const { hasSingleHotel, singleHotelId } = useUserHotels()
  const [instanceKey, setInstanceKey] = useState(0)

  const initialValues = {
    hotel: task?.hotel ?? (hasSingleHotel ? singleHotelId : ''),
    room: task?.room ?? '',
    task_type: task?.task_type ?? 'daily',
    status: task?.status ?? 'pending',
    assigned_to_user: '',
    notes: task?.notes ?? '',
    priority: typeof task?.priority === 'number' ? String(task.priority) : (task?.priority ?? '1'),
    zone: task?.zone ?? '',
  }

  const { mutate: createTask, isPending: creating } = useCreate({
    resource: 'housekeeping/tasks',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
    },
  })
  const { mutate: updateTask, isPending: updating } = useUpdate({
    resource: 'housekeeping/tasks',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
    },
  })

  useEffect(() => {
    if (isOpen && !isEdit) {
      setInstanceKey((k) => k + 1)
    }
  }, [isOpen, isEdit])

  return (
    <Formik
      key={isEdit ? `edit-${task?.id ?? 'new'}` : `create-${instanceKey}`}
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema(t)}
      onSubmit={(values) => {
        const payload = {
          hotel: values.hotel || undefined,
          room: values.room || undefined,
          task_type: values.task_type || undefined,
          status: values.status || undefined,
          assigned_to_user: values.assigned_to_user || undefined,
          notes: values.notes || undefined,
          priority: values.priority != null ? parseInt(values.priority, 10) : 0,
          zone: values.zone || undefined,
        }
        if (isEdit && task?.id) {
          updateTask({ id: task.id, body: payload })
        } else {
          createTask(payload)
        }
      }}
    >
      {({ values, handleChange, handleSubmit, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('housekeeping.modal.edit_title') : t('housekeeping.modal.create_title')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('users_modal.save_changes') : t('users_modal.create_user_btn')}
          cancelText={t('users_modal.cancel')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='lg'
        >
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5'>
            <SelectAsync
              title={`${t('common.hotel')} *`}
              name='hotel'
              resource='hotels'
              placeholder={t('common.select_placeholder')}
              getOptionLabel={(h) => h?.name}
              getOptionValue={(h) => h?.id}
              onValueChange={(opt, val) => {
                setFieldValue('hotel', val)
                setFieldValue('room', '')
              }}
            />
            <SelectAsync
              title={`${t('housekeeping.room')} *`}
              name='room'
              resource='rooms'
              placeholder={t('common.select_placeholder')}
              extraParams={{ hotel: values.hotel || undefined }}
              getOptionLabel={(r) => `${r.number ? `#${r.number} - ` : ''}${r.name}`}
              getOptionValue={(r) => r.id}
            />
            <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5 lg:col-span-2'>
              <SelectBasic
                title={t('housekeeping.task_type')}
                name='task_type'
                options={[
                  { value: 'daily', label: t('housekeeping.types.daily') },
                  { value: 'checkout', label: t('housekeeping.types.checkout') },
                  { value: 'maintenance', label: t('housekeeping.types.maintenance') },
                ]}
                placeholder={t('common.select_placeholder')}
              />
              <SelectBasic
                title={t('housekeeping.status.title')}
                name='status'
                options={[
                  { value: 'pending', label: t('housekeeping.status.pending') },
                  { value: 'in_progress', label: t('housekeeping.status.in_progress') },
                  { value: 'completed', label: t('housekeeping.status.completed') },
                  { value: 'cancelled', label: t('housekeeping.status.cancelled') },
                ]}
                placeholder={t('common.select_placeholder')}
              />
            </div>
            <SelectAsync
              title={t('housekeeping.assigned_to')}
              name='assigned_to_user'
              resource='users'
              placeholder={t('common.select_placeholder')}
              extraParams={{ hotel: values.hotel || undefined, is_housekeeping_staff: true, is_active: true }}
              getOptionLabel={(s) => `${s.first_name}${s.last_name ? ' ' + s.last_name : ''}`}
              getOptionValue={(s) => s.user_id ?? s.id}
            />
            <SelectBasic
              title={t('housekeeping.priority')}
              name='priority'
              options={[
                { value: '2', label: t('housekeeping.priority_high') },
                { value: '1', label: t('housekeeping.priority_medium') },
                { value: '0', label: t('housekeeping.priority_low') },
              ]}
              placeholder={t('common.select_placeholder')}
            />
            <InputText
              title={t('housekeeping.zone')}
              name='zone'
              placeholder={t('housekeeping.zone_placeholder')}
            />
            <div className='lg:col-span-2'>
              <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('housekeeping.notes')}</label>
              <textarea
                name='notes'
                value={values.notes}
                onChange={handleChange}
                placeholder={t('housekeeping.notes_placeholder')}
                className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm min-h-[100px]'
              />
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default HousekeepingModal