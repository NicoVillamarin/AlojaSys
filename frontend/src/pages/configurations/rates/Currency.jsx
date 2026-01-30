import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import EditIcon from 'src/assets/icons/EditIcon'
import DeleteButton from 'src/components/DeleteButton'
import Button from 'src/components/Button'
import CurrencyModal from 'src/components/modals/CurrencyModal'

export default function Currency() {
  const { t } = useTranslation()
  const [showModal, setShowModal] = useState(false)
  const [editRow, setEditRow] = useState(null)
  const [filters, setFilters] = useState({ search: '' })
  const didMountRef = useRef(false)

  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'currencies',
    params: {},
  })

  const displayResults = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase()
    if (!q) return results
    return (results || []).filter((r) => {
      const code = String(r?.code ?? '').toLowerCase()
      const name = String(r?.name ?? '').toLowerCase()
      const symbol = String(r?.symbol ?? '').toLowerCase()
      return code.includes(q) || name.includes(q) || symbol.includes(q)
    })
  }, [results, filters.search])

  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true
      return
    }
    const id = setTimeout(() => refetch(), 300)
    return () => clearTimeout(id)
  }, [filters.search, refetch])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.configuration')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">Moneda</h1>
        </div>
        <Button variant="primary" size="md" onClick={() => setShowModal(true)}>
          Crear moneda
        </Button>
      </div>

      {/* Buscador simple */}
      <div className="flex items-center gap-3">
        <input
          value={filters.search}
          onChange={(e) => setFilters((s) => ({ ...s, search: e.target.value }))}
          placeholder="Buscar por código, nombre o símbolo…"
          className="w-full max-w-md border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-aloja-navy/20"
        />
      </div>

      <CurrencyModal isOpen={showModal} onClose={() => setShowModal(false)} isEdit={false} onSuccess={refetch} />
      <CurrencyModal isOpen={!!editRow} onClose={() => setEditRow(null)} isEdit={true} row={editRow} onSuccess={refetch} />

      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          { key: 'code', header: 'Código' },
          { key: 'name', header: 'Nombre' },
          { key: 'symbol', header: 'Símbolo', right: true },
          { key: 'is_active', header: 'Activa', render: (r) => (r.is_active ? 'Sí' : 'No'), right: true },
          {
            key: 'actions',
            header: t('dashboard.reservations_management.table_headers.actions'),
            right: true,
            render: (r) => (
              <div className="flex justify-end items-center gap-x-2">
                <EditIcon size="18" onClick={() => setEditRow(r)} className="cursor-pointer" />
                <DeleteButton
                  resource="currencies"
                  id={r.id}
                  onDeleted={refetch}
                  confirmMessage={`¿Eliminar la moneda ${r?.code || ''}?`}
                  title="Eliminar moneda"
                />
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