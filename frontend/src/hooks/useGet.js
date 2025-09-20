import { useQuery } from "@tanstack/react-query";
import { fetchResources } from "src/services/fetchResources";

/**
 * Hook para obtener un recurso por su ID.
 * @param {Object} options - Opciones para configurar el hook.
 * @param {string} options.resource - El nombre del recurso al que se apunta la llamada.
 * @param {string} [options.id] - El ID del recurso a obtener. Opcional.
 * @returns {Object} - Un objeto con los siguientes valores:
 * - `isPending`: Indica si la llamada está en curso.
 * - `isError`: Indica si hubo un error en la llamada.
 * - `results`: El resultado de la llamada, o un objeto vacío si no hay ID.
 * - `refetch`: Función para volver a ejecutar la llamada manualmente.
 *
 *
 * como se utilizar el hook:
 *
 * const { results: data, isPending, isError } = useGet({
 * resource: "documents",
 * id: 14, // el id no es obligatorio
 * })
 *
 */

export const useGet = ({ resource, id, onSuccess, enabled = true }) => {
    const shouldFetch = enabled && !!resource && (id !== undefined && id !== null);
  
    const { data, isError, isPending, isFetching, isSuccess, refetch } = useQuery({
      queryKey: [resource, id],
      queryFn: fetchResources,
      enabled: shouldFetch,
      onSuccess,
    });
  
    return {
      refetch,
      isPending: !!isPending,
      isError: !!isError,
      isFetching: !!isFetching,
      isSuccess: !!isSuccess,
      results: data ?? null,
    };
  };