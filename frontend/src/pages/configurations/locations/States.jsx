import { useMemo, useRef, useState, useEffect } from 'react'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import StatesModal from 'src/components/modals/StatesModal'
import EditIcon from 'src/assets/icons/EditIcon'
import DeleteButton from 'src/components/DeleteButton'
import Button from 'src/components/Button'

export default function States() {
  const [showModal, setShowModal] = useState(false)
  const [editState, setEditState] = useState(null)
  const [filters, setFilters] = useState({ search: '' })
  const didMountRef = useRef(false)

  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'states',
    params: { search: filters.search },
  })

  const displayResults = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase()
    if (!q) return results
    return (results || []).filter((s) => {
      const idStr = String(s.id ?? '')
      const nameStr = String(s.name ?? '')
      const codeStr = String(s.code ?? '')
      const countryStr = String(s.country_name ?? '')
      const countryCode2 = String(s.country_code2 ?? '')
      return (
        idStr.includes(q) ||
        nameStr.toLowerCase().includes(q) ||
        codeStr.toLowerCase().includes(q) ||
        countryStr.toLowerCase().includes(q) ||
        countryCode2.toLowerCase().includes(q)
      )
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
          <div className="text-xs text-aloja-gray-800/60">Configuración</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">Provincias/Estados</h1>
        </div>
        <Button variant="primary" size="md" onClick={() => setShowModal(true)}>
          Crear provincia/estado
        </Button>
      </div>

      <StatesModal isOpen={showModal} onClose={() => setShowModal(false)} isEdit={false} onSuccess={refetch} />
      <StatesModal isOpen={!!editState} onClose={() => setEditState(null)} isEdit={true} stateItem={editState} onSuccess={refetch} />

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
              placeholder="Buscar provincias/estados…"
              value={filters.search}
              onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
              onKeyDown={(e) => e.key === 'Enter' && refetch()}
            />
            {filters.search && (
              <button
                className="absolute inset-y-0 right-1 my-1 px-2 rounded-md text-xs text-aloja-gray-800/70 hover:bg-gray-100"
                onClick={() => { setFilters((f) => ({ ...f, search: '' })); setTimeout(() => refetch(), 0) }}
                aria-label="Limpiar búsqueda"
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
        getRowId={(s) => s.id}
        columns={[
          { key: 'name', header: 'Nombre', sortable: true },
          { key: 'code', header: 'Código', sortable: true },
          {
            key: 'country',
            header: 'País',
            sortable: true,
            accessor: (s) => s.country_name,
            render: (s) => `${s.country_name} (${s.country_code2})`,
          },
          {
            key: 'actions',
            header: 'Acciones',
            sortable: false,
            right: true,
            render: (s) => (
              <div className="flex justify-end items-center gap-x-2">
                <EditIcon size="18" onClick={() => setEditState(s)} className="cursor-pointer" />
                <DeleteButton resource="states" id={s.id} onDeleted={refetch} className="cursor-pointer" />
              </div>
            ),
          },
        ]}
      />

      {hasNextPage && (
        <div>
          <button className="px-3 py-2 rounded-md border" onClick={() => fetchNextPage()}>
            Cargar más
          </button>
        </div>
      )}
    </div>
  )
}
