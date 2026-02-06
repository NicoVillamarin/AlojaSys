import { useEffect, useState, useRef } from 'react'
import { Formik } from 'formik'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectBasic from 'src/components/selects/SelectBasic'
import Checkbox from 'src/components/Checkbox'
import HelpTooltip from 'src/components/HelpTooltip'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import { useList } from 'src/hooks/useList'

const PaymentPoliciesModal = ({ isOpen, onClose, isEdit = false, policy, onSuccess }) => {
  const { t } = useTranslation()
  const [methods, setMethods] = useState([])
  const [loadingMethods, setLoadingMethods] = useState(false)
  const formikRef = useRef()

  // Obtener lista de hoteles y métodos de pago
  const { results: hotels } = useList({
    resource: 'hotels',
    params: {},
  })

  const { results: paymentMethods } = useList({
    resource: 'payments/methods',
    params: {},
  })

  const { mutate: createPolicy, isPending: creating } = useCreate({
    resource: 'payments/policies',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  const { mutate: updatePolicy, isPending: updating } = useUpdate({
    resource: 'payments/policies',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const initialValues = {
    name: isEdit ? (policy?.name ?? '') : '',
    hotel: isEdit ? (policy?.hotel ?? '') : '',
    is_default: isEdit ? (policy?.is_default ?? false) : false,
    allow_deposit: isEdit ? (policy?.allow_deposit ?? true) : true,
    deposit_type: isEdit ? (policy?.deposit_type ?? 'none') : 'none',
    deposit_value: isEdit ? (policy?.deposit_value ?? 0) : 0,
    deposit_due: isEdit ? (policy?.deposit_due ?? 'confirmation') : 'confirmation',
    deposit_days_before: isEdit ? (policy?.deposit_days_before ?? 0) : 0,
    balance_due: isEdit ? (policy?.balance_due ?? 'check_in') : 'check_in',
    auto_cancel_enabled: isEdit ? (policy?.auto_cancel_enabled ?? true) : true,
    auto_cancel_days: isEdit ? (policy?.auto_cancel_days ?? 7) : 7,
  }


  const validationSchema = Yup.object({
    name: Yup.string().required(t('common.required')),
    hotel: Yup.mixed().test('hotel-required', t('common.required'), function(value) {
      return value !== '' && value != null && value !== undefined
    }),
    deposit_type: Yup.string().required(t('common.required')),
    deposit_value: Yup.number().min(0, t('common.min_value_0')),
    deposit_due: Yup.string().required(t('common.required')),
    balance_due: Yup.string().required(t('common.required')),
    auto_cancel_days: Yup.number().min(1, t('common.min_value_1')).max(365, t('common.max_value_365')),
  })

  const handleSubmit = (values) => {
    const data = {
      name: values.name,
      hotel: values.hotel,
      is_default: values.is_default,
      allow_deposit: values.allow_deposit,
      deposit_type: values.deposit_type,
      deposit_value: parseFloat(values.deposit_value) || 0,
      deposit_due: values.deposit_due,
      deposit_days_before: parseInt(values.deposit_days_before) || 0,
      balance_due: values.balance_due,
      auto_cancel_enabled: values.auto_cancel_enabled,
      auto_cancel_days: parseInt(values.auto_cancel_days) || 7,
    }

    // Forzar que hotel siempre esté presente en actualizaciones
    if (isEdit && !data.hotel) {
      data.hotel = policy.hotel
    }

    if (isEdit) {
      // useUpdate espera { id, body }
      updatePolicy({ id: policy.id, body: data })
    } else {
      createPolicy(data)
    }
  }

  const depositTypeOptions = [
    { value: 'none', label: t('payments.policies.deposit_types.none') },
    { value: 'percentage', label: t('payments.policies.deposit_types.percentage') },
    { value: 'fixed', label: t('payments.policies.deposit_types.fixed') }
  ]

  const depositDueOptions = [
    { value: 'confirmation', label: t('payments.policies.deposit_due.confirmation') },
    { value: 'days_before', label: t('payments.policies.deposit_due.days_before') },
    { value: 'check_in', label: t('payments.policies.deposit_due.check_in') }
  ]

  const balanceDueOptions = [
    { value: 'check_in', label: t('payments.policies.balance_due.check_in') },
    { value: 'check_out', label: t('payments.policies.balance_due.check_out') }
  ]

  const hotelOptions = hotels?.map(h => ({ value: h.id, label: h.name })) || []
  const methodOptions = paymentMethods?.map(m => ({ value: m.id, label: m.name })) || []

  return (
    <Formik
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={handleSubmit}
      enableReinitialize
    >
      {({ values, errors, touched, handleChange, handleBlur, handleSubmit, setFieldValue }) => {

        return (
        <ModalLayout 
          isOpen={isOpen} 
          onClose={onClose} 
          title={isEdit ? t('payments.policies.edit_policy_payment') : t('payments.policies.add_policy_payment')}
          size="lg"
          onSubmit={handleSubmit}
          submitText={isEdit ? t('common.save') : t('common.create')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InputText
                title={t('payments.policies.policy_name')}
                name="name"
                value={values.name}
                onChange={handleChange}
                onBlur={handleBlur}
                error={touched.name && errors.name}
                placeholder={t('payments.policies.policy_name')}
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
                      label={t('payments.policies.is_default')}
                      checked={values.is_default}
                      onChange={(checked) => setFieldValue('is_default', checked)}
                    />
                    <Checkbox
                      label={t('payments.policies.allow_deposit')}
                      checked={values.allow_deposit}
                      onChange={(checked) => setFieldValue('allow_deposit', checked)}
                    />
                  </div>

            <div className="border-t pt-4">
              <div className="flex items-center gap-2 mb-3">
                <h5 className="text-sm font-medium text-gray-700">
                  {t('payments.policies.deposit_section')}
                </h5>
                <HelpTooltip text={t('payments.policies.deposit_section_help')} />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <SelectBasic
                  title={t('payments.policies.deposit_type')}
                  name="deposit_type"
                  options={depositTypeOptions}
                />
                <InputText
                  title={t('payments.policies.deposit_value')}
                  name="deposit_value"
                  type="number"
                  step="0.01"
                  value={values.deposit_value}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  error={touched.deposit_value && errors.deposit_value}
                  placeholder={values.deposit_type === 'percentage' ? '30' : '500.00'}
                />
                <SelectBasic
                  title={t('payments.policies.deposit_due_title')}
                  name="deposit_due"
                  options={depositDueOptions}
                />
              </div>
              {values.deposit_due === 'days_before' && (
                <div className="mt-4">
                  <InputText
                    title={t('payments.policies.deposit_days_before')}
                    name="deposit_days_before"
                    type="number"
                    value={values.deposit_days_before}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    placeholder="7"
                  />
                </div>
              )}
            </div>

            {values.deposit_type !== 'none' && (
              <div className="border-t pt-4">
                <div className="flex items-center gap-2 mb-3">
                  <h5 className="text-sm font-medium text-gray-700">
                    {t('payments.policies.balance_section')}
                  </h5>
                  <HelpTooltip text={t('payments.policies.balance_section_help')} />
                </div>
                <SelectBasic
                  title={t('payments.policies.balance_due_title')}
                  name="balance_due"
                  options={balanceDueOptions}
                />
              </div>
            )}

            <div className="border-t pt-4">
              <div className="flex items-center gap-2 mb-3">
                <h5 className="text-sm font-medium text-gray-700">
                  {t('payments.policies.auto_cancel_section')}
                </h5>
                <HelpTooltip text={t('payments.policies.auto_cancel_section_help')} />
              </div>
              <div className="space-y-4">
                <Checkbox
                  name="auto_cancel_enabled"
                  label={t('payments.policies.auto_cancel_enabled')}
                  description={t('payments.policies.auto_cancel_enabled_desc')}
                  checked={values.auto_cancel_enabled}
                  onChange={(checked) => setFieldValue('auto_cancel_enabled', checked)}
                />
                <InputText
                  title={t('payments.policies.auto_cancel_days')}
                  name="auto_cancel_days"
                  type="number"
                  min="1"
                  max="365"
                  description={t('payments.policies.auto_cancel_days_desc')}
                />
              </div>
            </div>
          </div>
        </ModalLayout>
        )
      }}
    </Formik>
  )
}

export default PaymentPoliciesModal