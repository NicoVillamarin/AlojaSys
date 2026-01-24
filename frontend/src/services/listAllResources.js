import fetchWithAuth from "./fetchWithAuth";
import { getApiParams, getApiURL } from "./utils";

/**
 * listAllResources
 * Trae todos los resultados de un endpoint paginado estilo DRF:
 * { count, next, previous, results }
 *
 * - **genérico**: sirve para rooms, reservations, housekeeping_tasks, etc.
 * - **seguro**: corta por maxPages para evitar loops si algo viene mal.
 */
export async function listAllResources({
  resource,
  params = {},
  pageSize = 1000,
  maxPages = 50,
} = {}) {
  if (!resource) throw new Error("Falta 'resource' para listar.");

  const base = getApiURL() || "";
  const initialParams = { ...params };
  if (pageSize) initialParams.page_size = pageSize;

  let url = `${base}/api/${resource}/${getApiParams(initialParams)}`;
  let results = [];
  let pages = 0;

  while (url) {
    pages += 1;
    if (pages > maxPages) {
      throw new Error(
        "No se pudo completar la carga: demasiadas páginas (revisar filtros)."
      );
    }

    const json = await fetchWithAuth(url, { method: "GET" });

    // Endpoints que devuelven array directamente (sin paginación)
    if (Array.isArray(json)) return json;

    results = results.concat(json?.results ?? []);
    url = json?.next ?? null;
  }

  return results;
}

