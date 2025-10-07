const API_POOL = parseInt(import.meta.env.VITE_API_POOL || "1", 10) || 1;

let apiPool = 0;

export const getApiURL = () => {
  // Permite configurar en runtime via window.__API_URL__ (inyectado por /public/config.js)
  const runtimeApiUrl = typeof window !== 'undefined' && window.__API_URL__ ? window.__API_URL__ : "";
  const baseApiUrl = runtimeApiUrl || import.meta.env.VITE_API_URL || "";

  // En dev, si no hay VITE_API_URL ni runtime, forzar backend local
  if (!baseApiUrl) {
    const host = typeof window !== 'undefined' ? window.location.hostname : ''
    const isLocal = host === 'localhost' || host === '127.0.0.1' || host === '[::1]'
    if (isLocal) return 'http://localhost:8000'
    return ""; // fallback a proxy si aplica
  }
  if (API_POOL === 1) return baseApiUrl;

  const [prefix, domain] = baseApiUrl.split("//");
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