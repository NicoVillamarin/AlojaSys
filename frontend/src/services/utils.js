const API_URL = import.meta.env.VITE_API_URL || "";
const API_POOL = parseInt(import.meta.env.VITE_API_POOL || "1", 10) || 1;

let apiPool = 0;

export const getApiURL = () => {
  if (!API_URL) return ""; // usará proxy /api de Vite
  if (API_POOL === 1) return API_URL;

  const [prefix, domain] = API_URL.split("//");
  apiPool = apiPool === API_POOL ? 1 : apiPool + 1;
  return `${prefix}//${apiPool}.${domain}`;
};

export const getApiParams = (params = {}) => {
  if (!params || typeof params !== "object") return "";
  const qs = Object.entries(params)
    .filter(([_, v]) => v !== undefined && v !== null && v !== "")
    .map(([k, v]) => encodeURIComponent(k) + "=" + encodeURIComponent(v))
    .join("&");
  return qs ? `?${qs}` : "";
};