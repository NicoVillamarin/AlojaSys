import React from 'react'
import Chart from 'react-apexcharts'
import SpinnerLoading from 'src/components/SpinnerLoading'
import { format, parseISO, addDays } from 'date-fns'

const FutureReservationsChart = ({ 
  futureReservations = [], 
  dateRange = {}, 
  isLoading = false,
  selectedPeriod = '30-days'
}) => {
  // Procesar datos para gráfico de reservas futuras
  const getFutureReservationsData = () => {
    console.log('📅 Reservas Futuras - Procesando datos')
    console.log('Total de futureReservations recibidas:', futureReservations?.length || 0)
    
    if (!futureReservations || futureReservations.length === 0) {
      console.log('⚠️ No hay reservas futuras disponibles')
      return { series: [], categories: [] }
    }

    // Calcular fecha de MAÑANA para filtrar en el frontend
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    tomorrow.setHours(0, 0, 0, 0) // Resetear a medianoche
    
    console.log('Fecha de mañana para filtrar:', format(tomorrow, 'yyyy-MM-dd'))

    // FILTRAR EN EL FRONTEND: Solo reservas desde mañana en adelante
    const filteredReservations = futureReservations.filter(reservation => {
      const checkInDate = parseISO(reservation.check_in)
      const isFuture = checkInDate >= tomorrow
      
      if (!isFuture) {
        console.log('❌ Descartando reserva antigua:', reservation.check_in, reservation.status)
      }
      
      return isFuture
    })

    console.log('✅ Reservas filtradas (desde mañana):', filteredReservations.length, 'de', futureReservations.length)

    if (filteredReservations.length === 0) {
      console.log('⚠️ No hay reservas realmente futuras (desde mañana)')
      return { series: [], categories: [] }
    }

    // Mostrar primeras 5 reservas filtradas
    console.log('Primeras 5 reservas filtradas:', filteredReservations.slice(0, 5).map(r => ({
      check_in: r.check_in,
      status: r.status,
      guest: r.guests_data?.[0]?.name || 'N/A'
    })))

    // Agrupar reservas filtradas por fecha
    const reservationsByDate = {}
    filteredReservations.forEach(reservation => {
      const date = reservation.check_in
      if (!reservationsByDate[date]) {
        reservationsByDate[date] = 0
      }
      reservationsByDate[date]++
    })

    console.log('Reservas agrupadas por fecha:', reservationsByDate)

    // Crear arrays para el gráfico - ordenar fechas correctamente
    const dates = Object.keys(reservationsByDate).sort((a, b) => new Date(a) - new Date(b))
    const counts = dates.map(date => reservationsByDate[date])
    
    // Formatear fechas para mostrar en DD-MM-YYYY usando parseISO
    const formattedDates = dates.map(date => {
      try {
        const parsedDate = parseISO(date)
        return format(parsedDate, 'dd-MM-yyyy')
      } catch (error) {
        console.error('Error formateando fecha:', date, error)
        return date
      }
    })

    console.log('✅ Gráfico con', dates.length, 'fechas, total reservas:', counts.reduce((a, b) => a + b, 0))

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
      type: 'bar',
      height: 350,
      toolbar: { show: true },
      zoom: { enabled: true }
    },
    plotOptions: {
      bar: {
        borderRadius: 4,
        columnWidth: '60%',
        dataLabels: {
          position: 'top'
        }
      }
    },
    dataLabels: {
      enabled: false,
      formatter: (val) => val,
      offsetY: -20,
      style: {
        fontSize: '12px',
        colors: ['#304758']
      }
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
      text: `Reservas Futuras (Desde Mañana)`,
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
      type="bar"
      height={350}
    />
  )
}

export default FutureReservationsChart