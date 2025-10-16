import React from 'react'
import PropTypes from 'prop-types'
import ModalLayout from 'src/layouts/ModalLayout'
import WarningIcon from 'src/assets/icons/WarningIcon'
import CheckCircleIcon from 'src/assets/icons/CheckCircleIcon'
import SpinnerData from 'src/components/SpinnerData'
import Button from './Button'
import { useTranslation } from 'react-i18next'

const AlertSwal = ({
  isOpen,
  onClose,
  title = 'Confirmar acción',
  description = '¿Estás seguro que querés continuar? Esta acción no se puede deshacer.',
  confirmText = 'Confirmar',
  cancelText = 'Cancelar',
  onConfirm,
  confirmLoading = false,
  tone = 'danger', // 'danger' | 'primary' | 'warning' | 'info' | 'success'
  children,
}) => {
  const { t } = useTranslation()
  const getToneStyles = (tone) => {
    switch (tone) {
      case 'danger':
        return {
          accentText: 'text-red-600',
          ringClass: 'ring-red-200/60',
          haloBg: 'bg-red-200/30',
          chipBg: 'bg-red-50',
          confirmBtnClass: 'from-red-600 to-red-700 hover:from-red-700 hover:to-red-800'
        }
      case 'warning':
        return {
          accentText: 'text-yellow-600',
          ringClass: 'ring-yellow-200/60',
          haloBg: 'bg-yellow-200/30',
          chipBg: 'bg-yellow-50',
          confirmBtnClass: 'from-yellow-600 to-yellow-700 hover:from-yellow-700 hover:to-yellow-800'
        }
      case 'info':
        return {
          accentText: 'text-blue-600',
          ringClass: 'ring-blue-200/60',
          haloBg: 'bg-blue-200/30',
          chipBg: 'bg-blue-50',
          confirmBtnClass: 'from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800'
        }
      case 'success':
        return {
          accentText: 'text-green-600',
          ringClass: 'ring-green-200/60',
          haloBg: 'bg-green-200/30',
          chipBg: 'bg-green-50',
          confirmBtnClass: 'from-green-600 to-green-700 hover:from-green-700 hover:to-green-800'
        }
      default: // primary
        return {
          accentText: 'text-aloja-navy',
          ringClass: 'ring-aloja-navy/25',
          haloBg: 'bg-aloja-navy/15',
          chipBg: 'bg-aloja-navy/5',
          confirmBtnClass: 'from-aloja-navy to-aloja-navy2 hover:from-aloja-navy2 hover:to-aloja-navy2'
        }
    }
  }

  const styles = getToneStyles(tone)
  
  // Seleccionar el icono correcto según el tone
  const getIcon = () => {
    if (tone === 'success') {
      return <CheckCircleIcon size="50" className={styles.accentText} />
    }
    return <WarningIcon size="50" className={styles.accentText} />
  }

  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={onClose}
      title={""}
      customFooter={(
        <>
          {cancelText && (
            <Button variant="danger" size="md" onClick={onClose}>
              {cancelText}
            </Button>
          )}
          <Button 
            variant="success" 
            size="md" 
            onClick={onConfirm} 
            disabled={confirmLoading}
            className={`bg-gradient-to-r ${styles.confirmBtnClass} text-white`}
          >
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
          <span className={`absolute inset-0 rounded-full ${styles.haloBg} animate-ping`} />
          <div className={`relative w-25 h-25 rounded-full ${styles.chipBg} ring-2 ${styles.ringClass} flex items-center justify-center`}>
            {getIcon()}
          </div>
        </div>
        <div className="text-center space-y-2 max-w-md">
          {title && <div className={`text-xl font-semibold ${styles.accentText}`}>{title}</div>}
          <div className="text-[15px] leading-relaxed text-aloja-gray-800">
            {description}
          </div>
          {children}
        </div>
      </div>
    </ModalLayout>
  )
}

AlertSwal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  title: PropTypes.node,
  description: PropTypes.node,
  confirmText: PropTypes.node,
  cancelText: PropTypes.node,
  onConfirm: PropTypes.func,
  confirmLoading: PropTypes.bool,
  tone: PropTypes.oneOf(['danger', 'primary', 'warning', 'info', 'success']),
  children: PropTypes.node,
}

export default AlertSwal
