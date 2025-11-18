import React, { useState } from "react";
import { useUnreadCount, useRecentNotifications, useNotifications } from "src/hooks/useNotifications";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";
import BellRealIcon from "src/assets/icons/BellRealIcon";
import CheckCircleIcon from "src/assets/icons/CheckCircleIcon";

// Función para agrupar notificaciones relacionadas
const groupRelatedNotifications = (notifications) => {
  const grouped = [];
  const processed = new Set();

  notifications.forEach((notification, index) => {
    if (processed.has(index)) return;

    const related = [notification];
    const reservationId = notification.reservation_id;
    const hotelId = notification.hotel_id;
    const timeDiff = 2 * 60 * 1000; // 2 minutos en milisegundos

    // Buscar notificaciones relacionadas
    notifications.forEach((otherNotification, otherIndex) => {
      if (otherIndex !== index && !processed.has(otherIndex)) {
        const isSameReservation = otherNotification.reservation_id === reservationId;
        const isSameHotel = otherNotification.hotel_id === hotelId;
        const timeDifference = Math.abs(
          new Date(notification.created_at) - new Date(otherNotification.created_at)
        );

        if ((isSameReservation || isSameHotel) && timeDifference <= timeDiff) {
          related.push(otherNotification);
          processed.add(otherIndex);
        }
      }
    });

    processed.add(index);
    grouped.push({
      id: `group-${index}`,
      notifications: related,
      isGroup: related.length > 1,
      reservationId,
      hotelId
    });
  });

  return grouped;
};

