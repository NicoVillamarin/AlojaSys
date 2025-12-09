import { useMemo, useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import PaymentDetailModal from 'src/components/modals/PaymentDetailModal'
import { useList } from 'src/hooks/useList'
import { useUserHotels } from 'src/hooks/useUserHotels'
import SelectAsync from 'src/components/selects/SelectAsync'
import { Formik } from 'formik'
import { format, parseISO } from 'date-fns'
import { convertToDecimal, getStatusLabel } from './utils'
import Filter from 'src/components/Filter'
import Badge from 'src/components/Badge'
import { useGet } from 'src/hooks/useGet'
import Tabs from 'src/components/Tabs'
import Button from 'src/components/Button'
import { usePermissions } from 'src/hooks/usePermissions'

export default function Payments() {
  const { t } = useTranslation()

  // Permisos de pagos (solo lectura de cobros)
  const canViewPayments = usePermissions('payments.view_payment')
  const [paymentDetailOpen, setPaymentDetailOpen] = useState(false)
  const [selectedPayment, setSelectedPayment] = useState(null)
  const [stats, setStats] = useState(null)
  const [activeTab, setActiveTab] = useState('all')
  const [filters, setFilters] = useState({ 
    search: '', 
    hotel: '', 
    type: '', 
    method: '', 
    status: '', 
    dateFrom: '', 
    dateTo: '',
    minAmount: '',
    maxAmount: ''
  })
  const didMountRef = useRef(false)
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()
  
  // Función para confirmar pago POSTNET
  const handleSettlePayment = async (paymentId, action) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/payments/settle-postnet/${paymentId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ action, notes: '' })
      })
      
      if (response.ok) {
        refetch() // Recargar la lista
      } else {
        console.error('Error settling payment')
      }
    } catch (error) {
      console.error('Error settling payment:', error)
    }
  }

  // Generar columnas dinámicamente según la pestaña activa
  const getColumns = () => {
    if (activeTab === 'postnet') {
      return [
        { 
          key: 'reservation_id', 
          header: 'Reserva', 
          sortable: true, 
          render: (r) => (
            <button
              className="link text-blue-600 hover:text-blue-800"
              onClick={() => {
                setSelectedPayment(r)
                setPaymentDetailOpen(true)
              }}
            >
              #{r.reservation_id}
            </button>
          )
        },
        { key: 'guest_name', header: 'Huésped', sortable: true },
        { key: 'hotel_name', header: 'Hotel', sortable: true },
        { 
          key: 'amount', 
          header: 'Monto', 
          sortable: true, 
          right: true, 
          render: (r) => (
            <span className="font-semibold text-green-600">
              ${r.amount?.toLocaleString() || '0'}
            </span>
          ) 
        },
        { 
          key: 'terminal_id', 
          header: 'Terminal ID', 
          sortable: true,
          render: (r) => r.terminal_id || '-'
        },
        { 
          key: 'batch_number', 
          header: 'Batch', 
          sortable: true,
          render: (r) => r.batch_number || '-'
        },
        { 
          key: 'status', 
          header: 'Estado', 
          sortable: true, 
          render: (r) => {
            const statusVariant = r.status === 'approved' ? 'payment-paid' : 
                                r.status === 'pending_settlement' ? 'payment-pending' :
                                r.status === 'failed' ? 'payment-rejected' : 'payment-default'
            
            return (
              <Badge variant={statusVariant} size="sm">
                {r.status === 'pending_settlement' ? 'Pendiente Liquidación' : 
                 r.status === 'approved' ? 'Aprobado' :
                 r.status === 'failed' ? 'Fallido' : r.status}
              </Badge>
            )
          }
        },
        {
          key: 'date',
          header: 'Fecha Pago',
          sortable: true,
          render: (e) => e.date ? format(parseISO(e.date), 'dd/MM/yyyy') : '',
        },
        {
          key: 'actions',
          header: 'Acciones',
          sortable: false,
          render: (r) => {
            if (r.status === 'pending_settlement') {
              return (
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="success"
                    onClick={() => handleSettlePayment(r.id, 'approve')}
                  >
                    Aprobar
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleSettlePayment(r.id, 'reject')}
                  >
                    Rechazar
                  </Button>
                </div>
              )
            }
            return '-'
          }
        },
      ]
    }

    // Columnas por defecto para todos los pagos
    return [
      { 
        key: 'reservation_id', 
        header: 'Reserva', 
        sortable: true, 
        render: (r) => (
          <div className="flex items-center gap-2">
            <button
              className="link text-blue-600 hover:text-blue-800"
              onClick={() => {
                setSelectedPayment(r)
                setPaymentDetailOpen(true)
              }}
            >
              #{r.reservation_id}
            </button>
          </div>
        ) 
      },
      { key: 'guest_name', header: 'Huésped', sortable: true },
      { key: 'hotel_name', header: 'Hotel', sortable: true },
      { key: 'room_name', header: 'Habitación', sortable: true },
      {
        key: 'check_in',
        header: 'Check-in',
        sortable: true,
        render: (e) => e.check_in ? format(parseISO(e.check_in), 'dd/MM/yyyy') : '',
      },
      {
        key: 'check_out',
        header: 'Check-out',
        sortable: true,
        render: (e) => e.check_out ? format(parseISO(e.check_out), 'dd/MM/yyyy') : '',
      },
      { 
        key: 'amount', 
        header: 'Monto', 
        sortable: true, 
        right: true, 
        render: (r) => (
          <span className="font-semibold text-green-600">
            ${r.amount?.toLocaleString() || '0'}
          </span>
        ) 
      },
      { 
        key: 'method', 
        header: 'Método', 
        sortable: true, 
        render: (r) => {
          const methodVariant = r.method === 'cash' ? 'payment-cash' : 
                              r.method === 'card' ? 'payment-card' :
                              r.method === 'bank_transfer' ? 'payment-transfer' :
                              r.method === 'mercado_pago' ? 'payment-online' :
                              r.method === 'pos' ? 'payment-pos' :
                              r.method === 'pending' ? 'payment-pending' : 'payment-default'
          
          return (
            <Badge variant={methodVariant} size="sm">
              {getMethodLabel(r.method)}
            </Badge>
          )
        }
      },
      { 
        key: 'type', 
        header: 'Tipo', 
        sortable: true, 
        render: (r) => {
          const typeVariant = r.type === 'manual' ? 'type-manual' : 
                            r.type === 'online' ? 'type-online' :
                            r.type === 'bank_transfer' ? 'type-transfer' :
                            r.type === 'pending' ? 'type-pending' : 'type-default'
          
          return (
            <Badge variant={typeVariant} size="sm">
              {getTypeLabel(r.type)}
            </Badge>
          )
        }
      },
      { 
        key: 'status', 
        header: 'Estado', 
        sortable: true, 
        render: (r) => {
          const statusVariant = r.status === 'approved' ? 'payment-paid' : 
                              r.status === 'pending' ? 'payment-pending' :
                              r.status === 'rejected' ? 'payment-rejected' :
                              r.status === 'cancelled' ? 'payment-cancelled' : 'payment-default'
          
          return (
            <Badge variant={statusVariant} size="sm">
              {getStatusLabel(r.status)}
            </Badge>
          )
        }
      },
      {
        key: 'date',
        header: 'Fecha Pago',
        sortable: true,
        render: (e) => e.date ? format(parseISO(e.date), 'dd/MM/yyyy') : '',
      },
      {
        key: 'created_at',
        header: 'Creado',
        sortable: true,
        render: (e) => e.created_at ? format(parseISO(e.created_at), 'dd/MM/yyyy HH:mm') : '',
      },
      { 
        key: 'description', 
        header: 'Descripción', 
        sortable: true, 
        render: (r) => (
          <span className="text-sm text-gray-600 truncate max-w-32" title={r.description}>
            {r.description}
          </span>
        )
      },
    ]
  }
  
  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'payments/collections',
    params: { 
      search: filters.search, 
      hotel_id: filters.hotel || undefined, 
      type: filters.type || undefined,
      method: activeTab === 'postnet' ? 'pos' : (filters.method || undefined),
      status: filters.status || undefined,
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
      min_amount: filters.minAmount || undefined,
      max_amount: filters.maxAmount || undefined,
    },
    enabled: canViewPayments,
  })

  // Cargar estadísticas usando useGet
  const { data: statsData, isLoading: statsLoading } = useGet({
    resource: 'payments/collections/stats',
    enabled: canViewPayments
  })

  useEffect(() => {
    if (statsData) {
      setStats(statsData)
    }
  }, [statsData])

  const displayResults = useMemo(() => {
    return results || []
  }, [results])

  // Funciones de traducción para badges
  const getTypeLabel = (type) => {
    const typeMap = {
      'manual': t('payments.type.manual'),
      'online': t('payments.type.online'),
      'bank_transfer': t('payments.type.bank_transfer'),
      'pending': t('payments.type.pending'),
    }
    return typeMap[type] || type
  }

  const getMethodLabel = (method) => {
    const methodMap = {
      'cash': t('payments.method.cash'),
      'card': t('payments.method.card'),
      'bank_transfer': t('payments.method.bank_transfer'),
      'mercado_pago': t('payments.method.mercado_pago'),
      'pending': t('payments.method.pending'),
    }
    return methodMap[method] || method
  }

  const getStatusLabel = (status) => {
    const statusMap = {
      'approved': t('payments.status.approved'),
      'pending': t('payments.status.pending'),
      'rejected': t('payments.status.rejected'),
      'cancelled': t('payments.status.cancelled'),
    }
    return statusMap[status] || status
  }

  useEffect(() => {
    if (!didMountRef.current) { didMountRef.current = true; return }
    const id = setTimeout(() => refetch(), 400)
    return () => clearTimeout(id)
  }, [filters.search, filters.hotel, filters.type, filters.method, filters.status, filters.dateFrom, filters.dateTo, filters.minAmount, filters.maxAmount, refetch])

  const handleExport = async () => {
    try {
      const params = new URLSearchParams()
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          const paramKey = key === 'dateFrom' ? 'date_from' : 
                          key === 'dateTo' ? 'date_to' :
                          key === 'minAmount' ? 'min_amount' :
                          key === 'maxAmount' ? 'max_amount' : key
          params.append(paramKey, value)
        }
      })
      
      // Usar fetch directamente para la descarga
      const response = await fetch(`/api/payments/collections/export/?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        }
      })
      
      if (response.ok) {
        const blob = await response.blob()
        const downloadUrl = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = `cobros_${new Date().toISOString().split('T')[0]}.csv`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(downloadUrl)
      }
    } catch (error) {
      console.error('Error exportando cobros:', error)
    }
  }

  if (!canViewPayments) {
    return (
      <div className="p-6 text-center text-gray-600">
        {t('payments.no_permission', 'No tenés permiso para ver los cobros.')}
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.history')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">Cobros</h1>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            Exportar CSV
          </button>
        </div>
      </div>

      {/* Pestañas */}
      <Tabs 
        tabs={[
          { id: 'all', label: 'Todos los Pagos' },
          { id: 'postnet', label: 'POS / POSTNET' }
        ]} 
        activeTab={activeTab} 
        onTabChange={setActiveTab} 
      />

      {/* Estadísticas */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
          <div className="text-center">
            <div className="text-2xl font-bold text-aloja-navy">{stats.summary?.total_payments || 0}</div>
            <div className="text-sm text-gray-600">Total Cobros</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">${stats.summary?.total_amount?.toLocaleString() || 0}</div>
            <div className="text-sm text-gray-600">Monto Total</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">${stats.summary?.average_amount?.toLocaleString() || 0}</div>
            <div className="text-sm text-gray-600">Promedio</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {Object.keys(stats.by_method || {}).length}
            </div>
            <div className="text-sm text-gray-600">Métodos</div>
          </div>
        </div>
      )}

      <PaymentDetailModal
        isOpen={paymentDetailOpen}
        onClose={() => { setPaymentDetailOpen(false); setSelectedPayment(null) }}
        reservationId={selectedPayment?.reservation_id}
        reservationData={selectedPayment}
      />

      <Filter>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">Búsqueda</label>
            <input
              className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-64 transition-all"
              placeholder="Buscar por reserva, huésped, habitación..."
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
              <option value="manual">{t('payments.type.manual')}</option>
              <option value="online">{t('payments.type.online')}</option>
              <option value="bank_transfer">{t('payments.type.bank_transfer')}</option>
              <option value="pending">{t('payments.type.pending')}</option>
            </select>
          </div>

          <div className="w-40">
            <label className="text-xs text-aloja-gray-800/60">Método</label>
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full"
              value={filters.method}
              onChange={(e) => setFilters((f) => ({ ...f, method: e.target.value }))}
            >
              <option value="">Todos</option>
              <option value="cash">{t('payments.method.cash')}</option>
              <option value="card">{t('payments.method.card')}</option>
              <option value="bank_transfer">{t('payments.method.bank_transfer')}</option>
              <option value="mercado_pago">{t('payments.method.mercado_pago')}</option>
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
              <option value="approved">{t('payments.status.approved')}</option>
              <option value="pending">{t('payments.status.pending')}</option>
              <option value="rejected">{t('payments.status.rejected')}</option>
              <option value="cancelled">{t('payments.status.cancelled')}</option>
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
            <label className="text-xs text-aloja-gray-800/60">Monto Mín.</label>
            <input 
              type="number" 
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-24"
              placeholder="0"
              value={filters.minAmount}
              onChange={(e) => setFilters((f) => ({ ...f, minAmount: e.target.value }))}
            />
          </div>
          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">Monto Máx.</label>
            <input 
              type="number" 
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-24"
              placeholder="999999"
              value={filters.maxAmount}
              onChange={(e) => setFilters((f) => ({ ...f, maxAmount: e.target.value }))}
            />
          </div>

          <div className="ml-auto">
            <button className="px-3 py-2 rounded-md border text-sm" onClick={() => setFilters({ 
              search: '', hotel: '', type: '', method: '', status: '', 
              dateFrom: '', dateTo: '', minAmount: '', maxAmount: '' 
            })}>
              Limpiar Filtros
            </button>
          </div>
        </div>
      </Filter>

      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={getColumns()}
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
