import { useMutation } from "@tanstack/react-query";
import { createResource } from "src/services/createResources";
import { showSuccess, showErrorConfirm } from "src/services/toast";

/**
 * @module Hooks
 * Hook personalizado para crear un recurso utilizando `useMutation` de React Query.
 * Este hook se utiliza para manejar operaciones de creación (CRUD) en una API.
 *
 * @param {Object} options - Opciones para configurar el hook.
 * @param {string} options.resource - El nombre del recurso a crear.
 * @param {Function} options.onSuccess - Función que se ejecuta cuando la creación es exitosa.
 *
 * @returns {Object} - Retorna un objeto con los siguientes valores:
 * - `mutate`: Función que ejecuta la operación de creación del recurso.
 * - `isPending`: Indica si la operación está en curso.
 * - `isError`: Indica si hubo un error en la operación.
 * - `isSuccess`: Indica si la operación fue exitosa.
 *
 * @example
 * const onSuccess = (data) => {
 *   resetForm();
 *   if (onRefresh) {
 *     onRefresh();
 *   }
 *   if (closeModal) {
 *     closeModal();
 *   }
 * };
 *
 * const { mutate: createResource } = useCreate({
 *   resource: "comments",
 *   onSuccess,
 * });
 *
 * const handleCreate = useCallback(() => {
 *   createResource({
 *     object_id: objId,
 *     resource,
 *     description: comment,
 *   });
 * }, [comment, objId, createResource]);
 *
 * <Button onClick={handleCreate}>Create</Button>
 */

export const useCreate = ({ resource, onSuccess, onError }) => {
  const { mutate, isPending, isError, isSuccess } = useMutation({
    mutationFn: (body) => createResource(resource, body),
    onSuccess: (data) => {
      showSuccess("Se creó correctamente");
      onSuccess && onSuccess(data?.data ?? data);
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
