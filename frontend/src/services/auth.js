import { useAuthStore } from "src/stores/useAuthStore";
import { getApiURL } from "./utils";

export const login = async (username, password) => {
  const resp = await fetch(`${getApiURL()}/api/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!resp.ok) throw new Error("Credenciales incorrectas");
  const tokens = await resp.json(); // { access, refresh }

  // Traer datos del usuario
  const meResp = await fetch(`${getApiURL()}/api/me/`, {
    headers: { Authorization: `Bearer ${tokens.access}` },
  });
  if (!meResp.ok) throw new Error("No se pudo obtener el usuario");
  const me = await meResp.json();

  // Guardar en store
  useAuthStore.getState().login(me, tokens.access, tokens.refresh, me.user_id);
  sessionStorage.setItem("refreshToken", tokens.refresh);
  return { ...tokens, user: me };
};

export const refreshAccessToken = async (refreshToken) => {
  const resp = await fetch(`${getApiURL()}/api/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: refreshToken }),
  });
  if (!resp.ok) throw new Error("No se pudo refrescar el token.");
  const data = await resp.json();
  return data.access;
};