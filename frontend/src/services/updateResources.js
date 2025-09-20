import fetchWithAuth from "./fetchWithAuth";
import { getApiURL } from "./utils";

/**
 * @module Services
 *
 * Actualiza un recurso en el servidor.
 *
 * @param {string} resource - Recurso sobre el que se desea realizar la actualizacion.
 * @param {string | number} id - Identificador del recurso.
 * @param {object | FormData} body - Objeto o FormData que contiene los datos a actualizar.
 *
 * @returns {Promise<object | null>} - Promesa que resuelve con el resultado de la
 *                                      actualizacion del recurso, o null si no
 *                                      se encontro el recurso.
 */

export const updateResources = async (resource, id, body) => {
  const isFormData = body instanceof FormData;

  return await fetchWithAuth(getApiURL() + `/api/${resource}/${id}/`, {
    method: "PUT",
    headers: isFormData
      ? undefined // No se necesita encabezado para FormData
      : { "Content-Type": "application/json" },
    body: isFormData ? body : JSON.stringify(body),
  });
};

