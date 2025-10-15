import React, { useState, useMemo, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
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
import RoomStatusLegend from 'src/components/RoomStatusLegend'
import SpinnerData from 'src/components/SpinnerData'
import ToggleButton from 'src/components/ToggleButton'
import EyeIcon from 'src/assets/icons/EyeIcon'
import EyeSlashIcon from 'src/assets/icons/EyeSlashIcon'
import InfoIcon from 'src/assets/icons/InfoIcon'

const Reception = () => {
  const { t, i18n } = useTranslation()
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()
  const [activeTab, setActiveTab] = useState(null)
  const [selectedHotel, setSelectedHotel] = useState(null)
  const [filters, setFilters] = useState({ search: "", status: "" })
  const [showReservationModal, setShowReservationModal] = useState(false)
  const [selectedRoomData, setSelectedRoomData] = useState(null)
  const [showLegend, setShowLegend] = useState(false)
  const didMountRef = useRef(false)
  const [language, setLanguage] = useState(i18n.language)

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

  // Escuchar cambios de idioma
  useEffect(() => {
    const handleLanguageChange = (lng) => {
      setLanguage(lng)
    }
    
    i18n.on('languageChanged', handleLanguageChange)
    
    return () => {
      i18n.off('languageChanged', handleLanguageChange)
    }
  }, [i18n])


  const onSearch = () => refetchRooms();
  const onClear = () => {
    setFilters({ search: "", status: "" });
    setTimeout(() => refetchRooms(), 0);
  };

  const handleRoomClick = (data) => {
    console.log(t('reception.room_clicked'), data);
    setSelectedRoomData(data);
    setShowReservationModal(true);
  };

  const handleReservationSuccess = (reservation) => {
    console.log(t('reception.reservation_created_successfully'), reservation);
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

  // Forzar re-render cuando cambie el idioma
  const currentLanguage = language

  // Crear leyenda de colores para estados de habitaciones
  const roomColorLegend = useMemo(() => [
    { status: 'available', label: 'Disponible', color: '#10B981', description: 'Habitación libre y lista para ocupar' },
    { status: 'confirmed', label: 'Confirmada', color: '#3B82F6', description: 'Reserva confirmada para hoy (pendiente check-in)' },
    { status: 'occupied', label: 'Ocupada', color: '#F59E0B', description: 'Habitación con huésped actualmente (check-in)' },
    { status: 'maintenance', label: 'Mantenimiento', color: '#EAB308', description: 'Habitación en reparación o mantenimiento' },
    { status: 'cleaning', label: 'Limpieza', color: '#3B82F6', description: 'Habitación siendo limpiada' },
    { status: 'blocked', label: 'Bloqueada', color: '#8B5CF6', description: 'Habitación bloqueada temporalmente' },
    { status: 'out_of_service', label: 'Fuera de servicio', color: '#6B7280', description: 'Habitación no disponible' }
  ], [])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('reception.title')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('reception.room_map')}</h1>
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

      <div className="space-y-4">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
            <Filter>
              <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
                <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3 flex-1">
                  <div className="relative w-full lg:w-80">
                  <span className="pointer-events-none absolute inset-y-0 left-2 flex items-center text-aloja-gray-800/60">
                    <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fillRule="evenodd" d="M12.9 14.32a8 8 0 111.414-1.414l3.387 3.387a1 1 0 01-1.414 1.414l-3.387-3.387zM14 8a6 6 0 11-12 0 6 6 0 0112 0z" clipRule="evenodd" />
                    </svg>
                  </span>
                  <input
                    className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg pl-8 pr-8 py-2 text-sm w-full transition-all"
                    placeholder={t('reception.search_rooms_placeholder')}
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
                      aria-label={t('reception.clear_search')}
                    >
                      ✕
                    </button>
                  )}
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="w-full lg:w-56">
                    <label className="block text-xs font-medium text-aloja-gray-800/70 mb-1">{t('reception.status')}</label>
                    <Select
                      value={statusList.find(s => String(s.value) === String(filters.status)) || null}
                      onChange={(option) => setFilters((f) => ({ ...f, status: option ? String(option.value) : '' }))}
                      options={[
                        { value: "", label: t('reception.all') },
                        ...statusList
                      ]}
                      placeholder={t('reception.all')}
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
          </div>
          
          <div className="flex items-center gap-3">
            <ToggleButton
              isOpen={showLegend}
              onToggle={() => setShowLegend(!showLegend)}
              openLabel="Ocultar Leyenda"
              closedLabel="Leyenda"
              icon={EyeSlashIcon}
              closedIcon={EyeIcon}
            />
          </div>
        </div>

      {/* Leyenda de colores con animación */}
      <div 
        className={`overflow-hidden transition-all duration-500 ease-in-out ${
          showLegend 
            ? 'max-h-96 opacity-100 transform translate-y-0' 
            : 'max-h-0 opacity-0 transform -translate-y-4'
        }`}
      >
        <div className={`transition-all duration-300 delay-75 ${
          showLegend ? 'opacity-100 transform translate-y-0' : 'opacity-0 transform -translate-y-2'
        }`}>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <InfoIcon className="w-5 h-5 text-blue-600" />
              Leyenda de Estados de Habitaciones
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {roomColorLegend.map((item) => (
                <div key={item.status} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors duration-200">
                  <div 
                    className="w-4 h-4 rounded-full flex-shrink-0"
                    style={{ backgroundColor: item.color }}
                  ></div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900">{item.label}</div>
                    <div className="text-sm text-gray-600">{item.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      </div>

      {/* Mapa de habitaciones */}
      {hotelsLoading ? (
        <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
          <div className="text-gray-500">
            <SpinnerData size={80} className="mb-4" />
            <h3 className="text-lg font-medium text-gray-700 mb-2">{t('reception.loading_hotels')}</h3>
            <p className="text-sm">{t('reception.getting_hotel_info')}</p>
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
            <h3 className="text-lg font-medium text-gray-700 mb-2">{t('reception.no_hotels_available')}</h3>
            <p className="text-sm">{t('reception.no_hotels_found')}</p>
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