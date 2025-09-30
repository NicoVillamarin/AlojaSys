import { toast } from "react-toastify";

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

export function getStatusLabel(value) {
  const found = RES_STATUS.find((s) => s.value === value)
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
  