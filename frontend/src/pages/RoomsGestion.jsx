import { useState, useMemo, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import TableGeneric from "src/components/TableGeneric";
import { getStatusMeta } from "src/utils/statusList";
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
import { convertToDecimal } from "./utils";
import Badge from "src/components/Badge";
import ToggleButton from "src/components/ToggleButton";
import EyeIcon from "src/assets/icons/EyeIcon";
import EyeSlashIcon from "src/assets/icons/EyeSlashIcon";
import { usePermissions } from "src/hooks/usePermissions";
import { usePlanFeatures } from "src/hooks/usePlanFeatures";
import RoomStatusModal from "src/components/modals/RoomStatusModal";
import Button from "src/components/Button";

export default function RoomsGestion() {
  const { t, i18n } = useTranslation();
  // Permisos CRUD de habitaciones
  const canViewRoom = usePermissions("rooms.view_room");
  const canChangeRoom = usePermissions("rooms.change_room");
  const { housekeepingEnabled } = usePlanFeatures();
  const [filters, setFilters] = useState({ search: "", hotel: "", status: "" });
  const [showKpis, setShowKpis] = useState(false);
  const didMountRef = useRef(false);
  const [selectedRoomIds, setSelectedRoomIds] = useState(() => new Set());
  const [showStatusModal, setShowStatusModal] = useState(false);

  const { results, count, isPending, hasNextPage, fetchNextPage, refetch } =
    useList({ 
      resource: "rooms", 
      params: { search: filters.search, hotel: filters.hotel, status: filters.status },
      enabled: canViewRoom,
    });

  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()
  
  // Lista de hoteles para el filtro (filtrados por usuario si no es superuser)
  const { results: hotels } = useList({ 
    resource: "hotels",
    params: !isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {},
    enabled: canViewRoom,
  });


  // Auto-seleccionar hotel si el usuario solo tiene uno asignado
  useEffect(() => {
    if (hasSingleHotel && singleHotelId && !filters.hotel && hotels && hotels.length === 1) {
      setFilters((f) => ({ ...f, hotel: String(singleHotelId) }));
    }
  }, [hasSingleHotel, singleHotelId, hotels, filters.hotel]);

  // Forzar refetch cuando se auto-selecciona el hotel
  useEffect(() => {
    if (filters.hotel && hasSingleHotel) {
      refetch();
    }
  }, [filters.hotel, hasSingleHotel, refetch]);

  // KPIs de hotel (cuando hay hotel seleccionado o cuando el usuario tiene un solo hotel)
  const shouldUseSummary = !!filters.hotel || (hasSingleHotel && singleHotelId);
  const hotelForSummary = filters.hotel || (hasSingleHotel ? String(singleHotelId) : undefined);
  
  const { results: summary, isPending: kpiLoading } = useAction({
    resource: 'status',
    action: 'summary',
    params: { hotel: hotelForSummary },
    enabled: Boolean(shouldUseSummary),
  });

  const kpi = useMemo(() => {
    if (shouldUseSummary && summary) {
      // Usar datos del summary del hotel cuando hay filtro o cuando el usuario tiene un solo hotel
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
      // Cuando no hay filtro de hotel y no se puede usar summary, usar el count total y calcular correctamente
      const total = count ?? 0;
      const page = results || [];
      
      // Contar por estado en la página actual
      const occupied = page.filter((r) => r.status === "occupied" || r.status === "OCCUPIED").length;
      const available = page.filter((r) => r.status === "available" || r.status === "AVAILABLE").length;
      const maintenance = page.filter((r) => r.status === "maintenance" || r.status === "MAINTENANCE").length;
      const outOfService = page.filter((r) => r.status === "out_of_service" || r.status === "OUT_OF_SERVICE").length;

      // Calcular capacidad total y huéspedes actuales
      const totalCapacity = page.reduce((sum, r) => sum + (r.capacity || 0), 0);
      const maxCapacity = page.reduce((sum, r) => sum + (r.max_capacity || 0), 0);
      const currentGuests = page.reduce((sum, r) => sum + (r.current_guests || 0), 0);

      // Si tenemos el total real del count, usar ese para el cálculo de disponibles
      // En lugar de solo contar la página actual
      const actualAvailable = total > 0 ? total - occupied - maintenance - outOfService : available;

      return {
        total,
        occupied,
        available: Math.max(0, actualAvailable), // Asegurar que no sea negativo
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
  }, [results, count, shouldUseSummary, summary]);

  // Si no puede ver habitaciones, mostrar mensaje
  if (!canViewRoom) {
    return (
      <div className="p-6 text-center text-gray-600">
        {t("rooms.no_permission_view", "No tenés permiso para ver la gestión de habitaciones.")}
      </div>
    );
  }

  // Crear KPIs para RoomsGestion
  const roomsGestionKpis = useMemo(() => {
    if (!kpi) return [];

    return [
      {
        title: t('dashboard.kpis.total_rooms'),
        value: kpi.total,
        icon: HomeIcon,
        color: "from-indigo-500 to-indigo-600",
        bgColor: "bg-indigo-100",
        iconColor: "text-indigo-600",
        change: "+2",
        changeType: "positive",
        subtitle: t('dashboard.kpis.in_all_hotels'),
        showProgress: false
      },
      {
        title: t('dashboard.kpis.occupied_rooms'),
        value: kpi.occupied,
        icon: PleopleOccupatedIcon,
        color: "from-emerald-500 to-emerald-600",
        bgColor: "bg-emerald-100",
        iconColor: "text-emerald-600",
        change: "+1",
        changeType: "positive",
        subtitle: t('dashboard.kpis.of_total', { total: kpi.total }),
        progressWidth: kpi.total > 0 ? `${Math.min((kpi.occupied / kpi.total) * 100, 100)}%` : '0%'
      },
      {
        title: t('dashboard.kpis.available_rooms'),
        value: kpi.available,
        icon: CheckIcon,
        color: "from-blue-500 to-blue-600",
        bgColor: "bg-blue-100",
        iconColor: "text-blue-600",
        change: "-1",
        changeType: "negative",
        subtitle: t('dashboard.charts.available'),
        progressWidth: kpi.total > 0 ? `${Math.min((kpi.available / kpi.total) * 100, 100)}%` : '0%'
      },
      {
        title: t('dashboard.kpis.maintenance_rooms'),
        value: kpi.maintenance,
        icon: ConfigurateIcon,
        color: "from-orange-500 to-orange-600",
        bgColor: "bg-orange-100",
        iconColor: "text-orange-600",
        change: kpi.maintenance > 0 ? "+1" : "0",
        changeType: kpi.maintenance > 0 ? "positive" : "neutral",
        subtitle: t('dashboard.charts.maintenance_subtitle'),
        progressWidth: kpi.total > 0 ? `${Math.min((kpi.maintenance / kpi.total) * 100, 100)}%` : '0%'
      },
      {
        title: t('dashboard.kpis.current_guests'),
        value: kpi.currentGuests,
        icon: PleopleOccupatedIcon,
        color: "from-purple-500 to-purple-600",
        bgColor: "bg-purple-100",
        iconColor: "text-purple-600",
        change: "+3",
        changeType: "positive",
        subtitle: t('dashboard.kpis.today'),
        showProgress: false
      },
      {
        title: t('dashboard.kpis.occupancy_rate'),
        value: `${kpi.occupancyRate}%`,
        icon: ChartBarIcon,
        color: "from-indigo-500 to-indigo-600",
        bgColor: "bg-indigo-100",
        iconColor: "text-indigo-600",
        change: "+5%",
        changeType: "positive",
        subtitle: t('dashboard.kpis.average_current'),
        progressWidth: `${kpi.occupancyRate}%`
      }
    ];
  }, [kpi, t]);

  // KPIs adicionales cuando hay hotel seleccionado o cuando el usuario tiene un solo hotel
  const additionalKpis = useMemo(() => {
    if (!shouldUseSummary || !kpi) return [];

    return [
      {
        title: t('dashboard.kpis.out_of_service_rooms'),
        value: kpi.outOfService,
        icon: ExclamationTriangleIcon,
        color: "from-rose-500 to-rose-600",
        bgColor: "bg-rose-100",
        iconColor: "text-rose-600",
        change: "0",
        changeType: "neutral",
        subtitle: t('dashboard.charts.not_available'),
        progressWidth: kpi.total > 0 ? `${Math.min((kpi.outOfService / kpi.total) * 100, 100)}%` : '0%'
      },
      {
        title: t('dashboard.kpis.arrivals_today'),
        value: kpi.arrivals,
        icon: CheckinIcon,
        color: "from-green-500 to-green-600",
        bgColor: "bg-green-100",
        iconColor: "text-green-600",
        change: "+2",
        changeType: "positive",
        subtitle: t('dashboard.kpis.today'),
        showProgress: false
      },
      {
        title: t('dashboard.kpis.departures_today'),
        value: kpi.departures,
        icon: CheckoutIcon,
        color: "from-orange-500 to-orange-600",
        bgColor: "bg-orange-100",
        iconColor: "text-orange-600",
        change: "-1",
        changeType: "negative",
        subtitle: t('dashboard.kpis.today'),
        showProgress: false
      }
    ];
  }, [shouldUseSummary, kpi, t]);

  // Lista de estados traducida - simple
  const statusList = useMemo(() => {
    return [
      { value: "available", label: t('rooms.status.available') || 'Disponible' },
      { value: "occupied", label: t('rooms.status.occupied') || 'Ocupada' },
      { value: "maintenance", label: t('rooms.status.maintenance') || 'Mantenimiento' },
      { value: "cleaning", label: t('rooms.status.cleaning') || 'Limpieza' },
      { value: "blocked", label: t('rooms.status.blocked') || 'Bloqueada' },
      { value: "out_of_service", label: t('rooms.status.out_of_service') || 'Fuera de servicio' }
    ];
  }, [t, i18n.language]);

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

  const selectedRooms = useMemo(() => {
    const ids = selectedRoomIds
    return (displayResults || []).filter((r) => ids.has(r.id))
  }, [displayResults, selectedRoomIds])

  const selectedCount = selectedRoomIds.size

  const toggleOne = (id, checked) => {
    setSelectedRoomIds((prev) => {
      const next = new Set(prev)
      if (checked) next.add(id)
      else next.delete(id)
      return next
    })
  }

  const toggleAllVisible = (checked) => {
    setSelectedRoomIds((prev) => {
      const next = new Set(prev)
      ;(displayResults || []).forEach((r) => {
        if (checked) next.add(r.id)
        else next.delete(r.id)
      })
      return next
    })
  }

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
        <div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('rooms.title')}</h1>
          <div className="text-sm text-aloja-gray-800/70">{kpi.total} {t('rooms.rooms')}</div>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
            <Filter title={t('rooms.filters_title')}>
              <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
                <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3">
                  <div className="relative w-full lg:w-80">
                  <span className="pointer-events-none absolute inset-y-0 left-2 flex items-center text-aloja-gray-800/60">
                    <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fillRule="evenodd" d="M12.9 14.32a8 8 0 111.414-1.414l3.387 3.387a1 1 0 01-1.414 1.414l-3.387-3.387zM14 8a6 6 0 11-12 0 6 6 0 0112 0z" clipRule="evenodd" />
                    </svg>
                  </span>
                  <input
                    className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg pl-8 pr-8 py-2 text-sm w-full transition-all"
                    placeholder={t('rooms.search_placeholder')}
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
                      aria-label={t('common.clear_search')}
                    >
                      ✕
                    </button>
                  )}
                  </div>
                </div>
                <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3">
                  <SelectStandalone
                    title={t('common.status')}
                    className="w-full lg:w-56"
                    value={statusList.find(s => String(s.value) === String(filters.status)) || null}
                    onChange={(option) => setFilters((f) => ({ ...f, status: option ? String(option.value) : '' }))}
                    options={[
                      { value: "", label: t('common.all') },
                      ...statusList
                    ]}
                    placeholder={t('common.all')}
                    isClearable
                    isSearchable
                  />
                  
                  <SelectStandalone
                    title={hasSingleHotel ? t('rooms.hotel_autoselected') : t('common.hotel')}
                    className="w-full lg:w-56"
                    value={hotels?.find(h => String(h.id) === String(filters.hotel)) || null}
                    onChange={(option) => setFilters((f) => ({ ...f, hotel: option ? String(option.id) : '' }))}
                    options={hotels || []}
                    getOptionLabel={(h) => h?.name}
                    getOptionValue={(h) => h?.id}
                    placeholder={t('common.all')}
                    isClearable={!hasSingleHotel}
                    isSearchable
                    isDisabled={hasSingleHotel}
                  />
                </div>
              </div>
            </Filter>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Acción: edición manual de estado/subestado (solo si housekeeping NO está habilitado) */}
            {canChangeRoom && !housekeepingEnabled && (
              <Button
                variant="primary"
                size="md"
                disabled={selectedCount === 0}
                onClick={() => setShowStatusModal(true)}
              >
                {t('rooms.edit_status_action', 'Editar estados')} {selectedCount > 0 ? `(${selectedCount})` : ''}
              </Button>
            )}
            <ToggleButton
              isOpen={showKpis}
              onToggle={() => setShowKpis(!showKpis)}
              openLabel="Ocultar KPIs"
              closedLabel="Mostrar KPIs"
              icon={EyeSlashIcon}
              closedIcon={EyeIcon}
            />
          </div>
        </div>

        {/* KPIs principales con animación */}
        <div 
          className={`overflow-hidden transition-all duration-500 ease-in-out ${
            showKpis 
              ? 'max-h-96 opacity-100 transform translate-y-0' 
              : 'max-h-0 opacity-0 transform -translate-y-4'
          }`}
        >
          <div className={`transition-all duration-300 delay-75 ${
            showKpis ? 'opacity-100 transform translate-y-0' : 'opacity-0 transform -translate-y-2'
          }`}>
            <Kpis kpis={roomsGestionKpis} loading={shouldUseSummary && kpiLoading} />
          </div>
        </div>

        {/* KPIs adicionales cuando hay hotel seleccionado o cuando el usuario tiene un solo hotel */}
        {shouldUseSummary && (
          <div 
            className={`overflow-hidden transition-all duration-500 ease-in-out ${
              showKpis 
                ? 'max-h-96 opacity-100 transform translate-y-0' 
                : 'max-h-0 opacity-0 transform -translate-y-4'
            }`}
          >
            <div className={`transition-all duration-300 delay-75 ${
              showKpis ? 'opacity-100 transform translate-y-0' : 'opacity-0 transform -translate-y-2'
            }`}>
              <Kpis kpis={additionalKpis} loading={kpiLoading} />
            </div>
          </div>
        )}
      </div>

      {/* Tabla */}
      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          // Selección (solo cuando housekeeping NO está habilitado)
          ...(!housekeepingEnabled
            ? [
                {
                  key: "__select__",
                  header: (
                    <input
                      type="checkbox"
                      aria-label={t('common.select_all', 'Seleccionar todo')}
                      checked={displayResults?.length > 0 && displayResults.every((r) => selectedRoomIds.has(r.id))}
                      onChange={(e) => toggleAllVisible(e.target.checked)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  ),
                  sortable: false,
                  render: (r) => (
                    <input
                      type="checkbox"
                      aria-label={t('common.select', 'Seleccionar')}
                      checked={selectedRoomIds.has(r.id)}
                      onChange={(e) => toggleOne(r.id, e.target.checked)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  ),
                },
              ]
            : []),
          {
            key: "updated_at",
            header: t('rooms.last_updated'),
            sortable: true,
            accessor: (r) => r.updated_at ? format(parseISO(r.updated_at), 'dd/MM/yyyy HH:mm') : '',
            render: (r) => r.updated_at ? format(parseISO(r.updated_at), 'dd/MM/yyyy HH:mm') : '',
          },
          {
            key: "name",
            header: t('rooms.room_number'),
            sortable: true,
            accessor: (r) => r.name || r.number || `#${r.id}`,
            render: (r) => r.name || r.number || `#${r.id}`,
          },
          { key: "room_type", header: t('rooms.room_type'), sortable: true },
          {
            key: "status",
            header: t('common.status'),
            sortable: true,
            accessor: (r) => (r.status || "").toLowerCase(),
            render: (r) => {
              const meta = getStatusMeta(r.status, t);
              const cleaningStatus = r.cleaning_status;
              
              return (
                <div className="inline-flex items-center gap-2 flex-wrap">
                  <Badge variant={`room-${r.status}`} size="sm">
                    {meta.label}
                  </Badge>
                  {cleaningStatus === 'in_progress' && (
                    <Badge variant="info" size="sm" className="bg-blue-100 text-blue-700">
                      {t('rooms.cleaning_status.in_progress') || 'En limpieza'}
                    </Badge>
                  )}
                  {cleaningStatus === 'dirty' && (
                    <Badge variant="warning" size="sm" className="bg-amber-100 text-amber-700">
                      {t('rooms.cleaning_status.dirty') || 'Requiere limpieza'}
                    </Badge>
                  )}
                  {cleaningStatus === 'clean' && (
                    <Badge variant="success" size="sm" className="bg-emerald-100 text-emerald-700">
                      {t('rooms.cleaning_status.clean') || 'Limpia'}
                    </Badge>
                  )}
                </div>
              );
            },
          },
          { key: "base_price", header: t('rooms.price'), sortable: true, render: (r) => `$ ${convertToDecimal(r.base_price)}`, right: true } ,
          {
            key: "capacity",
            header: t('rooms.capacity'),
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
                    {maxCapacity > capacity ? `+$${extraFee} extra` : t('rooms.people')}
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
            {t('common.load_more')}
          </button>
        </div>
      )}

      <RoomStatusModal
        isOpen={showStatusModal}
        onClose={() => setShowStatusModal(false)}
        rooms={selectedRooms}
        onSuccess={() => {
          setShowStatusModal(false)
          setSelectedRoomIds(new Set())
          refetch()
        }}
      />
    </div>
  );
}
