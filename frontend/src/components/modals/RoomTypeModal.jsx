import { Formik } from 'formik'
import * as Yup from 'yup'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import Checkbox from 'src/components/Checkbox'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'

const RoomTypeModal = ({ isOpen, onClose, isEdit = false, row, onSuccess }) => {
  const { t } = useTranslation()

  const { mutate: createRow, isPending: creating } = useCreate({
    resource: 'room-types',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
      onClose && onClose()
    },
  })

  const { mutate: updateRow, isPending: updating } = useUpdate({
    resource: 'room-types',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
      onClose && onClose()
    },
  })

  const initialValues = {
    code: row?.code ?? '',
    name: row?.name ?? '',
    description: row?.description ?? '',
    sort_order: row?.sort_order != null ? String(row.sort_order) : '0',
    is_active: row?.is_active ?? true,
  }

  const validationSchema = Yup.object().shape({
    code: Yup.string()
      .transform((v) => (v ? String(v).trim().toLowerCase() : ''))
      .matches(/^[a-z0-9_-]+$/, t('room_types.validation.code_format', 'Usá solo letras minúsculas, números, guión (-) o guión bajo (_).'))
      .max(50, t('room_types.validation.code_max', 'Máximo 50 caracteres.'))
      .required(t('room_types.validation.code_required', 'El código es requerido.')),
    name: Yup.string()
      .transform((v) => (v ? String(v).trim() : ''))
      .max(120, t('room_types.validation.name_max', 'Máximo 120 caracteres.'))
      .required(t('room_types.validation.name_required', 'El nombre es requerido.')),
    description: Yup.string()
      .transform((v) => (v ? String(v).trim() : ''))
      .max(2000, t('room_types.validation.description_max', 'Máximo 2000 caracteres.'))
      .nullable(),
    sort_order: Yup.number()
      .transform((v, o) => (o === '' || o == null ? 0 : v))
      .typeError(t('room_types.validation.sort_order_number', 'El orden debe ser un número.'))
      .min(0, t('room_types.validation.sort_order_min', 'El orden debe ser >= 0.'))
      .required(),
  })

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          code: (values.code || '').trim().toLowerCase(),
          name: (values.name || '').trim(),
          description: (values.description || '').trim() || null,
          sort_order: values.sort_order === '' ? 0 : Number(values.sort_order),
          is_active: !!values.is_active,
        }

        if (isEdit && row?.id) updateRow({ id: row.id, body: payload })
        else createRow(payload)
      }}
    >
      {({ handleSubmit, values, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={
            isEdit
              ? t('room_types.modal.edit_title', 'Editar tipo de habitación')
              : t('room_types.modal.create_title', 'Crear tipo de habitación')
          }
          onSubmit={handleSubmit}
          submitText={isEdit ? t('common.save', 'Guardar') : t('common.create', 'Crear')}
          cancelText={t('common.cancel', 'Cancelar')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size="md"
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5">
            <InputText title={`${t('room_types.fields.code', 'Código')} *`} name="code" placeholder="single" />
            <InputText title={`${t('room_types.fields.name', 'Nombre')} *`} name="name" placeholder="Doble" />
            <div className="lg:col-span-2">
              <InputText
                title={t('room_types.fields.description', 'Descripción')}
                name="description"
                placeholder={t('room_types.fields.description_placeholder', 'Opcional…')}
                multiline
                rows={3}
              />
            </div>
            <InputText title={t('room_types.fields.sort_order', 'Orden')} name="sort_order" type="number" placeholder="0" />
            <div className="flex items-end">
              <Checkbox
                label={t('room_types.fields.is_active', 'Activo')}
                checked={!!values.is_active}
                onChange={(v) => setFieldValue('is_active', v)}
              />
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default RoomTypeModal