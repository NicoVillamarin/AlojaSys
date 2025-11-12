from rest_framework.permissions import BasePermission, SAFE_METHODS


class HousekeepingAccessPermission(BasePermission):
    """
    Permite acceso si:
    - es superusuario
    - tiene el permiso housekeeping.access_housekeeping
    - o su perfil tiene el flag is_housekeeping_staff
    """

    message = "Acceso restringido al módulo de housekeeping."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if user.has_perm("housekeeping.access_housekeeping"):
            return True
        profile = getattr(user, "profile", None)
        if profile and getattr(profile, "is_housekeeping_staff", False):
            return True
        return False


class HousekeepingManageAllPermission(BasePermission):
    """
    Permite gestionar todo si:
    - es superusuario
    - o tiene el permiso housekeeping.manage_all_tasks
    """

    message = "No tiene permisos para gestionar todas las tareas."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.has_perm("housekeeping.manage_all_tasks"):
            return True
        return False

