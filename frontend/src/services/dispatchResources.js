import fetchWithAuth from "./fetchWithAuth";
import { getApiURL } from "./utils";

/**
 * @module Services
 *
 * Ejecuta el metodo de un recurso en el servidor.
 *
 * @param {string} resource - Recurso sobre el que se desea realizar la actualizacion.
 * @param {string} action - Accion sobre el recurso.
 * @param {object} body - Objeto que contiene los datos a actualizar.
 *
 * @returns {Promise<object | null>} - Promesa que resuelve con el resultado de la
 *                                      actualizacion del recurso, o null si no
 *                                      se encontro el recurso.
 */

export const dispatchResources = async (
  resource,
  action,
  body,
  method = "PUT"
) => {
  return await fetchWithAuth(getApiURL() + `/api/${resource}/${action}/`, {
    method: method,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
};

