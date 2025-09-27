try:
    from .celery import app as celery_app  # type: ignore
except Exception:  # Celery puede no estar instalado/levantado en entornos locales
    celery_app = None  # pragma: no cover
__all__ = ("celery_app",)