import { NavLink, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import logo from "../assets/img/logo_white_alone.png";
import logo_name from "../assets/img/name_white.png";
import { Chevron } from "src/assets/icons/Chevron";

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
  const location = useLocation();
  const [openGroups, setOpenGroups] = useState({ settings: false, locations: false });
  useEffect(() => {
    const isSettings = location.pathname.startsWith("/settings");
    const isLocations = location.pathname.startsWith("/settings/locations");
    setOpenGroups((s) => ({ ...s, settings: isSettings, locations: isLocations }));
  }, [location.pathname]);
  const toggleGroup = (key) => setOpenGroups((s) => ({ ...s, [key]: !s[key] }));
  return (
    <aside className="hidden md:flex md:flex-col md:w-64 bg-aloja-navy text-white p-3 gap-2 overflow-y-auto">
      <div className="flex items-center justify-center h-16 px-2 shrink-0">
        <img src={logo} alt="AlojaSys" className="block h-23 w-auto object-contain" />
        <img src={logo_name} alt="AlojaSys" className="block h-20 w-auto object-contain" />
      </div>
      <nav className="mt-2 flex flex-col gap-1">
        <Item to="/">Dashboard</Item>
        <Item to="/clients">Clientes</Item>
        <Item to="/reservations">Gestión de Reservas</Item>
        <Item to="/rooms-gestion">Gestión de Habitaciones</Item>
        <Item to="/rates">Gestión de Tarifas</Item>
        <div className="mt-1">
          <button
            type="button"
            onClick={() => toggleGroup("settings")}
            className={`w-full flex items-center justify-between h-10 px-4 text-sm rounded-md transition-colors ${
              openGroups.settings ? "text-white bg-white/5" : "text-white/80 hover:text-white hover:bg-white/5"
            }`}
            aria-expanded={openGroups.settings}
          >
            <span className="inline-flex items-center gap-2">
              <span>Configuración</span>
            </span>
            <Chevron open={openGroups.settings} />
          </button>
          <div
            className={`mt-1 ml-4 flex flex-col gap-1 overflow-hidden transition-all duration-200 ${
              openGroups.settings ? "max-h-96 opacity-100" : "max-h-0 opacity-0"
            }`}
          >
            <Item to="/settings/rooms">Habitaciones</Item>
            <Item to="/settings/hotels">Hoteles</Item>
            <div className="mt-1 ml-2">
              <button
                type="button"
                onClick={() => toggleGroup("locations")}
                className={`w-full flex items-center justify-between h-9 px-3 text-sm rounded-md transition-colors ${
                  openGroups.locations ? "text-white bg-white/5" : "text-white/80 hover:text-white hover:bg-white/5"
                }`}
                aria-expanded={openGroups.locations}
              >
                <span>Locaciones</span>
                <Chevron open={openGroups.locations} />
              </button>
              <div
                className={`mt-1 ml-4 flex flex-col gap-1 overflow-hidden transition-all duration-200 ${
                  openGroups.locations ? "max-h-48 opacity-100" : "max-h-0 opacity-0"
                }`}
              >
                <Item to="/settings/locations/countries">Países</Item>
                <Item to="/settings/locations/states">Provincias</Item>
                <Item to="/settings/locations/cities">Ciudades</Item>
              </div>
            </div>
            {/** futuros submenús: tarifas, impuestos, usuarios, etc. */}
          </div>
        </div>
      </nav>
      <div className="mt-auto text-[10px] text-white/50 px-2">v0.1</div>
    </aside>
  );
}


