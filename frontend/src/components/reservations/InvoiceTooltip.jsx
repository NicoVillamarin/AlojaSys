import Badge from 'src/components/Badge'
import { format, parseISO } from 'date-fns'

// Función para formatear y traducir mensajes de error comunes
const formatErrorMessage = (errorMsg) => {
  if (!errorMsg) return ''
  
  let msg = errorMsg
  
  // Traducciones comunes
  const translations = {
    'Error sending invoice': 'Error enviando factura',
    'AFIP rejected the invoice': 'AFIP rechazó la factura',
    'Error processing AFIP response': 'Error procesando respuesta de AFIP',
    'Error de autenticación': 'Error de autenticación AFIP',
    'Error enviando factura': 'Error enviando factura a AFIP',
    'Connection error': 'Error de conexión',
    'SOAP Fault': 'Error SOAP de AFIP',
    'Empty response': 'Respuesta vacía de AFIP',
    'Unknown error': 'Error desconocido',
  }
  
  // Aplicar traducciones
  Object.entries(translations).forEach(([en, es]) => {
    if (msg.includes(en)) {
      msg = msg.replace(new RegExp(en, 'gi'), es)
    }
  })
  
  // Limpiar mensajes repetidos o redundantes
  msg = msg.replace(/Error\s+enviando\s+factura\s*:\s*Error\s+enviando\s+factura/gi, 'Error enviando factura')
  msg = msg.replace(/Error\s+procesando\s+respuesta\s+de\s+AFIP\s*:\s*AFIP\s+rechazó\s+la\s+factura/gi, 'AFIP rechazó la factura')
  
  return msg
}

const InvoiceTooltip = ({ invoice }) => {
  if (!invoice) {
    return (
      <div className="space-y-2 min-w-[240px]">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-gray-100">Estado Facturación</span>
          <Badge variant="invoice-draft" size="sm">
            Sin facturar
          </Badge>
        </div>
      </div>
    )
  }

  const getStatusVariant = (status) => {
    const variantMap = {
      'draft': 'invoice-draft',
      'sent': 'invoice-sent',
      'approved': 'invoice-approved',
      'rejected': 'invoice-rejected',
      'cancelled': 'invoice-cancelled',
      'expired': 'invoice-expired',
    }
    return variantMap[status] || 'invoice-default'
  }

  const getStatusLabel = (status) => {
    const statusMap = {
      'draft': 'Borrador',
      'sent': 'Enviada',
      'approved': 'Aprobada',
      'rejected': 'Rechazada',
      'cancelled': 'Cancelada',
      'expired': 'Expirada',
    }
    return statusMap[status] || status
  }

  return (
    <div className="space-y-3 min-w-[280px] max-w-[400px]">
      {/* Header con estado principal */}
      <div className="flex items-center justify-between">
        <span className="font-semibold text-gray-100">Estado Facturación</span>
        <Badge variant={getStatusVariant(invoice.status)} size="sm">
          {getStatusLabel(invoice.status)}
        </Badge>
      </div>

      {/* Información de la factura */}
      <div className="space-y-2">
        <div className="flex justify-between items-center py-1 border-b border-gray-700">
          <span className="text-gray-300">Número:</span>
          <span className="font-semibold text-white">
            #{invoice.number}
          </span>
        </div>

        {invoice.type && (
          <div className="flex justify-between items-center py-1 border-b border-gray-700">
            <span className="text-gray-300">Tipo:</span>
            <span className="text-gray-200">
              Factura {invoice.type}
            </span>
          </div>
        )}

        {invoice.issue_date && (
          <div className="flex justify-between items-center py-1 border-b border-gray-700">
            <span className="text-gray-300">Fecha Emisión:</span>
            <span className="text-gray-200">
              {format(parseISO(invoice.issue_date), 'dd/MM/yyyy')}
            </span>
          </div>
        )}

        {invoice.total && (
          <div className="flex justify-between items-center py-1 border-b border-gray-700">
            <span className="text-gray-300">Total:</span>
            <span className="font-semibold text-white">
              ${parseFloat(invoice.total).toLocaleString('es-AR', { minimumFractionDigits: 2 })}
            </span>
          </div>
        )}

        {invoice.cae && (
          <div className="flex justify-between items-center py-1 border-b border-gray-700">
            <span className="text-gray-300">CAE:</span>
            <span className="font-mono text-xs text-green-400">
              {invoice.cae}
            </span>
          </div>
        )}

        {invoice.cae_expiration && (
          <div className="flex justify-between items-center py-1 border-b border-gray-700">
            <span className="text-gray-300">Vto. CAE:</span>
            <span className="text-gray-200">
              {format(parseISO(invoice.cae_expiration), 'dd/MM/yyyy')}
            </span>
          </div>
        )}

        {invoice.last_error && (
          <div className="py-1 border-b border-gray-700">
            <span className="text-gray-300 text-xs block mb-1">Error:</span>
            <div className="mt-1 p-2 bg-red-900/20 rounded border border-red-700/30">
              <span className="text-red-400 text-xs break-words whitespace-pre-wrap">
                {formatErrorMessage(invoice.last_error)}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default InvoiceTooltip

