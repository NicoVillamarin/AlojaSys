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
import { useList } from 'src/hooks/useList'

const validationSchema = (t) => Yup.object().shape({
  hotel: Yup.number().required(t('housekeeping.staff.validations.hotel_required')),
  first_name: Yup.string().required(t('housekeeping.staff.validations.first_name_required')),
})

const CleaningStaffModal = ({ isOpen, onClose, isEdit = false, staff, onSuccess }) => {
  const { t } = useTranslation()
  const { hasSingleHotel, singleHotelId } = useUserHotels()
  const [instanceKey, setInstanceKey] = useState(0)

  const initialValues = {
    hotel: staff?.hotel ?? (hasSingleHotel ? singleHotelId : ''),
    first_name: staff?.first_name ?? '',
    last_name: staff?.last_name ?? '',
    shift: staff?.shift ?? '',
    work_start_time: staff?.work_start_time ?? '',
    work_end_time: staff?.work_end_time ?? '',
    zone: staff?.zone ?? '',
    cleaning_zone_ids: staff?.cleaning_zones?.map(z => z.id) ?? [],
    is_active: staff?.is_active ?? true,
  }

  const { mutate: createStaff, isPending: creating } = useCreate({
    resource: 'housekeeping/staff',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
    },
  })
  const { mutate: updateStaff, isPending: updating } = useUpdate({
    resource: 'housekeeping/staff',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
    },
  })

  // Obtener zonas de limpieza para el select (se actualiza cuando cambia el hotel)
  const [selectedHotel, setSelectedHotel] = useState(initialValues.hotel)
  const { results: zones } = useList({
    resource: 'housekeeping/zones',
    params: { hotel: selectedHotel },
    enabled: isOpen && !!selectedHotel,
  })
  

  useEffect(() => {
    if (isOpen && !isEdit) {
      setInstanceKey((k) => k + 1)
      setSelectedHotel(hasSingleHotel ? singleHotelId : '')
    } else if (isOpen && isEdit && staff?.hotel) {
      setSelectedHotel(staff.hotel)
    }
  }, [isOpen, isEdit, staff?.hotel, hasSingleHotel, singleHotelId])
  

  return (
    <Formik
      key={isEdit ? `edit-${staff?.id ?? 'new'}` : `create-${instanceKey}`}
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema(t)}
      onSubmit={(values) => {
        // Construir payload sin el campo user
        // El usuario se asigna automáticamente cuando se marca como is_housekeeping_staff en UsersModal
        const payload = {
          hotel: values.hotel || undefined,
          first_name: values.first_name || undefined,
          last_name: values.last_name || undefined,
          shift: values.shift || null,
          work_start_time: values.work_start_time || null,
          work_end_time: values.work_end_time || null,
          zone: values.zone || null,
          cleaning_zone_ids: values.cleaning_zone_ids || [],
          is_active: values.is_active ?? true,
        }
        
        if (isEdit && staff?.id) {
          updateStaff({ id: staff.id, body: payload })
        } else {
          createStaff(payload)
        }
      }}
    >
      {({ values, handleChange, handleSubmit, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('housekeeping.staff.modal.edit_title') : t('housekeeping.staff.modal.create_title')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('common.save') : t('housekeeping.staff.create_staff')}
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
              onValueChange={(opt, val) => {
                setSelectedHotel(val)
                setFieldValue('cleaning_zone_ids', []) // Limpiar zonas al cambiar hotel
              }}
            />
            <InputText 
              title={`${t('housekeeping.staff.first_name')} *`} 
              name='first_name' 
              placeholder={t('housekeeping.staff.first_name_placeholder')} 
            />
            <InputText 
              title={t('housekeeping.staff.last_name')} 
              name='last_name' 
              placeholder={t('housekeeping.staff.last_name_placeholder')} 
            />
            <SelectBasic
              title={t('housekeeping.staff.shift')}
              name='shift'
              options={[
                { value: '', label: t('common.none') },
                { value: 'morning', label: t('housekeeping.shift.morning') },
                { value: 'afternoon', label: t('housekeeping.shift.afternoon') },
                { value: 'night', label: t('housekeeping.shift.night') },
              ]}
              placeholder={t('common.select_placeholder')}
            />
            <div>
              <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>
                {t('housekeeping.staff.work_start_time')}
              </label>
              <input
                type='time'
                name='work_start_time'
                value={values.work_start_time || ''}
                onChange={handleChange}
                className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
              />
            </div>
            <div>
              <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>
                {t('housekeeping.staff.work_end_time')}
              </label>
              <input
                type='time'
                name='work_end_time'
                value={values.work_end_time || ''}
                onChange={handleChange}
                className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
              />
            </div>
            <InputText 
              title={t('housekeeping.staff.zone')} 
              name='zone' 
              placeholder={t('housekeeping.staff.zone_placeholder')} 
            />
            <div>
              <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>
                {t('housekeeping.staff.cleaning_zones')}
              </label>
              <SelectBasic
                name='cleaning_zone_ids'
                isMulti
                options={zones?.map(z => ({ value: z.id, label: z.name })) || []}
                value={values.cleaning_zone_ids?.map(id => ({ value: id, label: zones?.find(z => z.id === id)?.name || '' })) || []}
                onChange={(selected) => {
                  setFieldValue('cleaning_zone_ids', selected ? selected.map(s => s.value) : [])
                }}
                placeholder={t('housekeeping.staff.cleaning_zones_placeholder')}
              />
            </div>
            <div className='flex items-center gap-2'>
              <input
                type='checkbox'
                name='is_active'
                checked={!!values.is_active}
                onChange={(e) => setFieldValue('is_active', e.target.checked)}
                className='rounded border-gray-300'
              />
              <label className='text-sm text-aloja-gray-800/80 cursor-pointer'>
                {t('common.active')}
              </label>
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default CleaningStaffModal

