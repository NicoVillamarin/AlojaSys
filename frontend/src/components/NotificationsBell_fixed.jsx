import React, { useState } from "react";
import { useUnreadCount, useRecentNotifications, useNotifications } from "src/hooks/useNotifications";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";
import BellRealIcon from "src/assets/icons/BellRealIcon";
import CheckCircleIcon from "src/assets/icons/CheckCircleIcon";

const NotificationsBell = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { unreadCount, isLoading: isLoadingCount } = useUnreadCount();
  const { recentNotifications, isLoading: isLoadingRecent } = useRecentNotifications();
  const { markAsRead } = useNotifications();

  const handleMarkAsRead = (notificationId) => {
    markAsRead(notificationId);
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
    <div className="relative">
      {/* Botón de la campanita */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded-full"
      >
        <BellRealIcon size="20" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 h-5 w-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown de notificaciones */}
      {isOpen && (
        <>
          {/* Overlay para cerrar al hacer click fuera */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          
          {/* Panel de notificaciones */}
          <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 z-20">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">
                  Notificaciones
                </h3>
                {unreadCount > 0 && (
                  <span className="text-sm text-gray-500">
                    {unreadCount} sin leer
                  </span>
                )}
              </div>
            </div>

            <div className="max-h-96 overflow-y-auto">
              {isLoadingRecent ? (
                <div className="p-4 text-center text-gray-500">
                  Cargando notificaciones...
                </div>
              ) : recentNotifications.length === 0 ? (
                <div className="p-4 text-center text-gray-500">
                  No hay notificaciones
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {recentNotifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-4 hover:bg-gray-50 transition-colors ${
                        !notification.is_read ? "bg-blue-50" : ""
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0">
                          <span className="text-lg">
                            {getNotificationIcon(notification.type)}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {notification.title}
                            </p>
                            {!notification.is_read && (
                              <button
                                onClick={() => handleMarkAsRead(notification.id)}
                                className="ml-2 p-1 text-gray-400 hover:text-gray-600"
                                title="Marcar como leída"
                              >
                                <CheckCircleIcon size="16" />
                              </button>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                            {notification.message}
                          </p>
                          <div className="flex items-center justify-between mt-2">
                            <span className={`text-xs px-2 py-1 rounded-full border ${getNotificationColor(notification.type)}`}>
                              {notification.type_display || notification.type}
                            </span>
                            <span className="text-xs text-gray-500">
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

            {recentNotifications.length > 0 && (
              <div className="p-4 border-t border-gray-200">
                <a
                  href="/notificaciones"
                  className="block w-full text-center text-sm text-indigo-600 hover:text-indigo-500 font-medium"
                >
                  Ver todas las notificaciones
                </a>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default NotificationsBell;

