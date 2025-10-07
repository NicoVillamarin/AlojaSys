import { NavLink, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import logo from "../assets/img/logo_white_alone.png";
import logo_name from "../assets/img/name_white.png";
import { Chevron } from "src/assets/icons/Chevron";
import DashboardIcon from "src/assets/icons/DashboardIcon";
import BellIcon from "src/assets/icons/BellIcon";
import RoomsIcon from "src/assets/icons/RoomsIcon";
import ConfigurateIcon from "src/assets/icons/ConfigurateIcon";
import CurrencyIcon from "src/assets/icons/CurrencyIcon";
import ClientsIcon from "src/assets/icons/ClientsIcon";
import fondo from "src/assets/img/fondo_3.png";
import BitacoraIcon from "src/assets/icons/BitacoraIcon";
import UserIcon from "src/assets/icons/UserIcon";
import ReceptionIcon from "src/assets/icons/ReceptionIcon";

const Item = ({ to, children }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      `relative overflow-hidden flex items-center gap-3 h-10 px-4 text-sm rounded-md transition-colors ${isActive
        ? "text-white"
        : "text-white/80 hover:text-white"
      }`
    }
  >
    {({ isActive }) => (
      <>
        {/* Highlight de fondo con efecto barrido */}
        <span
          aria-hidden
          className={`pointer-events-none absolute left-0 top-0 h-full bg-white/5 rounded-md transition-[width] duration-250 ease-out ${isActive ? 'w-full' : 'w-0'}`}
          style={{ zIndex: 0 }}
        />
        {/* Barra dorada fija a la izquierda */}
        {isActive && (
          <span className="absolute left-0 top-0 h-full w-1.5 bg-aloja-gold rounded-r" />
        )}
        <span className="inline-flex items-center gap-2" style={{ zIndex: 1 }}>{children}</span>
      </>
    )}
  </NavLink>
);



