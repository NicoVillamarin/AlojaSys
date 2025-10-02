import { useState, useMemo, useEffect, useRef } from "react";
import TableGeneric from "src/components/TableGeneric";
import { getStatusMeta, statusList } from "src/utils/statusList";
import { useList } from "src/hooks/useList";
import { useAction } from "src/hooks/useAction";
import { format, parseISO } from "date-fns";
import Kpis from "src/components/Kpis";
import Filter from "src/components/Filter";
import HomeIcon from "src/assets/icons/HomeIcon";
import UsersIcon from "src/assets/icons/UsersIcon";
import BedAvailableIcon from "src/assets/icons/BedAvailableIcon";
import WrenchScrewdriverIcon from "src/assets/icons/WrenchScrewdriverIcon";
import ExclamationTriangleIcon from "src/assets/icons/ExclamationTriangleIcon";
import ChartBarIcon from "src/assets/icons/ChartBarIcon";
import PleopleOccupatedIcon from "src/assets/icons/PleopleOccupatedIcon";
import CheckIcon from "src/assets/icons/CheckIcon";
import ConfigurateIcon from "src/assets/icons/ConfigurateIcon";
import CheckoutIcon from "src/assets/icons/CheckoutIcon";
import CheckinIcon from "src/assets/icons/CheckinIcon";
import SelectStandalone from "src/components/selects/SelectStandalone";
import { useUserHotels } from "src/hooks/useUserHotels";

