import { useAuthStore } from "src/stores/useAuthStore";
import { refreshAccessToken } from "./auth";
import { getApiURL } from "./utils";

const parseResponse = async (resp) => {
  if (resp.status === 204) return null;
  const contentType = resp.headers.get("Content-Type") || resp.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    try {
      return await resp.json();
    } catch {
      return null;
    }
  }
  const text = await resp.text();
  try {
    return text ? JSON.parse(text) : null;
  } catch {
    return text || null;
  }
};

const fetchWithAuth = async (url, options = {}) => {
  const token = useAuthStore.getState().accessToken;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  let resp = await fetch(url, { credentials: "include", ...options, headers });
  if (resp.status !== 401) {
    if (resp.ok) return parseResponse(resp);
    const body = await parseResponse(resp);
    const msg = extractErrorMessage(body) || `HTTP ${resp.status}`;
    throw new Error(msg);
  }

  // Intentar refresh
  const refresh = sessionStorage.getItem("refreshToken");
  if (!refresh) throw new Error("Sesión expirada");
  const newAccess = await refreshAccessToken(refresh);
  useAuthStore.getState().setAccessToken(newAccess);
  const retryHeaders = { ...headers, Authorization: `Bearer ${newAccess}` };
  const retry = await fetch(url, { credentials: "include", ...options, headers: retryHeaders });
  if (retry.ok) return parseResponse(retry);
  const retryBody = await parseResponse(retry);
  const retryMsg = extractErrorMessage(retryBody) || `HTTP ${retry.status}`;
  throw new Error(retryMsg);
};

function extractErrorMessage(body) {
  if (!body) return null;
  if (typeof body === "string") return body;
  if (typeof body.detail === "string") return body.detail;
  
  // Django ValidationError: { '__all__': ['mensaje'] }
  if (body.__all__ && Array.isArray(body.__all__)) {
    return body.__all__[0];
  }
  
  // DRF validation errors: { field: ["error1", ...], ... }
  const firstKey = Object.keys(body)[0];
  if (firstKey) {
    const val = body[firstKey];
    if (Array.isArray(val)) return String(val[0]);
    if (typeof val === "string") return val;
  }
  return null;
}

export default fetchWithAuth;