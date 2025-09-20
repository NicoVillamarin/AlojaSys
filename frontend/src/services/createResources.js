import fetchWithAuth from "./fetchWithAuth";
import { getApiURL } from "./utils";

/**
 * @module Services
 *
 * Funcion que crea un recurso en el servidor.
 *
 * @param {string} resource - Recurso sobre el que se desea realizar la creacion.
 * @param {object|FormData} body - Objeto o FormData que contiene los datos del recurso.
 *
 * @returns {Promise<object>} - Promesa que resuelve con el resultado de la creacion
 *                              del recurso.
 */
export const createResource = async (resource, body) => {
  const isFormData = body instanceof FormData;

  try {
    const response = await fetchWithAuth(`${getApiURL()}/api/${resource}/`, {
      method: "POST",
      headers: isFormData
        ? undefined // Fetch gestiona automáticamente los encabezados para FormData
        : { "Content-Type": "application/json" },
      body: isFormData ? body : JSON.stringify(body),
    });

    // Si la respuesta es exitosa, devuelve los datos
    return response; // No es necesario verificar el success aquí
  } catch (error) {
    // Captura el error lanzado desde fetchWithAuth y muestra el mensaje adecuado
    throw new Error(error.message || "Ocurrió un error inesperado.");
  }
};

