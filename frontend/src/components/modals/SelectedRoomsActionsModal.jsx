import ModalLayout from 'src/layouts/ModalLayout'
import Button from 'src/components/Button'
import { useTranslation } from 'react-i18next'

/**
 * Modal para acciones sobre una selección de habitaciones (checkbox).
 * Muestra la lista y permite:
 * - Reserva simple (si hay 1 seleccionada o si el usuario quiere reservar la clickeada)
 * - Reserva multi-habitación (si hay 2+)
 * - Gestionar habitaciones (estado/subestado) si housekeeping NO está habilitado
 */
export default function SelectedRoomsActionsModal({
  isOpen,
  onClose,
  selectedRooms = [],
  activeRoom, // opcional: habitación sobre la cual se hizo click
  canCreateReservation = true,
  canManageRoom = true,
  housekeepingEnabled = false,
  onCreateSingleReservation,
  onCreateMultiReservation,
  onManageRooms,
  onClearSelection,
}) {
  const { t } = useTranslation()

  const count = Array.isArray(selectedRooms) ? selectedRooms.length : 0
  const active = activeRoom || (count === 1 ? selectedRooms[0] : null)

  const roomLabel = (r) => r?.name || r?.number || `#${r?.id}`

  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={onClose}
      title={t('rooms.selected_actions_title', 'Acciones sobre selección')}
      customFooter={
        <div className="flex items-center gap-2">
          {onClearSelection && (
            <Button variant="neutral" size="md" onClick={onClearSelection}>
              {t('common.clear', 'Limpiar')}
            </Button>
          )}
          <Button variant="neutral" size="md" onClick={onClose}>
            {t('common.close', 'Cerrar')}
          </Button>
        </div>
      }
      size="lg"
    >
      <div className="space-y-4">
        <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
          <div className="text-sm text-slate-700">
            <span className="font-semibold">{count}</span>{' '}
            {t('rooms.selected_rooms', { count, defaultValue: 'habitaciones seleccionadas' })}
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {(selectedRooms || []).slice(0, 20).map((r) => (
              <span
                key={r.id}
                className="inline-flex items-center rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-800 ring-1 ring-slate-200"
              >
                {roomLabel(r)}
              </span>
            ))}
            {(selectedRooms || []).length > 20 && (
              <span className="text-xs text-slate-600">
                {t('common.and_more', { count: (selectedRooms || []).length - 20, defaultValue: `y ${(selectedRooms || []).length - 20} más...` })}
              </span>
            )}
          </div>
        </div>

        {/* Acciones principales en row (desktop) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {count === 1 ? (
            <Button
              variant="primary"
              size="lg"
              fullWidth
              disabled={!canCreateReservation || !active}
              onClick={() => onCreateSingleReservation && onCreateSingleReservation(active)}
            >
              {t('rooms.create_reservation', 'Crear reserva')}
            </Button>
          ) : (
            <Button
              variant="primary"
              size="lg"
              fullWidth
              disabled={!canCreateReservation || count < 2}
              onClick={() => onCreateMultiReservation && onCreateMultiReservation(selectedRooms)}
            >
              {t('dashboard.reservations_management.create_multi_room_btn', 'Reserva multi-habitación')}
            </Button>
          )}

          <Button
            variant="outline"
            size="lg"
            fullWidth
            disabled={!canManageRoom || housekeepingEnabled || count === 0}
            onClick={() => onManageRooms && onManageRooms(selectedRooms)}
          >
            {housekeepingEnabled
              ? t('rooms.manage_room_disabled_housekeeping', 'No disponible: housekeeping está habilitado.')
              : t('rooms.manage_room', 'Gestionar habitaciones')}
          </Button>
        </div>
      </div>
    </ModalLayout>
  )
}


