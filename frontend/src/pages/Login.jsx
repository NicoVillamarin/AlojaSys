import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login as authLogin } from "src/services/auth";
import { showErrorConfirm, showSuccess } from "src/services/toast";
import fondo from "../assets/img/fondo.png";
import fondo2 from "../assets/img/fondo_2.png";
import fondo3 from "../assets/img/fondo_3.png";
import logo from "../assets/img/logo_complet_black.png";
import SpinnerLoading from "src/components/SpinnerLoading";

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);
  

  const onSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await authLogin(form.username, form.password);
      showSuccess("Inicio de sesión correcto");
      navigate("/", { replace: true });
    } catch (err) {
      showErrorConfirm(err?.message || "Credenciales inválidas");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative h-screen w-screen overflow-hidden">
      <img
        src={fondo}
        srcSet={`${fondo} 1280w, ${fondo2} 1920w, ${fondo3} 2560w`}
        sizes="100vw"
        alt="fondo"
        className="absolute inset-0 w-full h-full object-cover object-center select-none pointer-events-none"
        decoding="async"
        loading="eager"
      />

      {/* Overlay en degradado para suavizar el lado izquierdo */}
      <div className="absolute inset-0 bg-gradient-to-r from-white/70 via-white/40 to-transparent backdrop-blur-sm" />

      {/* Card centrada dentro del panel */}
      <div className="absolute inset-y-0 left-0 w-1/2 flex items-center justify-center p-6">
        <div className="w-full max-w-md rounded-2xl bg-white shadow-xl ring-1 ring-black/5 p-8 animate-intro-pop">
          <div className="flex flex-col items-center gap-3 mb-6">
            <img src={logo} alt="AlojaSys" className="h-50 object-contain" />
            <div className="text-center py-3">
              <h1 className="text-xl font-semibold text-aloja-navy">Iniciar Sesión</h1>
              <p className="text-xs text-aloja-gray-800/70">Bienvenido a AlojaSys PMS</p>
            </div>
          </div>
          <form onSubmit={onSubmit} className="space-y-5">
            <input
              className="w-full border rounded-md px-3 py-2 outline-none focus:ring-2 focus:ring-aloja-navy"
              value={form.username}
              onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
              placeholder="Nombre de Usuario"
              autoFocus
            />
            <input
              type="password"
              className="w-full border rounded-md px-3 py-2 outline-none focus:ring-2 focus:ring-aloja-navy"
              value={form.password}
              onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
              placeholder="Contraseña"
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-aloja-navy hover:bg-aloja-navy2 text-white rounded-md py-2 transition"
            >
              {loading ? (
                <span className="inline-flex items-center justify-center gap-2">
                  <SpinnerLoading inline size={18} label={null} />
                  <span>Ingresando…</span>
                </span>
              ) : (
                "Ingresar"
              )}
            </button>
            <div className="text-center">
              <button type="button" className="text-xs text-aloja-navy hover:text-aloja-navy2">¿Olvidaste tu contraseña?</button>
            </div>
          </form>
          <div className="mt-6 text-center text-[11px] text-aloja-gray-800/75">
            AlojaSys PMS – Gestión hotelera unificada
          </div>
        </div>
      </div>

      {/* Marca sutil en el panel derecho */}
      <div className="pointer-events-none absolute bottom-6 right-6 text-white/90 drop-shadow-sm text-xs">
        AlojaSys
      </div>

      {/* Overlay de envío */}
      {loading && (
        <div className="absolute inset-0 bg-white/60 backdrop-blur-[2px] flex items-center justify-center z-10">
          <SpinnerLoading size={96} label="Autenticando…" />
        </div>
      )}
    </div>
  );
}