import { useMemo, useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import { useUserHotels } from 'src/hooks/useUserHotels'
import { useDispatchAction } from 'src/hooks/useDispatchAction'
import { useGet } from 'src/hooks/useGet'
import SelectAsync from 'src/components/selects/SelectAsync'
import { Formik } from 'formik'
import { format, parseISO } from 'date-fns'
import Filter from 'src/components/Filter'
import Badge from 'src/components/Badge'
import Button from 'src/components/Button'
import InvoiceModal from 'src/components/invoicing/InvoiceModal'
import InvoicePDFViewer from 'src/components/invoicing/InvoicePDFViewer'

export default function InvoicesList() {
  const { t } = useTranslation()
  const [showInvoiceModal, setShowInvoiceModal] = useState(false)
  const [selectedInvoice, setSelectedInvoice] = useState(null)
  const [showPDFViewer, setShowPDFViewer] = useState(false)
  const [pdfUrl, setPdfUrl] = useState('')
  const [sendingInvoiceId, setSendingInvoiceId] = useState(null)
  const [filters, setFilters] = useState({ 
    search: '', 
    hotel: '', 
    type: '', 
    status: '', 
    dateFrom: '', 
    dateTo: '',
    cae: ''
  })
  const didMountRef = useRef(false)
  const { hotelIdsString, isSuperuser, hotelIds } = useUserHotels()
  
  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'invoicing/invoices',
    params: { 
      search: filters.search, 
      hotel: filters.hotel || undefined, 
      type: filters.type || undefined,
      status: filters.status || undefined,
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
      cae: filters.cae || undefined,
    },
  })

  // Cargar estadísticas de facturación
  const { data: statsData, isLoading: statsLoading } = useGet({
    resource: 'invoicing/invoices/stats',
    enabled: true
  })

  const { mutate: retryInvoice, isPending: retrying } = useDispatchAction({
    resource: 'invoicing/invoices',
    onSuccess: () => refetch()
  })

  const { mutate: cancelInvoice, isPending: cancelling } = useDispatchAction({
    resource: 'invoicing/invoices',
    onSuccess: () => refetch()
  })

  const { mutate: sendToAfip, isPending: sending } = useDispatchAction({
    resource: 'invoicing/invoices',
    onSuccess: () => {
      setSendingInvoiceId(null)
      refetch()
    },
    onError: () => {
      setSendingInvoiceId(null)
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

  const displayResults = useMemo(() => {
    return results || []
  }, [results])

  // Funciones de traducción para badges
  const getTypeLabel = (type) => {
    const typeMap = {
      'A': 'Factura A',
      'B': 'Factura B', 
      'C': 'Factura C',
      'NC': 'Nota de Crédito',
      'ND': 'Nota de Débito',
    }
    return typeMap[type] || type
  }

  const getStatusLabel = (status) => {
    const statusMap = {
      'draft': 'Borrador',
      'sent': 'Enviada',
      'approved': 'Aprobada',
      'error': 'Error',
      'rejected': 'Rechazada',
      'cancelled': 'Cancelada',
      'expired': 'Expirada',
    }
    return statusMap[status] || status
  }

  const getStatusVariant = (status) => {
    const variantMap = {
      'draft': 'invoice-draft',
      'sent': 'invoice-sent',
      'approved': 'invoice-approved',
      'error': 'invoice-rejected',
      'rejected': 'invoice-rejected',
      'cancelled': 'invoice-cancelled',
      'expired': 'invoice-expired',
    }
    return variantMap[status] || 'invoice-default'
  }

  const handleViewPDF = (invoice) => {
    getPDF({
      action: `${invoice.id}/pdf/?refresh=1`,
      method: 'GET'
    })
  }

  const handleRetryInvoice = (invoiceId) => {
    retryInvoice({ action: `${invoiceId}/retry`, body: {}, method: 'POST' })
  }

  const handleCancelInvoice = (invoiceId) => {
    if (window.confirm('¿Estás seguro de que quieres cancelar esta factura?')) {
      cancelInvoice({ action: `${invoiceId}/cancel`, body: {}, method: 'POST' })
    }
  }

  const handleCreateCreditNote = (invoice) => {
    setSelectedInvoice(invoice)
    setShowInvoiceModal(true)
  }

  const handleSendToAfip = (invoice) => {
    setSendingInvoiceId(invoice.id)
    const payload = invoice.can_be_resent ? {} : { force_send: true }
    sendToAfip({ action: `${invoice.id}/send_to_afip`, body: payload, method: 'POST' })
  }

  useEffect(() => {
    if (!didMountRef.current) { didMountRef.current = true; return }
    const id = setTimeout(() => refetch(), 400)
    return () => clearTimeout(id)
  }, [filters.search, filters.hotel, filters.type, filters.status, filters.dateFrom, filters.dateTo, filters.cae, refetch])

  const columns = [
    { 
      key: 'number', 
      header: 'Número', 
      sortable: true,
      render: (r) => (
        <button
          className="link text-blue-600 hover:text-blue-800"
          onClick={() => setSelectedInvoice(r)}
        >
          {r.number}
        </button>
      )
    },
    { key: 'type', header: 'Tipo', sortable: true, render: (r) => getTypeLabel(r.type) },
    { key: 'customer_name', header: 'Cliente', sortable: true },
    { key: 'hotel_name', header: 'Hotel', sortable: true },
    { 
      key: 'total', 
      header: 'Total', 
      sortable: true, 
      right: true, 
      render: (r) => (
        <span className="font-semibold text-green-600">
          ${r.total?.toLocaleString() || '0'}
        </span>
      ) 
    },
    { 
      key: 'status', 
      header: 'Estado', 
      sortable: true, 
      render: (r) => (
        <Badge variant={getStatusVariant(r.status)} size="sm">
          {getStatusLabel(r.status)}
        </Badge>
      ) 
    },
    { 
      key: 'cae', 
      header: 'CAE', 
      sortable: true,
      render: (r) => r.cae ? (
        <span className="font-mono text-sm">{r.cae}</span>
      ) : '-'
    },
    {
      key: 'issue_date',
      header: 'Fecha Emisión',
      sortable: true,
      render: (e) => e.issue_date ? format(parseISO(e.issue_date), 'dd/MM/yyyy') : '',
    },
    {
      key: 'cae_expiration',
      header: 'Vencimiento CAE',
      sortable: true,
      render: (e) => e.cae_expiration ? format(parseISO(e.cae_expiration), 'dd/MM/yyyy') : '-',
    },
    {
      key: 'attempts',
      header: 'Intentos',
      sortable: false,
      right: true,
      render: (r) => (
        <span
          className={`text-sm ${Number(r.retry_count || 0) > 0 ? 'font-semibold' : ''} ${r.last_error ? 'text-red-600' : ''}`}
          title={r.last_error || ''}
        >
          {r.retry_count ?? 0}{r.last_error ? ' ⚠️' : ''}
        </span>
      )
    },
    {
      key: 'actions',
      header: 'Acciones',
      sortable: false,
      right: true,
      render: (r) => (
        <div className="flex justify-end items-center gap-2">
          <button
            className="px-2 py-1 rounded text-xs border bg-blue-50 text-blue-700 border-blue-300 hover:bg-blue-100"
            onClick={() => handleViewPDF(r)}
            disabled={loadingPDF}
            title="Ver PDF"
          >
            {loadingPDF ? 'Cargando...' : 'PDF'}
          </button>
          
          {r.status === 'error' && (
            <button
              className="px-2 py-1 rounded text-xs border bg-orange-50 text-orange-700 border-orange-300 hover:bg-orange-100"
              onClick={() => handleRetryInvoice(r.id)}
              disabled={retrying}
              title="Reintentar"
            >
              Reintentar
            </button>
          )}

          {(r.status === 'draft' || r.status === 'error' || r.can_be_resent) && (
            <button
              className="px-2 py-1 rounded text-xs border bg-green-50 text-green-700 border-green-300 hover:bg-green-100"
              onClick={() => handleSendToAfip(r)}
              disabled={sendingInvoiceId === r.id}
              title={r.status === 'draft' ? 'Enviar a AFIP' : 'Re-enviar a AFIP'}
            >
              {sendingInvoiceId === r.id ? 'Enviando...' : (r.status === 'draft' ? 'Enviar AFIP' : 'Re-enviar AFIP')}
            </button>
          )}
          
          {r.status === 'approved' && (
            <button
              className="px-2 py-1 rounded text-xs border bg-purple-50 text-purple-700 border-purple-300 hover:bg-purple-100"
              onClick={() => handleCreateCreditNote(r)}
              title="Crear Nota de Crédito"
            >
              NC
            </button>
          )}
          
          {(r.status === 'draft' || r.status === 'sent') && (
            <button
              className="px-2 py-1 rounded text-xs border bg-red-50 text-red-700 border-red-300 hover:bg-red-100"
              onClick={() => handleCancelInvoice(r.id)}
              disabled={cancelling}
              title="Cancelar"
            >
              Cancelar
            </button>
          )}
        </div>
      )
    },
  ]

  return (
    <div className="flex flex-col h-full max-h-full overflow-hidden">
      {/* Contenedor fijo para estadísticas y filtros */}
      <div className="flex-shrink-0 space-y-5 pb-5">
        {/* Estadísticas */}
        {statsData && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
            <div className="text-center">
              <div className="text-2xl font-bold text-aloja-navy">{statsData.summary?.total_invoices || 0}</div>
              <div className="text-sm text-gray-600">Total Facturas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">${statsData.summary?.total_amount?.toLocaleString() || 0}</div>
              <div className="text-sm text-gray-600">Monto Total</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{statsData.summary?.approved_count || 0}</div>
              <div className="text-sm text-gray-600">Aprobadas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{statsData.summary?.rejected_count || 0}</div>
              <div className="text-sm text-gray-600">Rechazadas</div>
            </div>
          </div>
        )}

        <Filter>
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex flex-col">
              <label className="text-xs text-aloja-gray-800/60">Búsqueda</label>
              <input
                className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-64 transition-all"
                placeholder="Buscar por número, cliente, CAE..."
                value={filters.search}
                onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
              />
            </div>

            <Formik
              enableReinitialize
              initialValues={{ hotel: filters.hotel }}
              onSubmit={() => { }}
            >
              {() => (
                <div className="w-56">
                  <SelectAsync
                    title="Hotel"
                    name='hotel'
                    resource='hotels'
                    placeholder="Todos los hoteles"
                    getOptionLabel={(h) => h?.name}
                    getOptionValue={(h) => h?.id}
                    extraParams={!isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {}}
                    onValueChange={(opt, val) => setFilters((f) => ({ ...f, hotel: String(val || '') }))}
                  />
                </div>
              )}
            </Formik>

            <div className="w-40">
              <label className="text-xs text-aloja-gray-800/60">Tipo</label>
              <select
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full"
                value={filters.type}
                onChange={(e) => setFilters((f) => ({ ...f, type: e.target.value }))}
              >
                <option value="">Todos</option>
                <option value="A">Factura A</option>
                <option value="B">Factura B</option>
                <option value="C">Factura C</option>
                <option value="NC">Nota de Crédito</option>
                <option value="ND">Nota de Débito</option>
              </select>
            </div>

            <div className="w-40">
              <label className="text-xs text-aloja-gray-800/60">Estado</label>
              <select
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full"
                value={filters.status}
                onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
              >
                <option value="">Todos</option>
                <option value="draft">Borrador</option>
                <option value="sent">Enviada</option>
                <option value="approved">Aprobada</option>
                <option value="error">Error</option>
                <option value="rejected">Rechazada</option>
                <option value="cancelled">Cancelada</option>
                <option value="expired">Expirada</option>
              </select>
            </div>

            <div className="flex flex-col">
              <label className="text-xs text-aloja-gray-800/60">Desde</label>
              <input type="date" className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                value={filters.dateFrom}
                onChange={(e) => setFilters((f) => ({ ...f, dateFrom: e.target.value }))}
              />
            </div>
            <div className="flex flex-col">
              <label className="text-xs text-aloja-gray-800/60">Hasta</label>
              <input type="date" className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                value={filters.dateTo}
                onChange={(e) => setFilters((f) => ({ ...f, dateTo: e.target.value }))}
              />
            </div>

            <div className="flex flex-col">
              <label className="text-xs text-aloja-gray-800/60">CAE</label>
              <input
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-32"
                placeholder="12345678901234"
                value={filters.cae}
                onChange={(e) => setFilters((f) => ({ ...f, cae: e.target.value }))}
              />
            </div>

            <div className="ml-auto">
              <button className="px-3 py-2 rounded-md border text-sm" onClick={() => setFilters({ 
                search: '', hotel: '', type: '', status: '', 
                dateFrom: '', dateTo: '', cae: '' 
              })}>
                Limpiar Filtros
              </button>
            </div>
          </div>
        </Filter>
      </div>

      {/* Contenedor con scroll para la tabla */}
      <div className="flex-1 min-h-0 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto">
          <TableGeneric
            isLoading={isPending}
            data={displayResults}
            getRowId={(r) => r.id}
            columns={columns}
          />
        </div>

        {hasNextPage && (
          <div className="flex-shrink-0 pt-4 border-t">
            <button className="px-3 py-2 rounded-md border text-sm" onClick={() => fetchNextPage()}>
              Cargar más
            </button>
          </div>
        )}
      </div>

      {/* Modales */}
      <InvoiceModal
        isOpen={showInvoiceModal}
        onClose={() => setShowInvoiceModal(false)}
        invoice={selectedInvoice}
        onSuccess={() => {
          setShowInvoiceModal(false)
          setSelectedInvoice(null)
          refetch()
        }}
      />

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
