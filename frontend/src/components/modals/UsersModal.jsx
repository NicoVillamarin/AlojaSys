import { Formik } from 'formik'
import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import * as Yup from 'yup'

/**
 * UsersModal: crear/editar usuario con asignación de hoteles
 * Props:
 * - isOpen: boolean
 * - onClose: () => void
 * - isEdit?: boolean
 * - user?: objeto usuario existente (para editar)
 * - onSuccess?: (data) => void (se llama al crear/editar OK)
 */
const UsersModal = ({ isOpen, onClose, isEdit = false, user, onSuccess }) => {
  const { t } = useTranslation()
  const { mutate: createUser, isPending: creating } = useCreate({
    resource: 'users',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
      onClose && onClose()
    },
  })

  const { mutate: updateUser, isPending: updating } = useUpdate({
    resource: 'users',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
      onClose && onClose()
    },
  })

  const initialValues = {
    username: user?.username ?? '',
    email: user?.email ?? '',
    first_name: user?.first_name ?? '',
    last_name: user?.last_name ?? '',
    password: '',
    phone: user?.phone ?? '',
    position: user?.position ?? '',
    hotels: user?.hotels ?? [],
  }

  const validationSchema = Yup.object().shape({
    username: Yup.string()
      .required(t('users_modal.username_required'))
      .min(3, t('users_modal.username_min'))
      .matches(/^[\w.@+-]+$/, t('users_modal.username_matches')),
    email: Yup.string()
      .email(t('users_modal.email_valid'))
      .required(t('users_modal.email_required')),
    first_name: Yup.string()
      .required(t('users_modal.first_name_required')),
    last_name: Yup.string()
      .required(t('users_modal.last_name_required')),
    password: isEdit 
      ? Yup.string().min(8, t('users_modal.password_min'))
      : Yup.string()
          .required(t('users_modal.password_required'))
          .min(8, t('users_modal.password_min')),
    phone: Yup.string(),
    position: Yup.string(),
    hotels: Yup.array().min(1, t('users_modal.assigned_hotels_required')),
  })

  const [instanceKey, setInstanceKey] = useState(0)
  useEffect(() => {
    if (isOpen && !isEdit) {
      setInstanceKey((k) => k + 1)
    }
  }, [isOpen, isEdit])

  return (
    <Formik
      key={isEdit ? `edit-${user?.id ?? 'new'}` : `create-${instanceKey}`}
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          username: values.username || undefined,
          email: values.email || undefined,
          first_name: values.first_name || undefined,
          last_name: values.last_name || undefined,
          phone: values.phone || undefined,
          position: values.position || undefined,
          hotels: values.hotels || [],
        }
        
        // Solo incluir password si se proporcionó
        if (values.password) {
          payload.password = values.password
        }

        if (isEdit && user?.id) {
          updateUser({ id: user.id, body: payload })
        } else {
          createUser(payload)
        }
      }}
    >
      {({ values, handleChange, handleSubmit, errors, touched }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('users_modal.edit_user') : t('users_modal.create_user')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('users_modal.save_changes') : t('users_modal.create_user_btn')}
          cancelText={t('users_modal.cancel')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='lg'
        >
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5'>
            <InputText 
              title={`${t('users_modal.username')} *`} 
              name='username' 
              placeholder={t('users_modal.username_placeholder')}
              disabled={isEdit} 
            />
            <InputText 
              title={`${t('users_modal.email')} *`} 
              name='email' 
              placeholder={t('users_modal.email_placeholder')} 
              type='email'
            />
            <InputText 
              title={`${t('users_modal.first_name')} *`} 
              name='first_name' 
              placeholder={t('users_modal.first_name_placeholder')} 
            />
            <InputText 
              title={`${t('users_modal.last_name')} *`} 
              name='last_name' 
              placeholder={t('users_modal.last_name_placeholder')} 
            />
            <InputText 
              title={isEdit ? t('users_modal.password_edit') : `${t('users_modal.password')} *`} 
              name='password' 
              placeholder={t('users_modal.password_placeholder')} 
              type='password'
            />
            <InputText 
              title={t('users_modal.phone')} 
              name='phone' 
              placeholder={t('users_modal.phone_placeholder')} 
            />
            <InputText 
              title={t('users_modal.position')} 
              name='position' 
              placeholder={t('users_modal.position_placeholder')} 
            />
            <div className='lg:col-span-2'>
              <SelectAsync
                title={`${t('users_modal.assigned_hotels')} *`}
                name='hotels'
                resource='hotels'
                placeholder={t('users_modal.assigned_hotels_placeholder')}
                getOptionLabel={(h) => h?.name}
                getOptionValue={(h) => h?.id}
                isMulti={true}
              />
              {touched.hotels && errors.hotels && (
                <p className='mt-1 text-xs text-red-600'>{errors.hotels}</p>
              )}
            </div>
          </div>
          
          {isEdit && (
            <div className='mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200'>
              <p className='text-xs text-blue-800'>
                <strong>{t('users_modal.password_note')}</strong> {t('users_modal.password_note_text')}
              </p>
            </div>
          )}
        </ModalLayout>
      )}
    </Formik>
  )
}

export default UsersModal
