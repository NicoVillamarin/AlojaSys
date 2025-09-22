import { useAuthStore } from "src/stores/useAuthStore";
import { refreshAccessToken } from "./auth";
import { getApiURL } from "./utils";

const fetchWithAuth = async (url, options = {}) => {
  const token = useAuthStore.getState().accessToken;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  let resp = await fetch(url, { credentials: "include", ...options, headers });
  if (resp.status !== 401) return resp.json();

  // Intentar refresh
  const refresh = sessionStorage.getItem("refreshToken");
  if (!refresh) throw new Error("Sesión expirada");
  const newAccess = await refreshAccessToken(refresh);
  useAuthStore.getState().setAccessToken(newAccess);
  const retryHeaders = { ...headers, Authorization: `Bearer ${newAccess}` };
  const retry = await fetch(url, { credentials: "include", ...options, headers: retryHeaders });
  if (!retry.ok) throw new Error(`HTTP ${retry.status}`);
  return retry.json();
};

export default fetchWithAuth;