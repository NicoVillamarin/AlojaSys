import React from 'react'

const PeriodSelector = ({ 
  selectedPeriod, 
  onPeriodChange, 
  className = "" 
}) => {
  const periods = [
    { value: '7-days', label: 'Últimos 7 días' },
    { value: '15-days', label: 'Últimos 15 días' },
    { value: '30-days', label: 'Últimos 30 días' },
    { value: '90-days', label: 'Últimos 90 días' },
    { value: 'current-month', label: 'Mes actual' },
    { value: 'last-month', label: 'Mes anterior' },
    { value: 'custom', label: 'Personalizado' }
  ]

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <label className="text-sm font-medium text-gray-700">
        Período:
      </label>
      <select
        value={selectedPeriod}
        onChange={(e) => onPeriodChange(e.target.value)}
        className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      >
        {periods.map((period) => (
          <option key={period.value} value={period.value}>
            {period.label}
          </option>
        ))}
      </select>
    </div>
  )
}

export default PeriodSelector
