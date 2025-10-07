import { useMemo, useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import PromoRateModal from 'src/components/modals/PromoRateModal'
import EditIcon from 'src/assets/icons/EditIcon'
import DeleteButton from 'src/components/DeleteButton'
import Button from 'src/components/Button'

export default function Promos() {
  const { t } = useTranslation()
  const [showModal, setShowModal] = useState(false)
  const [editRow, setEditRow] = useState(null)
  const [filters, setFilters] = useState({ search: '' })
  const didMountRef = useRef(false)

  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'rates/promo-rules',
    params: {},
  })

  const displayResults = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase()
    if (!q) return results
    return (results || []).filter((r) => {
      const name = String(r?.name ?? '').toLowerCase()
      const code = String(r?.code ?? '').toLowerCase()
      return name.includes(q) || code.includes(q)
    })
  }, [results, filters.search])

  useEffect(() => {
    if (!didMountRef.current) { didMountRef.current = true; return }
    const id = setTimeout(() => refetch(), 400)
    return () => clearTimeout(id)
  }, [filters.search, refetch])

  const listDiscountTypes = [
    {
      label: t('promos.discount_percent'),
      value: 'percent',
    },
    {
      label: t('promos.discount_fixed'),
      value: 'fixed',
    },
  ]

  const DiscountType = ({ value }) => {
    const discountType = listDiscountTypes.find((t) => t.value === value)
    return discountType ? discountType.label : value
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.configuration')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('promos.title')}</h1>
        </div>
        <Button variant="primary" size="md" onClick={() => setShowModal(true)}>
          {t('promos.create_promo')}
        </Button>
      </div>

      <PromoRateModal 
        isOpen={showModal} 
        onClose={() => {
          setShowModal(false)
          setEditRow(null)
        }} 
        isEdit={false} 
        row={null}
        onSuccess={() => {
          refetch()
          setShowModal(false)
        }} 
      />
      <PromoRateModal 
        isOpen={!!editRow} 
        onClose={() => {
          setEditRow(null)
          setShowModal(false)
        }} 
        isEdit={true} 
        row={editRow} 
        onSuccess={() => {
          refetch()
          setEditRow(null)
        }} 
      />

      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          { key: 'hotel_name', header: t('promos.hotel')},
          { key: 'name', header: t('promos.name') },
          { key: 'code', header: t('promos.code') },
          { key: 'scope', header: t('promos.scope'), render: (r) => r.scope === 'per_reservation' ? t('promos.scope_per_reservation') : t('promos.scope_per_night') },
          { key: 'discount_type', header: t('promos.discount_type'), render: (r) => <DiscountType value={r.discount_type} /> },
          { key: 'discount_value', header: t('promos.value'), right: true },
          { key: 'combinable', header: t('promos.combinable'), render: (r)=> r.combinable ? t('promos.yes') : t('promos.no'), right: true },
          { key: 'is_active', header: t('promos.active'), render: (r)=> r.is_active ? t('promos.yes') : t('promos.no'), right: true },
          {
            key: 'actions',
            header: t('dashboard.reservations_management.table_headers.actions'),
            right: true,
            render: (r) => (
              <div className="flex justify-end items-center gap-x-2">
                <EditIcon size="18" onClick={() => setEditRow(r)} className="cursor-pointer" />
                <DeleteButton resource="rates/promo-rules" id={r.id} onDeleted={refetch} className="cursor-pointer" />
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