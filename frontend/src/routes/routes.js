import React from "react";
import MainLayout from "src/layouts/MainLayout";
import RoomsGestion from "src/pages/RoomsGestion";
import ReservationsGestions from "src/pages/ReservationsGestions";
import Hotels from "src/pages/configurations/Hotels";
import Rooms from "src/pages/configurations/Rooms";
import Enterprises from "src/pages/configurations/Enterprises";
import Cities from "src/pages/configurations/locations/Cities";
import Countries from "src/pages/configurations/locations/Countries";
import States from "src/pages/configurations/locations/States";
import Dashboard from "src/pages/Dashboard";
import ReservationHistorical from "src/pages/ReservationHistorical";
import Payments from "src/pages/Payments";
import Users from "src/pages/configurations/Users";
import Reception from "src/pages/Reception";
import PlanRates from "src/pages/configurations/rates/PlanRates";
import RulesRates from "src/pages/configurations/rates/RulesRates";
import Promos from "src/pages/configurations/rates/Promos";
import Taxes from "src/pages/configurations/rates/Taxes";
import Currency from "src/pages/configurations/rates/Currency";
import PaymentPolicies from "src/pages/configurations/policy/PaymentPolicies";
import ReservationsCalendar from "src/pages/ReservationsCalendar";
import CancellationPolicies from "src/pages/configurations/policy/CancellationPolicies";
import DevolutionPolicies from "src/pages/configurations/policy/DevolutionPolicies";
import RefundsManagement from "src/pages/RefundsManagement";
import RefundsHistorical from "src/pages/RefundsHistorical";
import VouchersManagement from "src/pages/VouchersManagement";
import Notifications from "src/pages/Notifications";
import BankReconciliation from "src/pages/financial/BankReconciliation";
import Cashbox from "src/pages/financial/Cashbox";
import InvoicingManagement from "src/pages/invoicing/InvoicingManagement";
import PaymentReceiptsManagement from "src/pages/invoicing/PaymentReceiptsManagement";
import AfipConfig from "src/pages/invoicing/AfipConfig";
import OtaConfig from "src/pages/configurations/OtaConfig";
import Otas from "src/pages/configurations/Otas";
import Roles from "src/pages/configurations/Roles";
import Housekeeping from "src/pages/Housekeeping";
import CleaningZones from "src/pages/configurations/housekeeping/CleaningZones";
import CleaningStaff from "src/pages/configurations/housekeeping/CleaningStaff";
import TaskTemplates from "src/pages/configurations/housekeeping/TaskTemplates";
import Checklists from "src/pages/configurations/housekeeping/Checklists";
import HousekeepingConfig from "src/pages/configurations/housekeeping/HousekeepingConfig";
import HousekeepingHistorical from "src/pages/HousekeepingHistorical";
import Whatsapp from "src/pages/configurations/Whatsapp";


export const appRoutes = [
  {
    path: "/",
    element: React.createElement(MainLayout),
    children: [
      { index: true, element: React.createElement(Dashboard) },
      { path: "reception", element: React.createElement(Reception) },
      { path: "rooms-gestion", element: React.createElement(RoomsGestion) },
      { path: "reservations-gestion", element: React.createElement(ReservationsGestions) },
      { path: "reservations/:id/history", element: React.createElement(ReservationHistorical) },
      { path: "payments", element: React.createElement(Payments) },
      { path: "settings/rooms", element: React.createElement(Rooms) },
      { path: "settings/hotels", element: React.createElement(Hotels) },
      { path: "settings/enterprises", element: React.createElement(Enterprises) },
      { path: "settings/users", element: React.createElement(Users) },
      { path: "settings/locations/countries", element: React.createElement(Countries) },
      { path: "settings/locations/states", element: React.createElement(States) },
      { path: "settings/locations/cities", element: React.createElement(Cities) },
      { path: "settings/rates/plans", element: React.createElement(PlanRates) },
      { path: "settings/rates/rules", element: React.createElement(RulesRates) },
      { path: "settings/rates/promos", element: React.createElement(Promos) },
      { path: "settings/rates/taxes", element: React.createElement(Taxes) },
      { path: "settings/rates/currency", element: React.createElement(Currency) },
      { path: "settings/payments/policies", element: React.createElement(PaymentPolicies) },
      { path: "settings/policies/cancellation", element: React.createElement(CancellationPolicies) },
      { path: "settings/policies/devolution", element: React.createElement(DevolutionPolicies) },
      { path: "settings/otas", element: React.createElement(OtaConfig) },
      { path: "otas", element: React.createElement(Otas) },
      { path: "refunds", element: React.createElement(RefundsManagement) },
      { path: "refunds/history", element: React.createElement(RefundsHistorical) },
      { path: "vouchers", element: React.createElement(VouchersManagement) },
      { path: "bank-reconciliation", element: React.createElement(BankReconciliation) },
      { path: "cashbox", element: React.createElement(Cashbox) },
      { path: "notificaciones", element: React.createElement(Notifications) },
      { path: "reservations-calendar", element: React.createElement(ReservationsCalendar) },
      { path: "invoicing", element: React.createElement(InvoicingManagement) },
      { path: "invoicing/receipts", element: React.createElement(PaymentReceiptsManagement) },
      { path: "settings/fiscal", element: React.createElement(AfipConfig) },
      { path: "settings/roles", element: React.createElement(Roles) },
      { path: "housekeeping", element: React.createElement(Housekeeping) },
      { path: "settings/housekeeping", element: React.createElement(HousekeepingConfig) },
      { path: "settings/housekeeping/zones", element: React.createElement(CleaningZones) },
      { path: "settings/housekeeping/staff", element: React.createElement(CleaningStaff) },
      { path: "settings/housekeeping/templates", element: React.createElement(TaskTemplates) },
      { path: "settings/housekeeping/checklists", element: React.createElement(Checklists) },
      { path: "housekeeping/historical", element: React.createElement(HousekeepingHistorical) },
      { path: "settings/whatsapp", element: React.createElement(Whatsapp) },
    ],
  },
];


