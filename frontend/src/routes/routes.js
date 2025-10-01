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


export const appRoutes = [
  {
    path: "/",
    element: React.createElement(MainLayout),
    children: [
      { index: true, element: React.createElement(Dashboard) },
      { path: "rooms-gestion", element: React.createElement(RoomsGestion) },
      { path: "reservations-gestion", element: React.createElement(ReservationsGestions) },
      { path: "reservations/:id/history", element: React.createElement(ReservationHistorical) },
      { path: "settings/rooms", element: React.createElement(Rooms) },
      { path: "settings/hotels", element: React.createElement(Hotels) },
      { path: "settings/enterprises", element: React.createElement(Enterprises) },
      { path: "settings/locations/countries", element: React.createElement(Countries) },
      { path: "settings/locations/states", element: React.createElement(States) },
      { path: "settings/locations/cities", element: React.createElement(Cities) },
    ],
  },
];


