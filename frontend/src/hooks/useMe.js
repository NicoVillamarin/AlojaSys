import { useQuery } from "@tanstack/react-query";
import { refreshAccessToken } from "src/services/auth";
import { getApiURL } from "src/services/utils";
import { useAuthStore } from "src/stores/useAuthStore";

export const useMe = () => {
  const { accessToken, login, logout } = useAuthStore();

  const fetchUserData = async () => {
    const meUrl = `${getApiURL()}/api/me/`;
    let resp = await fetch(meUrl, { headers: { Authorization: `Bearer ${accessToken}` } });
    if (resp.status === 401) {
      const refreshToken = sessionStorage.getItem("refreshToken");
      if (!refreshToken) throw new Error("Sesión expirada");
      const newAccess = await refreshAccessToken(refreshToken);
      resp = await fetch(meUrl, { headers: { Authorization: `Bearer ${newAccess}` } });
      if (!resp.ok) throw new Error("Sesión expirada");
      const me = await resp.json();
      login(me, newAccess, refreshToken, me.user_id);
      return me;
    }
    if (!resp.ok) throw new Error("Error al obtener usuario");
    const me = await resp.json();
    login(me, accessToken, sessionStorage.getItem("refreshToken"), me.user_id);
    return me;
  };

  return useQuery({ queryKey: ["me"], queryFn: fetchUserData, enabled: !!accessToken });
};