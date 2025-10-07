import React, { useState } from 'react';
import { getStatusMeta } from 'src/utils/statusList';

const RoomMap = ({ rooms = [], loading = false, onRoomClick, selectedHotel, hotels = [] }) => {
  const [hoveredRoom, setHoveredRoom] = useState(null);

  // Colores modernos para cada estado de habitación
  const getStatusColor = (status) => {
    const statusColors = {
      available: 'bg-gradient-to-br from-emerald-400 to-emerald-600',
      occupied: 'bg-gradient-to-br from-amber-400 to-amber-600',
      maintenance: 'bg-gradient-to-br from-yellow-400 to-yellow-600',
      cleaning: 'bg-gradient-to-br from-blue-400 to-blue-600',
      blocked: 'bg-gradient-to-br from-slate-400 to-slate-600',
      out_of_service: 'bg-gradient-to-br from-rose-400 to-rose-600'
    };
    return statusColors[status?.toLowerCase()] || 'bg-gradient-to-br from-gray-300 to-gray-500';
  };

  // Colores de sombra para hover
  const getStatusShadowColor = (status) => {
    const shadowColors = {
      available: 'shadow-emerald-200',
      occupied: 'shadow-amber-200',
      maintenance: 'shadow-yellow-200',
      cleaning: 'shadow-blue-200',
      blocked: 'shadow-slate-200',
      out_of_service: 'shadow-rose-200'
    };
    return shadowColors[status?.toLowerCase()] || 'shadow-gray-200';
  };

  // Ya no necesitamos calcular grid, usamos flexbox

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando habitaciones...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Flexbox de habitaciones moderno */}
      <div className="bg-gradient-to-br from-slate-50 to-gray-100 p-4 md:p-8 rounded-2xl shadow-inner">
        <div className="flex flex-wrap gap-2 md:gap-4 justify-center">
          {rooms.map((room) => {
            const statusMeta = getStatusMeta(room.status);
            const isHovered = hoveredRoom?.id === room.id;

            return (
              <div
                key={room.id}
                className={`
                  w-16 h-16 md:w-28 md:h-28 rounded-xl md:rounded-2xl cursor-pointer transition-all duration-300
                  flex flex-col items-center justify-center text-white font-medium
                  ${getStatusColor(room.status)}
                  ${isHovered ? getStatusShadowColor(room.status) : 'shadow-lg'}
                  hover:scale-105 md:hover:scale-110 hover:shadow-2xl hover:rotate-1
                  ${isHovered ? 'scale-105 md:scale-110 shadow-2xl rotate-1' : ''}
                  border-0
                  backdrop-blur-sm
                `}
                onMouseEnter={() => setHoveredRoom(room)}
                onMouseLeave={() => setHoveredRoom(null)}
                onClick={() => onRoomClick && onRoomClick({
                  room,
                  hotel: hotels.find(h => h.id === selectedHotel),
                  selectedHotel
                })}
                title={`${room.name || `Habitación #${room.number || room.id}`} - ${statusMeta.label}`}
              >
                {/* Número de habitación principal */}
                <div className="text-xs md:text-md font-bold drop-shadow-sm">
                  {room.name || `#${room.id}`}
                </div>
                
                {/* Piso si está disponible - solo en desktop */}
                {room.floor && (
                  <div className="hidden md:block text-xs opacity-80 mt-1 font-medium drop-shadow-sm">
                    Piso: {room.floor}
                  </div>
                )}
                
                {/* Tipo de habitación - solo en desktop */}
                <div className="hidden md:block text-xs opacity-90 mt-1 font-medium drop-shadow-sm text-center px-1">
                  {room.room_type || 'N/A'}
                </div>
                
                {/* Indicador de estado */}
                <div className="w-1.5 h-1.5 md:w-2 md:h-2 rounded-full bg-white/40 mt-1"></div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Tooltip moderno */}
      {hoveredRoom && (
        <div className="absolute top-2 right-2 md:top-6 md:right-6 bg-white/95 backdrop-blur-md p-2 md:p-4 rounded-xl md:rounded-2xl shadow-2xl border-0 z-20 animate-in slide-in-from-right-2 duration-300 max-w-xs">
          <div className="flex items-center space-x-3 mb-3">
            <div className={`w-4 h-4 rounded-full ${getStatusColor(hoveredRoom.status)}`}></div>
            <div>
              <div className="text-sm font-semibold text-gray-900">
                Habitación {hoveredRoom.number || hoveredRoom.name || `#${hoveredRoom.id}`}
              </div>
              <div className="text-xs text-gray-600 mt-1">
                {getStatusMeta(hoveredRoom.status).label}
              </div>
            </div>
          </div>
          <div className="space-y-2">
            {hoveredRoom.floor && (
              <div className="text-xs text-gray-600">
                <span className="font-medium">Piso:</span> {hoveredRoom.floor}
              </div>
            )}
            <div className="text-xs text-gray-600">
              <span className="font-medium">Número:</span> {hoveredRoom.number || hoveredRoom.id}
            </div>
            <div className="text-xs text-gray-600">
              <span className="font-medium">Tipo:</span> {hoveredRoom.room_type || 'N/A'}
            </div>
            {hoveredRoom.capacity && (
              <div className="text-xs text-gray-600">
                <span className="font-medium">Capacidad:</span> {hoveredRoom.capacity}
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
};

export default RoomMap;
