import { useMutation } from "@tanstack/react-query";
import { deleteResource } from "src/services/deleteResources";
import { showSuccess, showErrorConfirm } from "src/services/toast";

/**
 * @module Hooks
 *
 * Hook personalizado para eliminar un recurso utilizando `useMutation` de React Query.
 * Este hook se utiliza para manejar operaciones de eliminación (CRUD) en una API.
 *
 * @param {Object} options - Opciones para configurar el hook.
 * @param {string} options.resource - El nombre del recurso a eliminar.
 * @param {Function} [options.onError] - Función que se ejecuta cuando ocurre un error en la eliminación. Opcional.
 *
 * @returns {Object} - Retorna un objeto con las propiedades proporcionadas por `useMutation`:
 * - `mutate`: Función para ejecutar la operación de eliminación del recurso.
 * - `isPending`: Indica si la operación de eliminación está en curso.
 * - `isError`: Indica si hubo un error en la operación.
 * - `isSuccess`: Indica si la operación de eliminación fue exitosa.
 *
 * @example
 * const { mutate: deleteFunc, isSuccess } = useDelete({
 *   resource: "comments",
 * });
 *
 * if (isSuccess) {
 *   Swal.fire({
 *     position: "top",
 *     icon: "success",
 *     title: "Se eliminó correctamente",
 *     showConfirmButton: false,
 *     timer: 1500,
 *   });
 *   onDone && onDone();
 * }
 *
 * const handleClick = () => {
 *   deleteFunc(objId);  // Eliminar el recurso con el ID objId
 * };
 *
 * <Button onClick={handleClick}>Eliminar</Button>
 */

export const useDelete = ({ resource, onError, onSuccess }) => {
  const { mutate, isPending, isError, isSuccess } = useMutation({
    mutationFn: (id) => deleteResource(resource, id),
    onSuccess: (data) => {
      showSuccess("Se eliminó correctamente");
      onSuccess && onSuccess(data);
    },
    onError: (error) => {
      let errorMessage = error?.message;
      if (typeof errorMessage === "string") {
        errorMessage = errorMessage.replace(/^\['|'\]$/g, "");
      }
      showErrorConfirm(errorMessage || "Ocurrió un error");
    },
  });

  return { mutate, isPending, isError, isSuccess };
};
