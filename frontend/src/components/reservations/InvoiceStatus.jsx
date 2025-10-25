import { useList } from 'src/hooks/useList'
import { useDispatchAction } from 'src/hooks/useDispatchAction'
import Badge from 'src/components/Badge'
import { useState } from 'react'
import InvoicePDFViewer from 'src/components/invoicing/InvoicePDFViewer'
import Button from 'src/components/Button'

export default function InvoiceStatus({ reservationId, paymentId }) {
  const [showPDFViewer, setShowPDFViewer] = useState(false)
  const [pdfUrl, setPdfUrl] = useState('')

  // Buscar facturas relacionadas con esta reserva o pago
  const { results: invoices, isPending: isLoading } = useList({
    resource: 'invoicing/invoices',
    params: { 
      reservation: reservationId,
      payment: paymentId 
    }
  })

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
      <div className="flex items-center gap-2">
        <Badge variant="invoice-draft" size="sm">
          Sin facturar
        </Badge>
      </div>
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
    <div className="flex items-center gap-2">
      <Badge variant={getStatusVariant(invoice.status)} size="sm">
        {getStatusLabel(invoice.status)}
      </Badge>
      
      {invoice.status === 'approved' && (
        <Button
          size="sm"
          variant="secondary"
          onClick={() => handleViewPDF(invoice)}
          disabled={loadingPDF}
        >
          {loadingPDF ? 'Cargando...' : 'Ver PDF'}
        </Button>
      )}
      
      <span className="text-xs text-gray-500">
        #{invoice.number}
      </span>

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
    </div>
  )
}
