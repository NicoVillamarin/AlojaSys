import { useMemo } from "react";
import { useMe } from "./useMe";

/**
 * Hook para verificar si el usuario tiene un permiso específico
 * 
 * @param {string} permission - El permiso a verificar en formato "app.codename" (ej: "locations.view_city")
 * @returns {boolean} - true si el usuario tiene el permiso, false en caso contrario
 * 
 * @example
 * const ViewCities = usePermissions("locations.view_city");
 * const AddRoom = usePermissions("rooms.add_room");
 * 
 * if (ViewCities) {
 *   // El usuario puede ver ciudades
 * }
 */
export const usePermissions = (permission) => {
  const { data: user, isPending, isError } = useMe();

  const hasPermission = useMemo(() => {
    // Si está cargando o hay error, no tiene permiso por defecto
    if (isPending || isError || !user) {
      return false;
    }

    // Si es superuser, tiene todos los permisos (aunque esto no debería usarse en el frontend)
    if (user.is_superuser) {
      return true;
    }

    // Obtener permisos del usuario (array de strings: ["locations.view_city", ...])
    const userPermissions = user.permissions || [];

    // Verificar si el permiso está en el array
    const hasIt = userPermissions.includes(permission);
    
    // DEBUG: Log solo para permisos de configuración que no deberían tener los recepcionistas
    const configPermissions = [
      "enterprises.view_enterprise",
      "users.view_userprofile",
      "auth.view_group",
      "locations.view_country",
      "locations.view_state",
      "locations.view_city",
      "rates.view_rateplan",
      "payments.view_paymentpolicy"
    ];

    return hasIt;
  }, [user, permission, isPending, isError]);

  return hasPermission;
};

/**
 * Hook para verificar múltiples permisos
 * Útil cuando necesitas verificar varios permisos a la vez
 * 
 * @param {string[]} permissions - Array de permisos a verificar
 * @returns {Object} - Objeto con cada permiso como clave y su valor booleano
 * 
 * @example
 * const { viewCities, addRoom, deleteRoom } = useMultiplePermissions([
 *   "locations.view_city",
 *   "rooms.add_room",
 *   "rooms.delete_room"
 * ]);
 */
export const useMultiplePermissions = (permissions) => {
  const { data: user, isPending, isError } = useMe();

  const permissionsMap = useMemo(() => {
    // Si está cargando o hay error, todos los permisos son false
    if (isPending || isError || !user || !Array.isArray(permissions)) {
      return permissions?.reduce((acc, perm) => {
        acc[perm] = false;
        return acc;
      }, {}) || {};
    }

    const userPermissions = user.permissions || [];

    // Crear objeto con cada permiso y su valor booleano
    return permissions.reduce((acc, perm) => {
      // Convertir "locations.view_city" a "viewCities" para el nombre de la clave
      const keyName = perm
        .split(".")
        .slice(1) // Quitar el nombre de la app
        .join("_")
        .split("_")
        .map((word, index) => 
          index === 0 
            ? word 
            : word.charAt(0).toUpperCase() + word.slice(1)
        )
        .join("");
      
      acc[perm] = userPermissions.includes(perm);
      return acc;
    }, {});
  }, [user, permissions, isPending, isError]);

  return permissionsMap;
};

/**
 * Hook para verificar si el usuario tiene TODOS los permisos especificados
 * 
 * @param {string[]} permissions - Array de permisos requeridos
 * @returns {boolean} - true si el usuario tiene TODOS los permisos
 * 
 * @example
 * const canManageRooms = useHasAllPermissions([
 *   "rooms.view_room",
 *   "rooms.add_room",
 *   "rooms.change_room"
 * ]);
 */
export const useHasAllPermissions = (permissions) => {
  const { data: user, isPending, isError } = useMe();

  const hasAll = useMemo(() => {
    if (isPending || isError || !user || !Array.isArray(permissions) || permissions.length === 0) {
      return false;
    }

    const userPermissions = user.permissions || [];
    
    // Verificar que TODOS los permisos estén presentes
    return permissions.every(permission => userPermissions.includes(permission));
  }, [user, permissions, isPending, isError]);

  return hasAll;
};

/**
 * Hook para verificar si el usuario tiene AL MENOS UNO de los permisos especificados
 * 
 * @param {string[]} permissions - Array de permisos (cualquiera)
 * @returns {boolean} - true si el usuario tiene al menos uno de los permisos
 * 
 * @example
 * const canViewOrEdit = useHasAnyPermission([
 *   "rooms.view_room",
 *   "rooms.change_room"
 * ]);
 */
export const useHasAnyPermission = (permissions) => {
  const { data: user, isPending, isError } = useMe();

  const hasAny = useMemo(() => {
    if (isPending || isError || !user || !Array.isArray(permissions) || permissions.length === 0) {
      return false;
    }

    const userPermissions = user.permissions || [];
    
    // Verificar que AL MENOS UNO de los permisos esté presente
    return permissions.some(permission => userPermissions.includes(permission));
  }, [user, permissions, isPending, isError]);

  return hasAny;
};

