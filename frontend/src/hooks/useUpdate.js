import { useMutation } from "@tanstack/react-query";
import { showSuccess, showErrorConfirm } from "src/services/toast";
import { updateResources } from "../services/updateResources";

// Servicio mínimo para update (PUT/PATC
/**
 * useUpdate({ resource, onSuccess, method })
 * method: "PATCH" (default) o "PUT"
 */
export const useUpdate = ({ resource, onSuccess, onError, method = "PATCH" }) => {
  const { mutate, isPending, isError, isSuccess } = useMutation({
    mutationFn: ({ id, body }) => updateResources(resource, id, body, { method }),
    onSuccess: (data) => {
      showSuccess("Se actualizó correctamente");
      onSuccess && onSuccess(data);
    },
    onError: (error) => {
      // fetchWithAuth ya extrae el mensaje correctamente y lo pone en error.message
      const msg = error?.message || "Ocurrió un error";
      showErrorConfirm(msg);
      // Llamar callback personalizado si existe
      onError && onError(error);
    },
  });

  return { mutate, isPending, isError, isSuccess };
};


