import React from "react";
import MainLayout from "src/layouts/MainLayout";
import Rooms from "src/pages/Rooms";

export const appRoutes = [
  {
    path: "/",
    element: React.createElement(MainLayout),
    children: [
      { index: true, element: React.createElement("div", { className: "p-4" }, "Inicio AlojaSys") },
      { path: "rooms", element: React.createElement(Rooms) },
      // futuras: reservations, hotels, clients, etc.
    ],
  },
];


