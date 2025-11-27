import { useState } from 'react'
import { Formik } from 'formik'
import { useTranslation } from 'react-i18next'
import * as Yup from 'yup'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectBasic from 'src/components/selects/SelectBasic'
import Button from 'src/components/Button'
import { useCreate } from 'src/hooks/useCreate'
import { paymentPolicyService } from 'src/services/paymentPolicyService'

const DepositPaymentModal = ({ 
  isOpen, 
  onClose, 
  onSuccess, 
  reservation, 
  depositInfo, 
  paymentPolicy 
}) => {
  const { t } = useTranslation()
  const [isProcessing, setIsProcessing] = useState(false)

  const { mutate: createPayment, isPending: creating } = useCreate({
    resource: 'payments/process-deposit',
    onSuccess: (data) => { 
      onSuccess && onSuccess(data)
      onClose && onClose() 
    },
  })

  const initialValues = {
    amount: depositInfo?.amount || 0,
    method: '',
    notes: ''
  }

  // No permitir cambiar el monto del depósito
  const isAmountFixed = true

  const validationSchema = Yup.object({
    amount: Yup.number()
      .min(0.01, t('common.min_value_0_01'))
      .required(t('common.required')),
    method: Yup.string().required(t('common.required')),
  })

  const handleSubmit = (values) => {
    if (!reservation || !depositInfo) return

    // Validar que el monto sea el correcto
    const expectedAmount = depositInfo.amount
    const providedAmount = parseFloat(values.amount)
    
    if (Math.abs(providedAmount - expectedAmount) > 0.01) {
      alert(`El monto debe ser exactamente ${formatCurrency(expectedAmount)}`)
      return
    }

    setIsProcessing(true)
    
    const paymentData = {
      reservation: reservation.id,
      amount: providedAmount,
      method: values.method,
      notes: values.notes,
      type: 'deposit'
    }

    // Procesar el pago de depósito
    createPayment(paymentData)
  }

  const paymentMethods = paymentPolicyService.getEnabledMethods(paymentPolicy) || []
  const methodOptions = paymentMethods.map(method => ({
    value: method.code,
    label: method.name
  }))

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 2,
    }).format(amount)
  }

  return (
    <Formik
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={handleSubmit}
      enableReinitialize
    >
      {({ values, errors, touched, handleChange, handleBlur, handleSubmit, setFieldValue }) => (
        <ModalLayout 
          isOpen={isOpen} 
          onClose={onClose} 
          title={t('deposit_payment.title')}
          size="md"
          onSubmit={handleSubmit}
          submitText={t('deposit_payment.process_payment')}
          submitDisabled={creating || isProcessing}
          submitLoading={creating || isProcessing}
        >
          <div className="space-y-6">
            {/* Información del depósito */}
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <h4 className="font-semibold text-orange-800 mb-2">
                {t('deposit_payment.deposit_info')}
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-orange-700">{t('deposit_payment.required_amount')}</span>
                  <span className="font-semibold text-orange-800">
                    {formatCurrency(depositInfo?.amount || 0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-orange-700">{t('deposit_payment.reservation_total')}</span>
                  <span className="font-semibold text-orange-800">
                    {formatCurrency(reservation?.total_price || 0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-orange-700">{t('deposit_payment.remaining_after')}</span>
                  <span className="font-semibold text-orange-800">
                    {formatCurrency((reservation?.total_price || 0) - (depositInfo?.amount || 0))}
                  </span>
                </div>
              </div>
            </div>

            {/* Formulario de pago */}
            <div className="space-y-4">
              <InputText
                title={t('deposit_payment.amount')}
                name="amount"
                type="number"
                step="0.01"
                value={values.amount}
                onChange={handleChange}
                onBlur={handleBlur}
                error={touched.amount && errors.amount}
                placeholder="0.00"
                disabled={isAmountFixed}
                className={isAmountFixed ? "bg-gray-100 cursor-not-allowed" : ""}
              />

              <SelectBasic
                title={t('deposit_payment.payment_method')}
                name="method"
                options={methodOptions}
                placeholder={t('deposit_payment.select_method')}
                value={values.method}
                onChange={(value) => setFieldValue('method', value)}
                error={touched.method && errors.method}
              />

              <InputText
                title={t('deposit_payment.notes')}
                name="notes"
                value={values.notes}
                onChange={handleChange}
                onBlur={handleBlur}
                placeholder={t('deposit_payment.notes_placeholder')}
              />
            </div>

            {/* Información adicional */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start space-x-2">
                <span className="text-blue-600 text-lg">ℹ️</span>
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">{t('deposit_payment.important_note')}</p>
                  <p>{t('deposit_payment.payment_note')}</p>
                </div>
              </div>
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default DepositPaymentModal
