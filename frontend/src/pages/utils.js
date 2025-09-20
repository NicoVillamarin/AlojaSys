import { toast } from "react-toastify";

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
  