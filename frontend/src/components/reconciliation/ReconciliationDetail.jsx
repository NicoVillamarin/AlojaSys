import React, { useState, useEffect } from 'react'
import { reconciliationService } from 'src/services/reconciliationService'
import SpinnerLoading from 'src/components/SpinnerLoading'
import Badge from 'src/components/Badge'
import AlertSwal from 'src/components/AlertSwal'

const ReconciliationDetail = ({ reconciliation, onBack }) => {
  const [activeTab, setActiveTab] = useState('overview')
  const [transactions, setTransactions] = useState([])
  const [matches, setMatches] = useState([])
  const [auditLogs, setAuditLogs] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (reconciliation) {
      loadTransactions()
      loadMatches()
      loadAuditLogs()
    }
  }, [reconciliation])

  const loadTransactions = async () => {
    try {
      setLoading(true)
      const response = await reconciliationService.getTransactions(reconciliation.id)
      setTransactions(response.results || response)
    } catch (error) {
      console.error('Error cargando transacciones:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadMatches = async () => {
    try {
      const response = await reconciliationService.getMatches(reconciliation.id)
      setMatches(response.results || response)
    } catch (error) {
      console.error('Error cargando matches:', error)
    }
  }

  const loadAuditLogs = async () => {
    try {
      const response = await reconciliationService.getAuditLogs(reconciliation.id)
      setAuditLogs(response.results || response)
    } catch (error) {
      console.error('Error cargando logs:', error)
    }
  }

  const handleProcessReconciliation = async () => {
    try {
      await reconciliationService.processReconciliation(reconciliation.id)
      AlertSwal.success('Éxito', 'Conciliación programada para procesamiento')
      onBack() // Volver a la lista para refrescar
    } catch (error) {
      console.error('Error procesando conciliación:', error)
      AlertSwal.error('Error', 'Error al procesar la conciliación')
    }
  }

  const handleApproveMatch = async (matchId) => {
    try {
      await reconciliationService.approveMatch(matchId, { notes: 'Aprobado desde interfaz' })
      AlertSwal.success('Éxito', 'Match aprobado exitosamente')
      loadMatches() // Recargar matches
    } catch (error) {
      console.error('Error aprobando match:', error)
      AlertSwal.error('Error', 'Error al aprobar el match')
    }
  }

  const handleRejectMatch = async (matchId) => {
    try {
      await reconciliationService.rejectMatch(matchId)
      AlertSwal.success('Éxito', 'Match rechazado exitosamente')
      loadMatches() // Recargar matches
    } catch (error) {
      console.error('Error rechazando match:', error)
      AlertSwal.error('Error', 'Error al rechazar el match')
    }
  }

  if (!reconciliation) {
    return (
      <div className="flex justify-center items-center py-8">
        <SpinnerLoading />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Conciliación {reconciliation.id}
            </h2>
            <p className="text-sm text-gray-500">
              {reconciliationService.formatDate(reconciliation.reconciliation_date)}
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <Badge
              variant={reconciliationService.getStatusColor(reconciliation.status)}
              className="text-sm"
            >
              {reconciliationService.getStatusLabel(reconciliation.status)}
            </Badge>
            
            <button
              onClick={onBack}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Volver
            </button>
          </div>
        </div>

        {/* Estadísticas */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{reconciliation.total_transactions}</div>
            <div className="text-sm text-gray-500">Total Transacciones</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{reconciliation.matched_transactions}</div>
            <div className="text-sm text-gray-500">Matches</div>
          </div>
          <div className="bg-orange-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">{reconciliation.pending_review_transactions}</div>
            <div className="text-sm text-gray-500">Pendientes</div>
          </div>
          <div className="bg-red-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-red-600">{reconciliation.unmatched_transactions}</div>
            <div className="text-sm text-gray-500">Sin Match</div>
          </div>
        </div>

        {/* Acciones */}
        {reconciliation.status === 'pending' && (
          <div className="mt-4">
            <button
              onClick={handleProcessReconciliation}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Procesar Conciliación
            </button>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {[
              { id: 'overview', label: 'Resumen' },
              { id: 'transactions', label: 'Transacciones' },
              { id: 'matches', label: 'Matches' },
              { id: 'logs', label: 'Logs' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Información del Archivo</h3>
                  <dl className="space-y-2">
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Archivo</dt>
                      <dd className="text-sm text-gray-900">{reconciliation.csv_filename}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Tamaño</dt>
                      <dd className="text-sm text-gray-900">
                        {(reconciliation.csv_file_size / 1024).toFixed(1)} KB
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Procesamiento</dt>
                      <dd className="text-sm text-gray-900">
                        {reconciliation.processing_started_at
                          ? `Iniciado: ${reconciliationService.formatDateTime(reconciliation.processing_started_at)}`
                          : 'No iniciado'
                        }
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Completado</dt>
                      <dd className="text-sm text-gray-900">
                        {reconciliation.processing_completed_at
                          ? reconciliationService.formatDateTime(reconciliation.processing_completed_at)
                          : 'No completado'
                        }
                      </dd>
                    </div>
                  </dl>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Estadísticas de Matching</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Porcentaje de Match</span>
                      <span className="text-sm font-medium text-gray-900">
                        {reconciliation.match_percentage}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${reconciliation.match_percentage}%` }}
                      ></div>
                    </div>
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>0%</span>
                      <span>100%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'transactions' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Transacciones Bancarias</h3>
              {loading ? (
                <div className="flex justify-center py-8">
                  <SpinnerLoading />
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Fecha
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Descripción
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Monto
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Estado
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Confianza
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {transactions.map((transaction) => (
                        <tr key={transaction.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {reconciliationService.formatDate(transaction.transaction_date)}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                            {transaction.description}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {reconciliationService.formatAmount(transaction.amount)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <Badge
                              variant={transaction.is_matched ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}
                              className="text-xs"
                            >
                              {transaction.is_matched ? 'Match' : 'Sin Match'}
                            </Badge>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {transaction.match_confidence ? `${transaction.match_confidence.toFixed(1)}%` : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'matches' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Matches de Conciliación</h3>
              <div className="space-y-4">
                {matches.map((match) => (
                  <div key={match.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <span className="text-sm font-medium text-gray-900">
                            {match.payment_type}#{match.payment_id}
                          </span>
                          <Badge
                            variant={reconciliationService.getMatchTypeColor(match.match_type)}
                            className="text-xs"
                          >
                            {reconciliationService.getMatchTypeLabel(match.match_type)}
                          </Badge>
                          <Badge
                            variant={match.is_confirmed ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}
                            className="text-xs"
                          >
                            {match.is_confirmed ? 'Confirmado' : 'Pendiente'}
                          </Badge>
                        </div>
                        <div className="mt-1 text-sm text-gray-500">
                          Confianza: {match.confidence_score.toFixed(1)}% | 
                          Diferencia: {reconciliationService.formatAmount(match.amount_difference)} | 
                          Días: {match.date_difference_days}
                        </div>
                      </div>
                      
                      {!match.is_confirmed && (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleApproveMatch(match.id)}
                            className="px-3 py-1 text-xs font-medium text-white bg-green-600 rounded hover:bg-green-700"
                          >
                            Aprobar
                          </button>
                          <button
                            onClick={() => handleRejectMatch(match.id)}
                            className="px-3 py-1 text-xs font-medium text-white bg-red-600 rounded hover:bg-red-700"
                          >
                            Rechazar
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'logs' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Log de Auditoría</h3>
              <div className="space-y-3">
                {auditLogs.map((log) => (
                  <div key={log.id} className="border-l-4 border-blue-200 pl-4 py-2">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-medium text-gray-900">
                        {log.event_description}
                      </div>
                      <div className="text-xs text-gray-500">
                        {reconciliationService.formatDateTime(log.created_at)}
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {log.event_type} | Usuario: {log.created_by || 'Sistema'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ReconciliationDetail

