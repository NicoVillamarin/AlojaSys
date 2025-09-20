import fetchWithAuth from "./fetchWithAuth";
import { getApiParams, getApiURL } from "./utils";

// Extrae page=N de la URL next de DRF
function getNextPageFromDRF(nextUrl) {
  if (!nextUrl) return undefined;
  try {
    const u = new URL(nextUrl);
    const p = u.searchParams.get("page");
    return p ? Number(p) : undefined;
  } catch {
    return undefined;
  }
}

/**
 * queryKey = [resource, params]
 * pageParam = número de página (DRF usa 'page')
 */
export const listResources = async ({ queryKey, pageParam }) => {
  const [resource, params = {}] = queryKey;
  const queryParams = { ...params };
  if (pageParam != null) queryParams.page = pageParam;

  // baseURL: usa proxy /api (dev) o VITE_API_URL/api (prod)
  const base = getApiURL() || "";
  const url = `${base}/api/${resource}/${getApiParams(queryParams)}`;

  const json = await fetchWithAuth(url, {
    method: "GET",
  });

  // DRF: { count, next, previous, results }
  if (Array.isArray(json)) {
    return {
      results: json,
      count: json.length,
      next_page: undefined,
    };
  }
  return {
    results: json.results ?? [],
    count: json.count ?? 0,
    next_page: getNextPageFromDRF(json.next),
    raw: json,
  };
};