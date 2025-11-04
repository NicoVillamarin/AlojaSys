import { useAuthStore } from "src/stores/useAuthStore";
import { getApiURL } from "./utils";

export const login = async (username, password) => {
  // IMPORTANTE: Limpiar tokens anteriores antes de hacer login
  // Esto asegura que no haya conflictos con sesiones previas
  const authStore = useAuthStore.getState();
  if (authStore.accessToken || authStore.refreshToken) {
    console.log("🧹 Limpiando sesión anterior antes de login...");
    authStore.logout();
  }
  
  // Limpiar sessionStorage completamente para evitar tokens antiguos
  const gridStateKeys = Object.keys(sessionStorage).filter(k => k.startsWith('grid-state-'));
  gridStateKeys.forEach(k => sessionStorage.removeItem(k));
  sessionStorage.removeItem("accessToken");
  sessionStorage.removeItem("refreshToken");
  sessionStorage.removeItem("userId");
  
  const resp = await fetch(`${getApiURL()}/api/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!resp.ok) throw new Error("Credenciales incorrectas");
  const tokens = await resp.json(); // { access, refresh }
  
  console.log(`🔑 Tokens obtenidos para usuario: ${username}`);

  // Traer datos del usuario CON EL NUEVO TOKEN
  const meResp = await fetch(`${getApiURL()}/api/me/`, {
    headers: { Authorization: `Bearer ${tokens.access}` },
  });
  if (!meResp.ok) throw new Error("No se pudo obtener el usuario");
  const me = await meResp.json();
  
  console.log(`✅ Usuario obtenido: ${me.username} (ID: ${me.user_id})`);
  console.log(`   - is_superuser: ${me.is_superuser}`);
  console.log(`   - Total permisos: ${me.permissions?.length || 0}`);

  // Guardar en store con los nuevos datos
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
