# Dashboard App

Esta aplicación proporciona métricas y análisis para el sistema de gestión hotelera AlojaSys.

## Modelos

### DashboardMetrics

Modelo que almacena métricas calculadas para cada hotel en una fecha específica.

**Campos principales:**
- `hotel`: Referencia al hotel
- `date`: Fecha de las métricas
- `total_rooms`: Total de habitaciones
- `available_rooms`: Habitaciones disponibles
- `occupied_rooms`: Habitaciones ocupadas
- `occupancy_rate`: Tasa de ocupación (%)
- `total_revenue`: Ingresos totales
- `average_room_rate`: Tarifa promedio por habitación
- `total_guests`: Total de huéspedes
- `check_in_today`: Check-ins del día
- `check_out_today`: Check-outs del día

## API Endpoints

### Métricas del Dashboard

- `GET /api/dashboard/metrics/` - Lista todas las métricas
- `POST /api/dashboard/metrics/` - Crea nuevas métricas
- `GET /api/dashboard/metrics/{id}/` - Obtiene métricas específicas
- `PUT /api/dashboard/metrics/{id}/` - Actualiza métricas
- `DELETE /api/dashboard/metrics/{id}/` - Elimina métricas

### Resumen y Análisis

- `GET /api/dashboard/summary/?hotel_id={id}&date={date}` - Resumen de métricas
- `GET /api/dashboard/trends/?hotel_id={id}&days={n}` - Tendencias de métricas
- `GET /api/dashboard/occupancy-by-room-type/?hotel_id={id}&date={date}` - Ocupación por tipo
- `GET /api/dashboard/revenue-analysis/?hotel_id={id}&start_date={date}&end_date={date}` - Análisis de ingresos

### Utilidades

- `POST /api/dashboard/refresh-metrics/` - Refresca métricas para un hotel

## Uso

### Calcular métricas manualmente

```python
from apps.dashboard.models import DashboardMetrics
from apps.core.models import Hotel
from datetime import date

hotel = Hotel.objects.get(id=1)
metrics = DashboardMetrics.calculate_metrics(hotel, date.today())
```

### Comando de gestión

```bash
# Calcular métricas para un hotel específico
python manage.py calculate_dashboard_metrics --hotel-id 1

# Calcular métricas para todos los hoteles
python manage.py calculate_dashboard_metrics --all-hotels

# Calcular métricas para los últimos 7 días
python manage.py calculate_dashboard_metrics --all-hotels --days 7

# Calcular métricas para una fecha específica
python manage.py calculate_dashboard_metrics --hotel-id 1 --date 2024-01-15
```

## Métricas Calculadas

### Habitaciones
- Total de habitaciones
- Habitaciones disponibles
- Habitaciones ocupadas
- Habitaciones en mantenimiento
- Habitaciones fuera de servicio
- Habitaciones reservadas

### Reservas
- Total de reservas
- Reservas pendientes
- Reservas confirmadas
- Reservas canceladas
- Check-ins del día
- Check-outs del día
- No-shows del día

### Huéspedes
- Total de huéspedes
- Huéspedes actualmente hospedados
- Huéspedes esperados hoy
- Huéspedes que parten hoy

### Financieras
- Ingresos totales
- Tarifa promedio por habitación
- Tasa de ocupación

### Por Tipo de Habitación
- Ocupación de habitaciones single
- Ocupación de habitaciones double
- Ocupación de habitaciones triple
- Ocupación de habitaciones suite

## Consideraciones

- Las métricas se calculan en tiempo real cuando se solicitan
- Se recomienda ejecutar el comando de cálculo diariamente para optimizar rendimiento
- Las métricas se almacenan por fecha y hotel para análisis histórico
- El modelo incluye índices para optimizar consultas por fecha y hotel
