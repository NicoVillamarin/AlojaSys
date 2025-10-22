import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { reconciliationService } from 'src/services/reconciliationService'
import CSVUploadForm from 'src/components/reconciliation/CSVUploadForm'
import ReconciliationList from 'src/components/reconciliation/ReconciliationList'
import ReconciliationDetail from 'src/components/reconciliation/ReconciliationDetail'
import SpinnerLoading from 'src/components/SpinnerLoading'
import Button from 'src/components/Button'

const BankReconciliation = () => {
  const { t } = useTranslation()
  const [currentView, setCurrentView] = useState('list') // 'list', 'upload', 'detail'
  const [selectedReconciliation, setSelectedReconciliation] = useState(null)
  const [hotelId, setHotelId] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Obtener hotel del usuario (esto debería venir del contexto de autenticación)
    const userHotelId = localStorage.getItem('hotelId') || '1' // Temporal
    setHotelId(userHotelId)
    loadStats(userHotelId)
  }, [])

  const loadStats = async (hotelId) => {
    try {
      setLoading(true)
      const response = await reconciliationService.getReconciliationStats(hotelId)
      setStats(response)
    } catch (error) {
      console.error('Error cargando estadísticas:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleUploadSuccess = (reconciliation) => {
    setCurrentView('list')
    loadStats(hotelId) // Recargar estadísticas
  }

  const handleSelectReconciliation = (reconciliation) => {
    setSelectedReconciliation(reconciliation)
    setCurrentView('detail')
  }

  const handleBackToList = () => {
    setCurrentView('list')
    setSelectedReconciliation(null)
    loadStats(hotelId) // Recargar estadísticas
  }

  const handleBackToUpload = () => {
    setCurrentView('upload')
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <SpinnerLoading />
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs text-aloja-gray-800/60">{t('sidebar.financial')}</div>
            <h1 className="text-2xl font-semibold text-aloja-navy">{t('sidebar.bank_reconciliation')}</h1>
          </div>
          <div className="flex gap-2">
            {currentView === 'list' && (
              <Button variant="primary" size="md" onClick={() => setCurrentView('upload')}>
                Subir CSV
              </Button>
            )}

            {currentView === 'upload' && (
              <Button variant="secondary" size="md" onClick={() => setCurrentView('list')}>
                Ver Lista
              </Button>
            )}
          </div>
        </div>

        {/* Estadísticas */}
        {stats && currentView === 'list' && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
            <div className="text-center">
              <div className="text-2xl font-bold text-aloja-navy">{stats.total_reconciliations || 0}</div>
              <div className="text-sm text-gray-600">Total Conciliaciones</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats.completed_reconciliations || 0}</div>
              <div className="text-sm text-gray-600">Completadas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{stats.pending_reconciliations || 0}</div>
              <div className="text-sm text-gray-600">Pendientes</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {stats.average_match_percentage?.toFixed(1) || 0}%
              </div>
              <div className="text-sm text-gray-600">Match Promedio</div>
            </div>
          </div>
        )}

        {/* Contenido Principal */}
        {currentView === 'upload' && (
          <CSVUploadForm
            onSuccess={handleUploadSuccess}
            onCancel={() => setCurrentView('list')}
          />
        )}

        {currentView === 'list' && (
          <ReconciliationList
            hotelId={hotelId}
            onSelectReconciliation={handleSelectReconciliation}
          />
        )}

        {currentView === 'detail' && selectedReconciliation && (
          <ReconciliationDetail
            reconciliation={selectedReconciliation}
            onBack={handleBackToList}
          />
        )}
      </div>
      <div className="bg-green-50 border border-green-200 rounded-md p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h4 className="text-sm font-medium text-green-800 mb-2">¿Cómo funciona la Conciliación Automática?</h4>
            <div className="text-sm text-green-700 space-y-2">
              <p><strong>1. Sube el CSV del banco:</strong> Contiene todas las transferencias que llegaron a tu cuenta bancaria.</p>
              <p><strong>2. El sistema compara automáticamente:</strong> Busca coincidencias entre las transferencias del banco y las reservas pendientes de pago.</p>
              <p><strong>3. Confirma reservas automáticamente:</strong> Las reservas que coincidan por monto y fecha se marcan como "Pagadas" sin intervención manual.</p>
              <p className="text-xs text-green-600 italic">💡 <strong>Beneficio:</strong> Ahorra tiempo, reduce errores y mantiene actualizado el estado de tus reservas.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default BankReconciliation
