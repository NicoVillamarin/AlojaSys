import { Formik } from 'formik'
import React, { useEffect, useState } from 'react'
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
      .required('Usuario es requerido')
      .min(3, 'Usuario debe tener al menos 3 caracteres')
      .matches(/^[\w.@+-]+$/, 'Usuario solo puede contener letras, números y @/./+/-/_'),
    email: Yup.string()
      .email('Email debe ser válido')
      .required('Email es requerido'),
    first_name: Yup.string()
      .required('Nombre es requerido'),
    last_name: Yup.string()
      .required('Apellido es requerido'),
    password: isEdit 
      ? Yup.string().min(8, 'Contraseña debe tener al menos 8 caracteres')
      : Yup.string()
          .required('Contraseña es requerida')
          .min(8, 'Contraseña debe tener al menos 8 caracteres'),
    phone: Yup.string(),
    position: Yup.string(),
    hotels: Yup.array().min(1, 'Debe asignar al menos un hotel'),
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
          title={isEdit ? 'Editar usuario' : 'Crear usuario'}
          onSubmit={handleSubmit}
          submitText={isEdit ? 'Guardar cambios' : 'Crear usuario'}
          cancelText='Cancelar'
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='lg'
        >
          <div className='grid grid-cols-1 md:grid-cols-2 gap-5'>
            <InputText 
              title='Usuario *' 
              name='username' 
              placeholder='usuario123'
              disabled={isEdit} 
            />
            <InputText 
              title='Email *' 
              name='email' 
              placeholder='usuario@ejemplo.com' 
              type='email'
            />
            <InputText 
              title='Nombre *' 
              name='first_name' 
              placeholder='Juan' 
            />
            <InputText 
              title='Apellido *' 
              name='last_name' 
              placeholder='Pérez' 
            />
            <InputText 
              title={isEdit ? 'Contraseña (dejar en blanco para mantener)' : 'Contraseña *'} 
              name='password' 
              placeholder='••••••••' 
              type='password'
            />
            <InputText 
              title='Teléfono' 
              name='phone' 
              placeholder='+54 11 1234-5678' 
            />
            <InputText 
              title='Cargo' 
              name='position' 
              placeholder='Recepcionista' 
            />
            <div className='md:col-span-2'>
              <SelectAsync
                title='Hoteles asignados *'
                name='hotels'
                resource='hotels'
                placeholder='Seleccionar hoteles...'
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
                <strong>Nota:</strong> Si no deseas cambiar la contraseña, deja el campo en blanco.
              </p>
            </div>
          )}
        </ModalLayout>
      )}
    </Formik>
  )
}

export default UsersModal
