import threading

_request_local = threading.local()


def set_current_user(user):
    _request_local.user = user


def get_current_user():
    user = getattr(_request_local, "user", None)
    if getattr(user, "is_authenticated", False):
        return user
    return None


class CurrentUserMiddleware:
    """Guarda el request.user en un storage por hilo para usarlo en señales."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo persistimos usuarios autenticados; si es AnonymousUser guardamos None
        _request_local.user = request.user if getattr(request.user, "is_authenticated", False) else None
        try:
            response = self.get_response(request)
        finally:
            _request_local.user = None
        return response


