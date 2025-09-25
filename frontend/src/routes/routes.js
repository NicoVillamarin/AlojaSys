import React from "react";
import MainLayout from "src/layouts/MainLayout";
import RoomsGestion from "src/pages/RoomsGestion";
import Hotels from "src/pages/configurations/Hotels";
import Rooms from "src/pages/configurations/Rooms";
import Cities from "src/pages/configurations/locations/Cities";
import Countries from "src/pages/configurations/locations/Countries";
import States from "src/pages/configurations/locations/States";

export const appRoutes = [
  {
    path: "/",
    element: React.createElement(MainLayout),
    children: [
      { index: true, element: React.createElement("div", { className: "p-4" }, "Inicio AlojaSys") },
      { path: "rooms-gestion", element: React.createElement(RoomsGestion) },
      { path: "settings/rooms", element: React.createElement(Rooms) },
      { path: "settings/hotels", element: React.createElement(Hotels) },
      { path: "settings/locations/countries", element: React.createElement(Countries) },
      { path: "settings/locations/states", element: React.createElement(States) },
      { path: "settings/locations/cities", element: React.createElement(Cities) },
    ],
  },
];


