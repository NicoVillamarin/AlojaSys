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

    // Si hay tendencias del dashboard con un campo explícito de "reservas creadas/confirmadas",
    // usarlas como fuente principal. Evitar "check_in_today" porque refleja llegadas, no creaciones.
    const getTrendCreatedValue = (t) => {
      const possible = [
        // nombres potenciales si el backend los expone en el futuro
        t?.reservations_created,
        t?.confirmed_reservations,
        t?.total_reservations,
        t?.created_reservations
      ]
      const found = possible.find(v => typeof v !== 'undefined' && v !== null)
      return typeof found !== 'undefined' && found !== null ? Number(found || 0) : null
    }

    const trendsHaveCreatedMetric = Array.isArray(trends) && trends.length > 0 && trends.some(t => {
      const v = getTrendCreatedValue(t)
      return v !== null && v > 0
    })

    if (trendsHaveCreatedMetric) {
      const trendsMap = {}
      trends.forEach(t => {
        const value = getTrendCreatedValue(t)
        if (value !== null) {
          trendsMap[t.date] = value
        }
      })

      const categories = []
      const data = []

      if (dateRange && dateRange.start && dateRange.end) {
        let currentDate = parseISO(dateRange.start)
        const endDate = parseISO(dateRange.end)

        while (currentDate <= endDate) {
          const dateStr = format(currentDate, 'yyyy-MM-dd')
          const formatted = format(currentDate, 'dd-MM-yyyy')
          const value = trendsMap[dateStr] || 0

          categories.push(formatted)
          data.push(value)

          currentDate = addDays(currentDate, 1)
        }
      } else {
        trends.forEach(t => {
          try {
            const parsedDate = parseISO(t.date)
            const formatted = format(parsedDate, 'dd-MM-yyyy')
            const value = getTrendCreatedValue(t)
            if (value !== null) {
              categories.push(formatted)
              data.push(value)
            }
          } catch (error) {
            console.error('Error formateando fecha de trend:', t.date, error)
          }
        })
      }

      return { series: [{ name: 'Reservas', data }], categories }
    }

    // Si no hay trends con datos, usar las reservas directamente

    if (!reservations || reservations.length === 0) {
      return { series: [], categories: [] }
    }

    // Filtrar reservas que se crearon dentro del rango de fechas (usar created_at)
    // y que estén en estados válidos para "confirmadas" en sentido amplio
    // (confirmed, check_in, check_out)
    const validStatuses = new Set(['confirmed', 'check_in', 'check_out'])
    const filteredReservations = reservations.filter(reservation => {
      // Usar solo la fecha (sin hora) para la comparación
      const createdDate = new Date(reservation.created_at)
      const createdDateOnly = new Date(createdDate.getFullYear(), createdDate.getMonth(), createdDate.getDate())
      
      const startDate = parseISO(dateRange.start)
      const endDate = parseISO(dateRange.end)
      const isInRange = createdDateOnly >= startDate && createdDateOnly <= endDate
      
      const hasValidStatus = validStatuses.has(reservation.status)
      
      return isInRange && hasValidStatus
    })


    // Agrupar reservas por fecha de creación
    const reservationsByDate = {}
    filteredReservations.forEach(reservation => {
      const createdDate = new Date(reservation.created_at)
      const date = createdDate.toISOString().split('T')[0] // YYYY-MM-DD
      if (!reservationsByDate[date]) {
        reservationsByDate[date] = 0
      }
      reservationsByDate[date]++
    })


    // Generar todas las fechas en el rango (incluyendo las que tienen 0 reservas)
    const categories = []
    const data = []
    
    if (dateRange && dateRange.start && dateRange.end) {
      // Usar parseISO para evitar problemas de zona horaria
      let currentDate = parseISO(dateRange.start)
      const endDate = parseISO(dateRange.end)
      
      
      while (currentDate <= endDate) {
        const dateStr = format(currentDate, 'yyyy-MM-dd')
        const formatted = format(currentDate, 'dd-MM-yyyy')
        const value = reservationsByDate[dateStr] || 0
        
        categories.push(formatted)
        data.push(value)
        
        // Usar addDays en lugar de setDate para evitar problemas de zona horaria
        currentDate = addDays(currentDate, 1)
      }
      
    } else {
      // Fallback al comportamiento anterior si no hay dateRange
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

    return {
      series: [{
        name: 'Reservas',
        data: data
      }],
      categories: categories
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