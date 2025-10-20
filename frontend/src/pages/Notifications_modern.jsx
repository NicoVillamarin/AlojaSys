import React, { useState, useEffect } from "react";
import { useNotifications } from "src/hooks/useNotifications";
import { useUpdate } from "src/hooks/useUpdate";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";
import BellRealIcon from "src/assets/icons/BellRealIcon";
import XIcon from "src/assets/icons/Xicon";
import ExclamationTriangleIcon from "src/assets/icons/ExclamationTriangleIcon";
import CheckCircleIcon from "src/assets/icons/CheckCircleIcon";
import InfoIcon from "src/assets/icons/InfoIcon";

const Notifications = () => {
  const [filter, setFilter] = useState("all"); // all, unread, read
  const [typeFilter, setTypeFilter] = useState("all");
  const [animatingNotifications, setAnimatingNotifications] = useState(new Set());
  const [markedNotifications, setMarkedNotifications] = useState(new Set());
  
  const {
    notifications,
    unreadCount,
    isLoading,
    isError,
    markAsRead,
    markAllAsRead,
    isMarkingAllAsRead
  } = useNotifications();

  const { mutate: markAsReadMutation } = useUpdate({ 
    resource: "notifications",
    onSuccess: () => {
      // El hook ya maneja la invalidación del cache
    }
  });

  const handleMarkAsRead = (notificationId) => {
    // Agregar a la lista de notificaciones marcadas para animación
    setMarkedNotifications(prev => new Set([...prev, notificationId]));
    
    // Marcar como leída después de un pequeño delay para la animación
    setTimeout(() => {
      markAsReadMutation({ id: notificationId, body: { is_read: true } });
      setMarkedNotifications(prev => {
        const newSet = new Set(prev);
        newSet.delete(notificationId);
        return newSet;
      });
    }, 300);
  };

  const handleMarkAllAsRead = () => {
    markAllAsRead();
  };

  const getNotificationIcon = (type) => {
    const iconProps = { size: "20", className: "flex-shrink-0" };
    
    switch (type) {
      case "auto_cancel":
        return <XIcon {...iconProps} className="text-red-500" />;
      case "no_show":
        return <ExclamationTriangleIcon {...iconProps} className="text-purple-500" />;
      case "refund_auto":
        return <CheckCircleIcon {...iconProps} className="text-yellow-500" />;
      case "refund_failed":
        return <XIcon {...iconProps} className="text-orange-500" />;
      case "manual_cancel":
        return <XIcon {...iconProps} className="text-blue-500" />;
      default:
        return <InfoIcon {...iconProps} className="text-gray-500" />;
    }
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

  // Filtrar notificaciones
  const filteredNotifications = notifications.filter(notification => {
    const matchesStatus = filter === "all" || 
      (filter === "unread" && !notification.is_read) || 
      (filter === "read" && notification.is_read);
    
    const matchesType = typeFilter === "all" || notification.type === typeFilter;
    
    return matchesStatus && matchesType;
  });

  return (
    <>
      <style jsx>{`
        @keyframes slideInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes slideOutLeft {
          from {
            opacity: 1;
            transform: translateX(0);
          }
          to {
            opacity: 0;
            transform: translateX(-100%);
          }
        }
        
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
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
        
        @keyframes shimmer {
          0% {
            background-position: -200px 0;
          }
          100% {
            background-position: calc(200px + 100%) 0;
          }
        }
        
        .notification-card {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          animation: slideInUp 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .notification-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }
        
        .notification-card.marked {
          background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
          border-left: 4px solid #0ea5e9;
          transform: scale(0.98);
        }
        
        .notification-card.leaving {
          animation: slideOutLeft 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .skeleton {
          background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
          background-size: 200px 100%;
          animation: shimmer 1.5s infinite;
        }
        
        .gradient-text {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        
        .floating-action {
          animation: bounce 2s infinite;
        }
      `}</style>
      
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header mejorado */}
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 border border-gray-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl">
                  <BellRealIcon size="32" className="text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold gradient-text">
                    Notificaciones
                  </h1>
                  <p className="text-gray-600 mt-1">
                    {unreadCount > 0 
                      ? `${unreadCount} notificación${unreadCount !== 1 ? 'es' : ''} sin leer`
                      : "Todas las notificaciones están leídas"
                    }
                  </p>
                </div>
              </div>
              
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllAsRead}
                  disabled={isMarkingAllAsRead}
                  className="floating-action inline-flex items-center px-8 py-4 border border-transparent text-lg font-semibold rounded-2xl text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-all duration-300 shadow-xl hover:shadow-2xl transform hover:scale-105"
                >
                  <CheckCircleIcon size="20" className="mr-3" />
                  {isMarkingAllAsRead ? "Marcando..." : "Marcar todas como leídas"}
                </button>
              )}
            </div>
          </div>

          {/* Filtros mejorados */}
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-8 border border-gray-100">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Estado
                </label>
                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors duration-200"
                >
                  <option value="all">Todas</option>
                  <option value="unread">Sin leer</option>
                  <option value="read">Leídas</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Tipo
                </label>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors duration-200"
                >
                  <option value="all">Todos los tipos</option>
                  <option value="auto_cancel">Auto Cancelación</option>
                  <option value="manual_cancel">Cancelación Manual</option>
                  <option value="no_show">No Show</option>
                  <option value="refund_auto">Reembolso Automático</option>
                  <option value="refund_failed">Reembolso Fallido</option>
                  <option value="general">General</option>
                </select>
              </div>
            </div>
          </div>

          {/* Lista de notificaciones */}
          <div className="space-y-4">
            {isLoading ? (
              // Skeleton loading
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
                    <div className="flex items-start space-x-4">
                      <div className="skeleton w-12 h-12 rounded-full"></div>
                      <div className="flex-1 space-y-3">
                        <div className="skeleton h-4 w-3/4 rounded"></div>
                        <div className="skeleton h-3 w-1/2 rounded"></div>
                        <div className="skeleton h-3 w-1/4 rounded"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : isError ? (
              <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center">
                <XIcon size="48" className="mx-auto text-red-500 mb-4" />
                <h3 className="text-lg font-semibold text-red-800 mb-2">
                  Error al cargar notificaciones
                </h3>
                <p className="text-red-600">
                  Por favor, intenta recargar la página
                </p>
              </div>
            ) : filteredNotifications.length === 0 ? (
              <div className="bg-white rounded-2xl shadow-lg p-12 text-center border border-gray-100">
                <BellRealIcon size="64" className="mx-auto text-gray-300 mb-6" />
                <h3 className="text-2xl font-semibold text-gray-800 mb-2">
                  No hay notificaciones
                </h3>
                <p className="text-gray-600 text-lg">
                  {filter === "all" 
                    ? "No tienes notificaciones aún"
                    : `No hay notificaciones ${filter === "unread" ? "sin leer" : "leídas"}`
                  }
                </p>
              </div>
            ) : (
              filteredNotifications.map((notification, index) => (
                <div
                  key={notification.id}
                  className={`notification-card bg-white rounded-2xl shadow-lg p-6 border border-gray-100 ${
                    !notification.is_read ? "border-l-4 border-l-blue-400" : ""
                  } ${
                    markedNotifications.has(notification.id) ? "marked" : ""
                  }`}
                  style={{
                    animationDelay: `${index * 0.1}s`
                  }}
                >
                  <div className="flex items-start space-x-4">
                    {/* Icono */}
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center">
                        {getNotificationIcon(notification.type)}
                      </div>
                    </div>
                    
                    {/* Contenido */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            {notification.title}
                          </h3>
                          <p className="text-gray-600 leading-relaxed mb-4">
                            {notification.message}
                          </p>
                          
                          <div className="flex items-center space-x-4 text-sm text-gray-500">
                            <span className={`px-3 py-1 rounded-full border font-medium ${getNotificationColor(notification.type)}`}>
                              {notification.type_display || notification.type}
                            </span>
                            <span className="font-medium">
                              {formatNotificationTime(notification.created_at)}
                            </span>
                            {notification.hotel_id && (
                              <span>Hotel ID: {notification.hotel_id}</span>
                            )}
                            {notification.reservation_id && (
                              <span>Reserva ID: {notification.reservation_id}</span>
                            )}
                          </div>
                        </div>
                        
                        {/* Botón de marcar como leída */}
                        {!notification.is_read && !markedNotifications.has(notification.id) && (
                          <button
                            onClick={() => handleMarkAsRead(notification.id)}
                            className="ml-4 p-3 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all duration-200 group"
                            title="Marcar como leída"
                          >
                            <CheckCircleIcon size="20" className="group-hover:scale-110 transition-transform" />
                          </button>
                        )}
                        
                        {markedNotifications.has(notification.id) && (
                          <div className="ml-4 p-3 text-green-500">
                            <CheckCircleIcon size="20" className="animate-pulse" />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default Notifications;
