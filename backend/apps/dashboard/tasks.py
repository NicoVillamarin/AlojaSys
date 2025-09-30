from celery import shared_task
from datetime import date, timedelta
from apps.core.models import Hotel
from .models import DashboardMetrics


@shared_task
def calculate_dashboard_metrics_for_date(target_date_str: str | None = None):
    """Calcula métricas del dashboard para todos los hoteles en una fecha.

    Si no se provee fecha, usa la fecha actual.
    """
    target_date = date.fromisoformat(target_date_str) if target_date_str else date.today()
    hotels = Hotel.objects.filter(is_active=True)
    for hotel in hotels:
        DashboardMetrics.calculate_metrics(hotel, target_date)


@shared_task
def calculate_dashboard_metrics_daily():
    """Tarea diaria para calcular métricas del día actual para todos los hoteles."""
    calculate_dashboard_metrics_for_date.apply_async(kwargs={"target_date_str": date.today().isoformat()})


@shared_task
def backfill_dashboard_metrics(days: int = 7):
    """Rellena métricas hacia atrás N días para todos los hoteles."""
    today = date.today()
    for i in range(days):
        target_date = today - timedelta(days=i)
        calculate_dashboard_metrics_for_date.apply_async(kwargs={"target_date_str": target_date.isoformat()})