export default function Sidebar({ isCollapsed, isMini, onToggleCollapse, onToggleMini, onResetWidth, onForceOpen }) {
  const { t } = useTranslation();
  const location = useLocation();
  const [openGroups, setOpenGroups] = useState({ settings: false, locations: false });
  useEffect(() => {
    const isSettings = location.pathname.startsWith("/settings");
    const isLocations = location.pathname.startsWith("/settings/locations");
    setOpenGroups((s) => ({ ...s, settings: isSettings, locations: isLocations }));
  }, [location.pathname]);
  const toggleGroup = (key) => setOpenGroups((s) => ({ ...s, [key]: !s[key] }));
  return (
    <aside className="flex flex-col bg-aloja-navy text-white p-3 gap-2 overflow-y-auto no-scrollbar h-screen w-full relative">
      {/* Fondo decorativo sutil como background fijo */}
      <div
        aria-hidden
        className="pointer-events-none select-none absolute inset-0 opacity-[0.1] bg-contain bg-no-repeat bg-left-bottom bg-fixed"
        style={{
          backgroundImage: `linear-gradient(135deg, rgba(212,175,55,0.14), rgba(0,0,0,0)), url(${fondo})`,
        }}
      />
      <div className="flex items-center justify-center h-16 px-2 shrink-0">
        <div className="flex items-center gap-2">
          <img src={logo} alt="AlojaSys" className="block h-23 w-auto object-contain" />
          {!isMini && <img src={logo_name} alt="AlojaSys" className="block h-20 w-auto object-contain" />}
        </div>
      </div>
      <nav className="mt-2 flex flex-col gap-1">
        <Item to="/"><DashboardIcon size="20" /> {!isMini && <span>{t('sidebar.dashboard')}</span>}</Item>
        <Item to="/reception"><ReceptionIcon size="20" /> {!isMini && <span>{t('sidebar.reception')}</span>}</Item>
        <Item to="/reservations-gestion"><BellIcon size="20" /> {!isMini && <span>{t('sidebar.reservations_management')}</span>}</Item>
        <Item to="/rooms-gestion"><RoomsIcon size="20" /> {!isMini && <span>{t('sidebar.rooms_management')}</span>}</Item>
        {/* Link genérico: si querés, reemplazar por un link contextual desde el detalle de una reserva */}
        <Item to="/reservations/1/history"><BitacoraIcon size="20" /> {!isMini && <span>{t('sidebar.reservations_history')}</span>}</Item>
        {/*<Item to="/clients"><ClientsIcon size="20" /> {!isMini && <span>Clientes</span>}</Item>*/}
        {/*<Item to="/rates"><CurrencyIcon size="20" /> {!isMini && <span>Gestión de Tarifas</span>}</Item>*/}
        {!isMini && (
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
                <ConfigurateIcon size="20" />
                <span>{t('sidebar.configuration')}</span>
              </span>
              <Chevron open={openGroups.settings} />
            </button>
          <div
            className={`mt-1 ml-4 flex flex-col gap-1 overflow-hidden transition-[max-height,opacity] duration-200 ${
              openGroups.settings ? "max-h-[1200px] opacity-100" : "max-h-0 opacity-0"
            }`}
          >
            <Item to="/settings/enterprises">{t('sidebar.enterprises')}</Item>
            <Item to="/settings/rooms">{t('sidebar.rooms')}</Item>
            <Item to="/settings/hotels">{t('sidebar.hotels')}</Item>
            <Item to="/settings/users">{t('sidebar.users')}</Item>
            <div className="mt-1 ml-2">
              <button
                type="button"
                onClick={() => toggleGroup("locations")}
                className={`w-full flex items-center justify-between h-9 px-3 text-sm rounded-md transition-colors ${
                  openGroups.locations ? "text-white bg-white/5" : "text-white/80 hover:text-white hover:bg-white/5"
                }`}
                aria-expanded={openGroups.locations}
              >
                <span>{t('sidebar.locations')}</span>
                <Chevron open={openGroups.locations} />
              </button>
              <div
                className={`mt-1 ml-4 flex flex-col gap-1 overflow-hidden transition-all duration-200 ${
                  openGroups.locations ? "max-h-48 opacity-100" : "max-h-0 opacity-0"
                }`}
              >
                <Item to="/settings/locations/countries">{t('sidebar.countries')}</Item>
                <Item to="/settings/locations/states">{t('sidebar.states')}</Item>
                <Item to="/settings/locations/cities">{t('sidebar.cities')}</Item>
              </div>
            </div>
            <div className="mt-1 ml-2">
              <button
                type="button"
                onClick={() => toggleGroup("rates")}
                className={`w-full flex items-center justify-between h-9 px-3 text-sm rounded-md transition-colors ${
                  openGroups.rates ? "text-white bg-white/5" : "text-white/80 hover:text-white hover:bg-white/5"
                }`}
                aria-expanded={openGroups.rates}
              >
                <span>{t('sidebar.rates')}</span>
                <Chevron open={openGroups.rates} />
              </button>
              <div
                className={`mt-1 ml-4 flex flex-col gap-1 overflow-hidden transition-all duration-200 ${
                  openGroups.rates ? "max-h-48 opacity-100" : "max-h-0 opacity-0"
                }`}
              >
                <Item to="/settings/rates/plans">{t('sidebar.rate_plans')}</Item>
                <Item to="/settings/rates/rules">{t('sidebar.rate_rules')}</Item>
                <Item to="/settings/rates/promos">{t('sidebar.promotions')}</Item>
                <Item to="/settings/rates/taxes">{t('sidebar.taxes')}</Item>
              </div>
            </div>
            {/** futuros submenús: tarifas, impuestos, usuarios, etc. */}
          </div>
          </div>
        )}
      </nav>
      
      {!isMini && (
        <div className="mt-auto text-[10px] text-white/50 px-2">v0.1</div>
      )}
      
    </aside>
  );
}


