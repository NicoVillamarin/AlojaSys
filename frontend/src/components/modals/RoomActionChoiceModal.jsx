import ModalLayout from 'src/layouts/ModalLayout'
import { useTranslation } from 'react-i18next'
import RoomsIcon from 'src/assets/icons/RoomsIcon'
import BellIcon from 'src/assets/icons/BellIcon'
import CleaningIcon from 'src/assets/icons/CleaningIcon'
import Button from 'src/components/Button'

/**
 * Modal previo al click de una habitación en el mapa:
 * - Crear reserva
 * - Gestionar habitación (estado/subestado) cuando housekeeping NO está activo
 */
export default function RoomActionChoiceModal({
  isOpen,
  onClose,
  roomData,
  canCreateReservation = true,
  canManageRoom = true,
  housekeepingEnabled = false,
  onCreateReservation,
  onManageRoom,
}) {
  const { t } = useTranslation()

  const roomLabel = roomData?.room?.name || roomData?.room?.number || `#${roomData?.room?.id || ''}`
  const hotelName = roomData?.hotel?.name

  const showManage = !housekeepingEnabled
  const manageDisabled = !canManageRoom || !showManage

  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={onClose}
      title={t('rooms.quick_actions_title', 'Acciones de habitación')}
      customFooter={
        <Button variant="neutral" size="md" onClick={onClose}>
          {t('common.close', 'Cerrar')}
        </Button>
      }
      size="md"
    >
      <div className="space-y-4">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
          <div className="text-xs text-slate-600">{t('rooms.room', 'Habitación')}</div>
          <div className="text-lg font-semibold text-slate-900">{roomLabel}</div>
          {hotelName && <div className="text-xs text-slate-600 mt-0.5">{hotelName}</div>}
        </div>

        <div className="flex flex-col md:flex-row gap-3">
          <Button
            variant="primary"
            size="lg"
            fullWidth
            disabled={!canCreateReservation}
            leftIcon={<BellIcon size="18" />}
            onClick={() => onCreateReservation && onCreateReservation(roomData)}
            className="justify-center"
          >
            {t('rooms.create_reservation', 'Crear reserva')}
          </Button>

          <Button
            variant={manageDisabled ? 'neutral' : 'success'}
            size="lg"
            fullWidth
            disabled={manageDisabled}
            leftIcon={housekeepingEnabled ? <CleaningIcon size="18" /> : <RoomsIcon size="18" />}
            onClick={() => onManageRoom && onManageRoom(roomData)}
            className="justify-center text-nowrap"
          >
            {t('rooms.manage_room', 'Gestionar habitación')}
          </Button>
        </div>

        {!canCreateReservation && !canManageRoom && (
          <div className="text-xs text-slate-600">
            {t('common.no_permissions', 'No tenés permisos para realizar acciones sobre esta habitación.')}
          </div>
        )}
      </div>
    </ModalLayout>
  )
}