const NotificationsBell = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { unreadCount, isLoading: isLoadingCount } = useUnreadCount();
  const { recentNotifications, isLoading: isLoadingRecent } = useRecentNotifications();
  const { markAsRead } = useNotifications();

  // Agrupar notificaciones relacionadas
  const groupedNotifications = groupRelatedNotifications(recentNotifications);
  const displayCount = groupedNotifications.length;

  const handleMarkAsRead = (notificationId) => {
    // Pequeña animación antes de marcar como leída
    const element = document.querySelector(`[data-notification-id="${notificationId}"]`);
    if (element) {
      element.style.transition = 'all 0.3s ease';
      element.style.opacity = '0.5';
      element.style.transform = 'scale(0.95)';
    }
    
    setTimeout(() => {
      markAsRead(notificationId);
    }, 150);
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case "auto_cancel":
        return "🔴";
      case "no_show":
        return "🟣";
      case "refund_auto":
        return "🟡";
      case "refund_failed":
        return "🟠";
      default:
        return "🔔";
    }
  };

  const getNotificationColor = (type) => {
    switch (type) {
      case "auto_cancel":
        return "text-red-600 bg-red-50 border-red-200";
      case "no_show":
        return "text-purple-600 bg-purple-50 border-purple-200";
      case "refund_auto":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "refund_failed":
        return "text-orange-600 bg-orange-50 border-orange-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const formatNotificationTime = (createdAt) => {
    try {
      return formatDistanceToNow(new Date(createdAt), { 
        addSuffix: true, 
        locale: es 
      });
    } catch (error) {
      return "Hace un momento";
    }
  };


  return (
    <>
      <style jsx>{`
        @keyframes bellShake {
          0%, 100% { transform: rotate(0deg); }
          10% { transform: rotate(-10deg); }
          20% { transform: rotate(10deg); }
          30% { transform: rotate(-10deg); }
          40% { transform: rotate(10deg); }
          50% { transform: rotate(-5deg); }
          60% { transform: rotate(5deg); }
          70% { transform: rotate(-3deg); }
          80% { transform: rotate(3deg); }
          90% { transform: rotate(-1deg); }
        }
        
        @keyframes slideInDown {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes pulseGlow {
          0%, 100% {
            box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.6);
          }
          50% {
            box-shadow: 0 0 0 12px rgba(245, 158, 11, 0.2);
          }
        }
        
        @keyframes bellGlow {
          0%, 100% {
            box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.3);
          }
          50% {
            box-shadow: 0 0 0 8px rgba(245, 158, 11, 0.1);
          }
        }
      `}</style>
      
      <div className="relative">
        {/* Botón de la campanita modernizado */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`relative p-3 text-gray-500 hover:text-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-2 rounded-full transition-all duration-300 ${
            displayCount > 0 
              ? 'bg-amber-50 shadow-lg ring-2 ring-amber-200' 
              : 'hover:scale-110 hover:bg-amber-50'
          }`}
          style={{
            animation: displayCount > 0 ? 'bellGlow 2s ease-in-out infinite' : 'none'
          }}
        >
          <div 
            className={`transition-all duration-300 ${
              displayCount > 0 ? 'animate-pulse' : ''
            }`}
            style={{
              animation: displayCount > 0 ? 'bellShake 2s ease-in-out infinite' : 'none'
            }}
          >
            <BellRealIcon 
              size="24" 
              className={`transition-all duration-300 ${
                displayCount > 0 
                  ? 'text-amber-600 drop-shadow-lg' 
                  : 'text-gray-500'
              }`}
            />
          </div>
          {displayCount > 0 && (
            <span 
              className="absolute -top-0.5 -right-0.5 h-5 w-5 bg-gradient-to-r from-amber-500 to-amber-600 text-white text-xs rounded-full flex items-center justify-center font-bold shadow-lg ring-1 ring-amber-300"
              style={{
                animation: 'pulseGlow 2s infinite'
              }}
            >
              {displayCount > 99 ? "99+" : displayCount}
            </span>
          )}
        </button>

        {/* Dropdown de notificaciones modernizado */}
        {isOpen && (
          <>
            {/* Overlay para cerrar al hacer click fuera */}
            <div
              className="fixed inset-0 z-[100]"
              onClick={() => setIsOpen(false)}
            />
            
            {/* Panel de notificaciones con diseño moderno */}
            <div 
              className="absolute right-0 mt-2 w-96 max-w-[90vw] bg-white rounded-xl shadow-2xl ring-1 ring-gray-200 z-[101] overflow-hidden"
              style={{
                animation: 'slideInDown 0.3s ease-out'
              }}
            >
              {/* Header con gradiente dorado */}
              <div className="bg-gradient-to-r from-aloja-gold to-aloja-gold2 p-4 text-white">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-white bg-opacity-30 rounded-full shadow-lg">
                      <BellRealIcon size="20" className="text-aloja-gold drop-shadow-sm" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold drop-shadow-sm">
                        Notificaciones
                      </h3>
                      <p className="text-xs text-amber-100 font-medium">
                        Actualizando cada 5 segundos
                      </p>
                    </div>
                  </div>
                  {displayCount > 0 && (
                    <div className="flex items-center space-x-2">
                      <div className="px-3 py-1.5 bg-white text-aloja-gold rounded-full text-xs font-bold shadow-lg border border-white border-opacity-30">
                        {displayCount} {displayCount === 1 ? 'grupo' : 'grupos'} sin leer
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Contenido de notificaciones */}
              <div className="max-h-96 overflow-y-auto">
                {isLoadingRecent ? (
                  <div className="p-8 text-center">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-aloja-gold"></div>
                    <p className="mt-3 text-gray-500 font-medium">Cargando notificaciones...</p>
                  </div>
                ) : groupedNotifications.length === 0 ? (
                  <div className="p-8 text-center">
                    <div className="w-16 h-16 bg-gradient-to-br from-amber-100 to-amber-200 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                      <BellRealIcon size="24" className="text-amber-500" />
                    </div>
                    <p className="text-gray-600 font-semibold text-lg">No hay notificaciones</p>
                    <p className="text-sm text-gray-500 mt-2">Te notificaremos cuando haya novedades</p>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-100">
                    {groupedNotifications.map((group, groupIndex) => (
                      <div
                        key={group.id}
                        className={`p-3 hover:bg-amber-50 transition-all duration-300 hover:shadow-sm ${
                          group.isGroup ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-l-blue-500' : ''
                        }`}
                        style={{
                          animationDelay: `${groupIndex * 0.1}s`,
                          animation: 'slideInDown 0.5s ease-out'
                        }}
                      >
                        {group.isGroup ? (
                          // Grupo de notificaciones relacionadas
                          <div className="space-y-3">
                            <div className="flex items-center space-x-2 mb-2">
                              <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                                <span className="text-xs">📋</span>
                              </div>
                              <span className="text-xs font-semibold text-blue-700">
                                {group.notifications.length} notificaciones relacionadas
                              </span>
                            </div>
                            {group.notifications.map((notification, notifIndex) => (
                              <div key={notification.id} className="ml-4 pl-4 border-l-2 border-blue-200">
                                <div className="flex items-start space-x-3">
                                  <div className="flex-shrink-0">
                                    <div className="w-6 h-6 bg-amber-100 rounded-full flex items-center justify-center">
                                      <span className="text-xs">
                                        {getNotificationIcon(notification.type)}
                                      </span>
                                    </div>
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-gray-900 mb-1">
                                      {notification.title}
                                    </p>
                                    <p className="text-xs text-gray-600 mb-2">
                                      {notification.message}
                                    </p>
                                    <div className="flex items-center justify-between">
                                      <span className={`text-xs px-2 py-1 rounded-full font-medium ${getNotificationColor(notification.type)}`}>
                                        {notification.type_display || notification.type}
                                      </span>
                                      <span className="text-xs text-gray-500">
                                        {formatNotificationTime(notification.created_at)}
                                      </span>
                                    </div>
                                  </div>
                                  {!notification.is_read && (
                                    <button
                                      onClick={() => handleMarkAsRead(notification.id)}
                                      className="ml-2 p-1 text-gray-400 hover:text-amber-600 hover:bg-amber-100 rounded-full transition-all duration-200"
                                      title="Marcar como leída"
                                    >
                                      <CheckCircleIcon size="12" />
                                    </button>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          // Notificación individual
                          <div className="flex items-start space-x-3">
                            <div className="flex-shrink-0">
                              <div className="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center group-hover:bg-aloja-gold group-hover:text-white transition-all duration-300">
                                <span className="text-sm">
                                  {getNotificationIcon(group.notifications[0].type)}
                                </span>
                              </div>
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <p className="text-sm font-semibold text-gray-900 mb-1 line-clamp-1">
                                    {group.notifications[0].title}
                                  </p>
                                  <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                                    {group.notifications[0].message}
                                  </p>
                                  <div className="flex items-center justify-between">
                                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${getNotificationColor(group.notifications[0].type)}`}>
                                      {group.notifications[0].type_display || group.notifications[0].type}
                                    </span>
                                    <span className="text-xs text-gray-500 font-medium">
                                      {formatNotificationTime(group.notifications[0].created_at)}
                                    </span>
                                  </div>
                                </div>
                                {!group.notifications[0].is_read && (
                                  <button
                                    onClick={() => handleMarkAsRead(group.notifications[0].id)}
                                    className="ml-2 p-1.5 text-gray-400 hover:text-amber-600 hover:bg-amber-100 rounded-full transition-all duration-200 group-hover:scale-110"
                                    title="Marcar como leída"
                                  >
                                    <CheckCircleIcon size="14" />
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer con enlace modernizado */}
              {groupedNotifications.length > 0 && (
                <div className="p-4 bg-gradient-to-r from-gray-50 to-amber-50 border-t border-amber-200">
                  <a
                    href="/notificaciones"
                    className="block w-full text-center py-3 px-4 text-sm font-bold text-aloja-gold hover:text-aloja-gold2 hover:bg-white rounded-xl transition-all duration-300 hover:shadow-lg border border-amber-200 hover:border-amber-300"
                  >
                    Ver todas las notificaciones
                  </a>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </>
  );
};

export default NotificationsBell;
