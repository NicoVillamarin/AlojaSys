import { useMemo, useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import CancellationPoliciesModal from 'src/components/modals/CancellationPoliciesModal'
import EditIcon from 'src/assets/icons/EditIcon'
import DeleteButton from 'src/components/DeleteButton'
import Button from 'src/components/Button'
import CheckIcon from 'src/assets/icons/CheckIcon'
import XIcon from 'src/assets/icons/Xicon'

export default function CancellationPolicies() {
  const { t } = useTranslation()
  const [showModal, setShowModal] = useState(false)
  const [editPolicy, setEditPolicy] = useState(null)
  const [filters, setFilters] = useState({ search: '' })
  const didMountRef = useRef(false)

  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'payments/cancellation-policies',
    params: { 
      search: filters.search
    },
  })

  const displayResults = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase()
    if (!q) return results
    return (results || []).filter((p) => {
      const nameStr = String(p.name ?? '')
      const hotelStr = String(p.hotel_name ?? '')
      return nameStr.toLowerCase().includes(q) || hotelStr.toLowerCase().includes(q)
    })
  }, [results, filters.search])

  useEffect(() => {
    if (!didMountRef.current) { didMountRef.current = true; return }
    const id = setTimeout(() => refetch(), 400)
    return () => clearTimeout(id)
  }, [filters.search, refetch])

  const getFeeTypeLabel = (type) => {
    const types = {
      'none': t('payments.cancellation.policies.fee_types.none'),
      'percentage': t('payments.cancellation.policies.fee_types.percentage'),
      'fixed': t('payments.cancellation.policies.fee_types.fixed'),
      'first_night': t('payments.cancellation.policies.fee_types.first_night'),
      'nights_percentage': t('payments.cancellation.policies.fee_types.nights_percentage')
    }
    return types[type] || type
  }


  const getTimeUnitLabel = (unit) => {
    const units = {
      'hours': t('payments.cancellation.policies.time_units.hours'),
      'days': t('payments.cancellation.policies.time_units.days'),
      'weeks': t('payments.cancellation.policies.time_units.weeks')
    }
    return units[unit] || unit
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.configuration')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('payments.cancellation.policies.title')}</h1>
          <p className="text-sm text-gray-600 mt-1">{t('payments.cancellation.policies.subtitle')}</p>
        </div>
        <Button variant="primary" size="md" onClick={() => setShowModal(true)}>
          {t('payments.cancellation.policies.add_policy_cancellation')}
        </Button>
      </div>

      <CancellationPoliciesModal 
        isOpen={showModal} 
        onClose={() => setShowModal(false)} 
        isEdit={false} 
        onSuccess={refetch} 
      />
      <CancellationPoliciesModal 
        isOpen={!!editPolicy} 
        onClose={() => setEditPolicy(null)} 
        isEdit={true} 
        policy={editPolicy} 
        onSuccess={refetch} 
      />

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
              placeholder={t('payments.cancellation.policies.search_placeholder')}
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
        getRowId={(p) => p.id}
        columns={[
          { key: 'name', header: t('payments.cancellation.policies.policy_name'), sortable: true },
          { key: 'hotel_name', header: t('sidebar.hotels'), sortable: true },
          { 
            key: 'free_cancellation_time', 
            header: t('payments.cancellation.policies.free_cancellation'), 
            render: (p) => `${p.free_cancellation_time} ${getTimeUnitLabel(p.free_cancellation_unit)}`,
            sortable: true 
          },
          { 
            key: 'partial_refund_time', 
            header: t('payments.cancellation.policies.partial_refund'), 
            render: (p) => `${p.partial_refund_time} ${getTimeUnitLabel(p.partial_refund_unit)} (${p.partial_refund_percentage}%)`,
            sortable: true 
          },
          { 
            key: 'cancellation_fee_type', 
            header: t('payments.cancellation.policies.fee_type'), 
            render: (p) => getFeeTypeLabel(p.cancellation_fee_type),
            sortable: true 
          },
          { 
            key: 'is_default', 
            header: t('payments.cancellation.policies.is_default'), 
            render: (p) => p.is_default ? <CheckIcon color="green" /> : <XIcon color="red" />, 
            sortable: true 
          },
          { 
            key: 'is_active', 
            header: t('payments.cancellation.policies.is_active'), 
            render: (p) => p.is_active ? <CheckIcon color="green" /> : <XIcon color="red" />, 
            sortable: true 
          },
          {
            key: 'actions',
            header: t('common.actions'),
            sortable: false,
            right: true,
            render: (p) => (
              <div className="flex justify-end items-center gap-x-2">
                <EditIcon size="18" onClick={() => setEditPolicy(p)} />
                <DeleteButton resource="payments/cancellation-policies" id={p.id} onDeleted={refetch} />
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