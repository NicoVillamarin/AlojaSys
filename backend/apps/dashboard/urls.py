from django.urls import path
from . import views

urlpatterns = [
    # Métricas del dashboard
    path('metrics/', views.DashboardMetricsListCreateView.as_view(), name='dashboard-metrics-list'),
    path('metrics/<int:pk>/', views.DashboardMetricsDetailView.as_view(), name='dashboard-metrics-detail'),
    
    # Resumen y análisis
    path('summary/', views.dashboard_summary, name='dashboard-summary'),
    path('trends/', views.dashboard_trends, name='dashboard-trends'),
    path('occupancy-by-room-type/', views.dashboard_occupancy_by_room_type, name='dashboard-occupancy-by-room-type'),
    path('revenue-analysis/', views.dashboard_revenue_analysis, name='dashboard-revenue-analysis'),
    
    # Utilidades
    path('refresh-metrics/', views.refresh_dashboard_metrics, name='dashboard-refresh-metrics'),
]
