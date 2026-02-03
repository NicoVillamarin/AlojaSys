import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login as authLogin } from "src/services/auth";
import { showErrorConfirm, showSuccess } from "src/services/toast";
import fondo from "../assets/img/fondo.png";
import fondo2 from "../assets/img/fondo_2.png";
import fondo3 from "../assets/img/fondo_3.png";
import logo from "../assets/img/logo_complet_black_tranparent_2.png";
import SpinnerLoading from "src/components/SpinnerLoading";
import EyeIcon from "../assets/icons/EyeIcon";
import EyeSlashIcon from "../assets/icons/EyeSlashIcon";

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  

  const onSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await authLogin(form.username, form.password);
      showSuccess("Inicio de sesión correcto");
      // Invalidar caché de React Query para forzar recarga de datos del usuario
      // Esto se hace automáticamente con staleTime: 0 en useMe
      navigate("/", { replace: true });
    } catch (err) {
      showErrorConfirm(err?.message || "Credenciales inválidas");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full overflow-hidden flex flex-col md:flex-row" dir="ltr">
      <img
        src={fondo}
        srcSet={`${fondo} 1280w, ${fondo2} 1920w, ${fondo3} 2560w`}
        sizes="100vw"
        alt="fondo"
        className="absolute inset-0 w-full h-full object-cover object-center select-none pointer-events-none"
        decoding="async"
        loading="eager"
      />

      {/* Overlay: degradado suave con toque de marca */}
      <div className="absolute inset-0 bg-gradient-to-r from-white/80 via-white/50 to-transparent backdrop-blur-md" />

      {/* Panel del formulario: siempre a la IZQUIERDA (order-1 en desktop) */}
      <div className="relative z-[1] w-full flex items-center justify-center py-8 px-4 sm:px-6 md:pl-8 md:pr-6 md:w-[45%] md:max-w-[520px] md:min-w-[380px] md:justify-center md:py-0 md:min-h-screen md:order-1">
        <div className="w-full max-w-[400px] min-w-0 rounded-2xl bg-white/95 backdrop-blur-xl shadow-2xl shadow-aloja-navy/10 border border-white/80 overflow-hidden animate-intro-pop">
          {/* Línea de acento superior (marca) */}
          <div className="h-1 w-full bg-gradient-to-r from-aloja-gold via-aloja-gold2 to-aloja-gold" />

          <div className="p-6 sm:p-8">
            {/* Logo solo en responsive (móvil/tablet); en desktop está a la derecha */}
            <div className="flex flex-col items-center gap-3 mb-6 login-stagger-0 md:hidden">
              <div className="rounded-xl bg-aloja-gray-50/80 p-3 ring-1 ring-aloja-navy/5">
                <img src={logo} alt="AlojaSys" className="h-11 sm:h-14 w-auto object-contain select-none" />
              </div>
            </div>
            <div className="text-center pb-2 pt-0 md:pt-2 login-stagger-1">
              <h1 className="text-lg sm:text-xl font-bold text-aloja-navy tracking-tight">Iniciar Sesión</h1>
              <p className="text-xs text-aloja-gray-800/70 mt-0.5">Bienvenido a AlojaSys PMS</p>
            </div>

            <form onSubmit={onSubmit} className="space-y-4 sm:space-y-5">
              <div className="login-stagger-2">
                <input
                  className="w-full bg-gray-50/80 border border-gray-200/80 rounded-xl px-4 py-3 text-sm sm:text-base outline-none transition-all duration-200 placeholder:text-gray-400 focus:bg-white focus:border-aloja-navy focus:ring-2 focus:ring-aloja-navy/20 hover:border-gray-300"
                  value={form.username}
                  onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                  placeholder="Nombre de Usuario"
                  autoFocus
                />
              </div>
              <div className="relative login-stagger-3">
                <input
                  type={showPassword ? "text" : "password"}
                  className="w-full bg-gray-50/80 border border-gray-200/80 rounded-xl px-4 py-3 pr-11 text-sm sm:text-base outline-none transition-all duration-200 placeholder:text-gray-400 focus:bg-white focus:border-aloja-navy focus:ring-2 focus:ring-aloja-navy/20 hover:border-gray-300"
                  value={form.password}
                  onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                  placeholder="Contraseña"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-aloja-gray-800/60 hover:text-aloja-navy hover:bg-aloja-navy/5 transition-all duration-200 active:scale-95"
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                >
                  <div className="relative w-5 h-5">
                    <div
                      className={`absolute inset-0 transition-all duration-300 ${
                        showPassword
                          ? "opacity-0 rotate-90 scale-0"
                          : "opacity-100 rotate-0 scale-100"
                      }`}
                    >
                      <EyeIcon size="20" />
                    </div>
                    <div
                      className={`absolute inset-0 transition-all duration-300 ${
                        showPassword
                          ? "opacity-100 rotate-0 scale-100"
                          : "opacity-0 -rotate-90 scale-0"
                      }`}
                    >
                      <EyeSlashIcon size="20" />
                    </div>
                  </div>
                </button>
              </div>
              <div className="login-stagger-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-aloja-navy hover:bg-aloja-navy2 text-white rounded-xl py-3 text-sm font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-aloja-navy/40 focus:ring-offset-2 hover:shadow-lg hover:shadow-aloja-navy/25 hover:-translate-y-0.5 active:translate-y-0 disabled:hover:translate-y-0 disabled:hover:shadow-none"
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
                <div className="text-center mt-4">
                  <button type="button" className="text-xs text-aloja-navy/90 hover:text-aloja-navy font-medium underline-offset-2 hover:underline transition-colors">
                    ¿Olvidaste tu contraseña?
                  </button>
                </div>
              </div>
            </form>

            <div className="mt-6 pt-5 border-t border-gray-100 text-center text-[11px] text-aloja-gray-800/60 login-stagger-4">
              AlojaSys PMS – Gestión hotelera unificada
            </div>
          </div>
        </div>
      </div>

      {/* Panel del logo: siempre a la DERECHA en desktop (order-2) */}
      <div className="relative z-[1] hidden md:flex md:flex-1 md:items-center md:justify-center md:min-h-screen md:order-2">
        <div className="logo-login-wrapper">
          <img src={logo} alt="AlojaSys" className="logo-login-power h-32 lg:h-40 xl:h-44 w-auto object-contain select-none animate-intro-pop" />
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