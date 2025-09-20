import fetchWithAuth from "./fetchWithAuth";
import { getApiParams, getApiURL } from "./utils";

/**
 * @module Services
 *
 * Funcion que trae el resultado de una accion asociada a un recurso.
 *
 * @param {object} queryKey - Objeto que contiene la informacion para hacer la consulta.
 * @param {string} queryKey.resource - Recurso sobre el que se desea realizar la consulta.
 * @param {string} [queryKey.action=""] - Accion asociada al recurso.
 * @param {object} [queryKey.params={}] - Parametros adicionales para la peticion.
 *
 * @returns {Promise<object>} - Promesa que resuelve con el resultado de la accion
 *                              asociada al recurso.
 */

export const actionResources = async ({ queryKey }) => {
  // queryKey recibe, resource, action y params (es opcional), la misma se usara para hacer la llamada.
  const [resource, action = "", params = {}] = queryKey;
  return await fetchWithAuth(
    getApiURL() +
      `/api/${resource}/${action ? `${action}/` : ""}` +
      getApiParams(params),
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );
};

