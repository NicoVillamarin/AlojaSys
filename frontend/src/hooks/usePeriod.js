import { useState, useMemo } from 'react'

const usePeriod = (initialPeriod = 'current-month') => {
  const [selectedPeriod, setSelectedPeriod] = useState(initialPeriod)
  const [customStartDate, setCustomStartDate] = useState('')
  const [customEndDate, setCustomEndDate] = useState('')

  const getDateRange = (period) => {
    const now = new Date()
    
    switch (period) {
      case '7-days':
        const sevenDaysAgo = new Date(now)
        sevenDaysAgo.setDate(now.getDate() - 7)
        return {
          start: sevenDaysAgo.toISOString().split('T')[0],
          end: now.toISOString().split('T')[0],
          label: 'Últimos 7 días'
        }
      
      case '15-days':
        const fifteenDaysAgo = new Date(now)
        fifteenDaysAgo.setDate(now.getDate() - 15)
        return {
          start: fifteenDaysAgo.toISOString().split('T')[0],
          end: now.toISOString().split('T')[0],
          label: 'Últimos 15 días'
        }
      
      case '30-days':
        const thirtyDaysAgo = new Date(now)
        thirtyDaysAgo.setDate(now.getDate() - 30)
        return {
          start: thirtyDaysAgo.toISOString().split('T')[0],
          end: now.toISOString().split('T')[0],
          label: 'Últimos 30 días'
        }
      
      case '90-days':
        const ninetyDaysAgo = new Date(now)
        ninetyDaysAgo.setDate(now.getDate() - 90)
        return {
          start: ninetyDaysAgo.toISOString().split('T')[0],
          end: now.toISOString().split('T')[0],
          label: 'Últimos 90 días'
        }
      
      case 'current-month':
        const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
        const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0)
        return {
          start: firstDay.toISOString().split('T')[0],
          end: lastDay.toISOString().split('T')[0],
          label: now.toLocaleString('es-ES', { month: 'long', year: 'numeric' })
        }
      
      case 'last-month':
        const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
        const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 0)
        return {
          start: lastMonth.toISOString().split('T')[0],
          end: lastMonthEnd.toISOString().split('T')[0],
          label: lastMonth.toLocaleString('es-ES', { month: 'long', year: 'numeric' })
        }
      
      case 'custom':
        return {
          start: customStartDate,
          end: customEndDate,
          label: 'Período personalizado'
        }
      
      default:
        return {
          start: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          end: now.toISOString().split('T')[0],
          label: 'Últimos 30 días'
        }
    }
  }

  const dateRange = useMemo(() => getDateRange(selectedPeriod), [selectedPeriod, customStartDate, customEndDate])

  const handlePeriodChange = (newPeriod) => {
    setSelectedPeriod(newPeriod)
  }

  const handleCustomDateChange = (startDate, endDate) => {
    setCustomStartDate(startDate)
    setCustomEndDate(endDate)
    setSelectedPeriod('custom')
  }

  return {
    selectedPeriod,
    dateRange,
    handlePeriodChange,
    handleCustomDateChange,
    customStartDate,
    customEndDate
  }
}

export default usePeriod
