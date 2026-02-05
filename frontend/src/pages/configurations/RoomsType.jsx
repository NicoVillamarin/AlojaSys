import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import EditIcon from 'src/assets/icons/EditIcon'
import DeleteButton from 'src/components/DeleteButton'
import Button from 'src/components/Button'
import RoomTypeModal from 'src/components/modals/RoomTypeModal'

export default function RoomsType() {
  const { t } = useTranslation()
  const [showModal, setShowModal] = useState(false)
  const [editRow, setEditRow] = useState(null)
  const [filters, setFilters] = useState({ search: '', is_active: 'true' })
  const didMountRef = useRef(false)

  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'room-types',
    params: {
      is_active:
        filters.is_active === 'all'
          ? undefined
          : filters.is_active === 'true'
            ? 'true'
            : 'false',
    },
  })

  const displayResults = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase()
    if (!q) return results
    return (results || []).filter((r) => {
      const code = String(r?.code ?? '').toLowerCase()
      const name = String(r?.name ?? '').toLowerCase()
      const description = String(r?.description ?? '').toLowerCase()
      const sortOrder = String(r?.sort_order ?? '').toLowerCase()
      return code.includes(q) || name.includes(q) || description.includes(q) || sortOrder.includes(q)
    })
  }, [results, filters.search])

  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true
      return
    }
    const id = setTimeout(() => refetch(), 300)
    return () => clearTimeout(id)
  }, [filters.search, filters.is_active, refetch])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.configuration')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">
            {t('room_types.title', 'Tipos de habitación')}
          </h1>
        </div>
        <Button variant="primary" size="md" onClick={() => setShowModal(true)}>
          {t('room_types.create_button', 'Crear tipo')}
        </Button>
      </div>

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
              placeholder={t('room_types.search_placeholder', 'Buscar por código, nombre o descripción…')}
              value={filters.search}
              onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
              onKeyDown={(e) => e.key === 'Enter' && refetch()}
            />
            {filters.search && (
              <button
                className="absolute inset-y-0 right-1 my-1 px-2 rounded-md text-xs text-aloja-gray-800/70 hover:bg-gray-100"
                onClick={() => {
                  setFilters((f) => ({ ...f, search: '' }))
                  setTimeout(() => refetch(), 0)
                }}
                aria-label={t('common.clear_search', 'Limpiar búsqueda')}
              >
                ✕
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs text-aloja-gray-800/70">
              {t('room_types.filters.status', 'Estado')}
            </label>
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
              value={filters.is_active}
              onChange={(e) => setFilters((f) => ({ ...f, is_active: e.target.value }))}
            >
              <option value="true">{t('common.active', 'Activos')}</option>
              <option value="false">{t('common.inactive', 'Inactivos')}</option>
              <option value="all">{t('common.all', 'Todos')}</option>
            </select>
          </div>
        </div>
      </div>

      <RoomTypeModal isOpen={showModal} onClose={() => setShowModal(false)} isEdit={false} onSuccess={refetch} />
      <RoomTypeModal isOpen={!!editRow} onClose={() => setEditRow(null)} isEdit={true} row={editRow} onSuccess={refetch} />

      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          { key: 'code', header: t('room_types.table.code', 'Código'), sortable: true },
          { key: 'name', header: t('room_types.table.name', 'Nombre'), sortable: true },
          { key: 'sort_order', header: t('room_types.table.sort_order', 'Orden'), sortable: true, right: true },
          {
            key: 'is_active',
            header: t('room_types.table.active', 'Activo'),
            sortable: true,
            right: true,
            render: (r) => (r.is_active ? t('common.yes', 'Sí') : t('common.no', 'No')),
          },
          {
            key: 'actions',
            header: t('dashboard.reservations_management.table_headers.actions'),
            sortable: false,
            right: true,
            render: (r) => (
              <div className="flex justify-end items-center gap-x-2">
                <EditIcon size="18" onClick={() => setEditRow(r)} className="cursor-pointer" />
                <DeleteButton
                  resource="room-types"
                  id={r.id}
                  onDeleted={refetch}
                  confirmMessage={t(
                    'room_types.delete_confirm',
                    `¿Eliminar el tipo "${r?.name || r?.code || ''}"?`
                  )}
                  title={t('room_types.delete_title', 'Eliminar tipo de habitación')}
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