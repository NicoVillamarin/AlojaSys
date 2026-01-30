import { useMemo, useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import TableGeneric from "src/components/TableGeneric";
import { useList } from "src/hooks/useList";
import { getStatusMeta, statusList } from "src/utils/statusList";
import { getRoomSortKey } from "src/utils/roomSort";
import RoomsModal from "src/components/modals/RoomsModal";
import RoomDetailModal from "src/components/modals/RoomDetailModal";
import EditIcon from "src/assets/icons/EditIcon";
import DeleteButton from "src/components/DeleteButton";
import Button from "src/components/Button";
import SelectAsync from "src/components/selects/SelectAsync";
import Select from "react-select";
import { useAction } from "src/hooks/useAction";
import { Formik } from "formik";
import Kpis from "src/components/Kpis";
import UsersIcon from "src/assets/icons/UsersIcon";
import HomeIcon from "src/assets/icons/HomeIcon";
import ChartBarIcon from "src/assets/icons/ChartBarIcon";
import WrenchScrewdriverIcon from "src/assets/icons/WrenchScrewdriverIcon";
import ExclamationTriangleIcon from "src/assets/icons/ExclamationTriangleIcon";
import ConfigurateIcon from "src/assets/icons/ConfigurateIcon";
import BedAvailableIcon from "src/assets/icons/BedAvailableIcon";
import CheckinIcon from "src/assets/icons/CheckinIcon";
import CheckIcon from "src/assets/icons/CheckIcon";
import PleopleOccupatedIcon from "src/assets/icons/PleopleOccupatedIcon";
import Filter from "src/components/Filter";
import { useUserHotels } from "src/hooks/useUserHotels";

export default function Rooms() {
  const { t } = useTranslation()
  const [showModal, setShowModal] = useState(false);
  const [editRoom, setEditRoom] = useState(null);
  const [detailRoom, setDetailRoom] = useState(null);
  const [filters, setFilters] = useState({ search: "", hotel: "", status: "" });
  const didMountRef = useRef(false);
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()

  const { results, count, isPending, hasNextPage, fetchNextPage, refetch } =
    useList({ resource: "rooms", params: { search: filters.search, hotel: filters.hotel, status: filters.status } });

  const { results: summary, isPending: kpiLoading } = useAction({
    resource: 'status',
    action: 'summary',
    params: { hotel: filters.hotel || undefined },
    enabled: !!filters.hotel,
  });

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
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.configuration')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('sidebar.rooms')}</h1>
        </div>
        <Button variant="primary" size="md" onClick={() => setShowModal(true)}>
          {t('common.create')} {t('sidebar.rooms')}
        </Button>
      </div>

      <RoomsModal isOpen={showModal} onClose={() => setShowModal(false)} isEdit={false} onSuccess={refetch} />
      <RoomsModal isOpen={!!editRoom} onClose={() => setEditRoom(null)} isEdit={true} room={editRoom} onSuccess={refetch} />
      <RoomDetailModal isOpen={!!detailRoom} onClose={() => setDetailRoom(null)} room={detailRoom} />
        <Filter>
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
                aria-label="Limpiar búsqueda"
              >
                ✕
              </button>
            )}
            </div>
          </div>
          <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3">
            <div className="w-full lg:w-56">
              <Formik
                enableReinitialize
                initialValues={{}}
                onSubmit={() => { }}
              >
                <SelectAsync
                  title={t('common.hotel')}
                  name="hotel"
                  resource="hotels"
                  placeholder={t('common.all')}
                  getOptionLabel={(h) => h?.name}
                  getOptionValue={(h) => h?.id}
                  onValueChange={(opt, val) => setFilters((f) => ({ ...f, hotel: String(val || '') }))}
                  extraParams={!isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {}}
                />
              </Formik>
            </div>
            <div className="w-full lg:w-48">
              <label className="block text-xs font-medium text-aloja-gray-800/70 mb-1">{t('common.status')}</label>
              <Select
                value={statusList.find(s => String(s.value) === String(filters.status)) || null}
                onChange={(option) => setFilters((f) => ({ ...f, status: option ? String(option.value) : '' }))}
                options={[
                  { value: "", label: t('common.all') },
                  ...statusList
                ]}
                placeholder={t('common.all')}
                isClearable
                isSearchable
                classNamePrefix="rs"
                styles={{
                  control: (base) => ({
                    ...base,
                    minHeight: 36,
                    borderRadius: 6,
                    borderColor: '#e5e7eb',
                    fontSize: 14,
                  }),
                  valueContainer: (base) => ({ ...base, padding: '2px 8px' }),
                  indicatorsContainer: (base) => ({ ...base, paddingRight: 6 }),
                  dropdownIndicator: (base) => ({ ...base, padding: 6 }),
                  clearIndicator: (base) => ({ ...base, padding: 6 }),
                  menu: (base) => ({ ...base, borderRadius: 8, overflow: 'hidden', zIndex: 9999 }),
                }}
              />
            </div>
          </div>
        </div>
        </Filter>
      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          {
            key: "name",
            header: t('rooms.room_number'),
            sortable: true,
            // Importante: ordenar “humano” (1,2,3…10) en vez de lexicográfico (1,10,11,2…)
            accessor: (r) => getRoomSortKey(r),
            render: (r) => (
              <button
                onClick={() => setDetailRoom(r)}
                className="text-blue-600 hover:text-blue-800 hover:underline text-left"
              >
                {r.name || r.number || `#${r.id}`}
              </button>
            ),
          },
          { key: "room_type", header: t('rooms.room_type'), sortable: true },
          {
            key: "status",
            header: t('common.status'),
            sortable: true,
            accessor: (r) => (r.status || "").toLowerCase(),
            render: (r) => {
              const meta = getStatusMeta(r.status);
              return <span className={`px-2 py-1 rounded text-xs ${meta.className}`}>{meta.label}</span>;
            },
          },
          { key: "base_price", header: t('rooms.price'), sortable: true, right: true, render: (r) => `${r.base_currency_code || '$'} ${r.base_price ?? ''}` },
          { key: "capacity", header: t('rooms.capacity'), sortable: true, right: true },
          { key: "max_capacity", header: t('rooms.max_capacity'), sortable: true, right: true },
          {
            key: "actions",
            header: t('dashboard.reservations_management.table_headers.actions'),
            sortable: false,
            right: true,
            render: (r) => (
              <div className="flex justify-end items-center gap-x-2">
                <EditIcon size="18" onClick={() => setEditRoom(r)} className="cursor-pointer" />
                <DeleteButton resource="rooms" id={r.id} onDeleted={refetch} className="cursor-pointer" />
              </div>
            ),
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
    </div>
  );
}


