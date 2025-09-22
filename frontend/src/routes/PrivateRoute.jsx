import { Navigate } from "react-router-dom";
import { useAuthStore } from "src/stores/useAuthStore";

export default function PrivateRoute({ children }) {
  const { accessToken } = useAuthStore();
  return accessToken ? children : <Navigate to="/login" replace />;
}