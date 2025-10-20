import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listResources } from "src/services/listResources";
import { actionResources } from "src/services/actionResources";
import { updateResources } from "src/services/updateResources";


/**
 * Hook personalizado para gestionar notificaciones
 * Utiliza TanStack Query para manejar el estado y cache de notificaciones
 */
export const useNotifications = (options = {}) => {
  const queryClient = useQueryClient();
  const {
    enabled = true,
    refetchInterval = 5000, // 5 segundos para notificaciones más rápidas
    ...queryOptions
  } = options;

  // Query para obtener notificaciones
  const {
    data: notificationsData,
    isPending: isLoading,
    isError,
    refetch
  } = useQuery({
    queryKey: ["notifications"],
    queryFn: ({ queryKey }) => listResources({ queryKey }),
    enabled,
    refetchInterval,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    refetchIntervalInBackground: true,
    ...queryOptions
  });

  // Extraer las notificaciones del resultado de la API
  const notifications = notificationsData?.results || [];

  // Query para obtener conteo de no leídas
  const {
    data: unreadCountData,
    refetch: refetchUnreadCount
  } = useQuery({
    queryKey: ["notifications", "unread_count"],
    queryFn: ({ queryKey }) => actionResources({ queryKey }),
    enabled,
    refetchInterval,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    refetchIntervalInBackground: true
  });

  // Extraer el conteo de no leídas
  const unreadCount = unreadCountData?.unread_count || 0;

  // Query para obtener notificaciones recientes (últimas 5)
  const {
    data: recentNotificationsData,
    refetch: refetchRecent
  } = useQuery({
    queryKey: ["notifications", "recent"],
    queryFn: ({ queryKey }) => actionResources({ queryKey }),
    enabled,
    refetchInterval,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    refetchIntervalInBackground: true
  });

  // Extraer las notificaciones recientes
  const recentNotifications = recentNotificationsData || [];

  // Mutation para marcar como leída
  const markAsReadMutation = useMutation({
    mutationFn: (notificationId) => 
      updateResources("notifications", notificationId, { is_read: true }, { method: "PATCH" }),
    onSuccess: () => {
      // Invalidar queries relacionadas
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications", "unread_count"] });
      queryClient.invalidateQueries({ queryKey: ["notifications", "recent"] });
    }
  });

  // Mutation para marcar todas como leídas
  const markAllAsReadMutation = useMutation({
    mutationFn: () => 
      updateResources("notifications", "mark_all_read", {}, { method: "POST" }),
    onSuccess: () => {
      // Invalidar queries relacionadas
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications", "unread_count"] });
      queryClient.invalidateQueries({ queryKey: ["notifications", "recent"] });
    }
  });

  // Función para marcar una notificación como leída
  const markAsRead = (notificationId) => {
    markAsReadMutation.mutate(notificationId);
  };

  // Función para marcar todas como leídas
  const markAllAsRead = () => {
    markAllAsReadMutation.mutate();
  };

  // Función para refrescar todas las notificaciones
  const refreshAll = () => {
    refetch();
    refetchUnreadCount();
    refetchRecent();
  };

  return {
    // Datos
    notifications,
    unreadCount,
    recentNotifications,
    
    // Estados de carga
    isLoading,
    isError,
    isMarkingAsRead: markAsReadMutation.isPending,
    isMarkingAllAsRead: markAllAsReadMutation.isPending,
    
    // Acciones
    markAsRead,
    markAllAsRead,
    refreshAll,
    refetch,
    
    // Estados de mutaciones
    markAsReadError: markAsReadMutation.error,
    markAllAsReadError: markAllAsReadMutation.error
  };
};

/**
 * Hook simplificado para obtener solo el conteo de no leídas
 * Útil para el componente de campanita
 */
export const useUnreadCount = () => {
  const {
    data: unreadCountData,
    isLoading,
    isError,
    refetch
  } = useQuery({
    queryKey: ["notifications", "unread_count"],
    queryFn: ({ queryKey }) => actionResources({ queryKey }),
    refetchInterval: 5000 // 5 segundos para notificaciones más rápidas
  });

  const unreadCount = unreadCountData?.unread_count || 0;

  return {
    unreadCount,
    isLoading,
    isError,
    refetch
  };
};

/**
 * Hook para obtener notificaciones recientes
 * Útil para el dropdown de la campanita
 */
export const useRecentNotifications = () => {
  const {
    data: recentNotificationsData,
    isLoading,
    isError,
    refetch
  } = useQuery({
    queryKey: ["notifications", "recent"],
    queryFn: ({ queryKey }) => actionResources({ queryKey }),
    refetchInterval: 5000 // 5 segundos para notificaciones más rápidas
  });

  const recentNotifications = recentNotificationsData || [];

  return {
    recentNotifications,
    isLoading,
    isError,
    refetch
  };
};
