import React from 'react'
import { useTranslation } from 'react-i18next'
import Chart from 'react-apexcharts'
import SpinnerLoading from 'src/components/SpinnerLoading'

const RevenueChart = ({ 
  reservations = [], 
  dateRange = {}, 
  isLoading = false,
  selectedPeriod = '30-days',
  revenueAnalysis = null,
  metric = 'gross' // 'gross' | 'net'
}) => {
  const { t } = useTranslation()
  // Procesar datos para gráfico de ingresos
  const getRevenueData = () => {
    if (revenueAnalysis && Array.isArray(revenueAnalysis.daily_revenue) && revenueAnalysis.daily_revenue.length > 0) {
      const categories = revenueAnalysis.daily_revenue.map(d => d.date)
      const data = revenueAnalysis.daily_revenue.map(d => parseFloat((metric === 'net' ? (d.net ?? d.revenue) : d.revenue) || 0))
      
    }

    if (!reservations || reservations.length === 0) {
      return { series: [], categories: [] }
    }

    // Filtrar reservas que tienen check_in dentro del rango de fechas (ingresos reales)
    const filteredReservations = reservations.filter(reservation => {
      const checkInDate = new Date(reservation.check_in)
      const startDate = new Date(dateRange.start)
      const endDate = new Date(dateRange.end)
      
      // Incluir reservas que hicieron check-in dentro del período
      return checkInDate >= startDate && checkInDate <= endDate
    })

    // Calcular la diferencia en días para decidir si agrupar por día o por mes
    const startDate = new Date(dateRange.start)
    const endDate = new Date(dateRange.end)
    const diffDays = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24))
    


    const revenueByPeriod = {}
    let totalRevenue = 0

    filteredReservations.forEach(reservation => {
      const checkInDate = new Date(reservation.check_in)
      const price = parseFloat(reservation.total_price || 0)
      totalRevenue += price

      let periodKey
      if (diffDays <= 31) {
        // Si es menos de un mes, agrupar por día (usar fecha de check-in)
        periodKey = checkInDate.toISOString().split('T')[0]
      } else {
        // Si es más de un mes, agrupar por mes
        periodKey = `${checkInDate.getFullYear()}-${String(checkInDate.getMonth() + 1).padStart(2, '0')}`
      }

      if (!revenueByPeriod[periodKey]) {
        revenueByPeriod[periodKey] = 0
      }
      revenueByPeriod[periodKey] += price
      
    })

    // Generar todas las fechas del rango (incluyendo las que tienen 0 ingresos)
    const allPeriods = []
    const allRevenues = []
    
    if (dateRange && dateRange.start && dateRange.end) {
      const startDate = new Date(dateRange.start)
      const endDate = new Date(dateRange.end)
      
      let currentDate = new Date(startDate)
      while (currentDate <= endDate) {
        const periodKey = currentDate.toISOString().split('T')[0]
        allPeriods.push(periodKey)
        allRevenues.push(revenueByPeriod[periodKey] || 0)
        currentDate.setDate(currentDate.getDate() + 1)
      }
    } else {
      // Fallback al comportamiento anterior si no hay dateRange
      const periods = Object.keys(revenueByPeriod).sort()
      const revenues = periods.map(period => revenueByPeriod[period])
      allPeriods.push(...periods)
      allRevenues.push(...revenues)
    }

    return {
      series: [{
        name: metric === 'net' ? t('dashboard.charts.net_revenue') : t('dashboard.charts.gross_revenue'),
        data: allRevenues
      }],
      categories: allPeriods
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
      title: { text: getRevenueData().categories.length <= 31 ? t('dashboard.charts.date') : t('dashboard.charts.month') },
      labels: {
        rotate: -45,
        style: {
          fontSize: '12px'
        }
      }
    },
    yaxis: {
      title: { text: t('dashboard.charts.revenue_currency') },
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
      text: `${t('dashboard.charts.revenue')} - ${dateRange.label || t('dashboard.charts.selected_period')}`,
      align: 'left',
      style: { fontSize: '16px', fontWeight: 'bold' }
    },
    subtitle: {
      text: `${t('dashboard.charts.total')}: $${getRevenueData().series[0]?.data.reduce((a, b) => a + b, 0).toLocaleString() || '0'}`,
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
