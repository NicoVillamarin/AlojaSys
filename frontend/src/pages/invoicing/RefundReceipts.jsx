import { useState, useMemo, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import { useDispatchAction } from 'src/hooks/useDispatchAction'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import Button from 'src/components/Button'
import SelectAsync from 'src/components/selects/SelectAsync'
import { Formik } from 'formik'
import { format, parseISO } from 'date-fns'
import { convertToDecimal } from '../utils'
import Filter from 'src/components/Filter'
import { useUserHotels } from 'src/hooks/useUserHotels'
import Badge from 'src/components/Badge'
import Swal from 'sweetalert2'
import EyeIcon from 'src/assets/icons/EyeIcon'
import DocumentArrowDown from 'src/assets/icons/DocumentArrowDown'

export default function RefundReceipts() {
  const { t } = useTranslation()
  const [filters, setFilters] = useState({ 
    search: '', 
    hotel: '', 
    refund_method: '', 
    status: '', 
    dateFrom: '', 
    dateTo: '' 
  })
  const didMountRef = useRef(false)
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel } = useUserHotels()
  
  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'payments/refunds',
    params: { 
      search: filters.search,
      hotel: filters.hotel || undefined,
      refund_method: filters.refund_method || undefined,
      status: filters.status || undefined,
      show_historical: true,
    },
  })

  // Obtener lista de hoteles
  const { results: hotels } = useList({ 
    resource: "hotels",
    params: !isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {}
  })

  const displayResults = useMemo(() => {
    if (!results || !Array.isArray(results)) return []
    
    // Mostrar todos los reembolsos, no solo los que tienen comprobantes
    return results
  }, [results])

  const onGenerateReceipt = async (refund) => {
    try {
      const response = await fetchWithAuth(`${getApiURL()}/api/payments/generate-refund-receipt/${refund.id}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response?.receipt_pdf_url) {
        Swal.fire({
          title: 'Comprobante Generado',
          text: 'Se ha generado el comprobante de devolución exitosamente',
          icon: 'success',
          confirmButtonText: 'Ver Comprobante',
          showCancelButton: true,
          cancelButtonText: 'Cerrar'
        }).then((result) => {
          if (result.isConfirmed) {
            window.open(response.receipt_pdf_url, '_blank')
          }
        })
        // Refrescar la lista para que aparezca el link de comprobante
        try { await refetch() } catch {}
      } else {
        Swal.fire({
          title: 'Error',
          text: 'No se pudo generar el comprobante',
          icon: 'error',
          confirmButtonText: 'OK'
        })
      }
    } catch (error) {
      console.error('Error generando comprobante:', error)
      Swal.fire({
        title: 'Error',
        text: 'Error al generar el comprobante',
        icon: 'error',
        confirmButtonText: 'OK'
      })
    }
  }

  const onViewReceipt = (refund) => {
    if (refund.receipt_pdf_url) {
      // Construir URL completa si es relativa
      let pdfUrl = refund.receipt_pdf_url
      if (pdfUrl.startsWith('/media/')) {
        pdfUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${pdfUrl}`
      }
      
      window.open(pdfUrl, '_blank')
    }
  }

  const onDownloadReceipt = (refund) => {
    if (refund.receipt_pdf_url) {
      // Construir URL completa si es relativa
      let pdfUrl = refund.receipt_pdf_url
      if (pdfUrl.startsWith('/media/')) {
        pdfUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${pdfUrl}`
      }
      
      const link = document.createElement('a')
      link.href = pdfUrl
      link.download = `comprobante_devolucion_${refund.receipt_number || refund.id}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      'pending': { variant: 'warning', text: 'Pendiente' },
      'processing': { variant: 'info', text: 'Procesando' },
      'completed': { variant: 'success', text: 'Completado' },
      'failed': { variant: 'error', text: 'Fallido' },
      'cancelled': { variant: 'neutral', text: 'Cancelado' }
    }
    
    const config = statusConfig[status] || { variant: 'neutral', text: status }
    return <Badge variant={config.variant} size="sm">{config.text}</Badge>
  }

  const getRefundMethodBadge = (method) => {
    const methodConfig = {
      'cash': { variant: 'success', text: 'Efectivo' },
      'bank_transfer': { variant: 'info', text: 'Transferencia' },
      'credit_card': { variant: 'primary', text: 'Tarjeta' },
      'voucher': { variant: 'warning', text: 'Voucher' },
      'original_payment': { variant: 'neutral', text: 'Método Original' }
    }
    
    const config = methodConfig[method] || { variant: 'neutral', text: method }
    return <Badge variant={config.variant} size="sm">{config.text}</Badge>
  }

  const columns = [
    {
      key: 'receipt_number',
      header: 'N° Comprobante',
      render: (refund) => (
          <div>
            {refund.receipt_number || `#${refund.id}`}
          </div>
      )
    },
    {
      key: 'reservation',
      header: 'Reserva',
      render: (refund) => (
        <div>
          {refund.reservation_display_name}
        </div>
      )
    },
    {
      key: 'hotel',
      header: 'Hotel',
      render: (refund) => (
        <div>
          {refund.hotel_name || 'N/A'}
        </div>
      )
    },
    {
      key: 'amount',
      header: 'Monto',
      render: (refund) => `$${convertToDecimal(refund.amount).toLocaleString('es-AR', { minimumFractionDigits: 2 })}`
    },
    {
      key: 'refund_method',
      header: 'Método',
      render: (refund) => getRefundMethodBadge(refund.refund_method)
    },
    {
      key: 'status',
      header: 'Estado',
      render: (refund) => getStatusBadge(refund.status)
    },
    {
      key: 'created_at',
      header: 'Fecha',
      render: (refund) => format(parseISO(refund.created_at), 'dd/MM/yyyy HH:mm')
    },
    {
      key: 'actions',
      header: 'Acciones',
      sortable: false,
      right: true,
      render: (refund) => (
          <div className="flex justify-end items-center gap-2">
            {refund.receipt_pdf_url ? (
              <>
                <button
                  onClick={() => onViewReceipt(refund)}
                  className="p-2 rounded text-gray-600 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                  title="Ver comprobante"
                >
                  <EyeIcon size="18" />
                </button>
                <button
                  onClick={() => onDownloadReceipt(refund)}
                  className="p-2 rounded text-gray-600 hover:text-green-600 hover:bg-green-50 transition-colors"
                  title="Descargar comprobante"
                >
                  <DocumentArrowDown size="18" />
                </button>
              </>
            ) : (
              <Button
                onClick={() => onGenerateReceipt(refund)}
                variant="success"
                size="xs"
              >
                Generar Comprobante
              </Button>
            )}
          </div>
        )
    }
  ]

  const searchResults = useMemo(() => {
    if (!displayResults) return []
    
    let filtered = displayResults
    
    // Filtro por búsqueda
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      filtered = filtered.filter(refund => 
        refund.reservation_display_name?.toLowerCase().includes(searchLower) ||
        refund.hotel_name?.toLowerCase().includes(searchLower) ||
        refund.refund_method?.toLowerCase().includes(searchLower) ||
        refund.id.toString().includes(searchLower)
      )
    }
    
    return filtered
  }, [displayResults, filters.search])

  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true
    }
  }, [])

  return (
    <div className="space-y-5">
      <Filter>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">Buscar</label>
            <input
              className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-64 transition-all"
              placeholder="Reserva, hotel, método..."
              value={filters.search}
              onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
            />
          </div>

          <Formik
            enableReinitialize
            initialValues={{
              hotel: filters.hotel || '',
              refund_method: filters.refund_method || '',
              status: filters.status || '',
            }}
            onSubmit={(values) => {
              setFilters(prev => ({
                ...prev,
                hotel: values.hotel,
                refund_method: values.refund_method,
                status: values.status,
              }))
            }}
          >
            {({ values, setFieldValue, handleSubmit }) => (
              <>
                {!hasSingleHotel && (
                  <div className="flex flex-col">
                    <label className="text-xs text-aloja-gray-800/60">Hotel</label>
                    <SelectAsync
                      value={values.hotel}
                      onChange={(value) => setFieldValue('hotel', value)}
                      options={hotels?.map(hotel => ({
                        value: hotel.id,
                        label: hotel.name
                      })) || []}
                      placeholder="Todos los hoteles"
                      className="w-48"
                    />
                  </div>
                )}

                <div className="flex flex-col">
                  <label className="text-xs text-aloja-gray-800/60">Método</label>
                  <select
                    value={values.refund_method}
                    onChange={(e) => setFieldValue('refund_method', e.target.value)}
                    className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-40 transition-all"
                  >
                    <option value="">Todos</option>
                    <option value="cash">Efectivo</option>
                    <option value="bank_transfer">Transferencia</option>
                    <option value="credit_card">Tarjeta</option>
                    <option value="voucher">Voucher</option>
                    <option value="original_payment">Método Original</option>
                  </select>
                </div>

                <div className="flex flex-col">
                  <label className="text-xs text-aloja-gray-800/60">Estado</label>
                  <select
                    value={values.status}
                    onChange={(e) => setFieldValue('status', e.target.value)}
                    className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-40 transition-all"
                  >
                    <option value="">Todos</option>
                    <option value="pending">Pendiente</option>
                    <option value="processing">Procesando</option>
                    <option value="completed">Completado</option>
                    <option value="failed">Fallido</option>
                    <option value="cancelled">Cancelado</option>
                  </select>
                </div>

                <Button
                  type="button"
                  variant="primary"
                  onClick={handleSubmit}
                  className="px-4 py-2"
                >
                  Filtrar
                </Button>
              </>
            )}
          </Formik>
        </div>
      </Filter>

      <TableGeneric
        columns={columns}
        data={searchResults || []}
        loading={isPending}
        onLoadMore={hasNextPage ? fetchNextPage : null}
        emptyMessage="No hay reembolsos disponibles. Los reembolsos aparecerán aquí cuando se creen desde la gestión de reservas."
        className="min-h-[400px]"
      />

    </div>
  )
}
