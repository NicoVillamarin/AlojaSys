import { useMemo, useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import TaxesRateModal from 'src/components/modals/TaxesRateModal'
import EditIcon from 'src/assets/icons/EditIcon'
import DeleteButton from 'src/components/DeleteButton'
import Button from 'src/components/Button'

export default function Taxes() {
  const { t } = useTranslation()
  const [showModal, setShowModal] = useState(false)
  const [editRow, setEditRow] = useState(null)
  const [filters, setFilters] = useState({ search: '' })
  const didMountRef = useRef(false)

  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'rates/tax-rules',
    params: {},
  })

  const displayResults = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase()
    if (!q) return results
    return (results || []).filter((r) => {
      const name = String(r?.name ?? '').toLowerCase()
      const channel = String(r?.channel ?? '').toLowerCase()
      return name.includes(q) || channel.includes(q)
    })
  }, [results, filters.search])

  useEffect(() => {
    if (!didMountRef.current) { didMountRef.current = true; return }
    const id = setTimeout(() => refetch(), 400)
    return () => clearTimeout(id)
  }, [filters.search, refetch])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.configuration')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('taxes.title')}</h1>
        </div>
        <Button variant="primary" size="md" onClick={() => setShowModal(true)}>
          {t('taxes.create_tax')}
        </Button>
      </div>

      <TaxesRateModal isOpen={showModal} onClose={() => setShowModal(false)} isEdit={false} onSuccess={refetch} />
      <TaxesRateModal isOpen={!!editRow} onClose={() => setEditRow(null)} isEdit={true} row={editRow} onSuccess={refetch} />

      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          { key: 'hotel_name', header: t('taxes.hotel')},
          { key: 'name', header: t('taxes.name') },
          { key: 'channel', header: t('taxes.channel') },
          { key: 'percent', header: t('taxes.percent'), right: true },
          { key: 'scope', header: t('taxes.scope'), render: (r) => {
            if (r.scope === 'per_reservation') return t('taxes.scope_per_reservation')
            if (r.scope === 'per_guest_per_night') return t('taxes.scope_per_guest_per_night')
            return t('taxes.scope_per_night')
          }},
          { key: 'priority', header: t('taxes.priority'), right: true },
          { key: 'is_active', header: t('taxes.active'), render: (r)=> r.is_active ? t('taxes.yes') : t('taxes.no'), right: true },
          {
            key: 'actions',
            header: t('dashboard.reservations_management.table_headers.actions'),
            right: true,
            render: (r) => (
              <div className="flex justify-end items-center gap-x-2">
                <EditIcon size="18" onClick={() => setEditRow(r)} className="cursor-pointer" />
                <DeleteButton resource="rates/tax-rules" id={r.id} onDeleted={refetch} className="cursor-pointer" />
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