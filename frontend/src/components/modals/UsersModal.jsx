import { Formik } from 'formik'
import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQueryClient } from '@tanstack/react-query'
import ModalLayout from 'src/layouts/ModalLayout'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import InputText from 'src/components/inputs/InputText'
import SelectAsync from 'src/components/selects/SelectAsync'
import * as Yup from 'yup'
import FileImage from '../inputs/FileImage'
import { useMe } from 'src/hooks/useMe'

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
  const queryClient = useQueryClient()
  const { data: me } = useMe()
  
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
      // Si estamos editando el usuario actual, invalidar la query "me"
      if (user?.id && me?.user_id && user.id === me.user_id) {
        queryClient.invalidateQueries({ queryKey: ['me'] })
      }
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
    enterprise: user?.enterprise ?? null,
    hotels: user?.hotels ?? [],
    groups_ids: user?.groups?.map(g => g.id) ?? [], // IDs de los grupos/roles
    is_superuser: user?.is_superuser ?? false, // Campo para superuser
    avatar_image: null, // Archivo seleccionado
    existing_avatar_url: user?.avatar_image_url ?? null, // URL del avatar existente
    is_housekeeping_staff: user?.is_housekeeping_staff ?? false,
  }

  // Función para convertir archivo a base64
  const convertFileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.readAsDataURL(file)
      reader.onload = () => resolve(reader.result)
      reader.onerror = error => reject(error)
    })
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
    groups_ids: Yup.array().of(Yup.number()), // Opcional, no requerido
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
      onSubmit={async (values) => {
        const payload = {
          username: values.username || undefined,
          email: values.email || undefined,
          first_name: values.first_name || undefined,
          last_name: values.last_name || undefined,
          phone: values.phone || undefined,
          position: values.position || undefined,
          enterprise: values.enterprise?.id || undefined,
          hotels: values.hotels || [],
          groups_ids: values.groups_ids && values.groups_ids.length > 0 ? values.groups_ids : [], // Enviar array vacío si no hay grupos
          is_superuser: values.is_superuser || false, // Enviar si es superuser
          is_housekeeping_staff: values.is_housekeeping_staff || false,
        }
        
        // Solo incluir password si se proporcionó
        if (values.password) {
          payload.password = values.password
        }

        // Agregar avatar como base64 si se seleccionó uno nuevo
        if (values.avatar_image) {
          console.log('📎 Convirtiendo avatar a base64:', {
            name: values.avatar_image.name,
            size: values.avatar_image.size,
            type: values.avatar_image.type
          })
          
          // Convertir archivo a base64
          const avatarBase64 = await convertFileToBase64(values.avatar_image)
          payload.avatar_image_base64 = avatarBase64
          payload.avatar_image_filename = values.avatar_image.name
          
          console.log('✅ Avatar convertido a base64, tamaño:', avatarBase64.length, 'caracteres')
        } else {
          console.log('⚠️ No se seleccionó avatar')
        }
        
        console.log('📋 Payload final:', payload)
        
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
            <SelectAsync
              title={`${t('users_modal.enterprise')} *`}
              name='enterprise'
              resource='enterprises'
              placeholder={t('users_modal.enterprise_placeholder')}
              getOptionLabel={(e) => e?.name}
              getOptionValue={(e) => e?.id}
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
            <div className='lg:col-span-2'>
              <SelectAsync
                title={t('users_modal.assigned_roles')}
                name='groups_ids'
                resource='groups'
                placeholder={t('users_modal.assigned_roles_placeholder')}
                getOptionLabel={(g) => g?.name}
                getOptionValue={(g) => g?.id}
                isMulti={true}
              />
              {touched.groups_ids && errors.groups_ids && (
                <p className='mt-1 text-xs text-red-600'>{errors.groups_ids}</p>
              )}
            </div>
            <div className='lg:col-span-2 space-y-3'>
              <label className='flex items-center gap-2 p-3 rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100 cursor-pointer transition-colors'>
                <input
                  type='checkbox'
                  name='is_superuser'
                  checked={values.is_superuser}
                  onChange={handleChange}
                  className='w-4 h-4 text-aloja-navy border-gray-300 rounded focus:ring-aloja-navy cursor-pointer'
                />
                <div className='flex-1'>
                  <span className='text-sm font-medium text-aloja-gray-800'>
                    {t('users_modal.is_superuser')}
                  </span>
                  <p className='text-xs text-aloja-gray-600 mt-0.5'>
                    {t('users_modal.is_superuser_desc')}
                  </p>
                </div>
              </label>
              <label className='flex items-center gap-2 p-3 rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100 cursor-pointer transition-colors'>
                <input
                  type='checkbox'
                  name='is_housekeeping_staff'
                  checked={values.is_housekeeping_staff}
                  onChange={handleChange}
                  className='w-4 h-4 text-aloja-navy border-gray-300 rounded focus:ring-aloja-navy cursor-pointer'
                />
                <div className='flex-1'>
                  <span className='text-sm font-medium text-aloja-gray-800'>
                    {t('users_modal.is_housekeeping_staff')}
                  </span>
                  <p className='text-xs text-aloja-gray-600 mt-0.5'>
                    {t('users_modal.is_housekeeping_staff_desc')}
                  </p>
                </div>
              </label>
            </div>
            <div className='lg:col-span-2'>
              <FileImage
                name='avatar_image'
                label={t('users_modal.avatar_image')}
                placeholder={t('users_modal.avatar_image_placeholder')}
                existingImageUrl={isEdit ? values.existing_avatar_url : null}
                compress={true}
                maxWidth={800}
                maxHeight={800}
                quality={0.9}
                maxSize={2 * 1024 * 1024} // 2MB
                className='mb-4'
              />
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
