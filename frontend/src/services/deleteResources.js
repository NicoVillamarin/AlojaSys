import fetchWithAuth from "./fetchWithAuth";
import { getApiURL } from "./utils";

/**
 * @module Services
 * 
 * Funcion que elimina un recurso en el servidor.
 *
 * @param {string} resource - Recurso sobre el que se desea realizar la eliminacion.
 * @param {string | number} id - Identificador del recurso.
 *
 * @returns {Promise<object | null>} - Promesa que resuelve con el resultado de la eliminacion
 *                                      del recurso, o null si no se encontro el recurso.
 */
export const deleteResource = async (resource, id) => {
  try{
    const response = await fetchWithAuth(getApiURL() + `/api/${resource}/${id}/`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });
    return response; 
  } catch (error) {
    // Captura el error lanzado desde fetchWithAuth y muestra el mensaje adecuado
    throw new Error(error.message || "Ocurrió un error inesperado.");
  }
};

