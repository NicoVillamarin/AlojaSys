import React from 'react'
import Chart from 'react-apexcharts'
import SpinnerLoading from 'src/components/SpinnerLoading'

const RoomTypeOccupancyChart = ({ 
  rooms = [], 
  dateRange = {}, 
  isLoading = false,
  occupancyByType = null
}) => {
  // Procesar datos para gráfico de ocupación por tipo de habitación
  const getRoomTypeOccupancyData = () => {
    // Si llega ocupación desde el dashboard, priorizarla (global u hotel)
    if (occupancyByType && typeof occupancyByType === 'object') {
      const labels = Object.keys(occupancyByType)
      const occupiedData = labels.map(type => occupancyByType[type]?.occupied || 0)
      const totalData = labels.map(type => occupancyByType[type]?.total || 0)
      return {
        series: [
          { name: 'Ocupadas', data: occupiedData },
          { name: 'Disponibles', data: totalData.map((t, i) => Math.max(t - occupiedData[i], 0)) }
        ],
        labels: labels.map(type => {
          const typeNames = { single: 'Individual', double: 'Doble', triple: 'Triple', suite: 'Suite' }
          return typeNames[type] || type
        })
      }
    }

    if (!rooms || rooms.length === 0) return { series: [], labels: [] }

    const roomTypes = {}
    rooms.forEach(room => {
      const type = room.room_type
      if (!roomTypes[type]) {
        roomTypes[type] = { total: 0, occupied: 0 }
      }
      roomTypes[type].total++
      if (room.status === 'occupied') {
        roomTypes[type].occupied++
      }
    })

    const labels = Object.keys(roomTypes)
    const occupiedData = labels.map(type => roomTypes[type].occupied)
    const totalData = labels.map(type => roomTypes[type].total)

    return {
      series: [
        {
          name: 'Ocupadas',
          data: occupiedData
        },
        {
          name: 'Disponibles',
          data: totalData.map((total, index) => total - occupiedData[index])
        }
      ],
      labels: labels.map(type => {
        const typeNames = {
          'single': 'Individual',
          'double': 'Doble',
          'triple': 'Triple',
          'suite': 'Suite'
        }
        return typeNames[type] || type
      })
    }
  }

  // Configuración del gráfico
  const options = {
    chart: {
      type: 'bar',
      height: 350,
      stacked: true,
      toolbar: { show: true }
    },
    colors: ['#10B981', '#E5E7EB'],
    xaxis: {
      categories: getRoomTypeOccupancyData().labels
    },
    yaxis: {
      title: { text: 'Número de Habitaciones' }
    },
    legend: {
      position: 'top'
    },
    title: {
      text: `Ocupación por Tipo de Habitación - ${dateRange.monthName || 'Período seleccionado'}`,
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
      series={getRoomTypeOccupancyData().series}
      type="bar"
      height={350}
    />
  )
}

export default RoomTypeOccupancyChart
