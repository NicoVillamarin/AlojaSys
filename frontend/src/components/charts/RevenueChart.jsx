import React from 'react'
import Chart from 'react-apexcharts'
import SpinnerLoading from 'src/components/SpinnerLoading'

const RevenueChart = ({ 
  reservations = [], 
  dateRange = {}, 
  isLoading = false,
  selectedPeriod = '30-days',
  revenueAnalysis = null
}) => {
  // Procesar datos para gráfico de ingresos
  const getRevenueData = () => {
    // Preferir datos diarios de la API de dashboard si están disponibles
    if (revenueAnalysis && Array.isArray(revenueAnalysis.daily_revenue)) {
      const categories = revenueAnalysis.daily_revenue.map(d => d.date)
      const data = revenueAnalysis.daily_revenue.map(d => parseFloat(d.revenue || 0))
      return {
        series: [{ name: 'Ingresos', data }],
        categories
      }
    }

    if (!reservations || reservations.length === 0) {
      console.log('No hay reservas para calcular ingresos')
      return { series: [], categories: [] }
    }

    // Filtrar reservas que estén dentro del rango de fechas
    const filteredReservations = reservations.filter(reservation => {
      const checkInDate = new Date(reservation.check_in)
      const startDate = new Date(dateRange.start)
      const endDate = new Date(dateRange.end)
      return checkInDate >= startDate && checkInDate <= endDate
    })

    console.log('RevenueChart - Reservas filtradas:', filteredReservations.length, 'de', reservations.length)
    console.log('Rango de fechas:', dateRange.start, 'a', dateRange.end)

    // Calcular la diferencia en días para decidir si agrupar por día o por mes
    const startDate = new Date(dateRange.start)
    const endDate = new Date(dateRange.end)
    const diffDays = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24))
    
    console.log('Diferencia en días:', diffDays)

    const revenueByPeriod = {}
    let totalRevenue = 0

    filteredReservations.forEach(reservation => {
      const reservationDate = new Date(reservation.check_in)
      const price = parseFloat(reservation.total_price || 0)
      totalRevenue += price

      let periodKey
      if (diffDays <= 31) {
        // Si es menos de un mes, agrupar por día
        periodKey = reservation.check_in
      } else {
        // Si es más de un mes, agrupar por mes
        periodKey = `${reservationDate.getFullYear()}-${String(reservationDate.getMonth() + 1).padStart(2, '0')}`
      }

      if (!revenueByPeriod[periodKey]) {
        revenueByPeriod[periodKey] = 0
      }
      revenueByPeriod[periodKey] += price
    })

    console.log('Ingresos totales calculados:', totalRevenue)
    console.log('Datos agrupados:', revenueByPeriod)

    const periods = Object.keys(revenueByPeriod).sort()
    const revenues = periods.map(period => revenueByPeriod[period])

    // Si no hay datos, crear datos de ejemplo para mostrar el gráfico
    if (periods.length === 0) {
      console.log('No hay datos de ingresos, creando datos de ejemplo')
      return {
        series: [{
          name: 'Ingresos',
          data: [0]
        }],
        categories: ['Sin datos']
      }
    }

    return {
      series: [{
        name: 'Ingresos',
        data: revenues
      }],
      categories: periods
    }
  }

  // Configuración del gráfico
  const options = {
    chart: {
      type: 'area',
      height: 350,
      toolbar: { show: true },
      zoom: { enabled: true }
    },
    colors: ['#10B981'],
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.8,
        opacityTo: 0.2
      }
    },
    stroke: {
      curve: 'smooth',
      width: 3
    },
    xaxis: {
      categories: getRevenueData().categories,
      title: { text: getRevenueData().categories.length <= 31 ? 'Fecha' : 'Mes' },
      labels: {
        rotate: -45,
        style: {
          fontSize: '12px'
        }
      }
    },
    yaxis: {
      title: { text: 'Ingresos ($)' },
      labels: {
        formatter: (val) => `$${val.toLocaleString()}`
      }
    },
    tooltip: {
      y: {
        formatter: (val) => `$${val.toLocaleString()}`
      }
    },
    dataLabels: {
      enabled: false
    },
    grid: {
      borderColor: '#f1f5f9',
      strokeDashArray: 5
    },
    title: {
      text: `Ingresos - ${dateRange.label || 'Período seleccionado'}`,
      align: 'left',
      style: { fontSize: '16px', fontWeight: 'bold' }
    },
    subtitle: {
      text: `Total: $${getRevenueData().series[0]?.data.reduce((a, b) => a + b, 0).toLocaleString() || '0'}`,
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
      series={getRevenueData().series}
      type="area"
      height={350}
    />
  )
}

export default RevenueChart
