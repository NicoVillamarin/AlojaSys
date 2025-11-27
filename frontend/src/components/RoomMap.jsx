import React, { useState, useEffect, useRef } from 'react';
import { getStatusMeta } from 'src/utils/statusList';
import { format, parseISO, isToday, isSameDay } from 'date-fns';

const RoomMap = ({ rooms = [], loading = false, onRoomClick, selectedHotel, hotels = [] }) => {
  const [hoveredRoom, setHoveredRoom] = useState(null);
  const [showTooltip, setShowTooltip] = useState(false);
  const hoverTimeoutRef = useRef(null);

  // Limpiar timeout al desmontar
  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);

  // Manejar hover con delay para evitar parpadeo
  const handleMouseEnter = (room) => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
    setHoveredRoom(room);
    hoverTimeoutRef.current = setTimeout(() => {
      setShowTooltip(true);
    }, 150); // Pequeño delay para estabilizar
  };

  const handleMouseLeave = () => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
    // Pequeño delay antes de ocultar para evitar parpadeo si el mouse pasa por encima del tooltip
    hoverTimeoutRef.current = setTimeout(() => {
      setHoveredRoom(null);
      setShowTooltip(false);
    }, 100);
  };

  // Función para determinar el estado efectivo basado en reservas
  const getEffectiveStatus = (room) => {
    const status = room.status?.toLowerCase();
    const today = new Date();
    
    
    // Si hay una reserva actual, determinar el estado según el status de la reserva
    if (room.current_reservation) {
      // Si la reserva está en check_in, la habitación está ocupada
      if (room.current_reservation.status === 'check_in') {
        return 'occupied';
      }
      
      // Si la reserva está confirmada, la habitación está confirmada (pendiente check-in)
      if (room.current_reservation.status === 'confirmed') {
        return 'confirmed';
      }
      
      // Para otros estados, usar el estado de la reserva
      return room.current_reservation.status || 'occupied';
    }
    
    // Si hay reservas futuras confirmadas para HOY, mostrar como confirmada
    if (room.future_reservations && room.future_reservations.length > 0) {
      const hasConfirmedReservationForToday = room.future_reservations.some(res => {
        if (!res.check_in) return false;
        
        const checkInDate = parseISO(res.check_in);
        const isConfirmed = res.status === 'confirmed' || res.status === 'CONFIRMED';
        const isTodayCheckIn = isSameDay(checkInDate, today);
        
        
        return isConfirmed && isTodayCheckIn;
      });
      if (hasConfirmedReservationForToday) {
        return 'confirmed';
      }
    }
    
    // Si el estado dice "occupied" pero no hay current_reservation, tratarlo como available
    if (status === 'occupied' && !room.current_reservation) {
      return 'available';
    }
    
    return status || 'available';
  };

  // Función para determinar el color basado en el estado efectivo
  const getStatusColor = (room) => {
    const effectiveStatus = getEffectiveStatus(room);
    
    const statusColors = {
      available: 'bg-gradient-to-br from-emerald-400 to-emerald-600', // Verde - disponible
      confirmed: 'bg-gradient-to-br from-blue-400 to-blue-600', // Azul - confirmada
      occupied: 'bg-gradient-to-br from-amber-400 to-amber-600', // Naranja - ocupada
      maintenance: 'bg-gradient-to-br from-yellow-400 to-yellow-600',
      cleaning: 'bg-gradient-to-br from-blue-400 to-blue-600',
      blocked: 'bg-gradient-to-br from-slate-400 to-slate-600',
      out_of_service: 'bg-gradient-to-br from-rose-400 to-rose-600'
    };
    
    return statusColors[effectiveStatus] || 'bg-gradient-to-br from-gray-300 to-gray-500';
  };

  // Función para verificar si está en limpieza
  const isCleaning = (room) => {
    return room.cleaning_status === 'in_progress';
  };

  // Función para obtener el texto del estado efectivo
  const getEffectiveStatusLabel = (room) => {
    const effectiveStatus = getEffectiveStatus(room);
    
    const statusLabels = {
      available: 'Disponible',
      confirmed: 'Confirmada',
      occupied: 'Ocupada',
      maintenance: 'Mantenimiento',
      cleaning: 'Limpieza',
      blocked: 'Bloqueada',
      out_of_service: 'Fuera de servicio'
    };
    
    return statusLabels[effectiveStatus] || 'Desconocido';
  };

  // Colores de sombra para hover
  const getStatusShadowColor = (status) => {
    const shadowColors = {
      available: 'shadow-emerald-200',
      confirmed: 'shadow-blue-200',
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
            const effectiveStatus = getEffectiveStatus(room);
            const isHovered = hoveredRoom?.id === room.id;
            const cleaning = isCleaning(room);

            return (
              <div
                key={room.id}
                className={`
                  w-16 h-16 md:w-28 md:h-28 rounded-xl md:rounded-2xl cursor-pointer transition-all duration-300
                  flex flex-col items-center justify-center text-white font-medium
                  relative overflow-hidden
                  ${getStatusColor(room)}
                  ${isHovered ? getStatusShadowColor(effectiveStatus) : 'shadow-lg'}
                  hover:scale-105 md:hover:scale-110 hover:shadow-2xl hover:rotate-1
                  ${isHovered ? 'scale-105 md:scale-110 shadow-2xl rotate-1' : ''}
                  border-0
                  backdrop-blur-sm
                `}
                onMouseEnter={() => handleMouseEnter(room)}
                onMouseLeave={handleMouseLeave}
                onClick={() => onRoomClick && onRoomClick({
                  room,
                  hotel: hotels.find(h => h.id === selectedHotel),
                  selectedHotel
                })}
                title={`${room.name || `Habitación #${room.number || room.id}`} - ${getEffectiveStatusLabel(room)}${cleaning ? ' (En limpieza)' : ''}`}
              >
                {/* Overlay diagonal para estado de limpieza - mitad inferior derecha */}
                {cleaning && (
                  <div 
                    className="absolute inset-0 bg-gradient-to-br from-blue-500 to-blue-700"
                    style={{
                      clipPath: 'polygon(100% 0, 100% 100%, 0 100%)',
                      zIndex: 1
                    }}
                  />
                )}
                
                {/* Contenido con z-index para estar sobre el overlay */}
                <div className="relative z-10 flex flex-col items-center justify-center">
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
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Tooltip moderno */}
      {hoveredRoom && showTooltip && (
        <div 
          className="absolute top-2 right-2 md:top-6 md:right-6 bg-white/95 backdrop-blur-md p-2 md:p-4 rounded-xl md:rounded-2xl shadow-2xl border-0 z-50 animate-in slide-in-from-right-2 duration-300 max-w-xs pointer-events-none"
          onMouseEnter={() => {
            if (hoverTimeoutRef.current) {
              clearTimeout(hoverTimeoutRef.current);
            }
          }}
          onMouseLeave={handleMouseLeave}
        >
          <div className="flex items-center space-x-3 mb-3">
            <div className={`w-4 h-4 rounded-full ${getStatusColor(hoveredRoom)}`}></div>
            <div>
              <div className="text-sm font-semibold text-gray-900">
                Habitación {hoveredRoom.number || hoveredRoom.name || `#${hoveredRoom.id}`}
              </div>
              <div className="text-xs text-gray-600 mt-1">
                {getEffectiveStatusLabel(hoveredRoom)}
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

