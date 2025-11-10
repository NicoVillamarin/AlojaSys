import React, { useState } from "react";
import { useNotifications } from "src/hooks/useNotifications";
import { useUpdate } from "src/hooks/useUpdate";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";
import BellRealIcon from "src/assets/icons/BellRealIcon";
import XIcon from "src/assets/icons/Xicon";
import ExclamationTriangleIcon from "src/assets/icons/ExclamationTriangleIcon";
import CheckCircleIcon from "src/assets/icons/CheckCircleIcon";
import InfoIcon from "src/assets/icons/InfoIcon";
import Button from "src/components/Button";

const Notifications = () => {
  const [filter, setFilter] = useState("all"); // all, unread, read
  const [typeFilter, setTypeFilter] = useState("all");
  
  // Agregar CSS para animaciones
  React.useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      @keyframes fadeInUp {
        from {
          opacity: 0;
          transform: translateY(20px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
    `;
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);
  
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
    markAsReadMutation({ id: notificationId, body: { is_read: true } });
  };

  const handleMarkAllAsRead = () => {
    markAllAsRead();
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case "auto_cancel":
        return <XIcon size="16" className="text-red-500" />;
      case "no_show":
        return <ExclamationTriangleIcon size="16" className="text-purple-500" />;
      case "refund_auto":
        return <CheckCircleIcon size="16" className="text-yellow-500" />;
      case "refund_failed":
        return <XIcon size="16" className="text-orange-500" />;
      case "ota_reservation_received":
        return <CheckCircleIcon size="16" className="text-green-500" />;
      default:
        return <InfoIcon size="16" className="text-gray-500" />;
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
      case "ota_reservation_received":
        return "text-green-600 bg-green-50 border-green-200";
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

  // Filtrar notificaciones
  const filteredNotifications = notifications.filter(notification => {
    const matchesFilter = filter === "all" || 
      (filter === "unread" && !notification.is_read) ||
      (filter === "read" && notification.is_read);
    
    const matchesType = typeFilter === "all" || notification.type === typeFilter;
    
    return matchesFilter && matchesType;
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando notificaciones...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <XIcon size="20" className="text-red-500 mx-auto mb-4" />
          <p className="text-gray-600">Error al cargar las notificaciones</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <BellRealIcon size="20" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Notificaciones
                </h1>
                <p className="text-gray-600">
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
                className="flex flex-row items-center px-6 py-3 border border-transparent text-sm font-medium rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-all duration-200 shadow-lg hover:shadow-xl hover:scale-105"
              >
                <CheckCircleIcon className="mr-2 !w-6 !h-6" />
                {isMarkingAllAsRead ? "Marcando..." : "Marcar todas como leídas"}
              </button>
            )}
          </div>
        </div>

        {/* Filtros */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Filtro por estado */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Estado
              </label>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="all">Todas</option>
                <option value="unread">Sin leer</option>
                <option value="read">Leídas</option>
              </select>
            </div>

            {/* Filtro por tipo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo
              </label>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="all">Todos los tipos</option>
                <option value="auto_cancel">Auto Cancelación</option>
                <option value="no_show">No Show</option>
                <option value="refund_auto">Reembolso Automático</option>
                <option value="refund_failed">Reembolso Fallido</option>
                <option value="ota_reservation_received">Nueva Reserva OTA</option>
              </select>
            </div>
          </div>
        </div>

        {/* Lista de notificaciones */}
        <div className="bg-white rounded-lg shadow">
          {filteredNotifications.length === 0 ? (
            <div className="p-8 text-center">
              <BellRealIcon size="20" className="text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No hay notificaciones</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {filteredNotifications.map((notification, index) => (
                <div
                  key={notification.id}
                  className={`p-6 hover:bg-gray-50 transition-all duration-300 hover:shadow-md ${
                    !notification.is_read ? "bg-blue-50 border-l-4 border-l-blue-500" : ""
                  }`}
                  style={{
                    animationDelay: `${index * 0.1}s`,
                    animation: 'fadeInUp 0.5s ease-out'
                  }}
                >
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      {getNotificationIcon(notification.type)}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <h3 className="text-lg font-medium text-gray-900">
                            {notification.title}
                          </h3>
                          <span className={`text-xs px-2 py-1 rounded-full border ${getNotificationColor(notification.type)}`}>
                            {notification.type_display}
                          </span>
                          {!notification.is_read && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              Sin leer
                            </span>
                          )}
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-500">
                            {formatNotificationTime(notification.created_at)}
                          </span>
                          {!notification.is_read && (
                            <button
                              onClick={() => handleMarkAsRead(notification.id)}
                              className="p-1 text-gray-400 hover:text-gray-600"
                              title="Marcar como leída"
                            >
                              <CheckCircleIcon size="16" />
                            </button>
                          )}
                        </div>
                      </div>
                      
                      <p className="mt-2 text-gray-600 whitespace-pre-wrap">
                        {notification.message}
                      </p>
                      
                      {/* Información adicional */}
                      {(notification.hotel_id || notification.reservation_id) && (
                        <div className="mt-3 flex items-center space-x-4 text-sm text-gray-500">
                          {notification.hotel_id && (
                            <span>Hotel ID: {notification.hotel_id}</span>
                          )}
                          {notification.reservation_id && (
                            <span>Reserva ID: {notification.reservation_id}</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Notifications;
