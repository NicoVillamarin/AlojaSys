import { NavLink, useLocation } from "react-router-dom";
import { useState, useEffect, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { usePermissions, useHasAnyPermission } from "src/hooks/usePermissions";
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
import ReconciliationIcon from "src/assets/icons/ReconciliationIcon";
import ChannelsIcon from "src/assets/icons/ChannelsIcon";
import { useMe } from "src/hooks/useMe";
import CleaningIcon from "src/assets/icons/CleaningIcon";

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
  const [openGroups, setOpenGroups] = useState({ settings: false, locations: false, financial: false, histories: false, invoicing: false, rates: false, policies: false, housekeeping: false });
  const {data: me } = useMe();
  const isSuperuser = me?.is_superuser || false;
  
  // Permisos para el menú principal
  const hasViewDashboard = usePermissions("dashboard.view_dashboardmetrics");
  const hasViewReservations = usePermissions("reservations.view_reservation");
  const hasAddReservations = usePermissions("reservations.add_reservation");
  const hasReception = useHasAnyPermission(["reservations.view_reservation", "reservations.add_reservation", "reservations.change_reservation"]);
  const hasViewCalendar = usePermissions("calendar.view_calendarview");
  const hasViewRooms = usePermissions("rooms.view_room");
  const hasViewOTAs = usePermissions("otas.view_otaconfig");
  
  // Permisos para Histories
  const hasViewReservationsHistory = usePermissions("reservations.view_reservation");
  const hasViewPayments = usePermissions("payments.view_payment");
  const hasViewRefunds = usePermissions("payments.view_refund");
  const hasAnyHistory = useHasAnyPermission(["reservations.view_reservation", "payments.view_payment", "payments.view_refund"]);
  
  // Permisos para Financial
  const hasViewRefundsMenu = usePermissions("payments.view_refund");
  const hasViewVouchers = usePermissions("payments.view_refundvoucher");
  const hasViewInvoices = usePermissions("invoicing.view_invoice");
  const hasViewReceipts = usePermissions("invoicing.view_receipt");
  const hasViewInvoicing = useHasAnyPermission(["invoicing.view_invoice", "invoicing.view_receipt"]);
  const hasViewBankReconciliation = usePermissions("payments.view_bankreconciliation");
  const hasAnyFinancial = useHasAnyPermission(["payments.view_refund", "payments.view_refundvoucher", "invoicing.view_invoice", "invoicing.view_receipt", "payments.view_bankreconciliation"]);
  
  // Permisos para Configuration
  const hasViewEnterprises = usePermissions("enterprises.view_enterprise");
  const hasViewOTAsConfig = usePermissions("otas.view_otaconfig");
  const hasViewRoomsConfig = usePermissions("rooms.view_room");
  const hasViewHotels = usePermissions("core.view_hotel");
  const hasViewUsers = usePermissions("users.view_userprofile");
  const hasViewRoles = usePermissions("auth.view_group");
  
  // Permisos para Locations
  const hasViewCountries = usePermissions("locations.view_country");
  const hasViewStates = usePermissions("locations.view_state");
  const hasViewCities = usePermissions("locations.view_city");
  const hasAnyLocation = useHasAnyPermission(["locations.view_country", "locations.view_state", "locations.view_city"]);
  
  // Permisos para Rates
  const hasViewRatePlans = usePermissions("rates.view_rateplan");
  const hasViewRateRules = usePermissions("rates.view_raterule");
  const hasViewPromos = usePermissions("rates.view_promorule");
  const hasViewTaxes = usePermissions("rates.view_taxrule");
  const hasAnyRate = useHasAnyPermission(["rates.view_rateplan", "rates.view_raterule", "rates.view_promorule", "rates.view_taxrule"]);
  
  // Permisos para Policies
  const hasViewPaymentPolicies = usePermissions("payments.view_paymentpolicy");
  const hasViewCancellationPolicies = usePermissions("payments.view_cancellationpolicy");
  const hasViewRefundPolicies = usePermissions("payments.view_refundpolicy");
  const hasAnyPolicy = useHasAnyPermission(["payments.view_paymentpolicy", "payments.view_cancellationpolicy", "payments.view_refundpolicy"]);
  const hasViewHousekeeping = usePermissions("housekeeping.access_housekeeping");
  
  // Verificar si tiene permisos para acceder a configuraciones de housekeeping
  const hasHousekeepingConfig = useHasAnyPermission([
    "housekeeping.view_tasktemplate",
    "housekeeping.add_tasktemplate",
    "housekeeping.view_checklist",
    "housekeeping.add_checklist",
    "housekeeping.view_cleaningzone",
    "housekeeping.add_cleaningzone",
    "housekeeping.view_cleaningstaff",
    "housekeeping.add_cleaningstaff",
    "housekeeping.view_housekeepingconfig",
    "housekeeping.change_housekeepingconfig",
  ]);
  
  // Verificar si tiene algún permiso de configuración
  const hasAnySettings = useHasAnyPermission([
    "enterprises.view_enterprise",
    "otas.view_otaconfig",
    "rooms.view_room",
    "core.view_hotel",
    "users.view_userprofile",
    "auth.view_group",
    "locations.view_country",
    "locations.view_state",
    "locations.view_city",
    "rates.view_rateplan",
    "rates.view_raterule",
    "rates.view_promorule",
    "rates.view_taxrule",
    "payments.view_paymentpolicy",
    "payments.view_cancellationpolicy",
    "payments.view_refundpolicy"
  ]);
  
  // Verificar si es solo personal de limpieza (sin otros permisos importantes)
  const isOnlyHousekeepingStaff = useMemo(() => {
    if (!me || !me.profile) return false;
    const isHKStaff = me.profile.is_housekeeping_staff === true;
    if (!isHKStaff) return false;
    
    // Si es personal de limpieza, verificar si tiene otros permisos importantes
    const hasOtherPermissions = 
      hasViewDashboard || 
      hasReception || 
      hasViewReservations || 
      hasViewCalendar || 
      hasViewRooms || 
      hasViewOTAs ||
      hasAnyHistory ||
      hasAnyFinancial ||
      hasAnySettings;
    
    // Si es personal de limpieza pero NO tiene otros permisos, es "solo" personal de limpieza
    return !hasOtherPermissions;
  }, [me, hasViewDashboard, hasReception, hasViewReservations, hasViewCalendar, hasViewRooms, hasViewOTAs, hasAnyHistory, hasAnyFinancial, hasAnySettings]);
  
  useEffect(() => {
    const isSettings = location.pathname.startsWith("/settings");
    const isLocations = location.pathname.startsWith("/settings/locations");
    const isHousekeeping = location.pathname.startsWith("/settings/housekeeping");
    // Excluir /payments de isFinancial ya que pertenece a Histories
    const isFinancial = location.pathname === "/refunds" || 
                       (location.pathname.startsWith("/payments") && location.pathname !== "/payments") || 
                       location.pathname === "/vouchers" || 
                       location.pathname === "/bank-reconciliation" || 
                       location.pathname.startsWith("/invoicing");
    const isHistories = location.pathname.startsWith("/reservations/") && location.pathname.includes("/history") || 
                       location.pathname === "/payments" || 
                       location.pathname === "/refunds/history";
    const isInvoicing = location.pathname.startsWith("/invoicing");
    setOpenGroups((s) => ({ ...s, settings: isSettings, locations: isLocations, housekeeping: isHousekeeping, financial: isFinancial, histories: isHistories, invoicing: isInvoicing }));
  }, [location.pathname]);
  const toggleGroup = (key) => setOpenGroups((s) => ({ ...s, [key]: !s[key] }));
  return (
    <aside
      className="flex flex-col bg-aloja-navy text-white h-screen w-full relative"
      style={{
        // Fondo solo con imagen, sin tinte azul
        backgroundImage: `url(${fondo})`,
        backgroundSize: 'cover',
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'left bottom',
      }}
    >
      {/* Capa de blur y sombreado suave sobre TODO el sidebar */}
      <div
        aria-hidden
        className="pointer-events-none select-none absolute inset-0"
        style={{
          backdropFilter: 'blur(3px)',
          backgroundColor: 'rgba(6,24,48,0.45)',
          zIndex: 0,
        }}
      />

      {/* Contenido scrolleable por encima del blur */}
      <div className="flex flex-col p-3 gap-2 overflow-y-auto no-scrollbar h-full relative" style={{ zIndex: 1 }}>

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
      {/* Menú principal */}
      <nav className="mt-3 flex flex-col gap-1">
        {/* Si es solo personal de limpieza, mostrar solo housekeeping */}
        {isOnlyHousekeepingStaff ? (
          <Item to="/housekeeping" onMobileClose={onMobileClose} isMobile={isMobile} exact={true}>
            <CleaningIcon size="20" /> {!isMini && <span>{t('sidebar.housekeeping')}</span>}
          </Item>
        ) : (
          <>
            {hasViewDashboard && (
              <Item to="/" onMobileClose={onMobileClose} isMobile={isMobile}><DashboardIcon size="20" /> {!isMini && <span>{t('sidebar.dashboard')}</span>}</Item>
            )}
            {hasReception && (
              <Item to="/reception" onMobileClose={onMobileClose} isMobile={isMobile}><ReceptionIcon size="20" /> {!isMini && <span>{t('sidebar.reception')}</span>}</Item>
            )}
            {hasViewReservations && (
              <Item to="/reservations-gestion" onMobileClose={onMobileClose} isMobile={isMobile}><BellIcon size="20" /> {!isMini && <span>{t('sidebar.reservations_management')}</span>}</Item>
            )}
            {hasViewCalendar && (
              <Item to="/reservations-calendar" onMobileClose={onMobileClose} isMobile={isMobile}><CalendarIcon size="20" /> {!isMini && <span>Calendario de Reservas</span>}</Item>
            )}
            {hasViewHousekeeping && (
              <Item to="/housekeeping" onMobileClose={onMobileClose} isMobile={isMobile} exact={true}>
                <CleaningIcon size="20" /> {!isMini && <span>{t('sidebar.housekeeping')}</span>}
              </Item>
            )}
            {hasViewRooms && (
              <Item to="/rooms-gestion" onMobileClose={onMobileClose} isMobile={isMobile}><RoomsIcon size="20" /> {!isMini && <span>{t('sidebar.rooms_management')}</span>}</Item>
            )}
            {hasViewOTAs && (
              <Item to="/otas" onMobileClose={onMobileClose} isMobile={isMobile}><ChannelsIcon size="20" /> {!isMini && <span>{t('sidebar.channels')}</span>}</Item>
            )}
          </>
        )}
        {!isOnlyHousekeepingStaff && !isMini && hasAnyHistory && (
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
              {hasViewReservationsHistory && (
                <Item to="/reservations/1/history" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.reservations_history')}</Item>
              )}
              {hasViewPayments && (
                <Item to="/payments" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.payments')}</Item>
              )}
              {hasViewRefunds && (
                <Item to="/refunds/history" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.refunds_history')}</Item>
              )}
              {hasViewHousekeeping && (
                <Item to="/housekeeping/historical" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.housekeeping_historical')}</Item>
              )}
            </div>
          </div>
        )}
        {!isOnlyHousekeepingStaff && !isMini && hasAnyFinancial && (
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
              className={`mt-1 ml-4 flex flex-col gap-1 overflow-hidden transition-[max-height,opacity] duration-200 ${openGroups.financial ? "max-h-[1200px] opacity-100" : "max-h-0 opacity-0"
                }`}
            >
              {hasViewRefundsMenu && (
                <Item to="/refunds" onMobileClose={onMobileClose} isMobile={isMobile} exact={true}>{t('sidebar.refunds')}</Item>
              )}
              {hasViewVouchers && (
                <Item to="/vouchers" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.vouchers')}</Item>
              )}
              {hasViewInvoicing && (
                <div className="mt-1 ml-2">
                  <button
                    type="button"
                    onClick={() => toggleGroup("invoicing")}
                    className={`w-full flex items-center justify-between h-9 px-3 text-sm rounded-md transition-colors ${openGroups.invoicing ? "text-white bg-white/5" : "text-white/80 hover:text-white hover:bg-white/5"
                      }`}
                    aria-expanded={openGroups.invoicing}
                  >
                    <span>{t('sidebar.invoicing')}</span>
                    <Chevron open={openGroups.invoicing} />
                  </button>
                  <div
                    className={`mt-1 ml-4 flex flex-col gap-1 overflow-hidden transition-all duration-200 ${openGroups.invoicing ? "max-h-48 opacity-100" : "max-h-0 opacity-0"
                      }`}
                  >
                    {hasViewInvoices && (
                      <Item to="/invoicing" onMobileClose={onMobileClose} isMobile={isMobile} exact={true}>{t('sidebar.invoicing_electronic')}</Item>
                    )}
                    {hasViewReceipts && (
                      <Item to="/invoicing/receipts" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.invoicing_receipts')}</Item>
                    )}
                  </div>
                </div>
              )}
              {hasViewBankReconciliation && (
                <Item to="/bank-reconciliation" onMobileClose={onMobileClose} isMobile={isMobile}>{!isMini && <span>{t('sidebar.bank_reconciliation')}</span>}</Item>
              )}
            </div>
          </div>
        )}

        {/* Link genérico: si querés, reemplazar por un link contextual desde el detalle de una reserva */}
        {/*<Item to="/clients"><ClientsIcon size="20" /> {!isMini && <span>Clientes</span>}</Item>*/}
        {/*<Item to="/rates"><CurrencyIcon size="20" /> {!isMini && <span>Gestión de Tarifas</span>}</Item>*/}
        {!isOnlyHousekeepingStaff && !isMini && hasAnySettings && isSuperuser && (
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
              {hasViewEnterprises && (
                <Item to="/settings/enterprises" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.enterprises')}</Item>
              )}
              {hasViewOTAsConfig && (
                <Item to="/settings/otas" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.otas')}</Item>
              )}
              {hasViewRoomsConfig && (
                <Item to="/settings/rooms" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.rooms')}</Item>
              )}
              {hasViewHotels && (
                <>
                  <Item to="/settings/hotels" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.hotels')}</Item>
                  <Item to="/settings/whatsapp" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.whatsapp')}</Item>
                </>
              )}
              {hasViewUsers && (
                <Item to="/settings/users" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.users')}</Item>
              )}
              {hasViewRoles && (
                <Item to="/settings/roles" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.roles')}</Item>
              )}
              {/* Fiscal - por ahora sin permiso específico, se puede agregar después */}
              <Item to="/settings/fiscal" onMobileClose={onMobileClose} isMobile={isMobile}>Configuración Fiscal</Item>
              {hasViewHousekeeping && hasHousekeepingConfig && (
                <div className="mt-1 ml-2">
                  <button
                    type="button"
                    onClick={() => toggleGroup("housekeeping")}
                    className={`w-full flex items-center justify-between h-9 px-3 text-sm rounded-md transition-colors ${openGroups.housekeeping ? "text-white bg-white/5" : "text-white/80 hover:text-white hover:bg-white/5"
                      }`}
                    aria-expanded={openGroups.housekeeping}
                  >
                    <span>{t('sidebar.housekeeping_config')}</span>
                    <Chevron open={openGroups.housekeeping} />
                  </button>
                  <div
                    className={`mt-1 ml-4 flex flex-col gap-1 overflow-hidden transition-all duration-200 ${openGroups.housekeeping ? "max-h-48 opacity-100" : "max-h-0 opacity-0"
                      }`}
                  >
                    <Item to="/settings/housekeeping" onMobileClose={onMobileClose} isMobile={isMobile} exact={true}>{t('housekeeping.config.title')}</Item>
                    <Item to="/settings/housekeeping/zones" onMobileClose={onMobileClose} isMobile={isMobile}>{t('housekeeping.zones.title')}</Item>
                    <Item to="/settings/housekeeping/staff" onMobileClose={onMobileClose} isMobile={isMobile}>{t('housekeeping.staff.title')}</Item>
                    <Item to="/settings/housekeeping/templates" onMobileClose={onMobileClose} isMobile={isMobile}>{t('housekeeping.templates.title')}</Item>
                    <Item to="/settings/housekeeping/checklists" onMobileClose={onMobileClose} isMobile={isMobile}>{t('housekeeping.checklists.title')}</Item>
                  </div>
                </div>
              )}
              {hasAnyLocation && (
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
                    {hasViewCountries && (
                      <Item to="/settings/locations/countries" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.countries')}</Item>
                    )}
                    {hasViewStates && (
                      <Item to="/settings/locations/states" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.states')}</Item>
                    )}
                    {hasViewCities && (
                      <Item to="/settings/locations/cities" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.cities')}</Item>
                    )}
                  </div>
                </div>
              )}
              {hasAnyRate && (
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
                    {hasViewRatePlans && (
                      <Item to="/settings/rates/plans" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.rate_plans')}</Item>
                    )}
                    {hasViewRateRules && (
                      <Item to="/settings/rates/rules" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.rate_rules')}</Item>
                    )}
                    {hasViewPromos && (
                      <Item to="/settings/rates/promos" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.promotions')}</Item>
                    )}
                    {hasViewTaxes && (
                      <Item to="/settings/rates/taxes" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.taxes')}</Item>
                    )}
                  </div>
                </div>
              )}
              {hasAnyPolicy && (
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
                    {hasViewPaymentPolicies && (
                      <Item to="/settings/payments/policies" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.payment_policies')}</Item>
                    )}
                    {hasViewCancellationPolicies && (
                      <Item to="/settings/policies/cancellation" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.cancellation_policies')}</Item>
                    )}
                    {hasViewRefundPolicies && (
                      <Item to="/settings/policies/devolution" onMobileClose={onMobileClose} isMobile={isMobile}>{t('sidebar.devolution_policies')}</Item>
                    )}
                  </div>
                </div>
              )}
              {/** futuros submenús: tarifas, impuestos, usuarios, etc. */}
            </div>
          </div>
        )}
      </nav>

        {!isMini && (
          <div className="mt-auto text-[10px] text-white/50 px-2">v0.1</div>
        )}
      </div>
    </aside>
  );
}


