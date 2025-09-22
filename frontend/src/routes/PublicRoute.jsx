import { Navigate } from "react-router-dom";
import { useAuthStore } from "src/stores/useAuthStore";

export default function PublicRoute({ children }) {
  const { accessToken } = useAuthStore();
  return accessToken ? <Navigate to="/" replace /> : children;
}