import React, { useState, useMemo, useEffect, useRef } from 'react'
import HotelIcon from 'src/assets/icons/HotelIcon'
import Tabs from 'src/components/Tabs'
import { useList } from 'src/hooks/useList'
import { useUserHotels } from 'src/hooks/useUserHotels'
import RoomMap from 'src/components/RoomMap'
import Filter from 'src/components/Filter'
import { Formik } from 'formik'
import SelectAsync from 'src/components/selects/SelectAsync'
import Select from 'react-select'
import { statusList } from 'src/utils/statusList'
import { getStatusMeta } from 'src/utils/statusList'
import Kpis from 'src/components/Kpis'
import { useAction } from 'src/hooks/useAction'
import HomeIcon from 'src/assets/icons/HomeIcon'
import ChartBarIcon from 'src/assets/icons/ChartBarIcon'
import CheckIcon from 'src/assets/icons/CheckIcon'
import PleopleOccupatedIcon from 'src/assets/icons/PleopleOccupatedIcon'
import ConfigurateIcon from 'src/assets/icons/ConfigurateIcon'
import ExclamationTriangleIcon from 'src/assets/icons/ExclamationTriangleIcon'
import ReservationsModal from 'src/components/modals/ReservationsModal'

const Reception = () => {
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()
  const [activeTab, setActiveTab] = useState(null)
  const [selectedHotel, setSelectedHotel] = useState(null)
  const [filters, setFilters] = useState({ search: "", status: "" })
  const [showReservationModal, setShowReservationModal] = useState(false)
  const [selectedRoomData, setSelectedRoomData] = useState(null)
  const didMountRef = useRef(false)

  const { results: hotels, isPending: hotelsLoading } = useList({
    resource: 'hotels',
    params: {
      page_size: 100,
      ...(!isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {})
    }
  })

  const { results: rooms, isPending: roomsLoading, refetch: refetchRooms } = useList({
    resource: 'rooms',
    params: {
      page_size: 100,
      hotel: selectedHotel,
      search: filters.search,
      status: filters.status
    }
  })

  const { results: summary, isPending: kpiLoading } = useAction({
    resource: 'status',
    action: 'summary',
    params: { hotel: selectedHotel || undefined },
    enabled: !!selectedHotel,
  })

  const getTabs = () => {
    if (!hotels) return []

    if (hasSingleHotel && !isSuperuser) {
      return hotels.map(hotel => ({
        id: hotel.id.toString(),
        label: hotel.name,
        icon: <HotelIcon />
      }))
    }
    const tabs = [
      ...hotels.map(hotel => ({
        id: hotel.id.toString(),
        label: hotel.name,
        icon: <HotelIcon />
      }))
    ]
    return tabs
  }

  const handleTabChange = (tabId) => {
    setActiveTab(tabId)
    setSelectedHotel(Number(tabId))
  }

  // Seleccionar automáticamente el primer hotel cuando se carguen los datos
  useEffect(() => {
    if (hotels && hotels.length > 0 && !activeTab) {
      const firstHotel = hotels[0]
      setActiveTab(firstHotel.id.toString())
      setSelectedHotel(firstHotel.id)
    }
  }, [hotels, activeTab])

  const onSearch = () => refetchRooms();
  const onClear = () => {
    setFilters({ search: "", status: "" });
    setTimeout(() => refetchRooms(), 0);
  };

  const handleRoomClick = (data) => {
    console.log('Habitación clickeada:', data);
    setSelectedRoomData(data);
    setShowReservationModal(true);
  };

  const handleReservationSuccess = (reservation) => {
    console.log('Reserva creada exitosamente:', reservation);
    // Aquí puedes agregar lógica adicional si es necesario
    // Por ejemplo, actualizar la lista de habitaciones o mostrar una notificación
  };

  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true;
      return;
    }
    const id = setTimeout(() => {
      refetchRooms();
    }, 400);
    return () => clearTimeout(id);
  }, [filters.search, filters.status, refetchRooms]);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">Recepción</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">Mapa de Habitaciones</h1>
        </div>
      </div>

      {/* Tabs para seleccionar hotel */}
      <div className="bg-white rounded-lg shadow-lg p-1">
        <Tabs
          tabs={getTabs()}
          activeTab={activeTab}
          onTabChange={handleTabChange}
          className="px-4"
        />
      </div>

      {/* Filtros */}
      <Filter>
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
                  setTimeout(() => refetchRooms(), 0);
                }}
                aria-label="Limpiar búsqueda"
              >
                ✕
              </button>
            )}
          </div>
          <div className="flex gap-3">
            <div className="w-48">
              <label className="block text-xs font-medium text-aloja-gray-800/70 mb-1">Estado</label>
              <Select
                value={statusList.find(s => String(s.value) === String(filters.status)) || null}
                onChange={(option) => setFilters((f) => ({ ...f, status: option ? String(option.value) : '' }))}
                options={[
                  { value: "", label: "Todos" },
                  ...statusList
                ]}
                placeholder="Todos"
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
      {/* Mapa de habitaciones */}
      {hotelsLoading ? (
        <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
          <div className="text-gray-500">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <h3 className="text-lg font-medium text-gray-700 mb-2">Cargando hoteles...</h3>
            <p className="text-sm">Obteniendo información de hoteles disponibles</p>
          </div>
        </div>
      ) : selectedHotel ? (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <RoomMap 
            rooms={rooms || []} 
            loading={roomsLoading} 
            onRoomClick={handleRoomClick}
            selectedHotel={selectedHotel}
            hotels={hotels || []}
          />
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
          <div className="text-gray-500">
            <HotelIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-700 mb-2">No hay hoteles disponibles</h3>
            <p className="text-sm">No se encontraron hoteles para mostrar</p>
          </div>
        </div>
      )}

      {/* Modal de Reservas */}
      <ReservationsModal
        isOpen={showReservationModal}
        onClose={() => {
          setShowReservationModal(false);
          setSelectedRoomData(null);
        }}
        onSuccess={handleReservationSuccess}
        isEdit={false}
        reservation={{
          hotel: selectedRoomData?.selectedHotel,
          room: selectedRoomData?.room?.id,
          room_data: selectedRoomData?.room
        }}
      />
    </div>
  )
}

export default Reception