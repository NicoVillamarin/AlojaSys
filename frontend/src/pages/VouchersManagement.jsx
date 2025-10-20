import { useMemo, useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import { useDispatchAction } from 'src/hooks/useDispatchAction'
import Button from 'src/components/Button'
import { format, parseISO } from 'date-fns'
import { useUserHotels } from 'src/hooks/useUserHotels'
import Badge from 'src/components/Badge'
import VouchersManagementModal from 'src/components/modals/VouchersManagementModal'
import EditIcon from 'src/assets/icons/EditIcon'
import DeleteButton from 'src/components/DeleteButton'
import CancelIcon from 'src/assets/icons/CancelIcon'

export default function VouchersManagement() {
  const { t } = useTranslation()
  const [showModal, setShowModal] = useState(false)
  const [editVoucher, setEditVoucher] = useState(null)
  const [filters, setFilters] = useState({ search: '' })
  const didMountRef = useRef(false)
  const { hotelIdsString, isSuperuser, hotelIds, hasSingleHotel, singleHotelId } = useUserHotels()
  
  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'payments/refund-vouchers',
    params: { search: filters.search },
  })

  const { mutate: doAction, isPending: acting } = useDispatchAction({ 
    resource: 'payments/refund-vouchers', 
    onSuccess: () => {
      refetch()
    } 
  })

  const displayResults = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase()
    if (!q) return results
    return (results || []).filter((v) => {
      const code = String(v.code ?? '').toLowerCase()
      const hotel = String(v.hotel_name ?? '').toLowerCase()
      const status = String(v.status ?? '').toLowerCase()
      const notes = String(v.notes ?? '').toLowerCase()
      return code.includes(q) || hotel.includes(q) || status.includes(q) || notes.includes(q)
    })
  }, [results, filters.search])

  useEffect(() => {
    if (!didMountRef.current) { didMountRef.current = true; return }
    const id = setTimeout(() => refetch(), 400)
    return () => clearTimeout(id)
  }, [filters.search, refetch])

  const getStatusBadgeVariant = (status) => {
    const variants = {
      'active': 'success',
      'used': 'neutral',
      'expired': 'error',
      'cancelled': 'error'
    }
    return variants[status] || 'neutral'
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS'
    }).format(amount)
  }

  const handleCancelVoucher = (voucherId) => {
    doAction({
      action: `${voucherId}/cancel_voucher`,
      body: { reason: 'Cancelado por administrador' },
      method: 'POST'
    })
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.configuration')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('sidebar.vouchers')}</h1>
        </div>
        <Button variant="primary" size="md" onClick={() => setShowModal(true)}>
          {t('common.create')} {t('sidebar.vouchers')}
        </Button>
      </div>

      <VouchersManagementModal isOpen={showModal} onClose={() => setShowModal(false)} isEdit={false} onSuccess={refetch} />
      <VouchersManagementModal isOpen={!!editVoucher} onClose={() => setEditVoucher(null)} isEdit={true} voucher={editVoucher} onSuccess={refetch} />

      <div className="bg-white rounded-xl shadow p-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <span className="pointer-events-none absolute inset-y-0 left-2 flex items-center text-aloja-gray-800/60">
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M12.9 14.32a8 8 0 111.414-1.414l3.387 3.387a1 1 0 01-1.414 1.414l-3.387-3.387zM14 8a6 6 0 11-12 0 6 6 0 0112 0z" clipRule="evenodd" />
              </svg>
            </span>
            <input
              className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg pl-8 pr-8 py-2 text-sm w-64 transition-all"
              placeholder={t('vouchers.search_placeholder')}
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
      </div>

      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(v) => v.id}
        columns={[
          { 
            key: 'code', 
            header: t('vouchers.code'), 
            sortable: true,
            render: (v) => (
              <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                {v.code}
              </span>
            )
          },
          { 
            key: 'hotel_name', 
            header: t('common.hotel'), 
            sortable: true 
          },
          { 
            key: 'amount', 
            header: t('vouchers.amount'), 
            sortable: true, 
            right: true, 
            render: (v) => formatCurrency(v.amount)
          },
          { 
            key: 'remaining_amount', 
            header: t('vouchers.remaining_amount'), 
            sortable: true, 
            right: true, 
            render: (v) => v.remaining_amount ? formatCurrency(v.remaining_amount) : '—'
          },
          {
            key: 'status',
            header: t('vouchers.status'),
            sortable: true,
            render: (v) => (
              <Badge variant={getStatusBadgeVariant(v.status)} size="sm">
                {v.status_display}
              </Badge>
            )
          },
          {
            key: 'expiry_date',
            header: t('vouchers.expiry_date'),
            sortable: true,
            render: (v) => v.expiry_date ? format(parseISO(v.expiry_date), 'dd/MM/yyyy') : '—'
          },
          {
            key: 'created_at',
            header: t('vouchers.created_at'),
            sortable: true,
            render: (v) => v.created_at ? format(parseISO(v.created_at), 'dd/MM/yyyy HH:mm') : '—'
          },
          {
            key: 'actions',
            header: t('dashboard.reservations_management.table_headers.actions'),
            sortable: false,
            right: true,
            render: (v) => (
              <div className="flex justify-end items-center gap-x-2">
                <EditIcon size="18" onClick={() => setEditVoucher(v)} className="cursor-pointer" />
                {v.status === 'active' && (
                    <CancelIcon size="20" onClick={() => handleCancelVoucher(v.id)} className="cursor-pointer text-red-500" />
                )}
                <DeleteButton resource="payments/refund-vouchers" id={v.id} onDeleted={refetch} className="cursor-pointer" />
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
