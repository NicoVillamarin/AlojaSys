import CheckCircleIcon from 'src/assets/icons/CheckCircleIcon'
import ExclamationTriangleIcon from 'src/assets/icons/ExclamationTriangleIcon'
import ClockIcon from 'src/assets/icons/ClockIcon'
import CancelIcon from 'src/assets/icons/CancelIcon'
import CheckIcon from 'src/assets/icons/CheckIcon'
import WarningIcon from 'src/assets/icons/WarningIcon'
import WrenchScrewdriverIcon from 'src/assets/icons/WrenchScrewdriverIcon'
import XIcon from 'src/assets/icons/Xicon'
import HomeIcon from 'src/assets/icons/HomeIcon'
import BookingIcon from 'src/assets/icons/BookingIcon'
import Airbnbicon from 'src/assets/icons/Airbnbicon'

/**
 * Variantes predefinidas para el componente Badge.
 * Cada variante incluye colores de fondo, texto, borde e icono.
 */
export const badgeVariants = {
  // Estados de pago
  'payment-pending': {
    bg: 'bg-yellow-50',
    text: 'text-yellow-800',
    border: 'border-yellow-200',
    icon: ClockIcon,
    iconColor: 'text-yellow-600'
  },
  'payment-paid': {
    bg: 'bg-green-50',
    text: 'text-green-800',
    border: 'border-green-200',
    icon: CheckCircleIcon,
    iconColor: 'text-green-600'
  },
  'payment-failed': {
    bg: 'bg-red-50',
    text: 'text-red-800',
    border: 'border-red-200',
    icon: ExclamationTriangleIcon,
    iconColor: 'text-red-600'
  },
  'payment-partial': {
    bg: 'bg-orange-50',
    text: 'text-orange-800',
    border: 'border-orange-200',
    icon: ClockIcon,
    iconColor: 'text-orange-600'
  },
  'payment-deposit': {
    bg: 'bg-blue-50',
    text: 'text-blue-800',
    border: 'border-blue-200',
    icon: CheckIcon,
    iconColor: 'text-blue-600'
  },
  
  // Estados de reserva
  'reservation-pending': {
    bg: 'bg-yellow-50',
    text: 'text-yellow-800',
    border: 'border-yellow-200',
    icon: ClockIcon,
    iconColor: 'text-yellow-600'
  },
  'reservation-confirmed': {
    bg: 'bg-blue-50',
    text: 'text-blue-800',
    border: 'border-blue-200',
    icon: CheckIcon,
    iconColor: 'text-blue-600'
  },
  'reservation-check_in': {
    bg: 'bg-green-50',
    text: 'text-green-800',
    border: 'border-green-200',
    icon: CheckCircleIcon,
    iconColor: 'text-green-600'
  },
  'reservation-check_out': {
    bg: 'bg-blue-50',
    text: 'text-blue-800',
    border: 'border-blue-200',
    icon: CheckCircleIcon,
    iconColor: 'text-blue-600'
  },
  'reservation-cancelled': {
    bg: 'bg-red-50',
    text: 'text-red-800',
    border: 'border-red-200',
    icon: CancelIcon,
    iconColor: 'text-red-600'
  },
  'reservation-no_show': {
    bg: 'bg-gray-50',
    text: 'text-gray-800',
    border: 'border-gray-200',
    icon: WarningIcon,
    iconColor: 'text-gray-600'
  },
  'reservation-early_check_in': {
    bg: 'bg-green-50',
    text: 'text-green-800',
    border: 'border-green-200',
    icon: CheckCircleIcon,
    iconColor: 'text-green-600'
  },
  'reservation-late_check_out': {
    bg: 'bg-orange-50',
    text: 'text-orange-800',
    border: 'border-orange-200',
    icon: ClockIcon,
    iconColor: 'text-orange-600'
  },
  
  // Estados de habitaciones
  'room-available': {
    bg: 'bg-green-50',
    text: 'text-green-800',
    border: 'border-green-200',
    icon: CheckIcon,
    iconColor: 'text-green-600'
  },
  'room-occupied': {
    bg: 'bg-red-50',
    text: 'text-red-800',
    border: 'border-red-200',
    icon: ExclamationTriangleIcon,
    iconColor: 'text-red-600'
  },
  'room-maintenance': {
    bg: 'bg-orange-50',
    text: 'text-orange-800',
    border: 'border-orange-200',
    icon: WrenchScrewdriverIcon,
    iconColor: 'text-orange-600'
  },
  'room-cleaning': {
    bg: 'bg-blue-50',
    text: 'text-blue-800',
    border: 'border-blue-200',
    icon: ClockIcon,
    iconColor: 'text-blue-600'
  },
  'room-blocked': {
    bg: 'bg-purple-50',
    text: 'text-purple-800',
    border: 'border-purple-200',
    icon: ExclamationTriangleIcon,
    iconColor: 'text-purple-600'
  },
  'room-out_of_service': {
    bg: 'bg-gray-50',
    text: 'text-gray-800',
    border: 'border-gray-200',
    icon: WarningIcon,
    iconColor: 'text-gray-600'
  },
  
  // Estados de facturación
  'invoice-draft': {
    bg: 'bg-orange-50',
    text: 'text-orange-800',
    border: 'border-orange-200',
    icon: ClockIcon,
    iconColor: 'text-orange-600'
  },
  'invoice-sent': {
    bg: 'bg-blue-50',
    text: 'text-blue-800',
    border: 'border-blue-200',
    icon: ClockIcon,
    iconColor: 'text-blue-600'
  },
  'invoice-approved': {
    bg: 'bg-green-50',
    text: 'text-green-800',
    border: 'border-green-200',
    icon: CheckCircleIcon,
    iconColor: 'text-green-600'
  },
  'invoice-rejected': {
    bg: 'bg-red-50',
    text: 'text-red-800',
    border: 'border-red-200',
    icon: ExclamationTriangleIcon,
    iconColor: 'text-red-600'
  },
  'invoice-cancelled': {
    bg: 'bg-yellow-50',
    text: 'text-yellow-800',
    border: 'border-yellow-200',
    icon: CancelIcon,
    iconColor: 'text-yellow-600'
  },
  'invoice-expired': {
    bg: 'bg-purple-50',
    text: 'text-purple-800',
    border: 'border-purple-200',
    icon: WarningIcon,
    iconColor: 'text-purple-600'
  },
  'invoice-default': {
    bg: 'bg-gray-50',
    text: 'text-gray-800',
    border: 'border-gray-200',
    icon: null,
    iconColor: 'text-gray-600'
  },
  
  // Estados AFIP
  'afip-test': {
    bg: 'bg-blue-50',
    text: 'text-blue-800',
    border: 'border-blue-200',
    icon: ClockIcon,
    iconColor: 'text-blue-600'
  },
  'afip-production': {
    bg: 'bg-green-50',
    text: 'text-green-800',
    border: 'border-green-200',
    icon: CheckCircleIcon,
    iconColor: 'text-green-600'
  },
  'afip-active': {
    bg: 'bg-green-50',
    text: 'text-green-800',
    border: 'border-green-200',
    icon: CheckCircleIcon,
    iconColor: 'text-green-600'
  },
  'afip-inactive': {
    bg: 'bg-gray-50',
    text: 'text-gray-800',
    border: 'border-gray-200',
    icon: XIcon,
    iconColor: 'text-gray-600'
  },
  
  // Estados generales
  'success': {
    bg: 'bg-green-50',
    text: 'text-green-800',
    border: 'border-green-200',
    icon: CheckCircleIcon,
    iconColor: 'text-green-600'
  },
  'warning': {
    bg: 'bg-yellow-50',
    text: 'text-yellow-800',
    border: 'border-yellow-200',
    icon: XIcon,
    iconColor: 'text-yellow-600'
  },
  'error': {
    bg: 'bg-red-50',
    text: 'text-red-800',
    border: 'border-red-200',
    icon: XIcon,
    iconColor: 'text-red-600'
  },
  'info': {
    bg: 'bg-blue-50',
    text: 'text-blue-800',
    border: 'border-blue-200',
    icon: ClockIcon,
    iconColor: 'text-blue-600'
  },
  'directo': {
    bg: 'bg-violet-50',
    text: 'text-violet-800',
    border: 'border-violet-200',
    icon: HomeIcon,
    iconColor: 'text-violet-600'
  },
  'booking': {
    bg: 'bg-orange-50',
    text: 'text-orange-800',
    border: 'border-orange-200',
    icon: BookingIcon,
    iconColor: 'text-orange-600'
  },
  'airbnb': {
    bg: 'bg-indigo-50',
    text: 'text-indigo-800',
    border: 'border-indigo-200',
    icon: Airbnbicon,
    iconColor: 'text-indigo-600'
  },
  'default': {
    bg: 'bg-gray-50',
    text: 'text-gray-800',
    border: 'border-gray-200',
    icon: null,
    iconColor: 'text-gray-600'
  }
}

/**
 * Configuraciones de tamaño para el componente Badge.
 */
export const badgeSizes = {
  'sm': {
    container: 'px-2 py-1 text-xs',
    icon: 'w-3 h-3',
    spacing: 'gap-1'
  },
  'md': {
    container: 'px-2.5 py-1.5 text-sm',
    icon: 'w-4 h-4',
    spacing: 'gap-1.5'
  },
  'lg': {
    container: 'px-3 py-2 text-base',
    icon: 'w-5 h-5',
    spacing: 'gap-2'
  }
}

