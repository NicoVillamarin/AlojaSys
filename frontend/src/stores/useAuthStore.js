import { create } from "zustand";

// Store de autenticación
export const useAuthStore = create((set) => ({
  user: null, // Almacenamos los datos del usuario (no solo el email)
  accessToken: sessionStorage.getItem("accessToken") || null,
  refreshToken: sessionStorage.getItem("refreshToken") || null,
  userId: sessionStorage.getItem("userId") || null, // Guardamos el user_id para consultas

  login: (user, accessToken, refreshToken, userId) => {
    set({ user, accessToken, refreshToken, userId });
    sessionStorage.setItem("accessToken", accessToken);
    sessionStorage.setItem("refreshToken", refreshToken);
    sessionStorage.setItem("userId", userId); // Guardamos el user_id en sessionStorage
  },

  logout: () => {
    set({ user: null, accessToken: null, refreshToken: null, userId: null });
    sessionStorage.removeItem("accessToken");
    sessionStorage.removeItem("refreshToken");
    sessionStorage.removeItem("userId"); // Eliminar el user_id de sessionStorage
    Object.keys(sessionStorage)
      .filter(k => k.startsWith('grid-state-'))
      .forEach(k => sessionStorage.removeItem(k));

    Object.keys(localStorage)
      .filter(k => k.startsWith('grid-state-'))
      .forEach(k => localStorage.removeItem(k));
  },

  setAccessToken: (newAccessToken) => {
    set({ accessToken: newAccessToken });
    sessionStorage.setItem("accessToken", newAccessToken);
  },
}));
