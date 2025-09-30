import React from 'react'
import Chart from 'react-apexcharts'
import SpinnerLoading from 'src/components/SpinnerLoading'
import { format } from 'date-fns'

const FutureReservationsChart = ({ 
  futureReservations = [], 
  dateRange = {}, 
  isLoading = false,
  selectedPeriod = '30-days'
}) => {
  // Procesar datos para gráfico de reservas futuras
  const getFutureReservationsData = () => {
    if (!futureReservations || futureReservations.length === 0) {
      return { series: [], categories: [] }
    }

    // Filtrar reservas futuras que estén dentro del rango de fechas
    const filteredReservations = futureReservations.filter(reservation => {
      const checkInDate = new Date(reservation.check_in)
      const startDate = new Date(dateRange.start)
      const endDate = new Date(dateRange.end)
      return checkInDate >= startDate && checkInDate <= endDate
    })

    console.log('FutureReservationsChart - Reservas filtradas:', filteredReservations.length, 'de', futureReservations.length)

    // Agrupar reservas futuras por fecha de check-in
    const reservationsByDate = {}
    filteredReservations.forEach(reservation => {
      const date = reservation.check_in
      if (!reservationsByDate[date]) {
        reservationsByDate[date] = 0
      }
      reservationsByDate[date]++
    })

    // Crear arrays para el gráfico
    const dates = Object.keys(reservationsByDate).sort((a, b) => new Date(a) - new Date(b))
    const counts = dates.map(date => reservationsByDate[date])
    
    // Formatear fechas para mostrar en DD-MM-YYYY
    const formattedDates = dates.map(date => {
      try {
        const parsedDate = new Date(date)
        return format(parsedDate, 'dd-MM-yyyy')
      } catch (error) {
        return date // Si hay error, mantener la fecha original
      }
    })

    return {
      series: [{
        name: 'Reservas Futuras',
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
    colors: ['#8B5CF6'],
    xaxis: {
      categories: getFutureReservationsData().categories,
      title: { text: 'Fecha de Check-in' },
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
      text: `Reservas Confirmadas Futuras - ${dateRange.label || 'Período seleccionado'}`,
      align: 'left',
      style: { fontSize: '16px', fontWeight: 'bold' }
    },
    subtitle: {
      text: `Total: ${getFutureReservationsData().series[0]?.data.reduce((a, b) => a + b, 0) || 0} reservas`,
      align: 'left',
      style: { fontSize: '12px', color: '#6B7280' }
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
      series={getFutureReservationsData().series}
      type="line"
      height={350}
    />
  )
}

export default FutureReservationsChart