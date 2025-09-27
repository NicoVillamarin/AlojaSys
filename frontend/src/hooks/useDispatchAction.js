import { useMutation } from "@tanstack/react-query";
import { AlertsComponent } from "src/pages/utils";
import { dispatchResources } from "src/services/dispatchResources";
import { showSuccess, showErrorConfirm } from "src/services/toast";

/**
 * @module Hooks
 * Hook para modificar un recurso con la API.
 * @param {Object} options - Opciones para configurar el hook.
 * @param {string} options.resource - El nombre del recurso a modificar.
 * @param {Function} [options.onSuccess] - Función que se ejecuta cuando la
 * llamada es exitosa, recibe los datos del recurso modificado.
 * @param {Function} [options.onError] - Función que se ejecuta cuando la
 * llamada falla, recibe el error.
 * @returns {Object} - Retorna un objeto con los siguientes valores:
 * - `mutate`: Función para modificar el recurso.
 * - `isLoading`: Indica si la llamada está en curso.
 * - `isError`: Indica si hubo un error en la llamada.
 * - `isSuccess`: Indica si la llamada fue exitosa.
 * - `reset`: Función para resetear el estado de `isSuccess`.
 *
 * como se usa:
 *
 *  const [updatedUser, setUpdatedUser] = useState(null)
 *
 *           const [userObj] = useGet({ resource: "users", id: me.id });
 *
 *           const { mutate: update, isSuccess, reset } = useUpdate({
 *             resource: "users",
 *             onSuccess: (data) => {
 *               setUpdatedUser(data);
 *             },
 *           });
 *
 *
 *           const onSubmit = useCallback(
 *             (values, { setSubmitting }) => {
 *               setSubmitting(true);
 *               update({ body: values, id: me.id });
 *               setSubmitting(false);
 *             },
 *             [update, me.id]
 *           );
 *  })
 */
export const useDispatchAction = ({ resource, onSuccess, onError }) => {
  const { mutate, isPending, isError, isSuccess, reset } = useMutation({
    mutationFn: ({ action, body, method }) =>
      dispatchResources(resource, action, body, method),
    onSuccess: (data) => {
      showSuccess("Se ejecuto la accion con exito");
      if (onSuccess) onSuccess(data);
    },
    onError: (error) => {
      // fetchWithAuth ya extrae el mensaje correctamente y lo pone en error.message
      const msg = error?.message || "Ocurrió un error";
      showErrorConfirm(msg);
      if (onError) onError(error);
    },
  });
  return { mutate, isPending, isError, isSuccess, reset };
};
