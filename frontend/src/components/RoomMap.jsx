import React, { useState, useMemo } from 'react';
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

  // Calcular el grid de habitaciones
  const gridData = useMemo(() => {
    if (!rooms || rooms.length === 0) return { rows: 0, cols: 0, grid: [] };

    const totalRooms = rooms.length;
    const cols = Math.ceil(Math.sqrt(totalRooms));
    const rows = Math.ceil(totalRooms / cols);
    
    // Crear grid vacío
    const grid = Array(rows).fill(null).map(() => Array(cols).fill(null));
    
    // Llenar grid con habitaciones
    rooms.forEach((room, index) => {
      const row = Math.floor(index / cols);
      const col = index % cols;
      grid[row][col] = room;
    });

    return { rows, cols, grid };
  }, [rooms]);

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
      {/* Grid de habitaciones moderno */}
      <div className="bg-gradient-to-br from-slate-50 to-gray-100 p-8 rounded-2xl shadow-inner">
        <div 
          className="grid gap-4 mx-auto"
          style={{
            gridTemplateColumns: `repeat(${gridData.cols}, minmax(120px, 1fr))`,
            maxWidth: 'fit-content'
          }}
        >
          {gridData.grid.map((row, rowIndex) =>
            row.map((room, colIndex) => {
              if (!room) {
                return (
                  <div 
                    key={`empty-${rowIndex}-${colIndex}`}
                    className="w-28 h-28 bg-transparent"
                  />
                );
              }

              const statusMeta = getStatusMeta(room.status);
              const isHovered = hoveredRoom?.id === room.id;

              return (
                <div
                  key={room.id}
                  className={`
                    w-28 h-28 rounded-2xl cursor-pointer transition-all duration-300
                    flex flex-col items-center justify-center text-white font-medium
                    ${getStatusColor(room.status)}
                    ${isHovered ? getStatusShadowColor(room.status) : 'shadow-lg'}
                    hover:scale-110 hover:shadow-2xl hover:rotate-1
                    ${isHovered ? 'scale-110 shadow-2xl rotate-1' : ''}
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
                  <div className="text-md font-bold drop-shadow-sm">
                    {room.name || `#${room.id}`}
                  </div>
                  
                  {/* Piso si está disponible */}
                  {room.floor && (
                    <div className="text-xs opacity-80 mt-1 font-medium drop-shadow-sm">
                      Piso: {room.floor}
                    </div>
                  )}
                  
                  {/* Tipo de habitación */}
                  <div className="text-xs opacity-90 mt-1 font-medium drop-shadow-sm text-center px-1">
                    {room.room_type || 'N/A'}
                  </div>
                  
                  {/* Indicador de estado */}
                  <div className="w-2 h-2 rounded-full bg-white/40 mt-1"></div>
                </div>
              );
            })
          )}
        </div>
      </div>
      
      {/* Tooltip moderno */}
      {hoveredRoom && (
        <div className="absolute top-6 right-6 bg-white/95 backdrop-blur-md p-4 rounded-2xl shadow-2xl border-0 z-10 animate-in slide-in-from-right-2 duration-300">
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

      {/* Leyenda moderna */}
      <div className="absolute bottom-6 left-6 bg-white/95 backdrop-blur-md p-4 rounded-2xl shadow-2xl border-0">
        <div className="text-sm font-semibold text-gray-800 mb-3">Estados</div>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries({
            available: 'Disponible',
            occupied: 'Ocupada', 
            maintenance: 'Mantenimiento',
            cleaning: 'Limpieza',
            blocked: 'Bloqueada',
            out_of_service: 'Fuera de servicio'
          }).map(([status, label]) => (
            <div key={status} className="flex items-center space-x-2">
              <div 
                className={`w-3 h-3 rounded-full ${getStatusColor(status)} shadow-sm`}
              />
              <span className="text-xs text-gray-700 font-medium">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RoomMap;
