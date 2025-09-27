import React from 'react'
import Kpis from './Kpis'
import UsersIcon from 'src/assets/icons/UsersIcon'
import HomeIcon from 'src/assets/icons/HomeIcon'
import ChartBarIcon from 'src/assets/icons/ChartBarIcon'

const KpisExample = () => {
  // Ejemplo de KPIs para habitaciones
  const roomsKpis = [
    {
      title: "Habitaciones Totales",
      value: 50,
      icon: HomeIcon,
      color: "from-indigo-500 to-indigo-600",
      bgColor: "bg-indigo-50",
      iconColor: "text-indigo-600",
      change: "+2",
      changeType: "positive",
      subtitle: "habitaciones disponibles",
      showProgress: false
    },
    {
      title: "Habitaciones Ocupadas",
      value: 23,
      icon: UsersIcon,
      color: "from-emerald-500 to-emerald-600",
      bgColor: "bg-emerald-50",
      iconColor: "text-emerald-600",
      change: "+5%",
      changeType: "positive",
      subtitle: "de 50 totales",
      progressWidth: "46%"
    },
    {
      title: "Tasa de Ocupación",
      value: "76%",
      icon: ChartBarIcon,
      color: "from-purple-500 to-purple-600",
      bgColor: "bg-purple-50",
      iconColor: "text-purple-600",
      change: "+3.2%",
      changeType: "positive",
      subtitle: "promedio del hotel",
      progressWidth: "76%"
    }
  ]

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-gray-700 mb-4">Estado de Habitaciones</h2>
      <Kpis kpis={roomsKpis} />
    </div>
  )
}

export default KpisExample
