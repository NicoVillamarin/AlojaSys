import { useMemo, useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useQueryClient } from '@tanstack/react-query'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import RefundDetailsModal from 'src/components/modals/RefundDetailsModal'
import Button from 'src/components/Button'
import CheckIcon from 'src/assets/icons/CheckIcon'
import XIcon from 'src/assets/icons/Xicon'
import EyeIcon from 'src/assets/icons/EyeIcon'
import Filter from 'src/components/Filter'
import Select from 'react-select'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

export default function RefundsManagement() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [selectedRefund, setSelectedRefund] = useState(null)
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    method: ''
  })
  const didMountRef = useRef(false)

  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'payments/refunds',
    params: { 
      search: filters.search,
      status: filters.status,
      refund_method: filters.method
    },
  })

  const displayResults = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase()
    if (!q) return results
    return (results || []).filter((r) => {
      const reservationStr = String(r.reservation_id ?? '')
      const amountStr = String(r.amount ?? '')
      const reasonStr = String(r.reason ?? '')
      return reservationStr.includes(q) || amountStr.includes(q) || reasonStr.toLowerCase().includes(q)
    })
  }, [results, filters.search])

  useEffect(() => {
    if (!didMountRef.current) { didMountRef.current = true; return }
    const id = setTimeout(() => refetch(), 400)
    return () => clearTimeout(id)
  }, [filters.search, refetch])

  const getStatusIcon = (status) => {
    const statusConfig = {
      'pending': { icon: <XIcon color="orange" />, label: t('payments.refunds.status.pending') },
      'processing': { icon: <XIcon color="blue" />, label: t('payments.refunds.status.processing') },
      'completed': { icon: <CheckIcon color="green" />, label: t('payments.refunds.status.completed') },
      'failed': { icon: <XIcon color="red" />, label: t('payments.refunds.status.failed') },
      'cancelled': { icon: <XIcon color="gray" />, label: t('payments.refunds.status.cancelled') }
    }
    return statusConfig[status] || { icon: <XIcon color="gray" />, label: status }
  }

  const getMethodLabel = (method) => {
    const methods = {
      'cash': t('payments.refunds.methods.cash'),
      'bank_transfer': t('payments.refunds.methods.bank_transfer'),
      'credit_card': t('payments.refunds.methods.credit_card'),
      'voucher': t('payments.refunds.methods.voucher'),
      'original_payment': t('payments.refunds.methods.original_payment')
    }
    return methods[method] || method
  }

  const getReasonLabel = (reason) => {
    const reasons = {
      'cancellation': t('payments.refunds.reasons.cancellation'),
      'partial_cancellation': t('payments.refunds.reasons.partial_cancellation'),
      'overpayment': t('payments.refunds.reasons.overpayment'),
      'discount_applied': t('payments.refunds.reasons.discount_applied'),
      'admin_adjustment': t('payments.refunds.reasons.admin_adjustment'),
      'customer_request': t('payments.refunds.reasons.customer_request'),
      'system_error': t('payments.refunds.reasons.system_error')
    }
    return reasons[reason] || reason
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    try {
      return format(new Date(dateString), 'dd/MM/yyyy HH:mm', { locale: es })
    } catch {
      return dateString
    }
  }

  const formatAmount = (amount) => {
    if (!amount) return '$0.00'
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 2
    }).format(amount)
  }

  const handleViewDetails = (refund) => {
    setSelectedRefund(refund)
    setShowModal(true)
  }

  const statusOptions = [
    { value: '', label: t('common.all_status') },
    { value: 'pending', label: t('payments.refunds.status.pending') },
    { value: 'processing', label: t('payments.refunds.status.processing') },
    { value: 'completed', label: t('payments.refunds.status.completed') },
    { value: 'failed', label: t('payments.refunds.status.failed') },
    { value: 'cancelled', label: t('payments.refunds.status.cancelled') }
  ]

  const methodOptions = [
    { value: '', label: t('common.all_methods') },
    { value: 'cash', label: t('payments.refunds.methods.cash') },
    { value: 'bank_transfer', label: t('payments.refunds.methods.bank_transfer') },
    { value: 'credit_card', label: t('payments.refunds.methods.credit_card') },
    { value: 'voucher', label: t('payments.refunds.methods.voucher') },
    { value: 'original_payment', label: t('payments.refunds.methods.original_payment') }
  ]

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.financial')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('payments.refunds.title')}</h1>
          <p className="text-sm text-gray-600 mt-1">{t('payments.refunds.subtitle')}</p>
        </div>
        <div className="flex items-center gap-3">
          <Button 
            variant="secondary" 
            size="md" 
            onClick={() => refetch()}
            disabled={isPending}
          >
            {t('common.refresh')}
          </Button>
        </div>
      </div>

      <RefundDetailsModal 
        isOpen={showModal} 
        onClose={() => setShowModal(false)} 
        refund={selectedRefund}
        onSuccess={(data) => {
          console.log('RefundDetailsModal onSuccess called:', data)
          // Invalidar el cache de reembolsos para forzar la actualización
          queryClient.invalidateQueries({ queryKey: ['payments/refunds'] })
          refetch()
        }}
      />

      {/* Filtros */}
      <Filter>
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
          <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3">
            <div className="relative w-full lg:w-80">
              <span className="pointer-events-none absolute inset-y-0 left-2 flex items-center text-aloja-gray-800/60">
                <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M12.9 14.32a8 8 0 111.414-1.414l3.387 3.387a1 1 0 01-1.414 1.414l-3.387-3.387zM14 8a6 6 0 11-12 0 6 6 0 0112 0z" clipRule="evenodd" />
                </svg>
              </span>
              <input
                className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg pl-8 pr-8 py-2 text-sm w-full transition-all"
                placeholder={t('payments.refunds.search_placeholder')}
                value={filters.search}
                onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
                onKeyDown={(e) => e.key === 'Enter' && refetch()}
              />
              {filters.search && (
                <button
                  className="absolute inset-y-0 right-1 my-1 px-2 rounded-md text-xs text-aloja-gray-800/70 hover:bg-gray-100"
                  onClick={() => { setFilters((f) => ({ ...f, search: '' })); setTimeout(() => refetch(), 0) }}
                  aria-label={t('common.clear_search')}
                >
                  ✕
                </button>
              )}
            </div>
          </div>
          <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3">
            <div className="w-full lg:w-48">
              <label className="block text-xs font-medium text-aloja-gray-800/70 mb-1">{t('payments.refunds.status_label')}</label>
              <Select
                value={statusOptions.find(s => String(s.value) === String(filters.status)) || null}
                onChange={(option) => setFilters((f) => ({ ...f, status: option ? String(option.value) : '' }))}
                options={statusOptions}
                placeholder={t('common.all_status')}
                isClearable
                isSearchable
                classNamePrefix="rs"
                styles={{
                  control: (base) => ({
                    ...base,
                    minHeight: 36,
                    borderRadius: 6,
                    borderColor: '#e5e7eb',
                    fontSize: 14,
                  }),
                  valueContainer: (base) => ({ ...base, padding: '2px 8px' }),
                  indicatorsContainer: (base) => ({ ...base, paddingRight: 6 }),
                  dropdownIndicator: (base) => ({ ...base, padding: 6 }),
                  clearIndicator: (base) => ({ ...base, padding: 6 }),
                  menu: (base) => ({ ...base, borderRadius: 8, overflow: 'hidden', zIndex: 9999 }),
                }}
              />
            </div>
            <div className="w-full lg:w-48">
              <label className="block text-xs font-medium text-aloja-gray-800/70 mb-1">{t('payments.refunds.method')}</label>
              <Select
                value={methodOptions.find(m => String(m.value) === String(filters.method)) || null}
                onChange={(option) => setFilters((f) => ({ ...f, method: option ? String(option.value) : '' }))}
                options={methodOptions}
                placeholder={t('common.all_methods')}
                isClearable
                isSearchable
                classNamePrefix="rs"
                styles={{
                  control: (base) => ({
                    ...base,
                    minHeight: 36,
                    borderRadius: 6,
                    borderColor: '#e5e7eb',
                    fontSize: 14,
                  }),
                  valueContainer: (base) => ({ ...base, padding: '2px 8px' }),
                  indicatorsContainer: (base) => ({ ...base, paddingRight: 6 }),
                  dropdownIndicator: (base) => ({ ...base, padding: 6 }),
                  clearIndicator: (base) => ({ ...base, padding: 6 }),
                  menu: (base) => ({ ...base, borderRadius: 8, overflow: 'hidden', zIndex: 9999 }),
                }}
              />
            </div>
          </div>
        </div>
      </Filter>

      {/* Tabla de reembolsos */}
      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          { 
            key: 'id', 
            header: t('payments.refunds.refund_id'), 
            sortable: true,
            render: (r) => `N° ${r.id}`
          },
          { 
            key: 'reservation_id', 
            header: t('payments.refunds.reservation_id'), 
            sortable: true,
            render: (r) => `N° ${r.reservation_id}`
          },
          { 
            key: 'amount', 
            header: t('payments.refunds.amount'), 
            sortable: true,
            render: (r) => formatAmount(r.amount)
          },
          { 
            key: 'status', 
            header: t('payments.refunds.status_label'), 
            sortable: true,
            render: (r) => {
              const statusInfo = getStatusIcon(r.status)
              return (
                <div className="flex items-center gap-2">
                  {statusInfo.icon}
                  <span className="text-sm">{statusInfo.label}</span>
                </div>
              )
            }
          },
          { 
            key: 'refund_method', 
            header: t('payments.refunds.method'), 
            sortable: true,
            render: (r) => getMethodLabel(r.refund_method)
          },
          { 
            key: 'reason', 
            header: t('payments.refunds.reason'), 
            sortable: true,
            render: (r) => getReasonLabel(r.reason)
          },
          { 
            key: 'created_at', 
            header: t('payments.refunds.created_at'), 
            sortable: true,
            render: (r) => formatDate(r.created_at)
          },
          {
            key: 'actions',
            header: t('common.actions'),
            sortable: false,
            right: true,
            render: (r) => (
              <div className="flex justify-end items-center gap-x-2">
                <button
                  onClick={() => handleViewDetails(r)}
                  className="p-1 text-aloja-navy hover:text-aloja-navy/70 transition-colors"
                  title={t('common.view_details')}
                >
                  <EyeIcon size="18" />
                </button>
              </div>
            ),
          },
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
