import React from 'react'
import PropTypes from 'prop-types'
import ModalLayout from 'src/layouts/ModalLayout'
import WarningIcon from 'src/assets/icons/WarningIcon'
import SpinnerData from 'src/components/SpinnerData'
import Button from './Button'

const ValidateAction = ({
  isOpen,
  onClose,
  title = 'Confirmar acción',
  description = '¿Estás seguro que querés continuar? Esta acción no se puede deshacer.',
  confirmText = 'Confirmar',
  cancelText = 'Cancelar',
  onConfirm,
  confirmLoading = false,
  tone = 'danger', // 'danger' | 'primary'
  children,
}) => {
  const isDanger = tone === 'danger'
  const accentText = isDanger ? 'text-red-600' : 'text-aloja-navy'
  const ringClass = isDanger ? 'ring-red-200/60' : 'ring-aloja-navy/25'
  const haloBg = isDanger ? 'bg-red-200/30' : 'bg-aloja-navy/15'
  const chipBg = isDanger ? 'bg-red-50' : 'bg-aloja-navy/5'
  const confirmBtnClass = isDanger
    ? 'from-red-600 to-red-700 hover:from-red-700 hover:to-red-800'
    : 'from-aloja-navy to-aloja-navy2 hover:from-aloja-navy2 hover:to-aloja-navy2'

  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={onClose}
      title={""}
      customFooter={(
        <>
        <Button variant="danger" size="md" onClick={onClose}>
        {cancelText}
        </Button>
        <Button variant="success" size="md" onClick={onConfirm} disabled={confirmLoading}>
        {confirmLoading ? (
              <span className="inline-flex items-center gap-2">
                <SpinnerData inline size={16} label={null} />
                <span>{confirmText}</span>
              </span>
            ) : (
              confirmText
            )}
        </Button>
        </>
      )}
    >
      <div className="flex flex-col justify-center items-center py-8 gap-4">
        <div className="relative">
          <span className={`absolute inset-0 rounded-full ${haloBg} animate-ping`} />
          <div className={`relative w-25 h-25 rounded-full ${chipBg} ring-2 ${ringClass} flex items-center justify-center`}>
            <WarningIcon size="50" className={accentText} />
          </div>
        </div>
        <div className="text-center space-y-2 max-w-md">
          {title && <div className={`text-base font-semibold ${accentText}`}>{title}</div>}
          <div className="text-[15px] leading-relaxed text-aloja-gray-800">
            {description}
          </div>
          {children}
        </div>
      </div>
    </ModalLayout>
  )
}

ValidateAction.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  title: PropTypes.node,
  description: PropTypes.node,
  confirmText: PropTypes.node,
  cancelText: PropTypes.node,
  onConfirm: PropTypes.func,
  confirmLoading: PropTypes.bool,
  tone: PropTypes.oneOf(['danger', 'primary']),
  children: PropTypes.node,
}

export default ValidateAction