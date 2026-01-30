import React, { useMemo, useState, useEffect, useRef } from 'react';
import { parseISO, isSameDay } from 'date-fns';
import CleaningIcon from 'src/assets/icons/CleaningIcon';
import DirtIcon from 'src/assets/icons/DirtIcon';

const DoorBadge = ({ children, className = '' }) => (
  <div
    // Dentro de la puerta (sin offsets negativos) para que no "flote" entre tiles
    className={`absolute top-1 right-1 z-20 grid place-items-center rounded-full shadow-lg ${className}`}
  >
    {children}
  </div>
);

const DoorBadgeLeft = ({ children, className = '' }) => (
  <div
    className={`absolute -top-3 -left-3 md:-top-4 md:-left-4 z-20 grid place-items-center rounded-full bg-white/95 text-slate-900 shadow-lg ring-1 ring-black/5 ${className}`}
  >
    {children}
  </div>
);

// (intencional) mantenemos el status en texto plano abajo para un look más limpio

const IconLock = ({ className = '' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path
      d="M7.5 11V8.8A4.5 4.5 0 0 1 12 4.3a4.5 4.5 0 0 1 4.5 4.5V11"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
    />
    <path
      d="M7.2 11h9.6a2 2 0 0 1 2 2v6.5a2 2 0 0 1-2 2H7.2a2 2 0 0 1-2-2V13a2 2 0 0 1 2-2Z"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinejoin="round"
    />
    <path
      d="M12 15.2v2.8"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
    />
  </svg>
);

const IconCheck = ({ className = '' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path
      d="M20 7.5 10.6 17 4 10.4"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const DoorVisual = ({
  variant, // 'open' | 'ajar' | 'closed'
  toneClass, // tailwind bg gradient for the frame
  dimmed = false,
}) => {
  const isOpen = variant === 'open';
  const isAjar = variant === 'ajar';
  const doorTransform = isOpen
    // Más “abierta” para que se note a simple vista
    ? 'rotateY(-52deg) translateX(-10px)'
    : isAjar
      ? 'rotateY(-26deg) translateX(-5px)'
      : 'rotateY(0deg) translateX(0px)';

  return (
    <div
      className={[
        // Compacto (como antes)
        'relative w-16 h-20 md:w-24 md:h-28 rounded-xl md:rounded-2xl',
        'transition-all duration-300 will-change-transform',
        'shadow-lg hover:shadow-2xl',
        'ring-1 ring-black/5',
        dimmed ? 'opacity-55 saturate-50' : '',
      ].join(' ')}
    >
      {/* Marco */}
      <div
        className={[
          'absolute inset-0 rounded-xl md:rounded-2xl',
          toneClass,
          'p-[3px] md:p-1',
        ].join(' ')}
      >
        {/* Hueco del marco */}
        <div className="absolute inset-[3px] md:inset-1 rounded-[10px] md:rounded-2xl bg-black/15" />

        {/* Puerta (3D fake con perspectiva) */}
        <div className="absolute inset-[6px] md:inset-2 rounded-[10px] md:rounded-xl [perspective:700px]">
          {/* “Interior” + luz (solo cuando está abierta/entreabierta) */}
          {(isOpen || isAjar) && (
            <>
              <div className="absolute inset-0 rounded-[10px] md:rounded-xl bg-gradient-to-br from-black/45 via-black/30 to-black/20" />
              {/* Luz entrando por el hueco (lado derecho) */}
              <div className="absolute inset-0 rounded-[10px] md:rounded-xl overflow-hidden">
                <div className="absolute right-0 top-0 h-full w-1/2 bg-gradient-to-l from-white/25 via-white/10 to-transparent" />
              </div>
            </>
          )}

          <div
            className={[
              'absolute inset-0 rounded-[10px] md:rounded-xl',
              'bg-gradient-to-br from-white/18 to-black/18',
              'ring-1 ring-white/20',
              'shadow-[inset_0_1px_0_rgba(255,255,255,0.25)]',
              'origin-left',
              'transition-transform duration-300',
            ].join(' ')}
            style={{ transform: doorTransform }}
          >
            {/* Paneles */}
            <div className="absolute inset-2 rounded-lg border border-white/20" />
            <div className="absolute inset-4 rounded-md border border-white/10" />
            {/* Canto de la puerta (para que se note el “espesor” al abrir) */}
            {(isOpen || isAjar) && (
              <div className="absolute top-1 bottom-1 right-0 w-1 rounded-full bg-white/25 shadow-[inset_0_0_0_1px_rgba(0,0,0,0.10)]" />
            )}
            {/* Picaporte */}
            <div
              className={[
                'absolute top-1/2 -translate-y-1/2 right-2',
                'w-2 h-2 rounded-full bg-white/80',
                'shadow ring-1 ring-black/10',
              ].join(' ')}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

const RoomMap = ({
  rooms = [],
  loading = false,
  onRoomClick,
  selectedHotel,
  hotels = [],
  enableDragSelect = false, // deprecated (no usar): se mantiene para compat, pero sin drag.
  selectedRoomIds,
  onSelectedRoomIdsChange,
  onSelectionEnd,
}) => {
  // No usamos i18n aquí para no cambiar toda la firma; mantenemos labels en español.
  const [hoveredRoom, setHoveredRoom] = useState(null);
  const [showTooltip, setShowTooltip] = useState(false);
  const hoverTimeoutRef = useRef(null);
  // Compat: algunas funciones aún chequean dragRef (drag-select fue removido).
  // Lo dejamos definido para evitar ReferenceError.
  const dragRef = useRef({ active: false });
  // Drag-select removido (preferimos checkbox manual).
  const [internalSelectedIds, setInternalSelectedIds] = useState(() => new Set());

  const effectiveSelectedIds = useMemo(() => {
    if (!selectedRoomIds) return internalSelectedIds;
    // aceptar Set o array
    if (selectedRoomIds instanceof Set) return selectedRoomIds;
    if (Array.isArray(selectedRoomIds)) return new Set(selectedRoomIds);
    return internalSelectedIds;
  }, [selectedRoomIds, internalSelectedIds]);

  const setSelectedIds = (updater) => {
    if (typeof updater === 'function') {
      if (typeof onSelectedRoomIdsChange === 'function') {
        onSelectedRoomIdsChange((prev) => updater(prev instanceof Set ? prev : new Set(prev || [])));
      } else {
        setInternalSelectedIds((prev) => updater(prev));
      }
      return;
    }
    // updater como Set
    if (typeof onSelectedRoomIdsChange === 'function') onSelectedRoomIdsChange(updater);
    else setInternalSelectedIds(updater);
  };

  // Limpiar timeout al desmontar
  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);

  // Si cambian las rooms (hotel/filtros), limpiar selección interna para evitar IDs colgados
  useEffect(() => {
    if (!selectedRoomIds) {
      setInternalSelectedIds(new Set());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rooms]);

  // Manejar hover con delay para evitar parpadeo
  const handleMouseEnter = (room) => {
    if (dragRef.current.active) return;
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
    setHoveredRoom(room);
    hoverTimeoutRef.current = setTimeout(() => {
      setShowTooltip(true);
    }, 150); // Pequeño delay para estabilizar
  };

  const handleMouseLeave = () => {
    if (dragRef.current.active) return;
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

  const getDoorTone = (room) => {
    const effectiveStatus = getEffectiveStatus(room);
    const tone = {
      available: 'bg-gradient-to-br from-emerald-400 to-emerald-600',
      confirmed: 'bg-gradient-to-br from-blue-400 to-blue-600',
      occupied: 'bg-gradient-to-br from-amber-400 to-amber-600',
      maintenance: 'bg-gradient-to-br from-yellow-400 to-yellow-600',
      cleaning: 'bg-gradient-to-br from-sky-400 to-sky-600',
      blocked: 'bg-gradient-to-br from-slate-400 to-slate-600',
      out_of_service: 'bg-gradient-to-br from-rose-400 to-rose-600',
    };
    return tone[effectiveStatus] || 'bg-gradient-to-br from-gray-300 to-gray-500';
  };

  // Función para verificar si está en limpieza
  const isCleaning = (room) => {
    return room.cleaning_status === 'in_progress';
  };

  // Función para verificar si está sucia
  const isDirty = (room) => {
    return room.cleaning_status === 'dirty';
  };

  // Función para verificar si está limpia
  const isClean = (room) => {
    return room.cleaning_status === 'clean';
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

  const getRoomStatusLine = (room) => {
    const effectiveStatus = getEffectiveStatus(room);
    const base = getEffectiveStatusLabel(room);
    const dirty = isDirty(room);
    const clean = isClean(room);
    const cleaning = isCleaning(room) || effectiveStatus === 'cleaning';
    // Si está ocupada/confirmada, no mostramos subestado de limpieza para no ensuciar la UI
    if (effectiveStatus === 'occupied' || effectiveStatus === 'confirmed') return base;
    if (dirty) return `${base} · Para limpiar`;
    if (clean) return `${base} · Limpia`;
    if (!cleaning) return base;
    if (effectiveStatus === 'cleaning') return 'En limpieza';
    return `${base} · En limpieza`;
  };

  // Colores de sombra para hover
  const getStatusShadowColor = (status) => {
    const shadowColors = {
      available: 'shadow-emerald-200',
      confirmed: 'shadow-blue-200',
      occupied: 'shadow-amber-200',
      maintenance: 'shadow-yellow-200',
      cleaning: 'shadow-sky-200',
      blocked: 'shadow-slate-200',
      out_of_service: 'shadow-rose-200',
    };
    return shadowColors[status?.toLowerCase()] || 'shadow-gray-200';
  };

  // Ya no necesitamos calcular grid, usamos flexbox

  const toggleSelected = (roomId) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(roomId)) next.delete(roomId);
      else next.add(roomId);
      return next;
    });
  };

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
        <div className="flex flex-wrap gap-2 md:gap-4 justify-center relative z-10">
          {rooms.map((room) => {
            const effectiveStatus = getEffectiveStatus(room);
            const isHovered = hoveredRoom?.id === room.id;
            const cleaning = isCleaning(room);
            const dirty = isDirty(room);
            const showCleaning = cleaning || effectiveStatus === 'cleaning';
            const isMaintenance = effectiveStatus === 'maintenance';
            const isBlocked = effectiveStatus === 'blocked' || effectiveStatus === 'out_of_service';
            const isOccupied = effectiveStatus === 'occupied';
            const isConfirmed = effectiveStatus === 'confirmed';
            const isAvailable = effectiveStatus === 'available';
            const showCleaningBadge = showCleaning && !isOccupied && !isConfirmed;
            // Prioridad: si está "en limpieza", no mostrar "sucia"
            const showDirtyBadge = dirty && !isOccupied && !isConfirmed && !showCleaningBadge;

            const plateText = room.name || room.number || `#${room.id}`;
            const doorVariant = isAvailable ? 'open' : isConfirmed ? 'ajar' : 'closed';
            const isSelected = effectiveSelectedIds.has(room.id);

            return (
              <div
                key={room.id}
                className={[
                  'group cursor-pointer transition-all duration-300',
                  'relative',
                  isSelected
                    ? [
                        // Selección sin línea: "tarjeta elevada" sobre el fondo
                        // Queremos que resalte (con scale), pero sin que se note desalineado:
                        // lo resolvemos centrando la puerta abajo (wrapper), no quitando el scale.
                        'z-20 isolate rounded-2xl bg-white/90',
                        'transform-gpu scale-[1.03]',
                        // Sombra un poco más suave
                        'shadow-[0_18px_55px_rgba(15,23,42,0.24)]',
                        // Halo suave azul (difuminado), sin línea
                        'before:content-[""] before:absolute before:inset-[-8px] before:rounded-[24px]',
                        'before:bg-aloja-navy/16 before:blur-[14px] before:-z-10',
                      ].join(' ')
                    : '',
                ].join(' ')}
                onMouseEnter={() => handleMouseEnter(room)}
                onMouseLeave={handleMouseLeave}
                onClick={() =>
                  onRoomClick &&
                  onRoomClick({
                    room,
                    hotel: hotels.find((h) => h.id === selectedHotel),
                    selectedHotel,
                  })
                }
                onKeyDown={(e) => {
                  if (!onRoomClick) return;
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onRoomClick({
                      room,
                      hotel: hotels.find((h) => h.id === selectedHotel),
                      selectedHotel,
                    });
                  }
                }}
                role={onRoomClick ? 'button' : undefined}
                tabIndex={onRoomClick ? 0 : -1}
                title={`${room.name || `Habitación #${room.number || room.id}`} - ${getEffectiveStatusLabel(room)}${cleaning ? ' (En limpieza)' : ''}`}
              >
                {/* Puerta (centrada dentro del tile) */}
                <div className="flex justify-center">
                  <div className="relative inline-block">
                    <DoorVisual
                      variant={doorVariant}
                      toneClass={getDoorTone(room)}
                      dimmed={isBlocked}
                    />

                  {/* Checkbox de selección: lo mostramos en la línea del nombre (abajo) para no tapar la puerta */}

                  {/* Cintas de peligro (mantenimiento) */}
                  {isMaintenance && (
                    <div className="pointer-events-none absolute inset-0 z-10">
                      <div className="absolute inset-0 rounded-xl md:rounded-2xl overflow-hidden">
                        <div
                          className="absolute -left-6 top-1/2 h-4 w-[140%] -translate-y-1/2 rotate-[-18deg] bg-[repeating-linear-gradient(45deg,rgba(0,0,0,0.75)_0,rgba(0,0,0,0.75)_10px,rgba(250,204,21,0.95)_10px,rgba(250,204,21,0.95)_20px)] shadow"
                          style={{ opacity: 0.95 }}
                        />
                        <div
                          className="absolute -left-6 top-1/2 h-4 w-[140%] -translate-y-1/2 rotate-[18deg] bg-[repeating-linear-gradient(45deg,rgba(0,0,0,0.75)_0,rgba(0,0,0,0.75)_10px,rgba(250,204,21,0.95)_10px,rgba(250,204,21,0.95)_20px)] shadow"
                          style={{ opacity: 0.95 }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Badges */}
                  {isOccupied && (
                    <DoorBadge className="w-6 h-6 md:w-7 md:h-7 bg-white/90 text-slate-900 ring-1 ring-black/5">
                      <IconLock className="w-4 h-4 md:w-4.5 md:h-4.5 text-slate-800" />
                    </DoorBadge>
                  )}
                  {isConfirmed && (
                    <DoorBadge className="w-6 h-6 md:w-7 md:h-7 bg-white/90 text-slate-900 ring-1 ring-black/5">
                      <IconCheck className="w-4 h-4 md:w-4.5 md:h-4.5 text-blue-700" />
                    </DoorBadge>
                  )}
                  {showCleaningBadge && (
                    <DoorBadge
                      className={[
                        "w-6 h-6 md:w-7 md:h-7",
                        // Resalte primary (azul) con gradiente
                        "bg-gradient-to-br from-sky-500 to-sky-700 ring-1 ring-white/60",
                        "shadow-[0_10px_24px_rgba(2,132,199,0.35)]",
                      ].join(" ")}
                    >
                      <CleaningIcon size="16" className="text-white" />
                    </DoorBadge>
                  )}
                  {showDirtyBadge && (
                    <DoorBadge
                      className={[
                        "w-6 h-6 md:w-7 md:h-7",
                        // Resalte warning (ámbar) con gradiente
                        "bg-gradient-to-br from-amber-500 to-amber-600 ring-1 ring-white/60",
                        "shadow-[0_10px_24px_rgba(245,158,11,0.38)]",
                      ].join(" ")}
                    >
                      <DirtIcon size={18} className="text-white" />
                    </DoorBadge>
                  )}
                  </div>
                </div>

                {/* Texto debajo (como antes) */}
                <div className="mt-1.5 md:mt-2 flex flex-col items-center gap-0.5 select-none">
                  <div className="text-[10px] md:text-xs font-semibold text-slate-800 inline-flex items-center gap-2">
                    {(typeof onSelectedRoomIdsChange === 'function' || !selectedRoomIds) && (
                      <input
                        type="checkbox"
                        aria-label="Seleccionar habitación"
                        checked={isSelected}
                        onChange={() => toggleSelected(room.id)}
                        onClick={(e) => e.stopPropagation()}
                        className="w-3.5 h-3.5 accent-[#0A304A]"
                      />
                    )}
                    <span>{plateText}</span>
                  </div>
                  <div className={`text-[10px] md:text-[11px] text-slate-600 text-center max-w-[110px] md:max-w-[150px] whitespace-nowrap overflow-hidden text-ellipsis ${room?.cleaning_status === 'clean' ? 'px-3' : ''}`}>
                    {getRoomStatusLine(room)}
                  </div>
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

