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
import PaymentPolicies from "src/pages/configurations/policy/PaymentPolicies";


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
      { path: "settings/payments/policies", element: React.createElement(PaymentPolicies) },
    ],
  },
];


