// Mapa de estados de habitaciones: valor backend (en inglés) -> etiqueta y clases de color
export const STATUS_MAP = {
  available: { label: "Disponible", className: "bg-green-100 shadow-md  text-green-700" },
  occupied: { label: "Ocupada", className: "bg-orange-100 shadow-md text-orange-700" },
  maintenance: { label: "Mantenimiento", className: "bg-yellow-100 shadow-md text-yellow-700" },
  cleaning: { label: "Limpieza", className: "bg-blue-100 shadow-md text-blue-700" },
  blocked: { label: "Bloqueada", className: "bg-gray-200 shadow-md text-gray-700" },
  out_of_service: { label: "Fuera de servicio", className: "bg-red-200 shadow-md text-red-700" }
};

// Lista conveniente si se necesita para selects
export const statusList = Object.entries(STATUS_MAP).map(([value, { label }]) => ({ value, label }));

// Helpers
export function getStatusMeta(status) {
  const key = String(status || "").toLowerCase();
  return STATUS_MAP[key] || { label: status || "-", className: "bg-aloja-gray-100 text-aloja-gray-800" };
}