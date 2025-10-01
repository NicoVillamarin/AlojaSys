import React from 'react'
import Chart from 'react-apexcharts'
import SpinnerLoading from 'src/components/SpinnerLoading'
import { format, parseISO, addDays } from 'date-fns'

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
      console.log('📊 Gráfico de Tendencias - Usando datos del dashboard')
      console.log('Rango de fechas:', dateRange)
      
      // Generar todas las fechas en el rango (incluyendo las que tienen 0 reservas)
      const trendsMap = {}
      trends.forEach(t => {
        trendsMap[t.date] = Number(t.check_in_today || 0)
      })
      
      // Crear array con todas las fechas del rango, rellenando con 0 si no hay datos
      const categories = []
      const data = []
      
      if (dateRange && dateRange.start && dateRange.end) {
        // Usar parseISO para evitar problemas de zona horaria
        let currentDate = parseISO(dateRange.start)
        const endDate = parseISO(dateRange.end)
        
        console.log(`📅 Generando fechas: ${format(currentDate, 'dd/MM/yyyy')} - ${format(endDate, 'dd/MM/yyyy')}`)
        
        while (currentDate <= endDate) {
          const dateStr = format(currentDate, 'yyyy-MM-dd')
          const formatted = format(currentDate, 'dd-MM-yyyy')
          const value = trendsMap[dateStr] || 0
          
          categories.push(formatted)
          data.push(value)
          
          // Usar addDays en lugar de setDate para evitar problemas de zona horaria
          currentDate = addDays(currentDate, 1)
        }
        
        console.log(`✅ ${categories.length} fechas generadas, total de reservas: ${data.reduce((a, b) => a + b, 0)}`)
      } else {
        // Fallback al comportamiento anterior si no hay dateRange
        trends.forEach(t => {
          try {
            // Usar parseISO para las fechas de trends también
            const parsedDate = parseISO(t.date)
            const formatted = format(parsedDate, 'dd-MM-yyyy')
            categories.push(formatted)
            data.push(Number(t.check_in_today || 0))
          } catch (error) {
            console.error('Error formateando fecha de trend:', t.date, error)
          }
        })
      }
      
      return { series: [{ name: 'Reservas', data }], categories }
    }

    if (!reservations || reservations.length === 0) return { series: [], categories: [] }

    // Filtrar reservas que estén dentro del rango de fechas usando parseISO
    const filteredReservations = reservations.filter(reservation => {
      const checkInDate = parseISO(reservation.check_in)
      const startDate = parseISO(dateRange.start)
      const endDate = parseISO(dateRange.end)
      return checkInDate >= startDate && checkInDate <= endDate
    })

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
      type="bar"
      height={350}
    />
  )
}

export default ReservationsTimelineChart