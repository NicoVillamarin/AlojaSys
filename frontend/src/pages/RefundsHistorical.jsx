import { useMemo, useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import RefundHistoricalModal from 'src/components/modals/RefundHistoricalModal'
import { useList } from 'src/hooks/useList'
import { useDispatchAction } from 'src/hooks/useDispatchAction'
import Button from 'src/components/Button'
import SelectAsync from 'src/components/selects/SelectAsync'
import { Formik } from 'formik'
import { format, parseISO } from 'date-fns'
import { convertToDecimal } from './utils'
import Filter from 'src/components/Filter'
import { useUserHotels } from 'src/hooks/useUserHotels'
import Badge from 'src/components/Badge'

export default function RefundsHistorical() {
  const { t } = useTranslation()
  const [historyRefundId, setHistoryRefundId] = useState(null)
  const [historyRefund, setHistoryRefund] = useState(null)
  const [filters, setFilters] = useState({ 
    search: '', 
    hotel: '', 
    status: '', 
    reason: '',
    dateFrom: '', 
    dateTo: '' 
  })
  const didMountRef = useRef(false)
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()
  
  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'payments/refunds',
    params: { 
      search: filters.search, 
      hotel: filters.hotel || undefined, 
      status: filters.status || undefined,
      reason: filters.reason || undefined
    },
  })

  const { mutate: doAction, isPending: acting } = useDispatchAction({ 
    resource: 'payments/refunds', 
    onSuccess: () => refetch() 
  })

  const displayResults = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase()
    const from = filters.dateFrom ? new Date(filters.dateFrom) : null
    const to = filters.dateTo ? new Date(filters.dateTo) : null
    let arr = results || []
    
    if (q) {
      arr = arr.filter((r) => {
        const reservation = String(r.reservation_display_name ?? '').toLowerCase()
        const hotel = String(r.hotel_name ?? '').toLowerCase()
        const status = String(r.status ?? '').toLowerCase()
        const reason = String(r.reason ?? '').toLowerCase()
        const externalRef = String(r.external_reference ?? '').toLowerCase()
        return reservation.includes(q) || hotel.includes(q) || status.includes(q) || 
               reason.includes(q) || externalRef.includes(q)
      })
    }
    
    if (from || to) {
      arr = arr.filter((r) => {
        const created = new Date(r.created_at)
        if (from && created < from) return false
        if (to && created > to) return false
        return true
      })
    }
    
    return arr
  }, [results, filters.search, filters.dateFrom, filters.dateTo])

  useEffect(() => {
    if (!didMountRef.current) { 
      didMountRef.current = true
      return 
    }
    const id = setTimeout(() => refetch(), 400)
    return () => clearTimeout(id)
  }, [filters.search, filters.hotel, filters.status, filters.reason, refetch])

  const getStatusBadgeVariant = (status) => {
    const variants = {
      'pending': 'warning',
      'processing': 'info',
      'completed': 'success',
      'failed': 'error',
      'cancelled': 'neutral'
    }
    return variants[status] || 'neutral'
  }

  const getReasonLabel = (reason) => {
    const reasons = {
      'cancellation': 'Cancelación',
      'partial_cancellation': 'Cancelación Parcial',
      'overpayment': 'Sobrepago',
      'discount_applied': 'Descuento Aplicado',
      'admin_adjustment': 'Ajuste Administrativo',
      'customer_request': 'Solicitud del Cliente',
      'system_error': 'Error del Sistema'
    }
    return reasons[reason] || reason
  }

  const getRefundMethodLabel = (method) => {
    const methods = {
      'cash': 'Efectivo',
      'bank_transfer': 'Transferencia Bancaria',
      'credit_card': 'Tarjeta de Crédito',
      'voucher': 'Voucher de Crédito',
      'original_payment': 'Método Original'
    }
    return methods[method] || method
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS'
    }).format(amount)
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.histories')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">Histórico de Reembolsos</h1>
        </div>
      </div>

      {!!historyRefundId && (
        <RefundHistoricalModal
          refundId={historyRefundId}
          displayName={historyRefund?.display_name}
          onClose={() => { 
            setHistoryRefundId(null)
            setHistoryRefund(null) 
          }}
        />
      )}

      <Filter>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">{t('common.search')}</label>
            <input
              className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-64 transition-all"
              placeholder="Reserva, hotel, estado, motivo..."
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
                  title={t('common.hotel')}
                  name='hotel'
                  resource='hotels'
                  placeholder={t('common.all')}
                  getOptionLabel={(h) => h?.name}
                  getOptionValue={(h) => h?.id}
                  extraParams={!isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {}}
                  onValueChange={(opt, val) => setFilters((f) => ({ ...f, hotel: String(val || '') }))}
                />
              </div>
            )}
          </Formik>

          <div className="w-48">
            <label className="text-xs text-aloja-gray-800/60">{t('common.status')}</label>
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full"
              value={filters.status}
              onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
            >
              <option value="">{t('common.all')}</option>
              <option value="pending">Pendiente</option>
              <option value="processing">Procesando</option>
              <option value="completed">Completado</option>
              <option value="failed">Fallido</option>
              <option value="cancelled">Cancelado</option>
            </select>
          </div>

          <div className="w-48">
            <label className="text-xs text-aloja-gray-800/60">Motivo</label>
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full"
              value={filters.reason}
              onChange={(e) => setFilters((f) => ({ ...f, reason: e.target.value }))}
            >
              <option value="">{t('common.all')}</option>
              <option value="cancellation">Cancelación</option>
              <option value="partial_cancellation">Cancelación Parcial</option>
              <option value="overpayment">Sobrepago</option>
              <option value="discount_applied">Descuento Aplicado</option>
              <option value="admin_adjustment">Ajuste Administrativo</option>
              <option value="customer_request">Solicitud del Cliente</option>
              <option value="system_error">Error del Sistema</option>
            </select>
          </div>

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
                status: '', 
                reason: '',
                dateFrom: '', 
                dateTo: '' 
              })}
            >
              {t('dashboard.reservations_management.clear_filters')}
            </button>
          </div>
        </div>
      </Filter>

      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          { 
            key: 'id', 
            header: 'ID', 
            sortable: true, 
            render: (r) => (
              <button
                className="link text-blue-600 hover:text-blue-800"
                onClick={() => { 
                  setHistoryRefund(r)
                  setHistoryRefundId(r.id) 
                }}
              >
                #{r.id}
              </button>
            )
          },
          { 
            key: 'reservation_display_name', 
            header: 'Reserva', 
            sortable: true,
            render: (r) => r.reservation_display_name || `Reserva #${r.reservation_id}`
          },
          { 
            key: 'hotel_name', 
            header: 'Hotel', 
            sortable: true 
          },
          { 
            key: 'amount', 
            header: 'Monto', 
            sortable: true, 
            right: true, 
            render: (r) => formatCurrency(r.amount)
          },
          { 
            key: 'reason', 
            header: 'Motivo', 
            sortable: true,
            render: (r) => getReasonLabel(r.reason)
          },
          { 
            key: 'refund_method', 
            header: 'Método', 
            sortable: true,
            render: (r) => getRefundMethodLabel(r.refund_method)
          },
          {
            key: 'status',
            header: 'Estado',
            sortable: true,
            render: (r) => (
              <Badge variant={getStatusBadgeVariant(r.status)} size="sm">
                {r.status}
              </Badge>
            )
          },
          {
            key: 'created_at',
            header: 'Creado',
            sortable: true,
            accessor: (e) => e.created_at ? format(parseISO(e.created_at), 'dd/MM/yyyy HH:mm') : '',
            render: (e) => e.created_at ? format(parseISO(e.created_at), 'dd/MM/yyyy HH:mm') : '',
          },
          {
            key: 'processed_at',
            header: 'Procesado',
            sortable: true,
            accessor: (e) => e.processed_at ? format(parseISO(e.processed_at), 'dd/MM/yyyy HH:mm') : '',
            render: (e) => e.processed_at ? format(parseISO(e.processed_at), 'dd/MM/yyyy HH:mm') : '',
          },
          { 
            key: 'external_reference', 
            header: 'Ref. Externa', 
            sortable: true,
            render: (r) => r.external_reference ? (
              <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                {r.external_reference}
              </span>
            ) : '—'
          },
          {
            key: 'generated_voucher',
            header: 'Voucher',
            sortable: false,
            render: (r) => r.generated_voucher ? (
              <div className="flex flex-col gap-0.5">
                <span className="font-mono text-xs bg-green-100 text-green-800 px-1.5 py-0.5 rounded text-center">
                  {r.generated_voucher.code}
                </span>
              </div>
            ) : '—'
          }
        ]}
      />

      {hasNextPage && (
        <div>
          <button className="px-3 py-2 rounded-md border" onClick={() => fetchNextPage()}>
            {t('common.load_more')}
          </button>
        </div>
      )}
    </div>
  )
}
