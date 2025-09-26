import { useMemo, useRef, useState, useEffect } from 'react'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import CitiesModal from 'src/components/modals/CitiesModal'
import EditIcon from 'src/assets/icons/EditIcon'
import DeleteButton from 'src/components/DeleteButton'
import Button from 'src/components/Button'

export default function Cities() {
  const [showModal, setShowModal] = useState(false)
  const [editCity, setEditCity] = useState(null)
  const [filters, setFilters] = useState({ search: '' })
  const didMountRef = useRef(false)

  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'cities',
    params: { search: filters.search },
  })

  const displayResults = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase()
    if (!q) return results
    return (results || []).filter((c) => {
      const idStr = String(c.id ?? '')
      const nameStr = String(c.name ?? '')
      const stateStr = String(c.state_name ?? '')
      const postalStr = String(c.postal_code ?? '')
      const latStr = String(c.lat ?? '')
      const lngStr = String(c.lng ?? '')
      return (
        idStr.includes(q) ||
        nameStr.toLowerCase().includes(q) ||
        stateStr.toLowerCase().includes(q) ||
        postalStr.toLowerCase().includes(q) ||
        latStr.toLowerCase().includes(q) ||
        lngStr.toLowerCase().includes(q)
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
          <h1 className="text-2xl font-semibold text-aloja-navy">Ciudades</h1>
        </div>
        <Button variant="primary" size="md" onClick={() => setShowModal(true)}>
          Crear ciudad
        </Button>
      </div>

      <CitiesModal isOpen={showModal} onClose={() => setShowModal(false)} isEdit={false} onSuccess={refetch} />
      <CitiesModal isOpen={!!editCity} onClose={() => setEditCity(null)} isEdit={true} city={editCity} onSuccess={refetch} />

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
              placeholder="Buscar ciudades…"
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
        getRowId={(c) => c.id}
        columns={[
          { key: 'name', header: 'Nombre', sortable: true },
          { key: 'state_name', header: 'Provincia/Estado', sortable: true },
          { key: 'postal_code', header: 'CP', sortable: true },
          { key: 'lat', header: 'Lat', sortable: true, right: true },
          { key: 'lng', header: 'Lng', sortable: true, right: true },
          {
            key: 'actions',
            header: 'Acciones',
            sortable: false,
            right: true,
            render: (c) => (
              <div className="flex justify-end items-center gap-x-2">
                <EditIcon size="18" onClick={() => setEditCity(c)} className="cursor-pointer" />
                <DeleteButton resource="cities" id={c.id} onDeleted={refetch} className="cursor-pointer" />
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