export default function RoomsGestion() {
  const [filters, setFilters] = useState({ search: "", hotel: "", status: "" });
  const didMountRef = useRef(false);

  const { results, count, isPending, hasNextPage, fetchNextPage, refetch } =
    useList({ resource: "rooms", params: { search: filters.search, hotel: filters.hotel, status: filters.status } });

  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()
  
  // Lista de hoteles para el filtro (filtrados por usuario si no es superuser)
  const { results: hotels } = useList({ 
    resource: "hotels",
    params: !isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {}
  });

  // Auto-seleccionar hotel si el usuario solo tiene uno asignado
  useEffect(() => {
    if (hasSingleHotel && singleHotelId && !filters.hotel && hotels && hotels.length === 1) {
      setFilters((f) => ({ ...f, hotel: String(singleHotelId) }));
    }
  }, [hasSingleHotel, singleHotelId, hotels, filters.hotel]);

  // KPIs de hotel (solo cuando hay hotel seleccionado)
  const { results: summary, isPending: kpiLoading } = useAction({
    resource: 'status',
    action: 'summary',
    params: { hotel: filters.hotel || undefined },
    enabled: !!filters.hotel,
  });

  const kpi = useMemo(() => {
    if (filters.hotel && summary) {
      // Usar datos del summary del hotel cuando hay filtro
      return {
        total: summary.rooms?.total ?? 0,
        occupied: summary.rooms?.occupied ?? 0,
        available: summary.rooms?.available ?? 0,
        maintenance: summary.rooms?.maintenance ?? 0,
        outOfService: summary.rooms?.out_of_service ?? 0,
        totalCapacity: summary.rooms?.total_capacity ?? 0,
        maxCapacity: summary.rooms?.max_capacity ?? 0,
        currentGuests: summary.rooms?.current_guests ?? 0,
        arrivals: summary.today?.arrivals ?? 0,
        inhouse: summary.today?.inhouse ?? 0,
        departures: summary.today?.departures ?? 0,
        occupancyRate: summary.rooms?.total > 0
          ? Math.round((summary.rooms?.occupied / summary.rooms?.total) * 100)
          : 0,
      };
    } else {
      // Usar datos de la página actual cuando no hay filtro de hotel
      const total = count ?? 0;
      const page = results || [];
      const occupied = page.filter((r) => r.status === "occupied" || r.status === "OCCUPIED").length;
      const available = page.filter((r) => r.status === "available" || r.status === "AVAILABLE").length;
      const maintenance = page.filter((r) => r.status === "maintenance" || r.status === "MAINTENANCE").length;
      const outOfService = page.filter((r) => r.status === "out_of_service" || r.status === "OUT_OF_SERVICE").length;

      // Calcular capacidad total y huéspedes actuales
      const totalCapacity = page.reduce((sum, r) => sum + (r.capacity || 0), 0);
      const maxCapacity = page.reduce((sum, r) => sum + (r.max_capacity || 0), 0);
      const currentGuests = page.reduce((sum, r) => sum + (r.current_guests || 0), 0);

      return {
        total,
        occupied,
        available,
        maintenance,
        outOfService,
        totalCapacity,
        maxCapacity,
        currentGuests,
        arrivals: 0,
        inhouse: 0,
        departures: 0,
        occupancyRate: total > 0 ? Math.round((occupied / total) * 100) : 0,
      };
    }
  }, [results, count, filters.hotel, summary]);

  // Crear KPIs para RoomsGestion
  const roomsGestionKpis = useMemo(() => {
    if (!kpi) return [];

    return [
      {
        title: "Habitaciones Totales",
        value: kpi.total,
        icon: HomeIcon,
        color: "from-indigo-500 to-indigo-600",
        bgColor: "bg-indigo-100",
        iconColor: "text-indigo-600",
        change: "+2",
        changeType: "positive",
        subtitle: "capacidad total del hotel",
        showProgress: false
      },
      {
        title: "Habitaciones Ocupadas",
        value: kpi.occupied,
        icon: PleopleOccupatedIcon,
        color: "from-emerald-500 to-emerald-600",
        bgColor: "bg-emerald-100",
        iconColor: "text-emerald-600",
        change: "+1",
        changeType: "positive",
        subtitle: `de ${kpi.total} totales`,
        progressWidth: kpi.total > 0 ? `${Math.min((kpi.occupied / kpi.total) * 100, 100)}%` : '0%'
      },
      {
        title: "Habitaciones Disponibles",
        value: kpi.available,
        icon: CheckIcon,
        color: "from-blue-500 to-blue-600",
        bgColor: "bg-blue-100",
        iconColor: "text-blue-600",
        change: "-1",
        changeType: "negative",
        subtitle: "listas para ocupar",
        progressWidth: kpi.total > 0 ? `${Math.min((kpi.available / kpi.total) * 100, 100)}%` : '0%'
      },
      {
        title: "En Mantenimiento",
        value: kpi.maintenance,
        icon: ConfigurateIcon,
        color: "from-orange-500 to-orange-600",
        bgColor: "bg-orange-100",
        iconColor: "text-orange-600",
        change: kpi.maintenance > 0 ? "+1" : "0",
        changeType: kpi.maintenance > 0 ? "positive" : "neutral",
        subtitle: "requieren reparación",
        progressWidth: kpi.total > 0 ? `${Math.min((kpi.maintenance / kpi.total) * 100, 100)}%` : '0%'
      },
      {
        title: "Huéspedes Hospedados",
        value: kpi.currentGuests,
        icon: PleopleOccupatedIcon,
        color: "from-purple-500 to-purple-600",
        bgColor: "bg-purple-100",
        iconColor: "text-purple-600",
        change: "+3",
        changeType: "positive",
        subtitle: "personas hoy",
        showProgress: false
      },
      {
        title: "Tasa de Ocupación",
        value: `${kpi.occupancyRate}%`,
        icon: ChartBarIcon,
        color: "from-indigo-500 to-indigo-600",
        bgColor: "bg-indigo-100",
        iconColor: "text-indigo-600",
        change: "+5%",
        changeType: "positive",
        subtitle: "promedio del hotel",
        progressWidth: `${kpi.occupancyRate}%`
      }
    ];
  }, [kpi]);

  // KPIs adicionales cuando hay hotel seleccionado
  const additionalKpis = useMemo(() => {
    if (!filters.hotel || !kpi) return [];

    return [
      {
        title: "Fuera de Servicio",
        value: kpi.outOfService,
        icon: ExclamationTriangleIcon,
        color: "from-rose-500 to-rose-600",
        bgColor: "bg-rose-100",
        iconColor: "text-rose-600",
        change: "0",
        changeType: "neutral",
        subtitle: "no disponibles",
        progressWidth: kpi.total > 0 ? `${Math.min((kpi.outOfService / kpi.total) * 100, 100)}%` : '0%'
      },
      {
        title: "Check-ins Hoy",
        value: kpi.arrivals,
        icon: CheckinIcon,
        color: "from-green-500 to-green-600",
        bgColor: "bg-green-100",
        iconColor: "text-green-600",
        change: "+2",
        changeType: "positive",
        subtitle: "llegadas hoy",
        showProgress: false
      },
      {
        title: "Check-outs Hoy",
        value: kpi.departures,
        icon: CheckoutIcon,
        color: "from-orange-500 to-orange-600",
        bgColor: "bg-orange-100",
        iconColor: "text-orange-600",
        change: "-1",
        changeType: "negative",
        subtitle: "salidas hoy",
        showProgress: false
      }
    ];
  }, [filters.hotel, kpi]);

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
    setFilters({ search: "", hotel: "", status: "" });
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
  }, [filters.search, filters.hotel, filters.status, refetch]);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-aloja-navy">Gestión de Habitaciones</h1>
        <div className="text-sm text-aloja-gray-800/70">{kpi.total} habitaciones</div>
      </div>

      {/* KPIs principales */}
      <Kpis kpis={roomsGestionKpis} loading={filters.hotel && kpiLoading} />

      {/* KPIs adicionales cuando hay hotel seleccionado */}
      {filters.hotel && (
        <Kpis kpis={additionalKpis} loading={kpiLoading} />
      )}

      {/* Filtros */}
      <Filter title="Filtros de Habitaciones">
        <div className="flex flex-wrap items-center justify-between gap-3">
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
          <div className="flex flex-wrap items-center gap-3">
            <SelectStandalone
              title="Estado"
              className="w-56"
              value={statusList.find(s => String(s.value) === String(filters.status)) || null}
              onChange={(option) => setFilters((f) => ({ ...f, status: option ? String(option.value) : '' }))}
              options={[
                { value: "", label: "Todos" },
                ...statusList
              ]}
              placeholder="Todos"
              isClearable
              isSearchable
            />
            
            <SelectStandalone
              title={hasSingleHotel ? "Hotel (autoseleccionado)" : "Hotel"}
              className="w-56"
              value={hotels?.find(h => String(h.id) === String(filters.hotel)) || null}
              onChange={(option) => setFilters((f) => ({ ...f, hotel: option ? String(option.id) : '' }))}
              options={hotels || []}
              getOptionLabel={(h) => h?.name}
              getOptionValue={(h) => h?.id}
              placeholder="Todos"
              isClearable={!hasSingleHotel}
              isSearchable
              isDisabled={hasSingleHotel}
            />
          </div>
        </div>
      </Filter>

      {/* Tabla */}
      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          {
            key: "updated_at",
            header: "Última actualización",
            sortable: true,
            accessor: (r) => r.updated_at ? format(parseISO(r.updated_at), 'dd/MM/yyyy HH:mm') : '',
            render: (r) => r.updated_at ? format(parseISO(r.updated_at), 'dd/MM/yyyy HH:mm') : '',
          },
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
          {
            key: "capacity",
            header: "Capacidad",
            sortable: true,
            render: (r) => {
              const capacity = r.capacity || 0;
              const maxCapacity = r.max_capacity || 0;
              const extraFee = r.extra_guest_fee || 0;

              return (
                <div className="text-center flex-row gap-x-1">
                  <div className="font-semibold text-sm">
                    {capacity}{maxCapacity > capacity ? `-${maxCapacity}` : ''}
                  </div>
                  <div className="text-xs text-gray-500">
                    {maxCapacity > capacity ? `+$${extraFee} extra` : 'personas'}
                  </div>
                </div>
              );
            }
          },
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