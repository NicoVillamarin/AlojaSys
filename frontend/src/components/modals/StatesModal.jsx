import { Formik } from 'formik'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'

const StatesModal = ({ isOpen, onClose, isEdit = false, stateItem, onSuccess }) => {
  const { t } = useTranslation()
  const { mutate: createState, isPending: creating } = useCreate({
    resource: 'states',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })
  const { mutate: updateState, isPending: updating } = useUpdate({
    resource: 'states',
    onSuccess: (data) => { onSuccess && onSuccess(data); onClose && onClose() },
  })

  const initialValues = {
    country: stateItem?.country ?? '',
    name: stateItem?.name ?? '',
    code: stateItem?.code ?? '',
  }

  const validationSchema = Yup.object().shape({
    country: Yup.string().required(t('states_modal.country_required')),
    name: Yup.string().required(t('states_modal.name_required')),
  })

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          country: values.country ? Number(values.country) : undefined,
          name: values.name || undefined,
          code: values.code || undefined,
        }
        if (isEdit && stateItem?.id) updateState({ id: stateItem.id, body: payload })
        else createState(payload)
      }}
    >
      {({ handleSubmit }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('states_modal.edit_state') : t('states_modal.create_state')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('states_modal.save_changes') : t('states_modal.create')}
          cancelText={t('states_modal.cancel')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='md'
        >
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5'>
            <SelectAsync
              title={`${t('states_modal.country')} *`}
              name='country'
              resource='countries'
              placeholder={t('states_modal.country_placeholder')}
              getOptionLabel={(c) => c?.name}
              getOptionValue={(c) => c?.id}
            />
            <InputText title={`${t('states_modal.name')} *`} name='name' placeholder={t('states_modal.name_placeholder')} />
            <InputText title={t('states_modal.code')} name='code' placeholder={t('states_modal.code_placeholder')} />
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default StatesModal