import { useEffect, useState, useRef } from 'react'
import { Formik } from 'formik'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectBasic from 'src/components/selects/SelectBasic'
import Checkbox from 'src/components/Checkbox'
import InputTextTarea from '../inputs/InputTextTarea'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import { useList } from 'src/hooks/useList'

const CancellationPoliciesModal = ({ isOpen, onClose, isEdit = false, policy, onSuccess }) => {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState('basic')
  const [instanceKey, setInstanceKey] = useState(0)
  const formikRef = useRef()

  // Obtener lista de hoteles
  const { results: hotels } = useList({
    resource: 'hotels',
    params: {},
  })

  const { mutate: createPolicy, isPending: creating } = useCreate({
    resource: 'payments/cancellation-policies',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  const { mutate: updatePolicy, isPending: updating } = useUpdate({
    resource: 'payments/cancellation-policies',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const initialValues = {
    name: isEdit ? (policy?.name ?? '') : '',
    hotel: isEdit ? (String(policy?.hotel ?? '')) : '',
    is_active: isEdit ? (policy?.is_active ?? true) : true,
    is_default: isEdit ? (policy?.is_default ?? false) : false,
    
    // Configuración de tiempos
    free_cancellation_time: isEdit ? (policy?.free_cancellation_time ?? 24) : 24,
    free_cancellation_unit: isEdit ? (policy?.free_cancellation_unit ?? 'hours') : 'hours',
    partial_refund_time: isEdit ? (policy?.partial_refund_time ?? 72) : 72,
    partial_refund_unit: isEdit ? (policy?.partial_refund_unit ?? 'hours') : 'hours',
    partial_refund_percentage: isEdit ? (policy?.partial_refund_percentage ?? 50) : 50,
    no_refund_time: isEdit ? (policy?.no_refund_time ?? 168) : 168,
    no_refund_unit: isEdit ? (policy?.no_refund_unit ?? 'hours') : 'hours',
    
    // Configuración de penalidades
    cancellation_fee_type: isEdit ? (policy?.cancellation_fee_type ?? 'percentage') : 'percentage',
    cancellation_fee_value: isEdit ? (policy?.cancellation_fee_value ?? 10) : 10,
    
    // Restricciones por estado
    allow_cancellation_after_checkin: isEdit ? (policy?.allow_cancellation_after_checkin ?? false) : false,
    allow_cancellation_after_checkout: isEdit ? (policy?.allow_cancellation_after_checkout ?? false) : false,
    allow_cancellation_no_show: isEdit ? (policy?.allow_cancellation_no_show ?? true) : true,
    allow_cancellation_early_checkout: isEdit ? (policy?.allow_cancellation_early_checkout ?? false) : false,
    
    
    // Mensajes personalizados
    free_cancellation_message: isEdit ? (policy?.free_cancellation_message ?? '') : '',
    partial_cancellation_message: isEdit ? (policy?.partial_cancellation_message ?? '') : '',
    no_cancellation_message: isEdit ? (policy?.no_cancellation_message ?? '') : '',
    cancellation_fee_message: isEdit ? (policy?.cancellation_fee_message ?? '') : '',
    
    // Configuración avanzada
    apply_to_all_room_types: isEdit ? (policy?.apply_to_all_room_types ?? true) : true,
    room_types: isEdit ? (policy?.room_types ?? []) : [],
    apply_to_all_channels: isEdit ? (policy?.apply_to_all_channels ?? true) : true,
    channels: isEdit ? (policy?.channels ?? []) : [],
    apply_to_all_seasons: isEdit ? (policy?.apply_to_all_seasons ?? true) : true,
    seasonal_rules: isEdit ? (policy?.seasonal_rules ?? []) : [],
  }

  const validationSchema = Yup.object({
    name: Yup.string().required(t('common.required')),
    hotel: Yup.string().required(t('common.required')),
    free_cancellation_time: Yup.number().min(0, t('common.min_value_0')),
    partial_refund_time: Yup.number().min(0, t('common.min_value_0')),
    no_refund_time: Yup.number().min(0, t('common.min_value_0')),
    partial_refund_percentage: Yup.number().min(0).max(100, t('common.max_value_100')),
    cancellation_fee_value: Yup.number().min(0, t('common.min_value_0')),
  })

  const handleSubmit = (values) => {
    const data = {
      name: values.name,
      hotel: values.hotel,
      is_active: values.is_active,
      is_default: values.is_default,
      
      // Configuración de tiempos
      free_cancellation_time: parseInt(values.free_cancellation_time) || 0,
      free_cancellation_unit: values.free_cancellation_unit,
      partial_refund_time: parseInt(values.partial_refund_time) || 0,
      partial_refund_unit: values.partial_refund_unit,
      partial_refund_percentage: parseFloat(values.partial_refund_percentage) || 0,
      no_refund_time: parseInt(values.no_refund_time) || 0,
      no_refund_unit: values.no_refund_unit,
      
      // Configuración de penalidades
      cancellation_fee_type: values.cancellation_fee_type,
      cancellation_fee_value: parseFloat(values.cancellation_fee_value) || 0,
      
      // Restricciones por estado
      allow_cancellation_after_checkin: values.allow_cancellation_after_checkin,
      allow_cancellation_after_checkout: values.allow_cancellation_after_checkout,
      allow_cancellation_no_show: values.allow_cancellation_no_show,
      allow_cancellation_early_checkout: values.allow_cancellation_early_checkout,
      
      
      // Mensajes personalizados
      free_cancellation_message: values.free_cancellation_message,
      partial_cancellation_message: values.partial_cancellation_message,
      no_cancellation_message: values.no_cancellation_message,
      cancellation_fee_message: values.cancellation_fee_message,
      
      // Configuración avanzada
      apply_to_all_room_types: values.apply_to_all_room_types,
      room_types: values.room_types,
      apply_to_all_channels: values.apply_to_all_channels,
      channels: values.channels,
      apply_to_all_seasons: values.apply_to_all_seasons,
      seasonal_rules: values.seasonal_rules,
    }

    if (isEdit) {
      updatePolicy({ id: policy.id, body: data })
    } else {
      createPolicy(data)
    }
  }

  const feeTypeOptions = [
    { value: 'none', label: t('payments.cancellation.policies.fee_types.none') },
    { value: 'percentage', label: t('payments.cancellation.policies.fee_types.percentage') },
    { value: 'fixed', label: t('payments.cancellation.policies.fee_types.fixed') },
    { value: 'first_night', label: t('payments.cancellation.policies.fee_types.first_night') },
    { value: 'nights_percentage', label: t('payments.cancellation.policies.fee_types.nights_percentage') }
  ]


  const timeUnitOptions = [
    { value: 'hours', label: t('payments.cancellation.policies.time_units.hours') },
    { value: 'days', label: t('payments.cancellation.policies.time_units.days') },
    { value: 'weeks', label: t('payments.cancellation.policies.time_units.weeks') }
  ]

  const hotelOptions = hotels?.map(h => ({ value: h.id, label: h.name })) || []

  useEffect(() => {
    if (isOpen && !isEdit) {
      setInstanceKey((k) => k + 1)
    }
  }, [isOpen, isEdit])

  const tabs = [
    { id: 'basic', label: t('payments.cancellation.policies.tabs.basic') },
    { id: 'times', label: t('payments.cancellation.policies.tabs.times') },
    { id: 'restrictions', label: t('payments.cancellation.policies.tabs.restrictions') },
    { id: 'messages', label: t('payments.cancellation.policies.tabs.messages') },
    { id: 'advanced', label: t('payments.cancellation.policies.tabs.advanced') }
  ]

  return (
    <Formik
      key={isEdit ? `edit-${policy?.id ?? 'new'}` : `create-${instanceKey}`}
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={handleSubmit}
      enableReinitialize
    >
      {({ values, errors, touched, handleChange, handleBlur, handleSubmit, setFieldValue }) => (
        <ModalLayout 
          isOpen={isOpen} 
          onClose={onClose} 
           title={isEdit ? t('payments.cancellation.policies.edit_policy_cancellation') : t('payments.cancellation.policies.add_policy_cancellation')}
          size="xl"
          onSubmit={handleSubmit}
          submitText={isEdit ? t('common.save') : t('common.create')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
        >
          <div className="space-y-6">
            {/* Tabs */}
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8 overflow-x-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap flex-shrink-0 ${
                      activeTab === tab.id
                        ? 'border-aloja-navy text-aloja-navy'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>

            {/* Tab Content */}
            {activeTab === 'basic' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <InputText
                    title={t('payments.cancellation.policies.policy_name')}
                    name="name"
                    value={values.name}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    error={touched.name && errors.name}
                    placeholder={t('payments.cancellation.policies.policy_name')}
                  />
                  <SelectBasic
                    title={t('sidebar.hotels')}
                    name="hotel"
                    options={hotelOptions}
                    placeholder={t('common.select_hotel')}
                  />
                </div>

                <div className="space-y-3">
                  <Checkbox
                    label={t('payments.cancellation.policies.is_active')}
                    checked={values.is_active}
                    onChange={(checked) => setFieldValue('is_active', checked)}
                  />
                  <Checkbox
                    label={t('payments.cancellation.policies.is_default')}
                    checked={values.is_default}
                    onChange={(checked) => setFieldValue('is_default', checked)}
                  />
                </div>
              </div>
            )}

            {activeTab === 'times' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <InputText
                      title={t('payments.cancellation.policies.free_cancellation_time')}
                      name="free_cancellation_time"
                      type="number"
                      value={values.free_cancellation_time}
                      onChange={handleChange}
                      onBlur={handleBlur}
                      error={touched.free_cancellation_time && errors.free_cancellation_time}
                    />
                  </div>
                  <SelectBasic
                    title={t('payments.cancellation.policies.time_unit')}
                    name="free_cancellation_unit"
                    options={timeUnitOptions}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <InputText
                      title={t('payments.cancellation.policies.partial_refund_time')}
                      name="partial_refund_time"
                      type="number"
                      value={values.partial_refund_time}
                      onChange={handleChange}
                      onBlur={handleBlur}
                      error={touched.partial_refund_time && errors.partial_refund_time}
                    />
                  </div>
                  <SelectBasic
                    title={t('payments.cancellation.policies.time_unit')}
                    name="partial_refund_unit"
                    options={timeUnitOptions}
                  />
                  <div>
                    <InputText
                      title={t('payments.cancellation.policies.partial_refund_percentage')}
                      name="partial_refund_percentage"
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      value={values.partial_refund_percentage}
                      onChange={handleChange}
                      onBlur={handleBlur}
                      error={touched.partial_refund_percentage && errors.partial_refund_percentage}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <InputText
                      title={t('payments.cancellation.policies.no_refund_time')}
                      name="no_refund_time"
                      type="number"
                      value={values.no_refund_time}
                      onChange={handleChange}
                      onBlur={handleBlur}
                      error={touched.no_refund_time && errors.no_refund_time}
                    />
                  </div>
                  <SelectBasic
                    title={t('payments.cancellation.policies.time_unit')}
                    name="no_refund_unit"
                    options={timeUnitOptions}
                  />
                </div>
              </div>
            )}

            {activeTab === 'restrictions' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <SelectBasic
                    title={t('payments.cancellation.policies.fee_type')}
                    name="cancellation_fee_type"
                    options={feeTypeOptions}
                  />
                  <InputText
                    title={t('payments.cancellation.policies.cancellation_fee_value')}
                    name="cancellation_fee_value"
                    type="number"
                    step="0.01"
                    value={values.cancellation_fee_value}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    error={touched.cancellation_fee_value && errors.cancellation_fee_value}
                  />
                </div>

                <div className="space-y-3">
                  <Checkbox
                    label={t('payments.cancellation.policies.allow_cancellation_after_checkin')}
                    checked={values.allow_cancellation_after_checkin}
                    onChange={(checked) => setFieldValue('allow_cancellation_after_checkin', checked)}
                  />
                  <Checkbox
                    label={t('payments.cancellation.policies.allow_cancellation_after_checkout')}
                    checked={values.allow_cancellation_after_checkout}
                    onChange={(checked) => setFieldValue('allow_cancellation_after_checkout', checked)}
                  />
                  <Checkbox
                    label={t('payments.cancellation.policies.allow_cancellation_no_show')}
                    checked={values.allow_cancellation_no_show}
                    onChange={(checked) => setFieldValue('allow_cancellation_no_show', checked)}
                  />
                  <Checkbox
                    label={t('payments.cancellation.policies.allow_cancellation_early_checkout')}
                    checked={values.allow_cancellation_early_checkout}
                    onChange={(checked) => setFieldValue('allow_cancellation_early_checkout', checked)}
                  />
                </div>
              </div>
            )}


            {activeTab === 'messages' && (
              <div className="space-y-4">
                <InputTextTarea
                  title={t('payments.cancellation.policies.free_cancellation_message')}
                  name="free_cancellation_message"
                  value={values.free_cancellation_message}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  placeholder={t('payments.cancellation.policies.free_cancellation_message_placeholder')}
                  rows={3}
                />
                <InputTextTarea
                  title={t('payments.cancellation.policies.partial_cancellation_message')}
                  name="partial_cancellation_message"
                  value={values.partial_cancellation_message}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  placeholder={t('payments.cancellation.policies.partial_cancellation_message')}
                  rows={3}
                />
                <InputTextTarea
                  title={t('payments.cancellation.policies.no_cancellation_message')}
                  name="no_cancellation_message"
                  value={values.no_cancellation_message}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  placeholder={t('payments.cancellation.policies.no_cancellation_message')}
                  rows={3}
                />
                <InputTextTarea
                  title={t('payments.cancellation.policies.cancellation_fee_message')}
                  name="cancellation_fee_message"
                  value={values.cancellation_fee_message}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  placeholder={t('payments.cancellation.policies.cancellation_fee_message_placeholder')}
                  rows={3}
                />
              </div>
            )}

            {activeTab === 'advanced' && (
              <div className="space-y-4">
                <div className="space-y-3">
                  <Checkbox
                    label={t('payments.cancellation.policies.apply_to_all_room_types')}
                    checked={values.apply_to_all_room_types}
                    onChange={(checked) => setFieldValue('apply_to_all_room_types', checked)}
                  />
                  <Checkbox
                    label={t('payments.cancellation.policies.apply_to_all_channels')}
                    checked={values.apply_to_all_channels}
                    onChange={(checked) => setFieldValue('apply_to_all_channels', checked)}
                  />
                  <Checkbox
                    label={t('payments.cancellation.policies.apply_to_all_seasons')}
                    checked={values.apply_to_all_seasons}
                    onChange={(checked) => setFieldValue('apply_to_all_seasons', checked)}
                  />
                </div>
              </div>
            )}
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default CancellationPoliciesModal
