import threading

_request_local = threading.local()


def set_current_user(user):
    _request_local.user = user


def get_current_user():
    return getattr(_request_local, "user", None)


class CurrentUserMiddleware:
    """Guarda el request.user en un storage por hilo para usarlo en señales."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request_local.user = getattr(request, "user", None)
        try:
            response = self.get_response(request)
        finally:
            _request_local.user = None
        return response


