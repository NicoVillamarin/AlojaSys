import { Navigate } from "react-router-dom";
import { useAuthStore } from "src/stores/useAuthStore";
import { useMe } from "src/hooks/useMe";
import SpinnerLoading from "src/components/SpinnerLoading";

export default function PrivateRoute({ children }) {
  const { accessToken } = useAuthStore();
  const { isPending, isError } = useMe();

  if (!accessToken) return <Navigate to="/login" replace />;

  if (isPending) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-white to-aloja-navy/5">
        <SpinnerLoading size={100} label="Validando sesión…" />
      </div>
    );
  }

  if (isError) {
    return <Navigate to="/login" replace />;
  }

  return children;
}