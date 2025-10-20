import React, { useState, useEffect } from "react";
import { useUnreadCount, useRecentNotifications, useNotifications } from "src/hooks/useNotifications";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";
import BellRealIcon from "src/assets/icons/BellRealIcon";
import CheckCircleIcon from "src/assets/icons/CheckCircleIcon";

const NotificationsBell = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [animatingOut, setAnimatingOut] = useState(false);
  const [markedNotifications, setMarkedNotifications] = useState(new Set());
  const { unreadCount, isLoading: isLoadingCount } = useUnreadCount();
  const { recentNotifications, isLoading: isLoadingRecent } = useRecentNotifications();
  const { markAsRead } = useNotifications();

  const handleMarkAsRead = (notificationId) => {
    // Agregar a la lista de notificaciones marcadas para animación
    setMarkedNotifications(prev => new Set([...prev, notificationId]));
    
    // Marcar como leída después de un pequeño delay para la animación
    setTimeout(() => {
      markAsRead(notificationId);
      setMarkedNotifications(prev => {
        const newSet = new Set(prev);
        newSet.delete(notificationId);
        return newSet;
      });
    }, 300);
  };

  const getNotificationIcon = (type) => {
    const icons = {
      auto_cancel: "🔴",
      no_show: "🟣", 
      refund_auto: "🟡",
      refund_failed: "🟠",
      manual_cancel: "🔵",
      general: "📢"
    };
    return icons[type] || "🔔";
  };

  const getNotificationColor = (type) => {
    const colors = {
      auto_cancel: "text-red-600 bg-red-50 border-red-200",
      no_show: "text-purple-600 bg-purple-50 border-purple-200",
      refund_auto: "text-yellow-600 bg-yellow-50 border-yellow-200",
      refund_failed: "text-orange-600 bg-orange-50 border-orange-200",
      manual_cancel: "text-blue-600 bg-blue-50 border-blue-200",
      general: "text-gray-600 bg-gray-50 border-gray-200"
    };
    return colors[type] || "text-gray-600 bg-gray-50 border-gray-200";
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

  const handleClose = () => {
    setAnimatingOut(true);
    setTimeout(() => {
      setIsOpen(false);
      setAnimatingOut(false);
    }, 200);
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
            transform: translateY(-20px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        
        @keyframes slideOutUp {
          from {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
          to {
            opacity: 0;
            transform: translateY(-20px) scale(0.95);
          }
        }
        
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        @keyframes slideInRight {
          from {
            opacity: 0;
            transform: translateX(20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        @keyframes slideOutLeft {
          from {
            opacity: 1;
            transform: translateX(0);
          }
          to {
            opacity: 0;
            transform: translateX(-20px);
          }
        }
        
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
        
        @keyframes bounce {
          0%, 20%, 53%, 80%, 100% {
            transform: translate3d(0,0,0);
          }
          40%, 43% {
            transform: translate3d(0, -8px, 0);
          }
          70% {
            transform: translate3d(0, -4px, 0);
          }
          90% {
            transform: translate3d(0, -2px, 0);
          }
        }
        
        .notification-item {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .notification-item.entering {
          animation: slideInRight 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .notification-item.leaving {
          animation: slideOutLeft 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .notification-item.marked {
          background: linear-gradient(90deg, #f0f9ff 0%, #e0f2fe 100%);
          border-left: 4px solid #0ea5e9;
        }
        
        .dropdown-enter {
          animation: slideInDown 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .dropdown-exit {
          animation: slideOutUp 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .bell-pulse {
          animation: pulse 2s infinite;
        }
        
        .bell-bounce {
          animation: bounce 1s infinite;
        }
      `}</style>
      
      <div className="relative">
        {/* Botón de la campanita mejorado */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`relative p-3 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded-full transition-all duration-300 ${
            unreadCount > 0 
              ? 'bell-pulse hover:bell-bounce' 
              : 'hover:scale-110'
          }`}
          style={{
            animation: unreadCount > 0 ? 'bellShake 2s ease-in-out infinite' : 'none'
          }}
        >
          <BellRealIcon size="22" />
          
          {/* Badge de notificaciones mejorado */}
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 h-6 w-6 bg-gradient-to-r from-red-500 to-pink-500 text-white text-xs rounded-full flex items-center justify-center animate-pulse shadow-lg ring-2 ring-red-200 font-bold">
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          )}
          
          {/* Indicador de actualización */}
          <div className="absolute -bottom-1 -right-1">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse shadow-sm" title="Actualizando cada 5 segundos" />
          </div>
        </button>

        {/* Dropdown de notificaciones moderno */}
        {isOpen && (
          <>
            {/* Overlay mejorado */}
            <div
              className="fixed inset-0 z-10 bg-black bg-opacity-20 backdrop-blur-sm"
              onClick={handleClose}
            />
            
            {/* Panel de notificaciones moderno */}
            <div className={`absolute right-0 mt-3 w-96 bg-white rounded-2xl shadow-2xl ring-1 ring-black ring-opacity-5 z-20 overflow-hidden ${
              animatingOut ? 'dropdown-exit' : 'dropdown-enter'
            }`}>
              {/* Header mejorado */}
              <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold flex items-center">
                      <BellRealIcon size="20" className="mr-2" />
                      Notificaciones
                    </h3>
                    <p className="text-indigo-100 text-sm mt-1">
                      Actualizando cada 5 segundos
                    </p>
                  </div>
                  {unreadCount > 0 && (
                    <div className="bg-white bg-opacity-20 rounded-full px-3 py-1">
                      <span className="text-sm font-semibold">
                        {unreadCount} sin leer
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Contenido de notificaciones */}
              <div className="max-h-96 overflow-y-auto">
                {isLoadingRecent ? (
                  <div className="p-8 text-center">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                    <p className="text-gray-500 mt-2">Cargando notificaciones...</p>
                  </div>
                ) : recentNotifications.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    <BellRealIcon size="48" className="mx-auto mb-4 text-gray-300" />
                    <p className="text-lg font-medium">No hay notificaciones</p>
                    <p className="text-sm">Te notificaremos cuando haya algo nuevo</p>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-100">
                    {recentNotifications.map((notification, index) => (
                      <div
                        key={notification.id}
                        className={`notification-item p-5 hover:bg-gray-50 transition-all duration-300 ${
                          !notification.is_read ? "bg-blue-50 border-l-4 border-blue-400" : ""
                        } ${
                          markedNotifications.has(notification.id) ? "marked" : ""
                        }`}
                        style={{
                          animationDelay: `${index * 0.1}s`
                        }}
                      >
                        <div className="flex items-start space-x-4">
                          {/* Icono mejorado */}
                          <div className="flex-shrink-0">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center">
                              <span className="text-lg">
                                {getNotificationIcon(notification.type)}
                              </span>
                            </div>
                          </div>
                          
                          {/* Contenido de la notificación */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <p className="text-sm font-semibold text-gray-900 truncate">
                                {notification.title}
                              </p>
                              {!notification.is_read && !markedNotifications.has(notification.id) && (
                                <button
                                  onClick={() => handleMarkAsRead(notification.id)}
                                  className="ml-2 p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-all duration-200 group"
                                  title="Marcar como leída"
                                >
                                  <CheckCircleIcon size="16" className="group-hover:scale-110 transition-transform" />
                                </button>
                              )}
                              {markedNotifications.has(notification.id) && (
                                <div className="ml-2 p-2 text-green-500">
                                  <CheckCircleIcon size="16" className="animate-pulse" />
                                </div>
                              )}
                            </div>
                            
                            <p className="text-sm text-gray-600 mt-2 line-clamp-2 leading-relaxed">
                              {notification.message}
                            </p>
                            
                            <div className="flex items-center justify-between mt-3">
                              <span className={`text-xs px-3 py-1 rounded-full border font-medium ${getNotificationColor(notification.type)}`}>
                                {notification.type_display || notification.type}
                              </span>
                              <span className="text-xs text-gray-500 font-medium">
                                {formatNotificationTime(notification.created_at)}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer mejorado */}
              {recentNotifications.length > 0 && (
                <div className="bg-gray-50 px-6 py-4 border-t border-gray-100">
                  <a
                    href="/notificaciones"
                    className="block w-full text-center text-sm text-indigo-600 hover:text-indigo-500 font-semibold transition-colors duration-200 hover:bg-indigo-50 py-2 rounded-lg"
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
