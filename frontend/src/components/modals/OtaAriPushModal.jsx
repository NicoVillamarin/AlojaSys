import { Formik } from 'formik'
import * as Yup from 'yup'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import SelectStandalone from 'src/components/selects/SelectStandalone'
import InputText from 'src/components/inputs/InputText'
import { useList } from 'src/hooks/useList'
import { useDispatchAction } from 'src/hooks/useDispatchAction'

export default function OtaAriPushModal({ isOpen, onClose, defaultHotelId, onQueued }) {
  const { t } = useTranslation()
  const { results: hotels } = useList({ resource: 'hotels' })
  const { mutate: dispatch } = useDispatchAction({ resource: 'otas', onSuccess: onQueued })

  const initialValues = {
    hotel: defaultHotelId ?? '',
    provider: 'booking',
    date_from: '',
    date_to: '',
  }

  const validationSchema = Yup.object().shape({
    hotel: Yup.number().required(t('common.required')),
    provider: Yup.string().required(t('common.required')),
    date_from: Yup.string().required(t('common.required')),
    date_to: Yup.string().required(t('common.required')),
  })

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        dispatch({ action: 'ari/push', body: values, method: 'POST' })
        onClose && onClose()
      }}
    >
      {({ handleSubmit, values, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={t('ota.ari.push_title')}
          onSubmit={handleSubmit}
          submitText={t('ota.ari.push_now')}
          cancelText={t('common.cancel')}
          size="md"
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5">
            <SelectStandalone
              title={t('ota.ari.hotel')}
              options={hotels}
              placeholder={t('ota.filters.hotel_placeholder')}
              value={hotels.find(h => String(h.id) === String(values.hotel)) || null}
              onChange={(opt) => setFieldValue('hotel', opt ? opt.id : '')}
              getOptionLabel={(h) => h?.name}
              getOptionValue={(h) => h?.id}
            />

            <div>
              <label className="block text-sm font-medium text-aloja-navy mb-1">{t('ota.ari.provider')}</label>
              <select
                className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-full"
                value={values.provider}
                onChange={(e) => setFieldValue('provider', e.target.value)}
              >
                <option value="booking">Booking</option>
                <option value="airbnb">Airbnb</option>
              </select>
            </div>

            <InputText title={t('ota.ari.date_from')} name="date_from" placeholder="YYYY-MM-DD" />
            <InputText title={t('ota.ari.date_to')} name="date_to" placeholder="YYYY-MM-DD" />
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}


