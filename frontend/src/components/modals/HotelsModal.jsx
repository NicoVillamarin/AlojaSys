import { Formik } from 'formik'
import React from 'react'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import FileImage from 'src/components/inputs/FileImage'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import SelectBasic from 'src/components/selects/SelectBasic'

/**
 * HotelsModal: crear/editar hotel
 */
const HotelsModal = ({ isOpen, onClose, isEdit = false, hotel, onSuccess }) => {
  const { t } = useTranslation()
  
  // Función para convertir archivo a base64
  const convertFileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.readAsDataURL(file)
      reader.onload = () => resolve(reader.result)
      reader.onerror = error => reject(error)
    })
  }
  const currentHotel = hotel
  const isEditMode = isEdit

  const { mutate: createHotel, isPending: creating } = useCreate({
    resource: 'hotels',
    onSuccess: (data) => { 
      onSuccess && onSuccess(data)
      onClose && onClose()
    },
  })
  const { mutate: updateHotel, isPending: updating } = useUpdate({
    resource: 'hotels',
    onSuccess: (data) => { 
      onSuccess && onSuccess(data)
      onClose && onClose()
    },
  })

  const initialValues = {
    name: currentHotel?.name ?? '',
    legal_name: currentHotel?.legal_name ?? '',
    tax_id: currentHotel?.tax_id ?? '',
    email: currentHotel?.email ?? '',
    phone: currentHotel?.phone ?? '',
    address: currentHotel?.address ?? '',
    country: currentHotel?.country ?? '',
    state: currentHotel?.state ?? '',
    city: currentHotel?.city ?? '',
    check_in_time: (currentHotel?.check_in_time ?? '15:00').slice(0, 5),
    check_out_time: (currentHotel?.check_out_time ?? '11:00').slice(0, 5),
    is_active: currentHotel?.is_active ?? true,
    auto_check_in_enabled: currentHotel?.auto_check_in_enabled ?? false,
    auto_check_out_enabled: currentHotel?.auto_check_out_enabled ?? true,
    auto_no_show_enabled: currentHotel?.auto_no_show_enabled ?? false,
    logo: null, // Archivo seleccionado
    existing_logo_url: currentHotel?.logo_url ?? null, // URL del logo existente
    // WhatsApp
    whatsapp_enabled: currentHotel?.whatsapp_enabled ?? false,
    whatsapp_phone: currentHotel?.whatsapp_phone ?? '',
    whatsapp_provider: currentHotel?.whatsapp_provider ?? '',
    whatsapp_business_id: currentHotel?.whatsapp_business_id ?? '',
    whatsapp_phone_number_id: currentHotel?.whatsapp_phone_number_id ?? '',
    whatsapp_api_token: '', // nunca mostramos el valor actual por seguridad
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
      onSubmit={async (values) => {
        
        try {
          // Crear payload como objeto JSON (no FormData)
          // IMPORTANTE: No usar || undefined porque JSON.stringify() elimina esos campos
          const payload = {
            name: values.name || '',
            enterprise: values.enterprise ? Number(values.enterprise) : null,
            legal_name: values.legal_name || '',
            tax_id: values.tax_id || '',
            email: values.email || '',
            phone: values.phone || '',
            address: values.address || '',
            country: values.country ? Number(values.country) : null,
            state: values.state ? Number(values.state) : null,
            city: values.city ? Number(values.city) : null,
            check_in_time: values.check_in_time || null,
            check_out_time: values.check_out_time || null,
            is_active: values.is_active !== undefined ? values.is_active : true,
            auto_check_in_enabled: values.auto_check_in_enabled || false,
            auto_check_out_enabled: values.auto_check_out_enabled !== undefined ? values.auto_check_out_enabled : true,
            auto_no_show_enabled: values.auto_no_show_enabled || false,
            // WhatsApp config
            whatsapp_enabled: !!values.whatsapp_enabled,
            whatsapp_phone: values.whatsapp_phone || '',
            whatsapp_provider: values.whatsapp_provider || '',
            whatsapp_business_id: values.whatsapp_business_id || '',
            whatsapp_phone_number_id: values.whatsapp_phone_number_id || '',
            whatsapp_api_token: values.whatsapp_api_token || '',
          }
          
          // Agregar logo como base64 si se seleccionó uno nuevo
          if (values.logo) {
            
            // Convertir archivo a base64
            const logoBase64 = await convertFileToBase64(values.logo)
            payload.logo_base64 = logoBase64
            payload.logo_filename = values.logo.name
            
            } else {
              console.log('⚠️ No se seleccionó logo')
          }
          
          
          if (isEditMode && currentHotel?.id) {
            updateHotel({ 
              id: currentHotel.id, 
              body: payload
            })
          } else {
            createHotel(payload)
          }
        } catch (error) {
          console.error('❌ Error procesando logo:', error)
          // En caso de error, enviar sin logo
          // IMPORTANTE: No usar || undefined porque JSON.stringify() elimina esos campos
          const payload = {
            name: values.name || '',
            enterprise: values.enterprise ? Number(values.enterprise) : null,
            legal_name: values.legal_name || '',
            tax_id: values.tax_id || '',
            email: values.email || '',
            phone: values.phone || '',
            address: values.address || '',
            country: values.country ? Number(values.country) : null,
            state: values.state ? Number(values.state) : null,
            city: values.city ? Number(values.city) : null,
            check_in_time: values.check_in_time || null,
            check_out_time: values.check_out_time || null,
            is_active: values.is_active !== undefined ? values.is_active : true,
            auto_check_in_enabled: values.auto_check_in_enabled || false,
            auto_check_out_enabled: values.auto_check_out_enabled !== undefined ? values.auto_check_out_enabled : true,
            auto_no_show_enabled: values.auto_no_show_enabled || false,
            // WhatsApp config
            whatsapp_enabled: !!values.whatsapp_enabled,
            whatsapp_phone: values.whatsapp_phone || '',
            whatsapp_provider: values.whatsapp_provider || '',
            whatsapp_business_id: values.whatsapp_business_id || '',
            whatsapp_phone_number_id: values.whatsapp_phone_number_id || '',
            whatsapp_api_token: values.whatsapp_api_token || '',
          }
          
          if (isEditMode && currentHotel?.id) {
            updateHotel({ id: currentHotel.id, body: payload })
          } else {
            createHotel(payload)
          }
        }
      }}
    >
      {({ values, handleChange, handleSubmit, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEditMode ? t('hotels_modal.edit_hotel') : t('hotels_modal.create_hotel')}
          onSubmit={handleSubmit}
          submitText={isEditMode ? t('hotels_modal.save_changes') : t('hotels_modal.create')}
          cancelText={t('hotels_modal.cancel')}
          submitDisabled={creating || updating}
          size='lg'
        >
          <div>
            <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5 pt-3'>
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
                  <label htmlFor='auto_check_out_enabled' className='flex items-center gap-2 cursor-pointer'>
                    <input
                      id='auto_check_out_enabled'
                      name='auto_check_out_enabled'
                      type='checkbox'
                      className='rounded border-gray-300'
                      checked={!!values.auto_check_out_enabled}
                      onChange={(e) => setFieldValue('auto_check_out_enabled', e.target.checked)}
                    />
                    <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.auto_check_out_enabled')}</span>
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
                <label className='text-xs text-aloja-gray-800/70'>{t('hotels_modal.whatsapp_settings')}</label>
                <div className='space-y-3 mt-2'>
                  <label htmlFor='whatsapp_enabled' className='flex items-center gap-2 cursor-pointer'>
                    <input
                      id='whatsapp_enabled'
                      name='whatsapp_enabled'
                      type='checkbox'
                      className='rounded border-gray-300'
                      checked={!!values.whatsapp_enabled}
                      onChange={(e) => setFieldValue('whatsapp_enabled', e.target.checked)}
                    />
                    <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.whatsapp_enabled')}</span>
                  </label>
                  {values.whatsapp_enabled && (
                    <div className='grid grid-cols-1 md:grid-cols-2 gap-3'>
                      <InputText
                        title={t('hotels_modal.whatsapp_phone')}
                        name='whatsapp_phone'
                        placeholder='+54911...'
                      />
                      <SelectBasic
                        title={t('hotels_modal.whatsapp_provider')}
                        name='whatsapp_provider'
                        options={[
                          { value: '', label: t('common.none') },
                          { value: 'meta_cloud', label: 'Meta WhatsApp Cloud API' },
                          { value: 'twilio', label: 'Twilio' },
                          { value: 'other', label: t('common.other') },
                        ]}
                      />
                      <InputText
                        title={t('hotels_modal.whatsapp_business_id')}
                        name='whatsapp_business_id'
                        placeholder='Business ID (Meta)'
                      />
                      <InputText
                        title={t('hotels_modal.whatsapp_phone_number_id')}
                        name='whatsapp_phone_number_id'
                        placeholder='Phone Number ID'
                      />
                      <InputText
                        title={t('hotels_modal.whatsapp_api_token')}
                        name='whatsapp_api_token'
                        type='password'
                        placeholder={t('hotels_modal.whatsapp_api_token_placeholder')}
                      />
                    </div>
                  )}
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
              {/* Logo del hotel */}
              <div>
                <FileImage
                  name='logo'
                  label={t('hotels_modal.logo') || 'Logo del hotel'}
                  compress={true}
                  maxWidth={800}
                  maxHeight={600}
                  quality={0.9}
                  maxSize={2 * 1024 * 1024} // 2MB
                  existingImageUrl={isEdit ? values.existing_logo_url : null}
                  className='mb-4'
                />
              </div>
            </div>
          </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default HotelsModal