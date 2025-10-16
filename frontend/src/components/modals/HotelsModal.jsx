import { Formik } from 'formik'
import React from 'react'
import { useTranslation } from 'react-i18next'
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
  const { t } = useTranslation()
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
    auto_check_in_enabled: hotel?.auto_check_in_enabled ?? false,
    auto_no_show_enabled: hotel?.auto_no_show_enabled ?? false,
  }

  const validationSchema = Yup.object().shape({
    name: Yup.string().required(t('hotels_modal.name_required')),
    email: Yup.string().email(t('hotels_modal.email_invalid')).nullable(),
  })

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          name: values.name || undefined,
          enterprise: values.enterprise ? Number(values.enterprise) : undefined,
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
          auto_check_in_enabled: values.auto_check_in_enabled || false,
          auto_no_show_enabled: values.auto_no_show_enabled || false,
        }
        if (isEdit && hotel?.id) updateHotel({ id: hotel.id, body: payload })
        else createHotel(payload)
      }}
    >
      {({ values, handleChange, handleSubmit, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('hotels_modal.edit_hotel') : t('hotels_modal.create_hotel')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('hotels_modal.save_changes') : t('hotels_modal.create')}
          cancelText={t('hotels_modal.cancel')}
          submitDisabled={creating || updating}
          size='lg'
        >
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5'>
            <SelectAsync
              title={t('sidebar.enterprises')}
              name='enterprise'
              resource='enterprises'
              placeholder={t('enterprises.select_enterprise')}
              getOptionLabel={(e) => e?.name}
              getOptionValue={(e) => e?.id}
            />
            <InputText title={`${t('hotels_modal.name')} *`} name='name' placeholder={t('hotels_modal.name_placeholder')} autoFocus />
            <InputText title={t('hotels_modal.legal_name')} name='legal_name' placeholder={t('hotels_modal.legal_name_placeholder')} />
            <InputText title={t('hotels_modal.tax_id')} name='tax_id' placeholder={t('hotels_modal.tax_id_placeholder')} />
            <InputText title={t('hotels_modal.email')} name='email' placeholder={t('hotels_modal.email_placeholder')} />
            <InputText title={t('hotels_modal.phone')} name='phone' placeholder={t('hotels_modal.phone_placeholder')} />
            <InputText title={t('hotels_modal.address')} name='address' placeholder={t('hotels_modal.address_placeholder')} />
            <SelectAsync
              title={t('hotels_modal.country')}
              name='country'
              resource='countries'
              placeholder={t('hotels_modal.country_placeholder')}
              getOptionLabel={(c) => c?.name}
              getOptionValue={(c) => c?.id}
              onValueChange={() => {
                // al cambiar país, limpiar state y city
                setFieldValue('state', '')
                setFieldValue('city', '')
              }}
            />
            <SelectAsync
              title={t('hotels_modal.state')}
              name='state'
              resource='states'
              placeholder={t('hotels_modal.state_placeholder')}
              extraParams={{ country: values.country || undefined }}
              getOptionLabel={(s) => s?.name}
              getOptionValue={(s) => s?.id}
              onValueChange={() => {
                // al cambiar state, limpiar city
                setFieldValue('city', '')
              }}
            />
            <SelectAsync
              title={t('hotels_modal.city')}
              name='city'
              resource='cities'
              placeholder={t('hotels_modal.city_placeholder')}
              extraParams={{ state: values.state || undefined, country: values.country || undefined }}
              getOptionLabel={(c) => c?.name}
              getOptionValue={(c) => c?.id}
            />
            <InputText title={t('hotels_modal.check_in_time')} name='check_in_time' type='time' />
            <InputText title={t('hotels_modal.check_out_time')} name='check_out_time' type='time' />
            <div className='lg:col-span-2 space-y-4'>
              <div>
                <label className='text-xs text-aloja-gray-800/70'>{t('hotels_modal.automation_settings')}</label>
                <div className='space-y-3 mt-2'>
                  <label htmlFor='auto_check_in_enabled' className='flex items-center gap-2 cursor-pointer'>
                    <input
                      id='auto_check_in_enabled'
                      name='auto_check_in_enabled'
                      type='checkbox'
                      className='rounded border-gray-300'
                      checked={!!values.auto_check_in_enabled}
                      onChange={(e) => setFieldValue('auto_check_in_enabled', e.target.checked)}
                    />
                    <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.auto_check_in_enabled')}</span>
                  </label>
                  <label htmlFor='auto_no_show_enabled' className='flex items-center gap-2 cursor-pointer'>
                    <input
                      id='auto_no_show_enabled'
                      name='auto_no_show_enabled'
                      type='checkbox'
                      className='rounded border-gray-300'
                      checked={!!values.auto_no_show_enabled}
                      onChange={(e) => setFieldValue('auto_no_show_enabled', e.target.checked)}
                    />
                    <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.auto_no_show_enabled')}</span>
                  </label>
                </div>
              </div>
              
              <div>
                <label className='text-xs text-aloja-gray-800/70'>{t('hotels_modal.status')}</label>
                <label htmlFor='is_active' className='flex items-center gap-2 cursor-pointer mt-2'>
                  <input
                    id='is_active'
                    name='is_active'
                    type='checkbox'
                    className='rounded border-gray-300'
                    checked={!!values.is_active}
                    onChange={(e) => setFieldValue('is_active', e.target.checked)}
                  />
                  <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.enabled_for_operation')}</span>
                </label>
              </div>
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default HotelsModal