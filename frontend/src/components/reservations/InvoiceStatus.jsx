import { useDispatchAction } from 'src/hooks/useDispatchAction'
import Badge from 'src/components/Badge'
import { useEffect, useState } from 'react'
import InvoicePDFViewer from 'src/components/invoicing/InvoicePDFViewer'
import Tooltip from 'src/components/Tooltip'
import InvoiceTooltip from './InvoiceTooltip'
import DownloadIcon from 'src/assets/icons/DownloadIcon'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'

export default function InvoiceStatus({ reservationId, paymentId }) {
  const [showPDFViewer, setShowPDFViewer] = useState(false)
  const [pdfUrl, setPdfUrl] = useState('')
  const [invoices, setInvoices] = useState([])
  const [isLoading, setIsLoading] = useState(false)

  // Cargar facturas por reserva usando el endpoint dedicado
  useEffect(() => {
    let cancelled = false
    const load = async () => {
      if (!reservationId) { setInvoices([]); return }
      setIsLoading(true)
      try {
        const data = await fetchWithAuth(`${getApiURL()}/api/invoicing/invoices/by-reservation/${reservationId}/`, { method: 'GET' })
        if (!cancelled) setInvoices(Array.isArray(data) ? data : [])
      } catch (e) {
        if (!cancelled) setInvoices([])
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [reservationId])

  const { mutate: getPDF, isPending: loadingPDF } = useDispatchAction({
    resource: 'invoicing/invoices',
    onSuccess: (data) => {
      console.log('Respuesta del PDF:', data)
      // Si data es un string (contenido del PDF), crear blob
      if (typeof data === 'string' && data.startsWith('%PDF')) {
        const blob = new Blob([data], { type: 'application/pdf' })
        const url = window.URL.createObjectURL(blob)
        setPdfUrl(url)
        setShowPDFViewer(true)
      } else if (data && data.pdf_url) {
        // Construir URL completa del PDF
        const fullPdfUrl = data.pdf_url.startsWith('http') 
          ? data.pdf_url 
          : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${data.pdf_url}`
        console.log('URL completa del PDF:', fullPdfUrl)
        setPdfUrl(fullPdfUrl)
        setShowPDFViewer(true)
      } else {
        console.error('No se recibió pdf_url en la respuesta')
      }
    },
    onError: (error) => {
      console.error('Error obteniendo PDF:', error)
    }
  })

  const handleViewPDF = (invoice) => {
    getPDF({
      action: `${invoice.id}/pdf/?refresh=1`,
      method: 'GET'
    })
  }

  if (isLoading) {
    return <span className="text-sm text-gray-500">Cargando...</span>
  }

  if (!invoices || invoices.length === 0) {
    return (
      <Tooltip
        content={<InvoiceTooltip invoice={null} />}
        position="bottom"
        maxWidth="320px"
      >
        <div className="inline-block">
          <Badge variant="invoice-draft" size="sm">
            Sin facturar
          </Badge>
        </div>
      </Tooltip>
    )
  }

  const invoice = invoices[0] // Tomar la primera factura

  const getStatusVariant = (status) => {
    const variantMap = {
      'draft': 'invoice-draft',
      'sent': 'invoice-sent',
      'approved': 'invoice-approved',
      'rejected': 'invoice-rejected',
      'cancelled': 'invoice-cancelled',
      'expired': 'invoice-expired',
      'error': 'error',
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
      'error': 'Error',
    }
    return statusMap[status] || status
  }

  return (
    <>
      <div className="flex items-center gap-1.5">
        <Tooltip
          content={<InvoiceTooltip invoice={invoice} />}
          position="bottom"
          maxWidth={invoice.last_error ? "450px" : "320px"}
        >
          <div className="inline-block">
            <Badge variant={getStatusVariant(invoice.status)} size="sm">
              {getStatusLabel(invoice.status)}
            </Badge>
          </div>
        </Tooltip>
        
        {invoice.status === 'approved' && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleViewPDF(invoice)
            }}
            disabled={loadingPDF}
            className="p-1 rounded hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Descargar PDF"
          >
            <DownloadIcon size="14" />
          </button>
        )}
      </div>

      <InvoicePDFViewer
        isOpen={showPDFViewer}
        onClose={() => {
          setShowPDFViewer(false)
          if (pdfUrl) {
            window.URL.revokeObjectURL(pdfUrl)
            setPdfUrl('')
          }
        }}
        pdfUrl={pdfUrl}
      />
    </>
  )
}
