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
import { useAction } from 'src/hooks/useAction'
import SelectBasic from 'src/components/selects/SelectBasic'
import Tabs from '../Tabs'
import Button from 'src/components/Button'

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
  // Estado para pestañas
  const [activeTab, setActiveTab] = React.useState('general')
  
  // Estado interno para manejar el hotel recién creado (para poder configurar limpieza)
  const [createdHotel, setCreatedHotel] = React.useState(null)
  const currentHotel = createdHotel || hotel
  const isEditMode = isEdit || !!createdHotel

  const { mutate: createHotel, isPending: creating } = useCreate({
    resource: 'hotels',
    onSuccess: (data) => { 
      console.log('✅ Hotel creado exitosamente:', data)
      // Guardar el hotel creado para mantener el modal en modo edición
      setCreatedHotel(data)
      // Cambiar a la pestaña de limpieza para que el usuario pueda configurarla
      setActiveTab('housekeeping')
      // Notificar al padre pero no cerrar el modal
      onSuccess && onSuccess(data)
      // NO cerrar el modal automáticamente, dejar que el usuario lo cierre
    },
  })
  const { mutate: updateHotel, isPending: updating } = useUpdate({
    resource: 'hotels',
    onSuccess: (data) => { 
      console.log('✅ Hotel actualizado exitosamente:', data)
      // Si había un hotel creado, actualizarlo también
      if (createdHotel) {
        setCreatedHotel(data)
      }
      onSuccess && onSuccess(data)
      // Solo cerrar si no estamos en la pestaña de limpieza
      // (si estamos en limpieza, el usuario puede querer seguir configurando)
      if (activeTab === 'general') {
        onClose && onClose()
      }
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
  }

  const validationSchema = Yup.object().shape({
    name: Yup.string().required(t('hotels_modal.name_required')),
    email: Yup.string().email(t('hotels_modal.email_invalid')).nullable(),
  })

  // Housekeeping config (solo en edición, porque requiere hotel.id)
  const hkEnabled = isEditMode && !!currentHotel?.id
  const { results: hkConfig, isPending: hkLoading, refetch: refetchHK } = useAction({
    resource: 'housekeeping/config',
    action: hkEnabled ? `by-hotel/${currentHotel.id}` : undefined,
    enabled: hkEnabled,
  })
  const [hkValues, setHkValues] = React.useState(null)
  React.useEffect(() => {
    if (hkConfig && hkEnabled) {
      setHkValues(hkConfig)
    }
  }, [hkConfig, hkEnabled])
  const { mutate: updateHK, isPending: savingHK } = useUpdate({
    resource: 'housekeeping/config',
    onSuccess: (data) => {
      refetchHK && refetchHK()
      // Después de guardar la configuración, cerrar el modal si el hotel fue recién creado
      if (createdHotel) {
        onClose && onClose()
      }
    },
    method: 'PATCH',
  })
  const handleSaveHK = () => {
    if (!hkValues?.id) return
    const payload = {
      enable_auto_assign: !!hkValues.enable_auto_assign,
      create_daily_tasks: !!hkValues.create_daily_tasks,
      daily_generation_time: hkValues.daily_generation_time || null,
      skip_service_on_checkin: !!hkValues.skip_service_on_checkin,
      skip_service_on_checkout: !!hkValues.skip_service_on_checkout,
      linens_every_n_nights: Number(hkValues.linens_every_n_nights ?? 3),
      towels_every_n_nights: Number(hkValues.towels_every_n_nights ?? 1),
      morning_window_start: hkValues.morning_window_start || null,
      morning_window_end: hkValues.morning_window_end || null,
      afternoon_window_start: hkValues.afternoon_window_start || null,
      afternoon_window_end: hkValues.afternoon_window_end || null,
      quiet_hours_start: hkValues.quiet_hours_start || null,
      quiet_hours_end: hkValues.quiet_hours_end || null,
      prefer_by_zone: !!hkValues.prefer_by_zone,
      rebalance_every_minutes: Number(hkValues.rebalance_every_minutes ?? 5),
      checkout_priority: Number(hkValues.checkout_priority ?? 2),
      daily_priority: Number(hkValues.daily_priority ?? 1),
      alert_checkout_unstarted_minutes: Number(hkValues.alert_checkout_unstarted_minutes ?? 30),
    }
    updateHK({ id: hkValues.id, body: payload })
  }
  
  // Resetear el estado cuando se cierra el modal
  React.useEffect(() => {
    if (!isOpen) {
      setCreatedHotel(null)
      setActiveTab('general')
    }
  }, [isOpen])

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={async (values) => {
        console.log('📤 Enviando datos del hotel:', values)
        
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
          }
          
          // Agregar logo como base64 si se seleccionó uno nuevo
          if (values.logo) {
            console.log('📎 Convirtiendo logo a base64:', {
              name: values.logo.name,
              size: values.logo.size,
              type: values.logo.type
            })
            
            // Convertir archivo a base64
            const logoBase64 = await convertFileToBase64(values.logo)
            payload.logo_base64 = logoBase64
            payload.logo_filename = values.logo.name
            
            console.log('✅ Logo convertido a base64, tamaño:', logoBase64.length, 'caracteres')
          } else {
            console.log('⚠️ No se seleccionó logo')
          }
          
          console.log('📋 Payload final:', payload)
          
          if (isEditMode && currentHotel?.id) {
            console.log('🔄 Actualizando hotel ID:', currentHotel.id)
            updateHotel({ 
              id: currentHotel.id, 
              body: payload
            })
          } else {
            console.log('➕ Creando nuevo hotel')
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
          onSubmit={activeTab === 'general' ? handleSubmit : undefined}
          submitText={isEditMode ? t('hotels_modal.save_changes') : t('hotels_modal.create')}
          cancelText={t('hotels_modal.cancel')}
          submitDisabled={creating || updating}
          customFooter={
            activeTab === 'housekeeping' && hkEnabled ? (
              <>
                <Button variant="danger" size="md" onClick={onClose}>
                  {t('hotels_modal.cancel')}
                </Button>
                <Button
                  variant="success"
                  size="md"
                  disabled={hkLoading || savingHK || !hkValues}
                  onClick={handleSaveHK}
                  loadingText={savingHK}
                >
                  {t('hotels_modal.housekeeping.save_config')}
                </Button>
              </>
            ) : undefined
          }
          size='lg'
        >
          <Tabs
            tabs={[
              { id: 'general', label: t('hotels_modal.general') },
              ...(hkEnabled ? [{ id: 'housekeeping', label: t('hotels_modal.housekeeping.title') }] : []),
            ]}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />
          
          {activeTab === 'general' && (
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
              <div className='lg:col-span-2'>
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
          )}

          {activeTab === 'housekeeping' && hkEnabled && (
            <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5 pt-3'>
              <div className='lg:col-span-2 grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5'>
                    {/* Activación y generación */}
                    <label className='flex items-center gap-2 cursor-pointer'>
                      <input
                        type='checkbox'
                        className='rounded border-gray-300'
                        checked={!!hkValues?.enable_auto_assign}
                        onChange={(e) => setHkValues((v) => ({ ...v, enable_auto_assign: e.target.checked }))}
                        disabled={hkLoading}
                      />
                      <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.housekeeping.enable_auto_assign')}</span>
                    </label>
                    <label className='flex items-center gap-2 cursor-pointer'>
                      <input
                        type='checkbox'
                        className='rounded border-gray-300'
                        checked={!!hkValues?.create_daily_tasks}
                        onChange={(e) => setHkValues((v) => ({ ...v, create_daily_tasks: e.target.checked }))}
                        disabled={hkLoading}
                      />
                      <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.housekeeping.create_daily_tasks')}</span>
                    </label>
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.daily_generation_time')}</label>
                      <input
                        type='time'
                        className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                        value={hkValues?.daily_generation_time || ''}
                        onChange={(e) => setHkValues((v) => ({ ...v, daily_generation_time: e.target.value }))}
                        disabled={hkLoading}
                      />
                    </div>
                    {/* Reglas de servicio */}
                    <label className='flex items-center gap-2 cursor-pointer'>
                      <input
                        type='checkbox'
                        className='rounded border-gray-300'
                        checked={!!hkValues?.skip_service_on_checkin}
                        onChange={(e) => setHkValues((v) => ({ ...v, skip_service_on_checkin: e.target.checked }))}
                        disabled={hkLoading}
                      />
                      <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.housekeeping.skip_service_on_checkin')}</span>
                    </label>
                    <label className='flex items-center gap-2 cursor-pointer'>
                      <input
                        type='checkbox'
                        className='rounded border-gray-300'
                        checked={!!hkValues?.skip_service_on_checkout}
                        onChange={(e) => setHkValues((v) => ({ ...v, skip_service_on_checkout: e.target.checked }))}
                        disabled={hkLoading}
                      />
                      <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.housekeeping.skip_service_on_checkout')}</span>
                    </label>
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.linens_every')}</label>
                      <input
                        type='number'
                        className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                        value={hkValues?.linens_every_n_nights ?? 3}
                        onChange={(e) => setHkValues((v) => ({ ...v, linens_every_n_nights: e.target.value }))}
                        placeholder='3'
                        disabled={hkLoading}
                      />
                    </div>
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.towels_every')}</label>
                      <input
                        type='number'
                        className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                        value={hkValues?.towels_every_n_nights ?? 1}
                        onChange={(e) => setHkValues((v) => ({ ...v, towels_every_n_nights: e.target.value }))}
                        placeholder='1'
                        disabled={hkLoading}
                      />
                    </div>
                    {/* Ventanas */}
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.morning_window_start')}</label>
                      <input
                        type='time'
                        className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                        value={hkValues?.morning_window_start || ''}
                        onChange={(e) => setHkValues((v) => ({ ...v, morning_window_start: e.target.value }))}
                        disabled={hkLoading}
                      />
                    </div>
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.morning_window_end')}</label>
                      <input
                        type='time'
                        className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                        value={hkValues?.morning_window_end || ''}
                        onChange={(e) => setHkValues((v) => ({ ...v, morning_window_end: e.target.value }))}
                        disabled={hkLoading}
                      />
                    </div>
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.afternoon_window_start')}</label>
                      <input
                        type='time'
                        className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                        value={hkValues?.afternoon_window_start || ''}
                        onChange={(e) => setHkValues((v) => ({ ...v, afternoon_window_start: e.target.value }))}
                        disabled={hkLoading}
                      />
                    </div>
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.afternoon_window_end')}</label>
                      <input
                        type='time'
                        className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                        value={hkValues?.afternoon_window_end || ''}
                        onChange={(e) => setHkValues((v) => ({ ...v, afternoon_window_end: e.target.value }))}
                        disabled={hkLoading}
                      />
                    </div>
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.quiet_hours_start')}</label>
                      <input
                        type='time'
                        className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                        value={hkValues?.quiet_hours_start || ''}
                        onChange={(e) => setHkValues((v) => ({ ...v, quiet_hours_start: e.target.value }))}
                        disabled={hkLoading}
                      />
                    </div>
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.quiet_hours_end')}</label>
                      <input
                        type='time'
                        className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                        value={hkValues?.quiet_hours_end || ''}
                        onChange={(e) => setHkValues((v) => ({ ...v, quiet_hours_end: e.target.value }))}
                        disabled={hkLoading}
                      />
                    </div>
                    {/* Asignación y prioridades */}
                    <label className='flex items-center gap-2 cursor-pointer'>
                      <input
                        type='checkbox'
                        className='rounded border-gray-300'
                        checked={!!hkValues?.prefer_by_zone}
                        onChange={(e) => setHkValues((v) => ({ ...v, prefer_by_zone: e.target.checked }))}
                      />
                      <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.housekeeping.prefer_by_zone')}</span>
                    </label>
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.rebalance_every_minutes')}</label>
                      <input
                        type='number'
                        className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                        value={hkValues?.rebalance_every_minutes ?? 5}
                        onChange={(e) => setHkValues((v) => ({ ...v, rebalance_every_minutes: e.target.value }))}
                        placeholder='5'
                        disabled={hkLoading}
                      />
                    </div>
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.checkout_priority')}</label>
                      <select
                        className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                        value={hkValues?.checkout_priority ?? 2}
                        onChange={(e) => setHkValues((v) => ({ ...v, checkout_priority: Number(e.target.value) }))}
                        disabled={hkLoading}
                      >
                        <option value={2}>{t('housekeeping.priority_high')}</option>
                        <option value={1}>{t('housekeeping.priority_medium')}</option>
                        <option value={0}>{t('housekeeping.priority_low')}</option>
                      </select>
                    </div>
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.daily_priority')}</label>
                      <select
                        className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                        value={hkValues?.daily_priority ?? 1}
                        onChange={(e) => setHkValues((v) => ({ ...v, daily_priority: Number(e.target.value) }))}
                        disabled={hkLoading}
                      >
                        <option value={2}>{t('housekeeping.priority_high')}</option>
                        <option value={1}>{t('housekeeping.priority_medium')}</option>
                        <option value={0}>{t('housekeeping.priority_low')}</option>
                      </select>
                    </div>
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.alert_checkout_unstarted_minutes')}</label>
                      <input
                        type='number'
                        className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                        value={hkValues?.alert_checkout_unstarted_minutes ?? 30}
                        onChange={(e) => setHkValues((v) => ({ ...v, alert_checkout_unstarted_minutes: e.target.value }))}
                        placeholder='30'
                        disabled={hkLoading}
                      />
                    </div>
                  </div>
            </div>
          )}
        </ModalLayout>
      )}
    </Formik>
  )
}

export default HotelsModal