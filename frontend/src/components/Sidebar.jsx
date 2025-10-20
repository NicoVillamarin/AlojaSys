import { NavLink, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import logo from "../assets/img/logo_new_alone_white.png";
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
import CardCreditIcon from "src/assets/icons/CardCreditIcon";
import UserIcon from "src/assets/icons/UserIcon";
import ReceptionIcon from "src/assets/icons/ReceptionIcon";
import CalendarIcon from "src/assets/icons/CalendarIcon";

const Item = ({ to, children, onMobileClose, isMobile, exact = false }) => (
  <NavLink
    to={to}
    end={exact}
    onClick={() => {
      if (isMobile && onMobileClose) {
        onMobileClose();
      }
    }}
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



export default function Sidebar({ isCollapsed, isMini, onToggleCollapse, onToggleMini, onResetWidth, onForceOpen, isMobile = false, onMobileClose }) {
  const { t } = useTranslation();
  const location = useLocation();
  const [openGroups, setOpenGroups] = useState({ settings: false, locations: false, financial: false, histories: false });
  useEffect(() => {
    const isSettings = location.pathname.startsWith("/settings");
    const isLocations = location.pathname.startsWith("/settings/locations");
    const isFinancial = location.pathname === "/refunds" || location.pathname.startsWith("/payments") || location.pathname === "/vouchers";
    const isHistories = location.pathname.startsWith("/reservations/") && location.pathname.includes("/history") || 
                       location.pathname === "/payments" || 
                       location.pathname === "/refunds/history";
    setOpenGroups((s) => ({ ...s, settings: isSettings, locations: isLocations, financial: isFinancial, histories: isHistories }));
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

      {/* Botón de cerrar para móvil */}
      {isMobile && (
        <div className="flex justify-end mb-2">
          <button
            onClick={onToggleCollapse}
            className="p-2 rounded-md text-white/80 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Cerrar menú"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      <div className="flex items-center justify-center h-auto px-2 shrink-0">
        <div className="flex flex-col items-center">
          <img src={logo} alt="AlojaSys" className="block h-15 w-auto object-contain" />
          {!isMini && <img src={logo_name} alt="AlojaSys" className="block h-5 w-auto object-contain" />}
        </div>
      </div>
      <nav className="mt-2 flex flex-col gap-1">
        <Item to="/" onMobileClose={onMobileClose} isMobile={isMobile}><DashboardIcon size="20" /> {!isMini && <span>{t('sidebar.dashboard')}</span>}</Item>
        <Item to="/reception" onMobileClose={onMobileClose} isMobile={isMobile}><ReceptionIcon size="20" /> {!isMini && <span>{t('sidebar.reception')}</span>}</Item>
        <Item to="/reservations-gestion" onMobileClose={onMobileClose} isMobile={isMobile}><BellIcon size="20" /> {!isMini && <span>{t('sidebar.reservations_management')}</span>}</Item>
        <Item to="/reservations-calendar" onMobileClose={onMobileClose} isMobile={isMobile}><CalendarIcon size="20" /> {!isMini && <span>Calendario de Reservas</span>}</Item>
        <Item to="/rooms-gestion" onMobileClose={onMobileClose} isMobile={isMobile}><RoomsIcon size="20" /> {!isMini && <span>{t('sidebar.rooms_management')}</span>}</Item>
       
        {!isMini && (
          <div className="mt-1">
            <button
              type="button"
              onClick={() => toggleGroup("histories")}
              className={`w-full flex items-center justify-between h-10 px-4 text-sm rounded-md transition-colors ${openGroups.histories ? "text-white bg-white/5" : "text-white/80 hover:text-white hover:bg-white/5"
                }`}
              aria-expanded={openGroups.histories}
            >
              <span className="inline-flex items-center gap-2">
                <BitacoraIcon size="20" />
                <span>{t('sidebar.histories')}</span>
              </span>
              <Chevron open={openGroups.histories} />
            </button>
            <div
              className={`mt-1 ml-4 flex flex-col gap-1 overflow-hidden transition-[max-height,opacity] duration-200 ${openGroups.histories ? "max-h-48 opacity-100" : "max-h-0 opacity-0"
                }`}
            >
              <Item to="/reservations/1/history" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.reservations_history')}</Item>
              <Item to="/payments" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.payments')}</Item>
              <Item to="/refunds/history" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.refunds_history')}</Item>
            </div>
          </div>
        )}
        {!isMini && (
          <div className="mt-1">
            <button
              type="button"
              onClick={() => toggleGroup("financial")}
              className={`w-full flex items-center justify-between h-10 px-4 text-sm rounded-md transition-colors ${openGroups.financial ? "text-white bg-white/5" : "text-white/80 hover:text-white hover:bg-white/5"
                }`}
              aria-expanded={openGroups.financial}
            >
              <span className="inline-flex items-center gap-2">
                <CurrencyIcon size="20" />
                <span>{t('sidebar.financial')}</span>
              </span>
              <Chevron open={openGroups.financial} />
            </button>
            <div
              className={`mt-1 ml-4 flex flex-col gap-1 overflow-hidden transition-[max-height,opacity] duration-200 ${openGroups.financial ? "max-h-48 opacity-100" : "max-h-0 opacity-0"
                }`}
            >
              <Item to="/refunds" onMobileClose={onMobileClose} isMobile={isMobile} exact={true}>{t('sidebar.refunds')}</Item>
              <Item to="/vouchers" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.vouchers')}</Item>
            </div>
          </div>
        )}

        {/* Link genérico: si querés, reemplazar por un link contextual desde el detalle de una reserva */}
        {/*<Item to="/clients"><ClientsIcon size="20" /> {!isMini && <span>Clientes</span>}</Item>*/}
        {/*<Item to="/rates"><CurrencyIcon size="20" /> {!isMini && <span>Gestión de Tarifas</span>}</Item>*/}
        {!isMini && (
          <div className="mt-1">
            <button
              type="button"
              onClick={() => toggleGroup("settings")}
              className={`w-full flex items-center justify-between h-10 px-4 text-sm rounded-md transition-colors ${openGroups.settings ? "text-white bg-white/5" : "text-white/80 hover:text-white hover:bg-white/5"
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
              className={`mt-1 ml-4 flex flex-col gap-1 overflow-hidden transition-[max-height,opacity] duration-200 ${openGroups.settings ? "max-h-[1200px] opacity-100" : "max-h-0 opacity-0"
                }`}
            >
              <Item to="/settings/enterprises" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.enterprises')}</Item>
              <Item to="/settings/rooms" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.rooms')}</Item>
              <Item to="/settings/hotels" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.hotels')}</Item>
              <Item to="/settings/users" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.users')}</Item>
              <div className="mt-1 ml-2">
                <button
                  type="button"
                  onClick={() => toggleGroup("locations")}
                  className={`w-full flex items-center justify-between h-9 px-3 text-sm rounded-md transition-colors ${openGroups.locations ? "text-white bg-white/5" : "text-white/80 hover:text-white hover:bg-white/5"
                    }`}
                  aria-expanded={openGroups.locations}
                >
                  <span>{t('sidebar.locations')}</span>
                  <Chevron open={openGroups.locations} />
                </button>
                <div
                  className={`mt-1 ml-4 flex flex-col gap-1 overflow-hidden transition-all duration-200 ${openGroups.locations ? "max-h-48 opacity-100" : "max-h-0 opacity-0"
                    }`}
                >
                  <Item to="/settings/locations/countries" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.countries')}</Item>
                  <Item to="/settings/locations/states" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.states')}</Item>
                  <Item to="/settings/locations/cities" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.cities')}</Item>
                </div>
              </div>
              <div className="mt-1 ml-2">
                <button
                  type="button"
                  onClick={() => toggleGroup("rates")}
                  className={`w-full flex items-center justify-between h-9 px-3 text-sm rounded-md transition-colors ${openGroups.rates ? "text-white bg-white/5" : "text-white/80 hover:text-white hover:bg-white/5"
                    }`}
                  aria-expanded={openGroups.rates}
                >
                  <span>{t('sidebar.rates')}</span>
                  <Chevron open={openGroups.rates} />
                </button>
                <div
                  className={`mt-1 ml-4 flex flex-col gap-1 overflow-hidden transition-all duration-200 ${openGroups.rates ? "max-h-48 opacity-100" : "max-h-0 opacity-0"
                    }`}
                >
                  <Item to="/settings/rates/plans" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.rate_plans')}</Item>
                  <Item to="/settings/rates/rules" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.rate_rules')}</Item>
                  <Item to="/settings/rates/promos" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.promotions')}</Item>
                  <Item to="/settings/rates/taxes" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.taxes')}</Item>
                </div>
              </div>
              <div className="mt-1 ml-2">
                <button
                  type="button"
                  onClick={() => toggleGroup("policies")}
                  className={`w-full flex items-center justify-between h-9 px-3 text-sm rounded-md transition-colors ${openGroups.policies ? "text-white bg-white/5" : "text-white/80 hover:text-white hover:bg-white/5"
                    }`}
                  aria-expanded={openGroups.policies}
                >
                  <span>{t('sidebar.policies')}</span>
                  <Chevron open={openGroups.policies} />
                </button>
                <div
                  className={`mt-1 ml-4 flex flex-col gap-1 overflow-hidden transition-all duration-200 ${openGroups.policies ? "max-h-48 opacity-100" : "max-h-0 opacity-0"
                    }`}
                >
                  <Item to="/settings/payments/policies" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.payment_policies')}</Item>
                  <Item to="/settings/policies/cancellation" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.cancellation_policies')}</Item>
                  <Item to="/settings/policies/devolution" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.devolution_policies')}</Item>
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


