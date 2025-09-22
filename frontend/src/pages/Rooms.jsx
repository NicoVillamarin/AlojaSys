import { useState, useMemo } from "react";
import { useList } from "src/hooks/useList";

export default function Rooms() {
  const [filters, setFilters] = useState({ search: "", hotel: "" });

  const { results, count, isPending, hasNextPage, fetchNextPage, refetch } =
    useList({ resource: "rooms", params: { search: filters.search, hotel: filters.hotel } });

  const kpi = useMemo(() => {
    const total = count ?? 0;
    const page = results || [];
    const occupied = page.filter((r) => r.status === "occupied" || r.status === "OCCUPIED").length;
    const available = page.filter((r) => r.status === "available" || r.status === "AVAILABLE").length;
    const checkins = page.filter((r) => r.current_reservation?.status === "check_in" || r.current_reservation?.status === "CHECK_IN").length;
    return { total, occupied, available, checkins };
  }, [results, count]);

  const onSearch = () => refetch();
  const onClear = () => {
    setFilters({ search: "", hotel: "" });
    setTimeout(() => refetch(), 0);
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-aloja-navy">Gestión de Habitaciones</h1>
        <div className="text-sm text-aloja-gray-800/70">{kpi.total} habitaciones</div>
      </div>

      {/* KPIs (rápidos, sobre la página actual) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-xs text-aloja-gray-800/70">Total</div>
          <div className="text-2xl font-semibold">{kpi.total}</div>
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-xs text-aloja-gray-800/70">Ocupadas (página)</div>
          <div className="text-2xl font-semibold">{kpi.occupied}</div>
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-xs text-aloja-gray-800/70">Disponibles (página)</div>
          <div className="text-2xl font-semibold">{kpi.available}</div>
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-xs text-aloja-gray-800/70">Check-ins activos (página)</div>
          <div className="text-2xl font-semibold">{kpi.checkins}</div>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap items-center gap-2 bg-white rounded-xl shadow p-3">
        <input
          className="border rounded-md px-3 py-2 text-sm w-56"
          placeholder="Buscar…"
          value={filters.search}
          onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
        />
        <input
          className="border rounded-md px-3 py-2 text-sm w-40"
          placeholder="Hotel ID"
          value={filters.hotel}
          onChange={(e) => setFilters((f) => ({ ...f, hotel: e.target.value }))}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
        />
        <button className="px-3 py-2 rounded-md bg-aloja-navy text-white" onClick={onSearch}>
          Buscar
        </button>
        <button className="px-3 py-2 rounded-md border" onClick={onClear}>
          Limpiar
        </button>
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-xl shadow overflow-x-auto">
        {isPending ? (
          <div className="p-6 text-sm text-aloja-gray-800/70">Cargando…</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-aloja-gray-800/70 border-b">
                <th className="py-2 px-3">Habitación</th>
                <th className="py-2 px-3">Tipo</th>
                <th className="py-2 px-3">Estado</th>
                <th className="py-2 px-3">Precio base</th>
                <th className="py-2 px-3">Capacidad</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.id} className="border-b last:border-0">
                  <td className="py-2 px-3">{r.name || r.number || `#${r.id}`}</td>
                  <td className="py-2 px-3">{r.room_type}</td>
                  <td className="py-2 px-3">
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        (r.status || "").toLowerCase() === "available"
                          ? "bg-green-100 text-green-700"
                          : (r.status || "").toLowerCase() === "occupied"
                          ? "bg-red-100 text-red-700"
                          : "bg-aloja-gray-100 text-aloja-gray-800"
                      }`}
                    >
                      {r.status}
                    </span>
                  </td>
                  <td className="py-2 px-3">{r.base_price}</td>
                  <td className="py-2 px-3">{r.capacity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {hasNextPage && (
        <div>
          <button className="px-3 py-2 rounded-md border" onClick={() => fetchNextPage()}>
            Cargar más
          </button>
        </div>
      )}
    </div>
  );
}