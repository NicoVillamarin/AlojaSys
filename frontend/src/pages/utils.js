import { toast } from "react-toastify";

// Lista de estados de reservas (versión estática para compatibilidad)
export const RES_STATUS = [
  { value: 'pending', label: 'Pendiente' },
  { value: 'confirmed', label: 'Confirmada' },
  { value: 'check_in', label: 'Check-in' },
  { value: 'check_out', label: 'Check-out' },
  { value: 'cancelled', label: 'Cancelada' },
  { value: 'no_show', label: 'No-show' },
  { value: 'early_check_in', label: 'Check-in anticipado' },
  { value: 'late_check_out', label: 'Check-out tardío' },
]

// Función para obtener la lista de estados de reservas con traducciones
export function getResStatusList(t) {
  return [
    { value: 'pending', label: t('reservations.status.pending') },
    { value: 'confirmed', label: t('reservations.status.confirmed') },
    { value: 'check_in', label: t('reservations.status.check_in') },
    { value: 'check_out', label: t('reservations.status.check_out') },
    { value: 'cancelled', label: t('reservations.status.cancelled') },
    { value: 'no_show', label: t('reservations.status.no_show') },
    { value: 'early_check_in', label: t('reservations.status.early_check_in') },
    { value: 'late_check_out', label: t('reservations.status.late_check_out') },
  ]
}

// Función para obtener el label de un estado con traducciones
export function getStatusLabel(value, t) {
  const statusList = getResStatusList(t)
  const found = statusList.find((s) => s.value === value)
  return found ? found.label : (value || '-')
}

export const AlertsComponent = ({ type, message }) => {
    if (type === 'success') {
      toast.success(message, {
        duration: 3000,
        position: 'top-center',
      });
    } else if (type === 'error') {
      toast.error(message, {
        duration: 3000,
        position: 'top-center',
      });
    }
  };

export const convertToDecimal = (value) => {
  // Convertir a número si es string
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  
  // Verificar que sea un número válido
  if (isNaN(numValue)) {
    return '0,00';
  }
  
  // Formatear con separadores de miles (puntos) y decimales con coma
  return new Intl.NumberFormat('es-ES', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(numValue);
}