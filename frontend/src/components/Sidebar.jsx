import { NavLink } from "react-router-dom";
import logo from "../assets/img/logo_white_alone.png";
import logo_name from "../assets/img/name_white.png";
const Item = ({ to, children }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      `relative flex items-center gap-3 h-10 px-4 text-sm rounded-md transition-colors ${isActive
        ? "text-white bg-white/5"
        : "text-white/80 hover:text-white hover:bg-white/5"
      }`
    }
  >
    {({ isActive }) => (
      <>
        {isActive && (
          <span className="absolute left-0 top-0 h-full w-1.5 bg-aloja-gold rounded-r" />
        )}
        <span>{children}</span>
      </>
    )}
  </NavLink>
);

export default function Sidebar() {
  return (
    <aside className="hidden md:flex md:flex-col md:w-64 bg-aloja-navy text-white p-3 gap-2 overflow-y-auto">
      <div className="flex items-center justify-center h-16 px-2 shrink-0">
        <img src={logo} alt="AlojaSys" className="block h-23 w-auto object-contain" />
        <img src={logo_name} alt="AlojaSys" className="block h-20 w-auto object-contain" />
      </div>
      <nav className="mt-2 flex flex-col gap-1">
        <Item to="/">Dashboard</Item>
        <Item to="/clients">Clientes</Item>
        <Item to="/reservations">Reservas</Item>
        <Item to="/rooms">Habitaciones</Item>
        <Item to="/rates">Tarifas</Item>
        <Item to="/settings">Configuración</Item>
      </nav>
      <div className="mt-auto text-[10px] text-white/50 px-2">v0.1</div>
    </aside>
  );
}


