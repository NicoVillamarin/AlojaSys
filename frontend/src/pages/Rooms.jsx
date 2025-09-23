import { useState, useMemo, useEffect, useRef } from "react";
import TableGeneric from "src/components/TableGeneric";
import { getStatusMeta } from "src/utils/statusList";
import { useList } from "src/hooks/useList";

export default function Rooms() {
  const [filters, setFilters] = useState({ search: "", hotel: "" });
  const didMountRef = useRef(false);

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

  // Filtrado en cliente para respuesta inmediata al escribir
  const displayResults = useMemo(() => {
    const q = (filters.search || "").trim().toLowerCase();
    if (!q) return results;
    return (results || []).filter((r) => {
      const idStr = String(r.id ?? "");
      const numberStr = String(r.number ?? "");
      const nameStr = String(r.name ?? "");
      const typeStr = String(r.room_type ?? "");
      const statusStr = String(r.status ?? "");
      return (
        idStr.includes(q) ||
        numberStr.toLowerCase().includes(q) ||
        nameStr.toLowerCase().includes(q) ||
        typeStr.toLowerCase().includes(q) ||
        statusStr.toLowerCase().includes(q)
      );
    });
  }, [results, filters.search]);

  const onSearch = () => refetch();
  const onClear = () => {
    setFilters({ search: "", hotel: "" });
    setTimeout(() => refetch(), 0);
  };

  // Debounce de búsqueda al escribir
  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true;
      return;
    }
    const id = setTimeout(() => {
      refetch();
    }, 400);
    return () => clearTimeout(id);
  }, [filters.search, filters.hotel, refetch]);

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
      <div className="bg-white rounded-xl shadow p-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <span className="pointer-events-none absolute inset-y-0 left-2 flex items-center text-aloja-gray-800/60">
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M12.9 14.32a8 8 0 111.414-1.414l3.387 3.387a1 1 0 01-1.414 1.414l-3.387-3.387zM14 8a6 6 0 11-12 0 6 6 0 0112 0z" clipRule="evenodd" />
              </svg>
            </span>
            <input
              className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg pl-8 pr-8 py-2 text-sm w-64 transition-all"
              placeholder="Buscar habitaciones…"
              value={filters.search}
              onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
              onKeyDown={(e) => e.key === "Enter" && onSearch()}
            />
            {filters.search && (
              <button
                className="absolute inset-y-0 right-1 my-1 px-2 rounded-md text-xs text-aloja-gray-800/70 hover:bg-gray-100"
                onClick={() => {
                  setFilters((f) => ({ ...f, search: "" }));
                  setTimeout(() => refetch(), 0);
                }}
                aria-label="Limpiar búsqueda"
              >
                ✕
              </button>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              className="px-4 py-2 rounded-lg border border-gray-200 text-sm hover:bg-gray-50 transition"
              onClick={onClear}
            >
              Limpiar
            </button>
          </div>
        </div>
      </div>

      {/* Tabla */}
      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          {
            key: "name",
            header: "Habitación",
            sortable: true,
            accessor: (r) => r.name || r.number || `#${r.id}`,
            render: (r) => r.name || r.number || `#${r.id}`,
          },
          { key: "room_type", header: "Tipo", sortable: true },
          {
            key: "status",
            header: "Estado",
            sortable: true,
            accessor: (r) => (r.status || "").toLowerCase(),
            render: (r) => {
              const meta = getStatusMeta(r.status);
              return <span className={`px-2 py-1 rounded text-xs ${meta.className}`}>{meta.label}</span>;
            },
          },
          { key: "base_price", header: "Precio base", sortable: true },
          { key: "capacity", header: "Capacidad", sortable: true },
        ]}
      />

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