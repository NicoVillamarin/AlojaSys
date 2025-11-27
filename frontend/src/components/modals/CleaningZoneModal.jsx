import React, { useEffect, useState } from 'react'
import { Formik } from 'formik'
import * as Yup from 'yup'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import InputTextTarea from 'src/components/inputs/InputTextTarea'
import SelectAsync from 'src/components/selects/SelectAsync'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import { useUserHotels } from 'src/hooks/useUserHotels'

const validationSchema = (t) => Yup.object().shape({
  hotel: Yup.number().required(t('housekeeping.zones.validations.hotel_required')),
  name: Yup.string().required(t('housekeeping.zones.validations.name_required')),
  floor: Yup.number().nullable(),
})

const CleaningZoneModal = ({ isOpen, onClose, isEdit = false, zone, onSuccess }) => {
  const { t } = useTranslation()
  const { hasSingleHotel, singleHotelId } = useUserHotels()
  const [instanceKey, setInstanceKey] = useState(0)

  const initialValues = {
    hotel: zone?.hotel ?? (hasSingleHotel ? singleHotelId : ''),
    name: zone?.name ?? '',
    description: zone?.description ?? '',
    floor: zone?.floor ?? '',
  }

  const { mutate: createZone, isPending: creating } = useCreate({
    resource: 'housekeeping/zones',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
    },
  })
  const { mutate: updateZone, isPending: updating } = useUpdate({
    resource: 'housekeeping/zones',
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
      key={isEdit ? `edit-${zone?.id ?? 'new'}` : `create-${instanceKey}`}
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema(t)}
      onSubmit={(values) => {
        const payload = {
          hotel: values.hotel || undefined,
          name: values.name || undefined,
          description: values.description || undefined,
          floor: values.floor ? parseInt(values.floor, 10) : null,
        }
        if (isEdit && zone?.id) {
          updateZone({ id: zone.id, body: payload })
        } else {
          createZone(payload)
        }
      }}
    >
      {({ values, handleChange, handleSubmit, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('housekeeping.zones.modal.edit_title') : t('housekeeping.zones.modal.create_title')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('common.save') : t('housekeeping.zones.create_zone')}
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
            <InputText
              title={`${t('housekeeping.zones.name')} *`}
              name='name'
              placeholder={t('housekeeping.zones.name_placeholder')}
            />
            <InputText
              title={t('housekeeping.zones.floor')}
              name='floor'
              type='number'
              placeholder={t('housekeeping.zones.floor_placeholder')}
            />
            <div className='lg:col-span-2'>
              <InputTextTarea
                title={t('housekeeping.zones.description')}
                name='description'
                placeholder={t('housekeeping.zones.description_placeholder')}
              />
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default CleaningZoneModal

