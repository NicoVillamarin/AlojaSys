import { useQuery } from "@tanstack/react-query";
import { refreshAccessToken } from "src/services/auth";
import { getApiURL } from "src/services/utils";
import { useAuthStore } from "src/stores/useAuthStore";

export const useMe = () => {
  const { accessToken, login, logout } = useAuthStore();

  const fetchUserData = async () => {
    const meUrl = `${getApiURL()}/api/me/`;
    const currentToken = accessToken || sessionStorage.getItem("accessToken");
    
    console.log(`🔍 useMe: Obteniendo datos del usuario con token...`);
    
    if (!currentToken) {
      console.error("❌ No hay access token disponible");
      throw new Error("No hay token de acceso");
    }
    
    let resp = await fetch(meUrl, { headers: { Authorization: `Bearer ${currentToken}` } });
    if (resp.status === 401) {
      const refreshToken = sessionStorage.getItem("refreshToken");
      if (!refreshToken) {
        console.error("❌ No hay refresh token - sesión expirada");
        logout();
        throw new Error("Sesión expirada");
      }
      console.log("🔄 Token expirado, refrescando...");
      const newAccess = await refreshAccessToken(refreshToken);
      resp = await fetch(meUrl, { headers: { Authorization: `Bearer ${newAccess}` } });
      if (!resp.ok) {
        console.error("❌ Error al refrescar token");
        logout();
        throw new Error("Sesión expirada");
      }
      const me = await resp.json();
      console.log(`✅ Usuario obtenido después de refresh: ${me.username} (ID: ${me.user_id})`);
      login(me, newAccess, refreshToken, me.user_id);
      return me;
    }
    if (!resp.ok) {
      console.error(`❌ Error al obtener usuario: ${resp.status}`);
      throw new Error("Error al obtener usuario");
    }
    const me = await resp.json();
    
    // DEBUG: Verificar que el usuario devuelto coincide con el token
    console.log(`✅ Usuario obtenido: ${me.username} (ID: ${me.user_id})`);
    console.log(`   - is_superuser: ${me.is_superuser}`);
    console.log(`   - Total permisos: ${me.permissions?.length || 0}`);
    
    // Actualizar el store con los datos actuales
    login(me, currentToken, sessionStorage.getItem("refreshToken"), me.user_id);
    return me;
  };

  return useQuery({ 
    queryKey: ["me"], 
    queryFn: fetchUserData, 
    enabled: !!accessToken || !!sessionStorage.getItem("accessToken"),
    staleTime: 0, // Siempre refrescar al montar
    cacheTime: 0, // No cachear para evitar datos antiguos
  });
};