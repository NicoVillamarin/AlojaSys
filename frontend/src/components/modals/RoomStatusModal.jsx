import { Formik } from 'formik'
import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import * as Yup from 'yup'

import ModalLayout from 'src/layouts/ModalLayout'
import SelectBasic from 'src/components/selects/SelectBasic'
import { updateResources } from 'src/services/updateResources'
import { showErrorConfirm, showSuccess } from 'src/services/toast.jsx'

/**
 * Modal para actualizar estado principal (status) y subestado de limpieza (cleaning_status)
 * para una o varias habitaciones.
 *
 * Nota: este modal debe mostrarse SOLO cuando housekeeping (por plan) NO está habilitado.
 */
const RoomStatusModal = ({ isOpen, onClose, rooms = [], onSuccess }) => {
  const { t } = useTranslation()

  const validationSchema = Yup.object().shape({
    status: Yup.string().nullable(),
    cleaning_status: Yup.string().nullable(),
  })

  const roomLabel = (r) => r?.name || r?.number || `#${r?.id}`

  const statusOptions = useMemo(
    () => [
      { value: '', label: t('common.no_change', 'No cambiar') },
      { value: 'available', label: t('rooms.status.available', 'Disponible') },
      { value: 'occupied', label: t('rooms.status.occupied', 'Ocupada') },
      { value: 'reserved', label: t('rooms.status.reserved', 'Reservada') },
      { value: 'maintenance', label: t('rooms.status.maintenance', 'Mantenimiento') },
      { value: 'out_of_service', label: t('rooms.status.out_of_service', 'Fuera de servicio') },
    ],
    [t]
  )

  const cleaningOptions = useMemo(
    () => [
      { value: '', label: t('common.no_change', 'No cambiar') },
      { value: 'dirty', label: t('rooms.cleaning_status.dirty', 'Requiere limpieza') },
      { value: 'in_progress', label: t('rooms.cleaning_status.in_progress', 'En limpieza') },
      { value: 'clean', label: t('rooms.cleaning_status.clean', 'Limpia') },
    ],
    [t]
  )

  const initialValues = {
    status: '',
    cleaning_status: '',
  }

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={async (values, helpers) => {
        const body = {}
        if (values.status) body.status = values.status
        if (values.cleaning_status) body.cleaning_status = values.cleaning_status

        if (Object.keys(body).length === 0) {
          showErrorConfirm(t('common.no_changes', 'No hay cambios para aplicar.'))
          return
        }

        const targetRooms = Array.isArray(rooms) ? rooms : []
        if (targetRooms.length === 0) {
          showErrorConfirm(t('rooms.no_rooms_selected', 'No hay habitaciones seleccionadas.'))
          return
        }

        helpers.setSubmitting(true)
        try {
          const results = await Promise.allSettled(
            targetRooms.map((r) => updateResources('rooms', r.id, body, { method: 'PATCH' }))
          )
          const ok = results.filter((x) => x.status === 'fulfilled').length
          const fail = results.length - ok

          if (ok > 0) {
            showSuccess(
              fail === 0
                ? t('rooms.bulk_update_success', { count: ok, defaultValue: `Se actualizaron ${ok} habitaciones.` })
                : t('rooms.bulk_update_partial', {
                    ok,
                    total: results.length,
                    defaultValue: `Se actualizaron ${ok}/${results.length} habitaciones.`,
                  })
            )
          }

          if (fail > 0) {
            const firstErr = results.find((x) => x.status === 'rejected')?.reason
            showErrorConfirm(firstErr?.message || t('common.error', 'Ocurrió un error'))
          }

          onSuccess && onSuccess({ ok, fail, total: results.length })
          onClose && onClose()
        } catch (e) {
          showErrorConfirm(e?.message || t('common.error', 'Ocurrió un error'))
        } finally {
          helpers.setSubmitting(false)
        }
      }}
    >
      {({ values, handleSubmit, isSubmitting, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={t('rooms.edit_status_title', 'Actualizar estado de habitaciones')}
          onSubmit={handleSubmit}
          submitText={t('common.apply', 'Aplicar')}
          cancelText={t('common.cancel', 'Cancelar')}
          submitDisabled={isSubmitting}
          submitLoading={isSubmitting}
          size="lg"
        >
          <div className="space-y-4">
            <div className="text-sm text-aloja-gray-800/70">
              {t('rooms.selected_rooms', { count: rooms?.length || 0, defaultValue: `Seleccionadas: ${rooms?.length || 0}` })}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <SelectBasic
                title={t('common.status', 'Estado')}
                name="status"
                options={statusOptions}
                placeholder={t('common.no_change', 'No cambiar')}
                isSearchable={false}
                onChangeExtra={(val) => setFieldValue('status', val)}
              />

              <SelectBasic
                title={t('sidebar.housekeeping_config', 'Limpieza')}
                name="cleaning_status"
                options={cleaningOptions}
                placeholder={t('common.no_change', 'No cambiar')}
                isSearchable={false}
                onChangeExtra={(val) => setFieldValue('cleaning_status', val)}
              />
            </div>

            <div className="border rounded-lg p-3 bg-aloja-gray-100/40">
              <div className="text-xs font-medium text-aloja-gray-800/70 mb-2">
                {t('rooms.rooms', 'Habitaciones')}
              </div>
              <div className="max-h-44 overflow-auto text-sm">
                <ul className="space-y-1">
                  {(rooms || []).slice(0, 50).map((r) => (
                    <li key={r.id} className="flex items-center justify-between gap-3">
                      <span className="text-aloja-gray-900">{roomLabel(r)}</span>
                      <span className="text-xs text-aloja-gray-800/60">#{r.id}</span>
                    </li>
                  ))}
                  {(rooms || []).length > 50 && (
                    <li className="text-xs text-aloja-gray-800/60">
                      {t('common.and_more', { count: (rooms || []).length - 50, defaultValue: `y ${(rooms || []).length - 50} más...` })}
                    </li>
                  )}
                </ul>
              </div>
            </div>

            <div className="text-xs text-aloja-gray-800/60">
              {t(
                'rooms.manual_cleaning_note',
                'Esta edición manual solo está disponible cuando el módulo de housekeeping no está habilitado.'
              )}
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default RoomStatusModal


