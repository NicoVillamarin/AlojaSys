import { Formik } from 'formik'
import * as Yup from 'yup'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'

const CurrencyModal = ({ isOpen, onClose, isEdit = false, row, onSuccess }) => {
  const { t } = useTranslation()

  const { mutate: createRow, isPending: creating } = useCreate({
    resource: 'currencies',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
      onClose && onClose()
    },
  })

  const { mutate: updateRow, isPending: updating } = useUpdate({
    resource: 'currencies',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
      onClose && onClose()
    },
  })

  const initialValues = {
    code: row?.code ?? '',
    name: row?.name ?? '',
    symbol: row?.symbol ?? '',
    is_active: row?.is_active ?? true,
  }

  const validationSchema = Yup.object().shape({
    code: Yup.string()
      .transform((v) => (v ? String(v).trim().toUpperCase() : ''))
      .min(1, 'Código requerido')
      .max(10, 'Máximo 10 caracteres')
      .required('Código requerido'),
    name: Yup.string().max(80, 'Máximo 80 caracteres').nullable(),
    symbol: Yup.string().max(10, 'Máximo 10 caracteres').nullable(),
  })

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          code: (values.code || '').trim().toUpperCase(),
          name: (values.name || '').trim() || '',
          symbol: (values.symbol || '').trim() || '',
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
          title={isEdit ? 'Editar moneda' : 'Crear moneda'}
          onSubmit={handleSubmit}
          submitText={isEdit ? 'Guardar' : 'Crear'}
          cancelText={t('common.cancel', 'Cancelar')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size="sm"
        >
          <div className="grid grid-cols-1 gap-4">
            <InputText title="Código *" name="code" placeholder="ARS" />
            <InputText title="Nombre" name="name" placeholder="Peso argentino" />
            <InputText title="Símbolo" name="symbol" placeholder="$" />

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={!!values.is_active}
                onChange={(e) => setFieldValue('is_active', e.target.checked)}
              />
              Activa
            </label>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default CurrencyModal