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

export default function PaymentReceipts() {
  const { t } = useTranslation()
  const [filters, setFilters] = useState({ 
    search: '', 
    hotel: '', 
    payment_method: '', 
    status: '', 
    dateFrom: '', 
    dateTo: '' 
  })
  const didMountRef = useRef(false)
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel } = useUserHotels()
  
  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'payments',
    params: { 
      search: filters.search,
      hotel: filters.hotel || undefined,
      payment_method: filters.payment_method || undefined,
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
    const q = (filters.search || '').trim().toLowerCase()
    const from = filters.dateFrom ? new Date(filters.dateFrom) : null
    const to = filters.dateTo ? new Date(filters.dateTo) : null
    let arr = results || []

    // Filtrar solo pagos de señas (aplicar heurística si is_deposit no está presente)
    arr = arr.filter((p) => {
      // Si está explícitamente marcado como is_deposit, incluirlo
      if (p.is_deposit === true) {
        return true
      }
      
      // Para la heurística, necesitamos obtener el total_price de la reserva
      // Como no lo tenemos en el serializer actual, usamos solo is_deposit
      return false
    })

    if (q) {
      arr = arr.filter((p) => {
        const guest = String(p.guest_name ?? '').toLowerCase()
        const hotel = String(p.hotel_name ?? '').toLowerCase()
        const method = String(p.method ?? '').toLowerCase()
        const status = String(p.status ?? '').toLowerCase()
        return guest.includes(q) || hotel.includes(q) || method.includes(q) || status.includes(q)
      })
    }

    if (from || to) {
      arr = arr.filter((p) => {
        const paymentDate = new Date(p.date)
        if (from && paymentDate < from) return false
        if (to && paymentDate > to) return false
        return true
      })
    }

    return arr
  }, [results, filters.search, filters.dateFrom, filters.dateTo])

  useEffect(() => {
    if (!didMountRef.current) { didMountRef.current = true; return }
    const id = setTimeout(() => refetch(), 400)
    return () => clearTimeout(id)
  }, [filters.search, filters.hotel, filters.payment_method, filters.status, refetch])

  const getStatusBadge = (status) => {
    const statusMap = {
      'pending': { variant: 'payment-pending', text: 'Pendiente' },
      'approved': { variant: 'payment-paid', text: 'Aprobado' },
      'failed': { variant: 'payment-failed', text: 'Fallido' },
      'cancelled': { variant: 'reservation-cancelled', text: 'Cancelado' }
    }
    const statusInfo = statusMap[status] || { variant: 'default', text: status }
    return (
      <Badge variant={statusInfo.variant} size="sm">
        {statusInfo.text}
      </Badge>
    )
  }

  const getMethodBadge = (method) => {
    const methodMap = {
      'cash': { variant: 'info', text: 'Efectivo' },
      'card': { variant: 'info', text: 'Tarjeta' },
      'transfer': { variant: 'info', text: 'Transferencia' },
      'pos': { variant: 'info', text: 'POS' },
      'mercadopago': { variant: 'info', text: 'MercadoPago' }
    }
    const methodInfo = methodMap[method] || { variant: 'default', text: method }
    return (
      <Badge variant={methodInfo.variant} size="sm">
        {methodInfo.text}
      </Badge>
    )
  }

  const onViewReceipt = async (payment) => {
    try {
      if (payment.receipt_pdf_url) {
        // Construir URL completa si es relativa
        let pdfUrl = payment.receipt_pdf_url
        if (pdfUrl.startsWith('/media/')) {
          pdfUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${pdfUrl}`
        }
        
        window.open(pdfUrl, '_blank')
      } else {
        Swal.fire({
          title: 'Comprobante no disponible',
          text: 'El comprobante PDF aún no está generado. Intenta nuevamente en unos momentos.',
          icon: 'warning',
          confirmButtonText: 'OK'
        })
      }
    } catch (error) {
      console.error('Error abriendo comprobante:', error)
      Swal.fire({
        title: 'Error',
        text: 'No se pudo abrir el comprobante',
        icon: 'error',
        confirmButtonText: 'OK'
      })
    }
  }

  const onDownloadReceipt = async (payment) => {
    try {
      if (payment.receipt_pdf_url) {
        // Construir URL completa si es relativa
        let pdfUrl = payment.receipt_pdf_url
        if (pdfUrl.startsWith('/media/')) {
          pdfUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${pdfUrl}`
        }
        
        const link = document.createElement('a')
        link.href = pdfUrl
        link.download = `comprobante-pago-${payment.id}.pdf`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } else {
        Swal.fire({
          title: 'Comprobante no disponible',
          text: 'El comprobante PDF aún no está generado. Intenta nuevamente en unos momentos.',
          icon: 'warning',
          confirmButtonText: 'OK'
        })
      }
    } catch (error) {
      console.error('Error descargando comprobante:', error)
      Swal.fire({
        title: 'Error',
        text: 'No se pudo descargar el comprobante',
        icon: 'error',
        confirmButtonText: 'OK'
      })
    }
  }

  return (
    <div className="space-y-5">
      <Filter>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">Buscar</label>
            <input
              className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-64 transition-all"
              placeholder="Huésped, hotel, método..."
              value={filters.search}
              onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
            />
          </div>

          <Formik
            enableReinitialize
            initialValues={{ 
              hotel: filters.hotel, 
              payment_method: filters.payment_method,
              status: filters.status 
            }}
            onSubmit={() => { }}
          >
            {() => (
              <>
                <div className="w-56">
                  <SelectAsync
                    title="Hotel"
                    name='hotel'
                    resource='hotels'
                    placeholder="Todos los hoteles"
                    getOptionLabel={(h) => h?.name}
                    getOptionValue={(h) => h?.id}
                    onValueChange={(opt, val) => setFilters((f) => ({ ...f, hotel: String(val || '') }))}
                    extraParams={!isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {}}
                  />
                </div>

                <div className="w-48">
                  <label className="text-xs text-aloja-gray-800/60">Método de Pago</label>
                  <select
                    className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full"
                    value={filters.payment_method}
                    onChange={(e) => setFilters((f) => ({ ...f, payment_method: e.target.value }))}
                  >
                    <option value="">Todos los métodos</option>
                    <option value="cash">Efectivo</option>
                    <option value="card">Tarjeta</option>
                    <option value="transfer">Transferencia</option>
                    <option value="pos">POS</option>
                    <option value="mercadopago">MercadoPago</option>
                  </select>
                </div>

                <div className="w-48">
                  <label className="text-xs text-aloja-gray-800/60">Estado</label>
                  <select
                    className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full"
                    value={filters.status}
                    onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
                  >
                    <option value="">Todos los estados</option>
                    <option value="pending">Pendiente</option>
                    <option value="approved">Aprobado</option>
                    <option value="failed">Fallido</option>
                    <option value="cancelled">Cancelado</option>
                  </select>
                </div>
              </>
            )}
          </Formik>

          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">Desde</label>
            <input 
              type="date" 
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
              value={filters.dateFrom}
              onChange={(e) => setFilters((f) => ({ ...f, dateFrom: e.target.value }))}
            />
          </div>
          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">Hasta</label>
            <input 
              type="date" 
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
              value={filters.dateTo}
              onChange={(e) => setFilters((f) => ({ ...f, dateTo: e.target.value }))}
            />
          </div>

          <div className="ml-auto">
            <button 
              className="px-3 py-2 rounded-md border text-sm" 
              onClick={() => setFilters({ 
                search: '', 
                hotel: '', 
                payment_method: '', 
                status: '', 
                dateFrom: '', 
                dateTo: '' 
              })}
            >
              Limpiar filtros
            </button>
          </div>
        </div>
      </Filter>

      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(p) => p.id}
        columns={[
          {
            key: 'receipt_number',
            header: 'N° Comprobante',
            sortable: true,
            render: (p) => (
              <div>
                  {p.receipt_number || `#${p.id}`}
              </div>
            )
          },
          { 
            key: 'reservation', 
            header: 'Reserva', 
            sortable: true,
            render: (p) => (
              <div>
                <div>{p.reservation_display_name || `#${p.reservation_id}`}</div>
              </div>
            )
          },
          { 
            key: 'hotel', 
            header: 'Hotel', 
            sortable: true,
            render: (p) => p.hotel_name || '-'
          },
          { 
            key: 'amount', 
            header: 'Monto', 
            sortable: true, 
            right: true,
            render: (p) => {
              const code = (p?.currency ? String(p.currency).toUpperCase() : "ARS")
              const number = new Intl.NumberFormat("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(parseFloat(p.amount || 0) || 0)
              return `$ ${number} ${code}`
            }
          },
          { 
            key: 'method', 
            header: 'Método', 
            sortable: true,
            render: (p) => getMethodBadge(p.method)
          },
          { 
            key: 'status', 
            header: 'Estado', 
            sortable: true,
            render: (p) => getStatusBadge(p.status)
          },
          { 
            key: 'date', 
            header: 'Fecha', 
            sortable: true,
            render: (p) => p.date ? format(parseISO(p.date), 'dd/MM/yyyy') : '-'
          },
          { 
            key: 'is_deposit', 
            header: 'Tipo', 
            sortable: true,
            render: (p) => {
              const isDeposit = p.is_deposit === true
              
              return (
                <Badge variant={isDeposit ? 'payment-deposit' : 'info'} size="sm">
                  {isDeposit ? 'Seña' : 'Pago'}
                </Badge>
              )
            }
          },
          {
            key: 'actions', 
            header: 'Acciones', 
            sortable: false, 
            right: true,
            render: (p) => (
              <div className="flex justify-end items-center gap-2">
                <button
                  onClick={() => onViewReceipt(p)}
                  className="p-2 rounded text-gray-600 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                  title="Ver comprobante"
                >
                  <EyeIcon size="18" />
                </button>
                <button
                  onClick={() => onDownloadReceipt(p)}
                  className="p-2 rounded text-gray-600 hover:text-green-600 hover:bg-green-50 transition-colors"
                  title="Descargar comprobante"
                >
                  <DocumentArrowDown size="18" />
                </button>
              </div>
            )
          }
        ]}
      />

      {hasNextPage && (displayResults?.length >= 50) && (
        <div>
          <button className="px-3 py-2 rounded-md border" onClick={() => fetchNextPage()}>
            Cargar más
          </button>
        </div>
      )}
    </div>
  )
}
