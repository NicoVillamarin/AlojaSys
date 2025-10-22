import { useState, useEffect } from "react";
import ModalLayout from "src/layouts/ModalLayout";
import { bankTransferService } from "src/services/bankTransferService";
import SpinnerLoading from "src/components/SpinnerLoading";
import AlertSwal from "src/components/AlertSwal";

export default function BankTransferAdminModal({
  isOpen,
  onClose,
  hotelId = null
}) {
  const [transfers, setTransfers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedTransfer, setSelectedTransfer] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [filters, setFilters] = useState({
    status: "",
    needs_review: false,
    search: ""
  });

  useEffect(() => {
    if (isOpen) {
      loadTransfers();
    }
  }, [isOpen, filters]);

  const loadTransfers = async () => {
    try {
      setLoading(true);
      setError("");
      
      const params = {
        hotel_id: hotelId,
        status: filters.status,
        needs_review: filters.needs_review,
        search: filters.search
      };
      
      const response = await bankTransferService.getTransfers(params);
      
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

  const handleAction = async (transferId, action, notes = "") => {
    try {
      setActionLoading(true);
      
      let response;
      switch (action) {
        case 'confirm':
          response = await bankTransferService.confirmTransfer(transferId, notes);
          break;
        case 'reject':
          response = await bankTransferService.rejectTransfer(transferId, notes);
          break;
        case 'mark_pending_review':
          response = await bankTransferService.markPendingReview(transferId);
          break;
        default:
          throw new Error('Acción no válida');
      }
      
      if (response.success) {
        // Recargar transferencias
        await loadTransfers();
        
        // Cerrar detalles si estaba abierto
        if (selectedTransfer && selectedTransfer.id === transferId) {
          setShowDetails(false);
          setSelectedTransfer(null);
        }
        
        // Mostrar mensaje de éxito
        AlertSwal({
          title: "Éxito",
          description: response.message,
          tone: "success"
        });
      } else {
        throw new Error(response.error || 'Error en la acción');
      }
    } catch (err) {
      console.error(`Error en ${action}:`, err);
      AlertSwal({
        title: "Error",
        description: err.message || `Error en ${action}`,
        tone: "danger"
      });
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusColor = (status) => {
    return bankTransferService.getStatusColor(status);
  };

  const formatCurrency = (amount) => {
    return bankTransferService.formatAmount(amount);
  };

  const formatDate = (dateString) => {
    return bankTransferService.formatDate(dateString);
  };

  const openDetails = (transfer) => {
    setSelectedTransfer(transfer);
    setShowDetails(true);
  };

  const closeDetails = () => {
    setShowDetails(false);
    setSelectedTransfer(null);
  };

  if (showDetails && selectedTransfer) {
    return (
      <ModalLayout
        isOpen={showDetails}
        onClose={closeDetails}
        title={`Detalles de Transferencia #${selectedTransfer.id}`}
        size="xl"
      >
        <div className="space-y-6">
          {/* Información básica */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-600">Reserva</label>
              <p className="text-lg font-semibold">#{selectedTransfer.reservation_id}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Hotel</label>
              <p className="text-lg">{selectedTransfer.hotel_name}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Monto</label>
              <p className="text-lg font-semibold text-green-600">
                {formatCurrency(selectedTransfer.amount)}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Fecha Transferencia</label>
              <p className="text-lg">
                {new Date(selectedTransfer.transfer_date).toLocaleDateString('es-AR')}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">CBU/IBAN</label>
              <p className="text-lg font-mono">{selectedTransfer.cbu_iban}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Estado</label>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(selectedTransfer.status)}`}>
                {selectedTransfer.status_display}
              </span>
            </div>
          </div>

          {/* Comprobante */}
          {selectedTransfer.receipt_url && (
            <div>
              <label className="text-sm font-medium text-gray-600 mb-2 block">Comprobante</label>
              <div className="border rounded-lg p-4">
                <a
                  href={selectedTransfer.receipt_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  Ver Comprobante
                </a>
              </div>
            </div>
          )}

          {/* Validación OCR */}
          {selectedTransfer.ocr_amount && (
            <div>
              <label className="text-sm font-medium text-gray-600 mb-2 block">Validación OCR</label>
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-sm text-gray-600">Monto OCR:</span>
                    <span className={`ml-2 font-semibold ${selectedTransfer.is_amount_valid ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(selectedTransfer.ocr_amount)}
                      {selectedTransfer.is_amount_valid !== null && (
                        <span className="ml-1">
                          {selectedTransfer.is_amount_valid ? '✓' : '✗'}
                        </span>
                      )}
                    </span>
                  </div>
                  {selectedTransfer.ocr_cbu && (
                    <div>
                      <span className="text-sm text-gray-600">CBU OCR:</span>
                      <span className={`ml-2 font-mono ${selectedTransfer.is_cbu_valid ? 'text-green-600' : 'text-red-600'}`}>
                        {selectedTransfer.ocr_cbu}
                        {selectedTransfer.is_cbu_valid !== null && (
                          <span className="ml-1">
                            {selectedTransfer.is_cbu_valid ? '✓' : '✗'}
                          </span>
                        )}
                      </span>
                    </div>
                  )}
                </div>
                {selectedTransfer.validation_notes && (
                  <div className="text-sm text-gray-600">
                    <strong>Notas:</strong> {selectedTransfer.validation_notes}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Notas */}
          {selectedTransfer.notes && (
            <div>
              <label className="text-sm font-medium text-gray-600 mb-2 block">Notas</label>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm">{selectedTransfer.notes}</p>
              </div>
            </div>
          )}

          {/* Acciones */}
          <div className="flex space-x-3 pt-4 border-t">
            {selectedTransfer.status === 'pending_review' && (
              <>
                <button
                  onClick={() => handleAction(selectedTransfer.id, 'confirm', 'Confirmado desde admin')}
                  disabled={actionLoading}
                  className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition disabled:opacity-50"
                >
                  {actionLoading ? <SpinnerLoading size={16} /> : 'Confirmar'}
                </button>
                <button
                  onClick={() => {
                    const notes = prompt('Motivo del rechazo:');
                    if (notes) {
                      handleAction(selectedTransfer.id, 'reject', notes);
                    }
                  }}
                  disabled={actionLoading}
                  className="flex-1 bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 transition disabled:opacity-50"
                >
                  Rechazar
                </button>
              </>
            )}
            <button
              onClick={closeDetails}
              className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-md hover:bg-gray-600 transition"
            >
              Cerrar
            </button>
          </div>
        </div>
      </ModalLayout>
    );
  }

  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={onClose}
      title="Administrar Transferencias Bancarias"
      size="xl"
    >
      <div className="space-y-4">
        {/* Filtros */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="">Todos</option>
                <option value="uploaded">Subido</option>
                <option value="pending_review">Pendiente de Revisión</option>
                <option value="confirmed">Confirmado</option>
                <option value="rejected">Rechazado</option>
                <option value="processing">Procesando</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Búsqueda</label>
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                placeholder="Reserva, CBU, banco..."
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
            </div>
            <div className="flex items-end">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.needs_review}
                  onChange={(e) => setFilters(prev => ({ ...prev, needs_review: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Solo pendientes</span>
              </label>
            </div>
            <div className="flex items-end">
              <button
                onClick={loadTransfers}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition"
              >
                Filtrar
              </button>
            </div>
          </div>
        </div>

        {/* Lista de transferencias */}
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <SpinnerLoading size={32} />
            <span className="ml-2 text-gray-600">Cargando transferencias...</span>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-red-700">{error}</p>
          </div>
        ) : transfers.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No hay transferencias que coincidan con los filtros</p>
          </div>
        ) : (
          <div className="space-y-3">
            {transfers.map((transfer) => (
              <div key={transfer.id} className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(transfer.status)}`}>
                        {transfer.status_display}
                      </span>
                      <span className="text-sm text-gray-500">
                        {formatDate(transfer.created_at)}
                      </span>
                      {transfer.needs_review && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                          Requiere Revisión
                        </span>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Reserva:</span>
                        <span className="font-semibold ml-1">#{transfer.reservation_id}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Monto:</span>
                        <span className="font-semibold ml-1 text-green-600">
                          {formatCurrency(transfer.amount)}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">CBU:</span>
                        <span className="ml-1 font-mono text-xs">{transfer.cbu_iban}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Hotel:</span>
                        <span className="ml-1">{transfer.hotel_name}</span>
                      </div>
                    </div>

                    {/* Validación rápida */}
                    {transfer.ocr_amount && (
                      <div className="mt-2 text-xs text-gray-600">
                        OCR: {formatCurrency(transfer.ocr_amount)}
                        {transfer.is_amount_valid !== null && (
                          <span className={`ml-1 ${transfer.is_amount_valid ? 'text-green-600' : 'text-red-600'}`}>
                            {transfer.is_amount_valid ? '✓' : '✗'}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="flex space-x-2 ml-4">
                    <button
                      onClick={() => openDetails(transfer)}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      Ver Detalles
                    </button>
                    {transfer.status === 'pending_review' && (
                      <>
                        <button
                          onClick={() => handleAction(transfer.id, 'confirm', 'Confirmado desde admin')}
                          disabled={actionLoading}
                          className="text-green-600 hover:text-green-800 text-sm disabled:opacity-50"
                        >
                          Confirmar
                        </button>
                        <button
                          onClick={() => {
                            const notes = prompt('Motivo del rechazo:');
                            if (notes) {
                              handleAction(transfer.id, 'reject', notes);
                            }
                          }}
                          disabled={actionLoading}
                          className="text-red-600 hover:text-red-800 text-sm disabled:opacity-50"
                        >
                          Rechazar
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </ModalLayout>
  );
}
