import { useState, useEffect } from "react";
import { bankTransferService } from "src/services/bankTransferService";
import SpinnerLoading from "src/components/SpinnerLoading";

export default function BankTransferStatus({
  reservationId,
  onStatusChange
}) {
  const [transfers, setTransfers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadTransfers();
  }, [reservationId]);

  const loadTransfers = async () => {
    try {
      setLoading(true);
      const response = await bankTransferService.getTransfers({
        reservation_id: reservationId
      });
      
      if (response.results) {
        setTransfers(response.results);
      } else {
        setTransfers([]);
      }
    } catch (err) {
      console.error('Error cargando transferencias:', err);
      setError('Error cargando transferencias bancarias');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmTransfer = async (transferId) => {
    try {
      setLoading(true);
      const response = await bankTransferService.confirmTransfer(transferId, "Confirmado manualmente desde frontend");
      
      if (response.success) {
        // Recargar transferencias
        await loadTransfers();
        // Notificar cambio de estado
        onStatusChange?.(response.transfer);
      } else {
        setError(response.error || 'Error confirmando transferencia');
      }
    } catch (err) {
      console.error('Error confirmando transferencia:', err);
      setError('Error confirmando transferencia');
    } finally {
      setLoading(false);
    }
  };

  const handleRejectTransfer = async (transferId) => {
    const reason = prompt('Motivo del rechazo:');
    if (!reason) return;
    
    try {
      setLoading(true);
      const response = await bankTransferService.rejectTransfer(transferId, reason);
      
      if (response.success) {
        // Recargar transferencias
        await loadTransfers();
        // Notificar cambio de estado
        onStatusChange?.(response.transfer);
      } else {
        setError(response.error || 'Error rechazando transferencia');
      }
    } catch (err) {
      console.error('Error rechazando transferencia:', err);
      setError('Error rechazando transferencia');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    return bankTransferService.getStatusColor(status);
  };

  const getStatusIcon = (status) => {
    const icons = {
      'uploaded': (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      ),
      'pending_review': (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      'confirmed': (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      ),
      'rejected': (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      ),
      'processing': (
        <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      )
    };
    return icons[status] || null;
  };

  const formatCurrency = (amount) => {
    return bankTransferService.formatAmount(amount);
  };

  const formatDate = (dateString) => {
    return bankTransferService.formatDate(dateString);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <SpinnerLoading size={32} />
        <span className="ml-2 text-gray-600">Cargando transferencias...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (transfers.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p>No hay transferencias bancarias registradas</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-800">Transferencias Bancarias</h3>
      
      {transfers.map((transfer) => (
        <div key={transfer.id} className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(transfer.status)}`}>
                  {getStatusIcon(transfer.status)}
                  <span className="ml-1">{transfer.status_display}</span>
                </span>
                <span className="text-sm text-gray-500">
                  {formatDate(transfer.created_at)}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Monto:</span>
                  <span className="font-semibold ml-1">{formatCurrency(transfer.amount)}</span>
                </div>
                <div>
                  <span className="text-gray-600">Fecha Transferencia:</span>
                  <span className="ml-1">{new Date(transfer.transfer_date).toLocaleDateString('es-AR')}</span>
                </div>
                <div>
                  <span className="text-gray-600">CBU/IBAN:</span>
                  <span className="ml-1 font-mono text-xs">{transfer.cbu_iban}</span>
                </div>
                {transfer.bank_name && (
                  <div>
                    <span className="text-gray-600">Banco:</span>
                    <span className="ml-1">{transfer.bank_name}</span>
                  </div>
                )}
              </div>

              {/* Solo mostrar botones para casos excepcionales que requieren revisión manual */}
              {transfer.status === 'pending_review' && (
                <div className="mt-4 pt-3 border-t border-gray-200">
                  <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-yellow-800">
                          Requiere revisión manual
                        </h3>
                        <div className="mt-2 text-sm text-yellow-700">
                          <p>Los datos extraídos del comprobante no coinciden. Un administrador revisará esta transferencia.</p>
                        </div>
                        <div className="mt-3">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleConfirmTransfer(transfer.id)}
                              disabled={loading}
                              className="bg-green-600 text-white py-1 px-3 rounded text-sm font-medium hover:bg-green-700 disabled:opacity-50"
                            >
                              {loading ? 'Procesando...' : 'Confirmar de todas formas'}
                            </button>
                            <button
                              onClick={() => handleRejectTransfer(transfer.id)}
                              disabled={loading}
                              className="bg-red-600 text-white py-1 px-3 rounded text-sm font-medium hover:bg-red-700 disabled:opacity-50"
                            >
                              Rechazar
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Mensaje de confirmación automática */}
              {transfer.status === 'confirmed' && (
                <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-md">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-green-800">
                        Transferencia confirmada automáticamente
                      </h3>
                      <div className="mt-1 text-sm text-green-700">
                        <p>La transferencia ha sido procesada y la reserva está confirmada.</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Validación OCR */}
              {transfer.ocr_amount && (
                <div className="mt-3 p-2 bg-gray-50 rounded text-xs">
                  <div className="font-medium text-gray-700 mb-1">Datos extraídos por OCR:</div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <span className="text-gray-600">Monto OCR:</span>
                      <span className={`ml-1 ${transfer.is_amount_valid ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(transfer.ocr_amount)}
                        {transfer.is_amount_valid !== null && (
                          <span className="ml-1">
                            {transfer.is_amount_valid ? '✓' : '✗'}
                          </span>
                        )}
                      </span>
                    </div>
                    {transfer.ocr_cbu && (
                      <div>
                        <span className="text-gray-600">CBU OCR:</span>
                        <span className={`ml-1 font-mono ${transfer.is_cbu_valid ? 'text-green-600' : 'text-red-600'}`}>
                          {transfer.ocr_cbu}
                          {transfer.is_cbu_valid !== null && (
                            <span className="ml-1">
                              {transfer.is_cbu_valid ? '✓' : '✗'}
                            </span>
                          )}
                        </span>
                      </div>
                    )}
                  </div>
                  {transfer.validation_notes && (
                    <div className="mt-1 text-gray-600">
                      {transfer.validation_notes}
                    </div>
                  )}
                </div>
              )}

              {/* Notas */}
              {transfer.notes && (
                <div className="mt-2 text-sm text-gray-600">
                  <span className="font-medium">Notas:</span> {transfer.notes}
                </div>
              )}
            </div>

            {/* Acciones */}
            <div className="flex space-x-2 ml-4">
              {transfer.receipt_url && (
                <a
                  href={transfer.receipt_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  Ver Comprobante
                </a>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
