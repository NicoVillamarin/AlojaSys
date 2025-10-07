import React, { useState } from 'react';

const RoomStatusLegend = () => {
  const [isHovered, setIsHovered] = useState(false);

  // Colores para cada estado de habitación (mismo que RoomMap)
  const getStatusColor = (status) => {
    const statusColors = {
      available: 'bg-gradient-to-br from-emerald-400 to-emerald-600',
      occupied: 'bg-gradient-to-br from-amber-400 to-amber-600',
      maintenance: 'bg-gradient-to-br from-yellow-400 to-yellow-600',
      cleaning: 'bg-gradient-to-br from-blue-400 to-blue-600',
      blocked: 'bg-gradient-to-br from-slate-400 to-slate-600',
      out_of_service: 'bg-gradient-to-br from-rose-400 to-rose-600'
    };
    return statusColors[status] || 'bg-gradient-to-br from-gray-300 to-gray-500';
  };

  return (
    <div className="relative inline-block">
      {/* Botón de ayuda */}
      <button
        className="w-8 h-8 rounded-full bg-aloja-navy text-white hover:bg-aloja-navy/90 transition-colors flex items-center justify-center text-sm font-medium shadow-lg hover:shadow-xl"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        title="Ver estados de habitaciones"
        aria-label="Ver estados de habitaciones"
      >
        ?
      </button>

      {/* Tooltip con leyenda */}
      {isHovered && (
        <div className="absolute right-full top-1/2 transform -translate-y-1/2 mr-2 bg-white/95 backdrop-blur-md p-4 rounded-xl shadow-2xl border-0 z-50 min-w-[200px] animate-in slide-in-from-right-2 duration-200">
          <div className="text-sm font-semibold text-gray-800 mb-3 text-center">Estados</div>
          <div className="grid grid-cols-1 gap-2">
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
          
          {/* Flecha apuntando hacia la derecha */}
          <div className="absolute left-full top-1/2 transform -translate-y-1/2 w-0 h-0 border-t-4 border-b-4 border-l-4 border-transparent border-l-white/95"></div>
        </div>
      )}
    </div>
  );
};

export default RoomStatusLegend;
