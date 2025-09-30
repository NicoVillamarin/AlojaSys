import React from 'react'
import Chart from 'react-apexcharts'
import SpinnerLoading from 'src/components/SpinnerLoading'
import { format } from 'date-fns'

const ReservationsTimelineChart = ({ 
  reservations = [], 
  dateRange = {}, 
  isLoading = false,
  selectedPeriod = '30-days',
  trends = []
}) => {
  // Procesar datos para gráfico de línea de tiempo de reservas
  const getReservationsTimelineData = () => {
    // Si hay tendencias del dashboard, usarlas como fuente principal (global u hotel)
    if (Array.isArray(trends) && trends.length > 0) {
      const categories = trends.map(t => {
        try {
          return format(new Date(t.date), 'dd-MM-yyyy')
        } catch {
          return t.date
        }
      })
      const data = trends.map(t => Number(t.check_in_today || 0))
      return { series: [{ name: 'Reservas', data }], categories }
    }

    if (!reservations || reservations.length === 0) return { series: [], categories: [] }

    // Filtrar reservas que estén dentro del rango de fechas
    const filteredReservations = reservations.filter(reservation => {
      const checkInDate = new Date(reservation.check_in)
      const startDate = new Date(dateRange.start)
      const endDate = new Date(dateRange.end)
      return checkInDate >= startDate && checkInDate <= endDate
    })

    console.log('ReservationsTimelineChart - Reservas filtradas:', filteredReservations.length, 'de', reservations.length)
    console.log('Rango de fechas:', dateRange.start, 'a', dateRange.end)

    // Agrupar reservas por fecha
    const reservationsByDate = {}
    filteredReservations.forEach(reservation => {
      const date = reservation.check_in
      if (!reservationsByDate[date]) {
        reservationsByDate[date] = 0
      }
      reservationsByDate[date]++
    })

    // Crear arrays para el gráfico - ordenar fechas correctamente
    const dates = Object.keys(reservationsByDate).sort((a, b) => new Date(a) - new Date(b))
    const counts = dates.map(date => reservationsByDate[date])
    
    // Formatear fechas para mostrar en DD-MM-YYYY
    const formattedDates = dates.map(date => {
      try {
        const parsedDate = new Date(date)
        return format(parsedDate, 'dd-MM-yyyy')
      } catch (error) {
        console.error('Error formateando fecha:', date, error)
        return date
      }
    })

    console.log('Fechas en el gráfico:', formattedDates)
    console.log('Conteos:', counts)

    return {
      series: [{
        name: 'Reservas',
        data: counts
      }],
      categories: formattedDates
    }
  }

  // Configuración del gráfico
  const options = {
    chart: {
      type: 'line',
      height: 350,
      toolbar: { show: true },
      zoom: { enabled: true }
    },
    stroke: {
      curve: 'smooth',
      width: 3
    },
    colors: ['#3B82F6'],
    xaxis: {
      categories: getReservationsTimelineData().categories,
      title: { text: 'Fecha' },
      labels: {
        rotate: -45,
        style: {
          fontSize: '12px'
        }
      }
    },
    yaxis: {
      title: { text: 'Número de Reservas' }
    },
    tooltip: {
      y: {
        formatter: (val) => `${val} reservas`
      }
    },
    title: {
      text: `Tendencia de Reservas - ${dateRange.label || 'Período seleccionado'}`,
      align: 'left',
      style: { fontSize: '16px', fontWeight: 'bold' }
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-80">
        <SpinnerLoading />
      </div>
    )
  }

  return (
    <Chart
      options={options}
      series={getReservationsTimelineData().series}
      type="line"
      height={350}
    />
  )
}

export default ReservationsTimelineChart