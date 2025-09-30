# Componentes del Dashboard

Esta carpeta contiene los componentes específicos para el dashboard del sistema AlojaSys.

## Componentes

### DashboardMetrics

Componente principal para mostrar métricas del dashboard.

**Props:**
- `metrics`: Objeto con las métricas del dashboard
- `isLoading`: Boolean indicando si está cargando
- `error`: String con el mensaje de error (opcional)
- `onRefresh`: Función para refrescar las métricas
- `showRefreshButton`: Boolean para mostrar/ocultar el botón de actualización

**Uso:**
```jsx
import DashboardMetrics from '../components/dashboard/DashboardMetrics'

<DashboardMetrics
  metrics={metrics}
  isLoading={isLoading}
  error={error}
  onRefresh={refreshMetrics}
  showRefreshButton={true}
/>
```

## Hooks

### useDashboardMetrics

Hook personalizado para obtener métricas de un hotel específico.

**Parámetros:**
- `hotelId`: ID del hotel (opcional, null para vista global)
- `date`: Fecha en formato YYYY-MM-DD (opcional, por defecto hoy)

**Retorna:**
- `metrics`: Objeto con las métricas
- `isLoading`: Boolean indicando si está cargando
- `error`: String con el mensaje de error
- `refreshMetrics`: Función para refrescar todas las métricas
- `refetchSummary`: Función para refrescar solo el resumen
- `refetchTrends`: Función para refrescar solo las tendencias
- `refetchOccupancy`: Función para refrescar solo la ocupación
- `refetchRevenue`: Función para refrescar solo el análisis de ingresos

**Uso:**
```jsx
import { useDashboardMetrics } from '../hooks/useDashboardMetrics'

const { metrics, isLoading, error, refreshMetrics } = useDashboardMetrics(hotelId, date)
```

### useGlobalDashboardMetrics

Hook para obtener métricas globales de todos los hoteles.

**Parámetros:**
- `date`: Fecha en formato YYYY-MM-DD (opcional, por defecto hoy)

**Retorna:**
- `globalMetrics`: Objeto con las métricas globales
- `isLoading`: Boolean indicando si está cargando
- `error`: String con el mensaje de error
- `refreshGlobalMetrics`: Función para refrescar las métricas globales
- `refetchGlobalSummary`: Función para refrescar solo el resumen global

**Uso:**
```jsx
import { useGlobalDashboardMetrics } from '../hooks/useDashboardMetrics'

const { globalMetrics, isLoading, error, refreshGlobalMetrics } = useGlobalDashboardMetrics(date)
```

## Estructura de Datos

### Métricas del Dashboard

```javascript
{
  summary: {
    hotel_id: 1,
    hotel_name: "Hotel Example",
    date: "2024-01-15",
    total_rooms: 50,
    available_rooms: 30,
    occupied_rooms: 20,
    occupancy_rate: 40.0,
    total_reservations: 25,
    check_in_today: 5,
    check_out_today: 3,
    total_guests: 40,
    guests_checked_in: 20,
    guests_expected_today: 5,
    guests_departing_today: 3,
    total_revenue: 5000.00,
    average_room_rate: 250.00
  },
  trends: [
    {
      date: "2024-01-15",
      occupancy_rate: 40.0,
      total_revenue: 5000.00,
      average_room_rate: 250.00,
      total_guests: 40,
      check_in_today: 5,
      check_out_today: 3
    }
  ],
  occupancyByType: {
    single: {
      total: 20,
      occupied: 8,
      available: 12
    },
    double: {
      total: 20,
      occupied: 10,
      available: 10
    },
    triple: {
      total: 8,
      occupied: 2,
      available: 6
    },
    suite: {
      total: 2,
      occupied: 0,
      available: 2
    }
  },
  revenueAnalysis: {
    period: {
      start_date: "2024-01-01",
      end_date: "2024-01-31",
      days: 31
    },
    revenue: {
      total: 150000.00,
      average_daily: 4838.71,
      average_room_rate: 250.00
    },
    revenue_by_room_type: {
      single: 60000.00,
      double: 80000.00,
      triple: 8000.00,
      suite: 2000.00
    },
    daily_revenue: [
      {
        date: "2024-01-01",
        revenue: 5000.00,
        occupancy_rate: 40.0
      }
    ]
  }
}
```

## Páginas de Ejemplo

### DashboardMetricsPage

Página de ejemplo que muestra cómo usar los componentes del dashboard.

**Características:**
- Selector de modo de vista (hotel específico o global)
- Selector de hotel
- Selector de fecha
- Visualización de métricas
- Botón de actualización

**Uso:**
```jsx
import DashboardMetricsPage from '../pages/DashboardMetrics'

// En tu router
<Route path="/dashboard-metrics" element={<DashboardMetricsPage />} />
```

## Consideraciones

- Los componentes están optimizados para mostrar datos en tiempo real
- Se incluyen estados de carga y error para mejor UX
- Los datos se actualizan automáticamente cuando cambian los parámetros
- Se incluyen funciones de refresco manual para casos específicos
- Los componentes son responsivos y se adaptan a diferentes tamaños de pantalla
