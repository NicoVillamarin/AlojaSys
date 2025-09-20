import fetchWithAuth from "./fetchWithAuth";
import { getApiURL } from "./utils";

/**
 * @module Services
 * 
 * Funcion que trae el detalle de un recurso.
 *
 * @param {object} queryKey - Objeto que contiene la informacion para hacer la
 *                            consulta.
 * @param {string} queryKey.resource - Recurso sobre el que se desea realizar la
 *                                     consulta.
 * @param {string} [queryKey.id=""] - Identificador del recurso.
 *
 * @returns {Promise<object>} - Promesa que resuelve con el detalle del recurso.
 */

export const fetchResources = async ({ queryKey }) => {
  const [resource, id = ""] = queryKey;

  return await fetchWithAuth(getApiURL() + `/api/${resource}/${id}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
};

