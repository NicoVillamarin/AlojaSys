import { useQuery } from "@tanstack/react-query";
import { actionResources } from "src/services/actionResources";

export const useAction = ({ resource, action, params, enabled = true }) => {
  /**
   * @module Hooks
   * Hook para realizar llamadas a recursos con acciones y parametros opcionales.
   *
   * @param {Object} options - Las opciones para configurar la llamada a la API.
   * @param {string} options.resource - El recurso al que se apunta en la llamada. Es requerido.
   * @param {string} options.action - La acción específica que se va a ejecutar sobre el recurso. Opcional.
   * @param {Object} [options.params] - Parámetros adicionales o filtros que se envían junto a la acción. Opcional.
   *
   * @returns {Object} - Retorna un objeto con los siguientes valores:
   * - `results`: Los datos obtenidos de la llamada, o un array vacío si no hay datos.
   * - `isPending`: Indica si la llamada está en curso (`true` si se está cargando, `false` si ya se completó).
   * - `isError`: Indica si hubo un error en la llamada (`true` si hay error, `false` en caso contrario).
   * - `refetch`: Función para volver a ejecutar la llamada manualmente.
   *
   * @example
   * const { results: data, isError, isPending, refetch } = useAction({
   *   resource: "reports",
   *   action: "variants.operations/kpi",
   *   params: {
   *     magnitude: firstWareMagnitudId
   *   },
   * });
   *
   * if (isPending) {
   *   console.log('Cargando datos...');
   * }
   *
   * if (isError) {
   *   console.error('Hubo un error en la solicitud');
   * }
   *
   * console.log('Datos:', data);
   *
   */

  const { data, isError, isPending, refetch, isRefetching } = useQuery({
    queryKey: [resource, action, params],
    queryFn: actionResources,
    enabled,
  });

  return {
    refetch,
    isRefetching,
    isPending,
    isError,
    results: data || [],
  };
};

