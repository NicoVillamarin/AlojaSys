import { Formik } from 'formik'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import { useUserHotels } from 'src/hooks/useUserHotels'

const VouchersManagementModal = ({ isOpen, onClose, isEdit = false, voucher, onSuccess }) => {
  const { t } = useTranslation()
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()
  
  const { mutate: createVoucher, isPending: creating } = useCreate({
    resource: 'payments/refund-vouchers',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  
  const { mutate: updateVoucher, isPending: updating } = useUpdate({
    resource: 'payments/refund-vouchers',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const initialValues = {
    amount: voucher?.amount ?? '',
    expiry_date: voucher?.expiry_date ? voucher.expiry_date.split('T')[0] : '',
    hotel: voucher?.hotel ?? (hasSingleHotel ? singleHotelId : ''),
    notes: voucher?.notes ?? '',
  }

  const validationSchema = Yup.object().shape({
    amount: Yup.number()
      .required(t('vouchers_modal.amount_required'))
      .min(0.01, t('vouchers_modal.amount_min')),
    expiry_date: Yup.date()
      .required(t('vouchers_modal.expiry_date_required'))
      .min(new Date(), t('vouchers_modal.expiry_date_future')),
    hotel: Yup.number()
      .required(t('vouchers_modal.hotel_required')),
    notes: Yup.string().nullable(),
  })

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          amount: Number(values.amount),
          expiry_date: values.expiry_date,
          hotel: Number(values.hotel),
          notes: values.notes || undefined,
        }
        if (isEdit && voucher?.id) updateVoucher({ id: voucher.id, body: payload })
        else createVoucher(payload)
      }}
    >
      {({ handleSubmit }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('vouchers_modal.edit_voucher') : t('vouchers_modal.create_voucher')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('vouchers_modal.save_changes') : t('vouchers_modal.create')}
          cancelText={t('vouchers_modal.cancel')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='md'
        >
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5'>
            <InputText 
              title={`${t('vouchers_modal.amount')} *`} 
              name='amount' 
              type="number"
              step="0.01"
              placeholder={t('vouchers_modal.amount_placeholder')} 
            />
            <InputText 
              title={`${t('vouchers_modal.expiry_date')} *`} 
              name='expiry_date' 
              type="date"
              placeholder={t('vouchers_modal.expiry_date_placeholder')} 
            />
            <div className="lg:col-span-2">
              <SelectAsync
                title={`${t('vouchers_modal.hotel')} *`}
                name='hotel'
                resource='hotels'
                placeholder={t('vouchers_modal.hotel_placeholder')}
                getOptionLabel={(h) => h?.name}
                getOptionValue={(h) => h?.id}
                extraParams={!isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {}}
              />
            </div>
            <div className="lg:col-span-2">
              <InputText 
                title={t('vouchers_modal.notes')} 
                name='notes' 
                type="textarea"
                rows={3}
                placeholder={t('vouchers_modal.notes_placeholder')} 
              />
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default VouchersManagementModal
