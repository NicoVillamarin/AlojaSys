import { Formik } from 'formik'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import SelectBasic from 'src/components/selects/SelectBasic'

const PlansRateModal = ({ isOpen, onClose, isEdit = false, row, onSuccess }) => {
    const { t } = useTranslation()
    const { mutate: createRow, isPending: creating } = useCreate({
        resource: 'rates/rate-plans',
        onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
    })
    const { mutate: updateRow, isPending: updating } = useUpdate({
        resource: 'rates/rate-plans',
        onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
    })

    const initialValues = {
        hotel: row?.hotel ?? '',
        name: row?.name ?? '',
        code: row?.code ?? '',
        is_active: row?.is_active ?? true,
        priority: row?.priority != null ? String(row.priority) : '100',
    }

    const validationSchema = Yup.object().shape({
        hotel: Yup.number().typeError(t('plans_rate_modal.hotel_required')).required(t('plans_rate_modal.hotel_required')),
        name: Yup.string().required(t('plans_rate_modal.name_required')),
        code: Yup.string().required(t('plans_rate_modal.code_required')),
        priority: Yup.number().typeError(t('plans_rate_modal.priority_number')).required(t('plans_rate_modal.priority_required')),
    })

    return (
        <Formik
            enableReinitialize
            initialValues={initialValues}
            validationSchema={validationSchema}
            onSubmit={(values) => {
                const payload = {
                    hotel: values.hotel ? Number(values.hotel) : undefined,
                    name: values.name || undefined,
                    code: values.code || undefined,
                    is_active: Boolean(values.is_active),
                    priority: values.priority !== '' ? Number(values.priority) : undefined,
                }
                if (isEdit && row?.id) updateRow({ id: row.id, body: payload })
                else createRow(payload)
            }}
        >
            {({ handleSubmit, values, setFieldValue }) => (
                <ModalLayout
                    isOpen={isOpen}
                    onClose={onClose}
                    title={isEdit ? t('plans_rate_modal.edit_plan') : t('plans_rate_modal.create_plan')}
                    onSubmit={handleSubmit}
                    submitText={isEdit ? t('plans_rate_modal.save_changes') : t('plans_rate_modal.create')}
                    cancelText={t('plans_rate_modal.cancel')}
                    submitDisabled={creating || updating}
                    submitLoading={creating || updating}
                    size='md'
                >
                    <div className='grid grid-cols-1 md:grid-cols-2 gap-5'>
                        <SelectAsync
                            title={`${t('plans_rate_modal.hotel')} *`}
                            name='hotel'
                            resource='hotels'
                            placeholder={t('plans_rate_modal.hotel_placeholder')}
                            getOptionLabel={(h) => h?.name}
                            getOptionValue={(h) => h?.id}
                        />
                        <InputText title={`${t('plans_rate_modal.name')} *`} name='name' placeholder={t('plans_rate_modal.name_placeholder')} />
                        <InputText title={`${t('plans_rate_modal.code')} *`} name='code' placeholder={t('plans_rate_modal.code_placeholder')} />
                        <InputText title={`${t('plans_rate_modal.priority')} *`} name='priority' placeholder={t('plans_rate_modal.priority_placeholder')} />
                        <div className='md:col-span-2'>
                            <label className='text-xs text-aloja-gray-800/70'>{t('plans_rate_modal.active')}</label>
                            <label htmlFor='is_active' className='flex items-center gap-2 cursor-pointer'>
                                <input
                                    id='is_active'
                                    name='is_active'
                                    type='checkbox'
                                    className='rounded border-gray-300'
                                    checked={!!values.is_active}
                                    onChange={(e) => setFieldValue('is_active', e.target.checked)}
                                />
                                <span className='text-sm text-aloja-gray-800/80'>{t('plans_rate_modal.enabled_for_operation')}</span>
                            </label>
                        </div>
                    </div>
                </ModalLayout>
            )}
        </Formik>
    )
}

export default PlansRateModal