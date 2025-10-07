import React from 'react'
import LinealDown from 'src/assets/icons/LinealDown'
import LinealIcon from 'src/assets/icons/LinealIcon'
import LinealUp from 'src/assets/icons/LinealUp'

const Kpis = ({ kpis = [], loading = false, className = "" }) => {
  // Calcular el número de columnas dinámicamente con mejor responsive
  const getGridCols = (count) => {
    if (count <= 2) return 'grid-cols-1 sm:grid-cols-2';
    if (count <= 3) return 'grid-cols-1 sm:grid-cols-2 xl:grid-cols-3';
    if (count <= 4) return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4';
    if (count <= 6) return 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6';
    return 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6';
  };

  if (loading) {
    const skeletonCount = kpis.length || 6;
    return (
      <div className={`grid ${getGridCols(skeletonCount)} gap-4 ${className}`}>
        {[...Array(skeletonCount)].map((_, i) => (
          <div key={i} className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 animate-pulse">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-gray-200 rounded-2xl"></div>
              <div className="w-16 h-4 bg-gray-200 rounded-full"></div>
            </div>
            <div className="space-y-2">
              <div className="w-20 h-8 bg-gray-200 rounded-lg"></div>
              <div className="w-24 h-4 bg-gray-200 rounded-full"></div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (!kpis || kpis.length === 0) {
    return (
      <div className={`text-center py-8 text-gray-500 ${className}`}>
        No hay KPIs para mostrar
      </div>
    )
  }

  return (
    <div className={`grid ${getGridCols(kpis.length)} gap-4 ${className}`}>
      {kpis.map((kpi, index) => {
        const IconComponent = kpi.icon
        return (
          <div 
            key={index}
            className="group bg-white rounded-xl shadow-sm border border-gray-100 p-3 sm:p-4 hover:shadow-md hover:border-gray-200 transition-all duration-200 hover:-translate-y-1 min-w-0"
          >
            {/* Header con icono y cambio */}
            <div className="flex items-center justify-between mb-2 sm:mb-3">
              <div className={`p-2 sm:p-2.5 rounded-lg ${kpi.bgColor} group-hover:scale-105 transition-transform duration-200`}>
                <IconComponent className={`w-4 h-4 sm:w-5 sm:h-5 ${kpi.iconColor}`} />
              </div>
              {kpi.change && (
                <div className={`flex items-center space-x-1 text-xs font-medium px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-md ${
                  kpi.changeType === 'positive' 
                    ? 'text-emerald-600 bg-emerald-50' 
                    : kpi.changeType === 'negative'
                    ? 'text-rose-600 bg-rose-50'
                    : 'text-orange-600 bg-orange-50'
                }`}>
                  <span className="text-xs">
                    {kpi.changeType === 'positive' ? <LinealUp /> : kpi.changeType === 'negative' ? <LinealDown /> : <LinealIcon />}
                  </span>
                  <span className="hidden sm:inline">{kpi.change}</span>
                </div>
              )}
            </div>

            {/* Valor principal */}
            <div className="space-y-1 mb-2 sm:mb-3">
              <div className="text-xl sm:text-2xl font-bold text-gray-900 group-hover:text-gray-700 transition-colors">
                {kpi.value}
              </div>
              <div className="text-xs text-gray-500 group-hover:text-gray-600 transition-colors truncate">
                {kpi.subtitle}
              </div>
            </div>

            {/* Barra de progreso sutil */}
            {kpi.showProgress !== false && (
              <div className="mb-2">
                <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                  <div 
                    className={`h-full bg-gradient-to-r ${kpi.color} rounded-full transition-all duration-1000 ease-out`}
                    style={{ 
                      width: kpi.progressWidth || '60%'
                    }}
                  ></div>
                </div>
              </div>
            )}

            {/* Título */}
            <div>
              <h3 className="text-xs sm:text-sm font-bold text-gray-700 group-hover:text-gray-900 transition-colors truncate">
                {kpi.title}
              </h3>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default Kpis