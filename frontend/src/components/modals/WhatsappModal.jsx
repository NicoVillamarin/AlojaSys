import React from 'react'
import { Formik } from 'formik'
import * as Yup from 'yup'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectBasic from 'src/components/selects/SelectBasic'
import Checkbox from 'src/components/Checkbox'
import { useUpdate } from 'src/hooks/useUpdate'

/**
 * WhatsappModal
 * Modal sencillo para editar SOLO la configuración de WhatsApp de un hotel.
 * Usa PATCH sobre el recurso `hotels`.
 */
const WhatsappModal = ({ isOpen, onClose, hotel, onSuccess }) => {
  const { t } = useTranslation()

  const { mutate: updateHotel, isPending: updating } = useUpdate({
    resource: 'hotels',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
      onClose && onClose()
    },
  })

  if (!hotel) {
    return null
  }

  const initialValues = {
    whatsapp_enabled: hotel?.whatsapp_enabled ?? false,
    whatsapp_phone: hotel?.whatsapp_phone ?? '',
    whatsapp_provider: hotel?.whatsapp_provider ?? 'meta_cloud',
    whatsapp_business_id: hotel?.whatsapp_business_id ?? '',
    whatsapp_phone_number_id: hotel?.whatsapp_phone_number_id ?? '',
    whatsapp_api_token: '',
  }

  const validationSchema = Yup.object().shape({
    whatsapp_phone: Yup.string().when('whatsapp_enabled', {
      is: true,
      then: (schema) =>
        schema
          .required(t('common.required'))
          // Permitimos formato E.164 con o sin espacios, ej: "+1 555 012 3075"
          .matches(/^\+?[0-9\s]+$/, t('common.invalid_format')),
    }),
    whatsapp_provider: Yup.string().when('whatsapp_enabled', {
      is: true,
      then: (schema) => schema.required(t('common.required')),
    }),
  })

  const handleSubmit = (values) => {
    const payload = {
      whatsapp_enabled: !!values.whatsapp_enabled,
      whatsapp_phone: values.whatsapp_phone || '',
      whatsapp_provider: values.whatsapp_provider || '',
      whatsapp_business_id: values.whatsapp_business_id || '',
      whatsapp_phone_number_id: values.whatsapp_phone_number_id || '',
      whatsapp_api_token: values.whatsapp_api_token || '',
    }

    // Si el token viene vacío, NO sobreescribimos el existente
    if (!values.whatsapp_api_token) {
      delete payload.whatsapp_api_token
    }

    updateHotel({ id: hotel.id, body: payload })
  }

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={handleSubmit}
    >
      {({ values, errors, touched, handleChange, handleBlur, handleSubmit, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={t('hotels_modal.whatsapp_settings')}
          onSubmit={handleSubmit}
          submitText={t('common.save')}
          submitDisabled={updating}
          submitLoading={updating}
          size="md"
        >
          <div className="space-y-4">
            <div>
              <p className="text-xs text-aloja-gray-800/60">
                {t('common.hotel')}: <span className="font-medium">{hotel.name}</span>
              </p>
            </div>

            <div className="space-y-3">
              <Checkbox
                label={t('hotels_modal.whatsapp_enabled')}
                checked={!!values.whatsapp_enabled}
                onChange={(checked) => setFieldValue('whatsapp_enabled', checked)}
              />

              {values.whatsapp_enabled && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <InputText
                    title={t('hotels_modal.whatsapp_phone')}
                    name="whatsapp_phone"
                    placeholder="+15550123075"
                    value={values.whatsapp_phone}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    error={touched.whatsapp_phone && errors.whatsapp_phone}
                  />

                  <SelectBasic
                    title={t('hotels_modal.whatsapp_provider')}
                    name="whatsapp_provider"
                    options={[
                      { value: 'meta_cloud', label: 'Meta WhatsApp Cloud API' },
                      { value: 'twilio', label: 'Twilio' },
                      { value: 'other', label: t('common.other') },
                    ]}
                  />

                  <InputText
                    title={t('hotels_modal.whatsapp_business_id')}
                    name="whatsapp_business_id"
                    placeholder="Business ID (Meta)"
                    value={values.whatsapp_business_id}
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />

                  <InputText
                    title={t('hotels_modal.whatsapp_phone_number_id')}
                    name="whatsapp_phone_number_id"
                    placeholder="Phone Number ID"
                    value={values.whatsapp_phone_number_id}
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />

                  <InputText
                    title={t('hotels_modal.whatsapp_api_token')}
                    name="whatsapp_api_token"
                    type="password"
                    placeholder={t('hotels_modal.whatsapp_api_token_placeholder')}
                    value={values.whatsapp_api_token}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    error={touched.whatsapp_api_token && errors.whatsapp_api_token}
                  />
                </div>
              )}
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default WhatsappModal


