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
import SelectAsync from '../selects/SelectAsync'

const DevolutionPoliciesModal = ({ isOpen, onClose, isEdit = false, policy, onSuccess }) => {
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
    resource: 'payments/refund-policies',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  const { mutate: updatePolicy, isPending: updating } = useUpdate({
    resource: 'payments/refund-policies',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const initialValues = {
    name: isEdit ? (policy?.name ?? '') : '',
    hotel: isEdit ? (policy?.hotel ?? '') : '',
    is_active: isEdit ? (policy?.is_active ?? true) : true,
    is_default: isEdit ? (policy?.is_default ?? false) : false,
    
    // Configuración de tiempos de devolución
    full_refund_time: isEdit ? (policy?.full_refund_time ?? 24) : 24,
    full_refund_unit: isEdit ? (policy?.full_refund_unit ?? 'hours') : 'hours',
    partial_refund_time: isEdit ? (policy?.partial_refund_time ?? 72) : 72,
    partial_refund_unit: isEdit ? (policy?.partial_refund_unit ?? 'hours') : 'hours',
    partial_refund_percentage: isEdit ? (policy?.partial_refund_percentage ?? 50) : 50,
    no_refund_time: isEdit ? (policy?.no_refund_time ?? 168) : 168,
    no_refund_unit: isEdit ? (policy?.no_refund_unit ?? 'hours') : 'hours',
    
    // Configuración de métodos de devolución
    refund_method: isEdit ? (policy?.refund_method ?? 'original_payment') : 'original_payment',
    refund_processing_days: isEdit ? (policy?.refund_processing_days ?? 7) : 7,
    
    // Configuración de voucher
    voucher_expiry_days: isEdit ? (policy?.voucher_expiry_days ?? 365) : 365,
    voucher_minimum_amount: isEdit ? (policy?.voucher_minimum_amount ?? 0) : 0,
    
    // Mensajes personalizados
    full_refund_message: isEdit ? (policy?.full_refund_message ?? '') : '',
    partial_refund_message: isEdit ? (policy?.partial_refund_message ?? '') : '',
    no_refund_message: isEdit ? (policy?.no_refund_message ?? '') : '',
    voucher_message: isEdit ? (policy?.voucher_message ?? '') : '',
    
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
    full_refund_time: Yup.number().min(0, t('common.min_value_0')),
    partial_refund_time: Yup.number().min(0, t('common.min_value_0')),
    no_refund_time: Yup.number().min(0, t('common.min_value_0')),
    partial_refund_percentage: Yup.number().min(0).max(100, t('common.max_value_100')),
    refund_processing_days: Yup.number().min(1, t('common.min_value_1')),
    voucher_expiry_days: Yup.number().min(1, t('common.min_value_1')),
    voucher_minimum_amount: Yup.number().min(0, t('common.min_value_0')),
  })

  const handleSubmit = (values) => {
    const data = {
      name: values.name,
      hotel: values.hotel ? Number(values.hotel) : null,
      is_active: values.is_active,
      is_default: values.is_default,
      
      // Configuración de tiempos de devolución
      full_refund_time: parseInt(values.full_refund_time) || 0,
      full_refund_unit: values.full_refund_unit,
      partial_refund_time: parseInt(values.partial_refund_time) || 0,
      partial_refund_unit: values.partial_refund_unit,
      partial_refund_percentage: parseFloat(values.partial_refund_percentage) || 0,
      no_refund_time: parseInt(values.no_refund_time) || 0,
      no_refund_unit: values.no_refund_unit,
      
      // Configuración de métodos de devolución
      refund_method: values.refund_method,
      refund_processing_days: parseInt(values.refund_processing_days) || 7,
      
      // Configuración de voucher
      voucher_expiry_days: parseInt(values.voucher_expiry_days) || 365,
      voucher_minimum_amount: parseFloat(values.voucher_minimum_amount) || 0,
      
      // Mensajes personalizados
      full_refund_message: values.full_refund_message,
      partial_refund_message: values.partial_refund_message,
      no_refund_message: values.no_refund_message,
      voucher_message: values.voucher_message,
      
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

  const refundMethodOptions = [
    { value: 'cash', label: t('payments.refund.policies.refund_methods.cash') },
    { value: 'bank_transfer', label: t('payments.refund.policies.refund_methods.bank_transfer') },
    { value: 'credit_card', label: t('payments.refund.policies.refund_methods.credit_card') },
    { value: 'voucher', label: t('payments.refund.policies.refund_methods.voucher') },
    { value: 'original_payment', label: t('payments.refund.policies.refund_methods.original_payment') }
  ]

  const timeUnitOptions = [
    { value: 'hours', label: t('payments.refund.policies.time_units.hours') },
    { value: 'days', label: t('payments.refund.policies.time_units.days') },
    { value: 'weeks', label: t('payments.refund.policies.time_units.weeks') }
  ]

  const hotelOptions = hotels?.map(h => ({ value: h.id, label: h.name })) || []

  useEffect(() => {
    if (isOpen && !isEdit) {
      setInstanceKey((k) => k + 1)
    }
  }, [isOpen, isEdit])

  const tabs = [
    { id: 'basic', label: t('payments.refund.policies.tabs.basic') },
    { id: 'times', label: t('payments.refund.policies.tabs.times') },
    { id: 'methods', label: t('payments.refund.policies.tabs.methods') },
    { id: 'voucher', label: t('payments.refund.policies.tabs.voucher') },
    { id: 'messages', label: t('payments.refund.policies.tabs.messages') },
    { id: 'advanced', label: t('payments.refund.policies.tabs.advanced') }
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
          title={isEdit ? t('payments.refund.policies.edit_policy_devolution') : t('payments.refund.policies.add_policy_devolution')}
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
                    title={t('payments.refund.policies.policy_name')}
                    name="name"
                    value={values.name}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    error={touched.name && errors.name}
                    placeholder={t('payments.refund.policies.policy_name')}
                  />
                  <SelectAsync
                    resource='hotels' 
                    title={t('sidebar.hotels')}
                    name="hotel"
                    placeholder={t('common.select_hotel')}
                    getOptionLabel={(h) => h?.name}
                    getOptionValue={(h) => h?.id}
                  />
                </div>

                <div className="space-y-3">
                  <Checkbox
                    label={t('payments.refund.policies.is_active')}
                    checked={values.is_active}
                    onChange={(checked) => setFieldValue('is_active', checked)}
                  />
                  <Checkbox
                    label={t('payments.refund.policies.is_default')}
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
                      title={t('payments.refund.policies.full_refund_time')}
                      name="full_refund_time"
                      type="number"
                      value={values.full_refund_time}
                      onChange={handleChange}
                      onBlur={handleBlur}
                      error={touched.full_refund_time && errors.full_refund_time}
                    />
                  </div>
                  <SelectBasic
                    title={t('payments.refund.policies.time_unit')}
                    name="full_refund_unit"
                    options={timeUnitOptions}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <InputText
                      title={t('payments.refund.policies.partial_refund_time')}
                      name="partial_refund_time"
                      type="number"
                      value={values.partial_refund_time}
                      onChange={handleChange}
                      onBlur={handleBlur}
                      error={touched.partial_refund_time && errors.partial_refund_time}
                    />
                  </div>
                  <SelectBasic
                    title={t('payments.refund.policies.time_unit')}
                    name="partial_refund_unit"
                    options={timeUnitOptions}
                  />
                  <div>
                    <InputText
                      title={t('payments.refund.policies.partial_refund_percentage')}
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
                      title={t('payments.refund.policies.no_refund_time')}
                      name="no_refund_time"
                      type="number"
                      value={values.no_refund_time}
                      onChange={handleChange}
                      onBlur={handleBlur}
                      error={touched.no_refund_time && errors.no_refund_time}
                    />
                  </div>
                  <SelectBasic
                    title={t('payments.refund.policies.time_unit')}
                    name="no_refund_unit"
                    options={timeUnitOptions}
                  />
                </div>
              </div>
            )}

            {activeTab === 'methods' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <SelectBasic
                    title={t('payments.refund.policies.refund_method')}
                    name="refund_method"
                    options={refundMethodOptions}
                  />
                  <InputText
                    title={t('payments.refund.policies.processing_days')}
                    name="refund_processing_days"
                    type="number"
                    value={values.refund_processing_days}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    error={touched.refund_processing_days && errors.refund_processing_days}
                  />
                </div>
              </div>
            )}

            {activeTab === 'voucher' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <InputText
                    title={t('payments.refund.policies.voucher_expiry_days')}
                    name="voucher_expiry_days"
                    type="number"
                    value={values.voucher_expiry_days}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    error={touched.voucher_expiry_days && errors.voucher_expiry_days}
                  />
                  <InputText
                    title={t('payments.refund.policies.voucher_minimum_amount')}
                    name="voucher_minimum_amount"
                    type="number"
                    step="0.01"
                    value={values.voucher_minimum_amount}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    error={touched.voucher_minimum_amount && errors.voucher_minimum_amount}
                  />
                </div>
              </div>
            )}

            {activeTab === 'messages' && (
              <div className="space-y-4">
                <InputTextTarea
                  title={t('payments.refund.policies.full_refund_message')}
                  name="full_refund_message"
                  value={values.full_refund_message}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  placeholder={t('payments.refund.policies.full_refund_message')}
                  rows={3}
                />
                <InputTextTarea
                  title={t('payments.refund.policies.partial_refund_message')}
                  name="partial_refund_message"
                  value={values.partial_refund_message}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  placeholder={t('payments.refund.policies.partial_refund_message')}
                  rows={3}
                />
                <InputTextTarea
                  title={t('payments.refund.policies.no_refund_message')}
                  name="no_refund_message"
                  value={values.no_refund_message}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  placeholder={t('payments.refund.policies.no_refund_message')}
                  rows={3}
                />
                <InputTextTarea
                  title={t('payments.refund.policies.voucher_message')}
                  name="voucher_message"
                  value={values.voucher_message}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  placeholder={t('payments.refund.policies.voucher_message')}
                  rows={3}
                />
              </div>
            )}

            {activeTab === 'advanced' && (
              <div className="space-y-4">
                <div className="space-y-3">
                  <Checkbox
                    label={t('payments.refund.policies.apply_to_all_room_types')}
                    checked={values.apply_to_all_room_types}
                    onChange={(checked) => setFieldValue('apply_to_all_room_types', checked)}
                  />
                  <Checkbox
                    label={t('payments.refund.policies.apply_to_all_channels')}
                    checked={values.apply_to_all_channels}
                    onChange={(checked) => setFieldValue('apply_to_all_channels', checked)}
                  />
                  <Checkbox
                    label={t('payments.refund.policies.apply_to_all_seasons')}
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

export default DevolutionPoliciesModal