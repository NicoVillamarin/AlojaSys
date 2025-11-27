import React, { useEffect, useState } from 'react'
import { Formik } from 'formik'
import * as Yup from 'yup'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import InputTextTarea from 'src/components/inputs/InputTextTarea'
import SelectAsync from 'src/components/selects/SelectAsync'
import SelectBasic from 'src/components/selects/SelectBasic'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import { useUserHotels } from 'src/hooks/useUserHotels'

const validationSchema = (t) => Yup.object().shape({
  hotel: Yup.number().required(t('housekeeping.templates.validations.hotel_required')),
  room_type: Yup.string().required(t('housekeeping.templates.validations.room_type_required')),
  task_type: Yup.string().required(t('housekeeping.templates.validations.task_type_required')),
  name: Yup.string().required(t('housekeeping.templates.validations.name_required')),
  estimated_minutes: Yup.number().min(1).required(t('housekeeping.templates.validations.estimated_minutes_required')),
})

const TaskTemplateModal = ({ isOpen, onClose, isEdit = false, template, onSuccess }) => {
  const { t } = useTranslation()
  const { hasSingleHotel, singleHotelId } = useUserHotels()
  const [instanceKey, setInstanceKey] = useState(0)

  const initialValues = {
    hotel: template?.hotel ?? (hasSingleHotel ? singleHotelId : ''),
    room_type: template?.room_type ?? '',
    task_type: template?.task_type ?? 'daily',
    name: template?.name ?? '',
    description: template?.description ?? '',
    estimated_minutes: template?.estimated_minutes ?? 15,
    is_required: template?.is_required ?? true,
    order: template?.order ?? 0,
  }

  const { mutate: createTemplate, isPending: creating } = useCreate({
    resource: 'housekeeping/templates',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
    },
  })
  const { mutate: updateTemplate, isPending: updating } = useUpdate({
    resource: 'housekeeping/templates',
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
      key={isEdit ? `edit-${template?.id ?? 'new'}` : `create-${instanceKey}`}
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema(t)}
      onSubmit={(values) => {
        const payload = {
          hotel: values.hotel || undefined,
          room_type: values.room_type || undefined,
          task_type: values.task_type || undefined,
          name: values.name || undefined,
          description: values.description || undefined,
          estimated_minutes: values.estimated_minutes ? parseInt(values.estimated_minutes, 10) : 15,
          is_required: values.is_required !== undefined ? values.is_required : true,
          order: values.order ? parseInt(values.order, 10) : 0,
        }
        if (isEdit && template?.id) {
          updateTemplate({ id: template.id, body: payload })
        } else {
          createTemplate(payload)
        }
      }}
    >
      {({ values, handleChange, handleSubmit, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('housekeeping.templates.modal.edit_title') : t('housekeeping.templates.modal.create_title')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('common.save') : t('common.create')}
          cancelText={t('common.cancel')}
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
            />
            <SelectBasic
              title={`${t('housekeeping.templates.room_type')} *`}
              name='room_type'
              options={[
                { value: 'single', label: t('rooms_modal.room_types.single') },
                { value: 'double', label: t('rooms_modal.room_types.double') },
                { value: 'triple', label: t('rooms_modal.room_types.triple') },
                { value: 'suite', label: t('rooms_modal.room_types.suite') },
              ]}
              placeholder={t('common.select_placeholder')}
            />
            <SelectBasic
              title={`${t('housekeeping.task_type')} *`}
              name='task_type'
              options={[
                { value: 'daily', label: t('housekeeping.types.daily') },
                { value: 'checkout', label: t('housekeeping.types.checkout') },
                { value: 'maintenance', label: t('housekeeping.types.maintenance') },
              ]}
              placeholder={t('common.select_placeholder')}
            />
            <InputText
              title={`${t('housekeeping.templates.name')} *`}
              name='name'
              placeholder={t('housekeeping.templates.name_placeholder')}
            />
            <InputText
              title={`${t('housekeeping.templates.estimated_minutes')} *`}
              name='estimated_minutes'
              type='number'
              placeholder='15'
            />
            <div className='lg:col-span-2'>
              <InputTextTarea
                title={t('housekeeping.templates.description')}
                name='description'
                placeholder={t('housekeeping.templates.description_placeholder')}
              />
            </div>
            <div className='lg:col-span-2'>
              <label htmlFor='is_required' className='flex items-center gap-2 cursor-pointer'>
                <input
                  id='is_required'
                  name='is_required'
                  type='checkbox'
                  className='rounded border-gray-300'
                  checked={!!values.is_required}
                  onChange={(e) => setFieldValue('is_required', e.target.checked)}
                />
                <span className='text-sm text-aloja-gray-800/80'>{t('housekeeping.templates.is_required')}</span>
              </label>
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default TaskTemplateModal

