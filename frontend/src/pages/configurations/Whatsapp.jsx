import React, { useMemo, useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import Button from 'src/components/Button'
import EditIcon from 'src/assets/icons/EditIcon'
import WhatsappModal from 'src/components/modals/WhatsappModal'

const Whatsapp = () => {
  const { t } = useTranslation()
  const [filters, setFilters] = useState({ search: '' })
  const [editHotel, setEditHotel] = useState(null)
  const didMountRef = useRef(false)

  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'hotels',
    params: { search: filters.search || undefined },
  })

  const displayResults = useMemo(() => {
    const q = (filters.search || '').trim().toLowerCase()
    if (!q) return results
    return (results || []).filter((h) => {
      const nameStr = String(h.name ?? '').toLowerCase()
      const enterpriseStr = String(h.enterprise_name ?? '').toLowerCase()
      const phoneStr = String(h.whatsapp_phone ?? '').toLowerCase()
      return (
        nameStr.includes(q) ||
        enterpriseStr.includes(q) ||
        phoneStr.includes(q)
      )
    })
  }, [results, filters.search])

  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true
      return
    }
    const id = setTimeout(() => refetch(), 400)
    return () => clearTimeout(id)
  }, [filters.search, refetch])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.configuration')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">WhatsApp</h1>
          <p className="text-xs text-aloja-gray-800/70 mt-1 max-w-2xl">
            Configurá el número oficial de WhatsApp y las credenciales del proveedor por hotel.
            Esta configuración se usa para el chatbot de reservas y futuras integraciones.
          </p>
        </div>
        <Button variant="secondary" size="md" onClick={() => refetch()}>
          {t('common.refresh')}
        </Button>
      </div>

      <WhatsappModal
        isOpen={!!editHotel}
        onClose={() => setEditHotel(null)}
        hotel={editHotel}
        onSuccess={refetch}
      />

      <div className="bg-white rounded-xl shadow p-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <span className="pointer-events-none absolute inset-y-0 left-2 flex items-center text-aloja-gray-800/60">
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path
                  fillRule="evenodd"
                  d="M12.9 14.32a8 8 0 111.414-1.414l3.387 3.387a1 1 0 01-1.414 1.414l-3.387-3.387zM14 8a6 6 0 11-12 0 6 6 0 0112 0z"
                  clipRule="evenodd"
                />
              </svg>
            </span>
            <input
              className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg pl-8 pr-8 py-2 text-sm w-64 transition-all"
              placeholder={t('hotels.search_placeholder')}
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
        getRowId={(h) => h.id}
        columns={[
          { key: 'enterprise_name', header: t('enterprises.name'), sortable: true },
          { key: 'name', header: t('hotels_modal.name'), sortable: true },
          {
            key: 'whatsapp_enabled',
            header: t('hotels_modal.whatsapp_enabled'),
            sortable: true,
            render: (h) => (
              <span
                className={
                  'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ' +
                  (h.whatsapp_enabled
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'bg-gray-50 text-gray-500')
                }
              >
                {h.whatsapp_enabled ? t('common.yes') : t('common.no')}
              </span>
            ),
          },
          {
            key: 'whatsapp_phone',
            header: t('hotels_modal.whatsapp_phone'),
            sortable: true,
          },
          {
            key: 'whatsapp_provider',
            header: t('hotels_modal.whatsapp_provider'),
            sortable: true,
          },
          {
            key: 'actions',
            header: t('dashboard.reservations_management.table_headers.actions'),
            sortable: false,
            right: true,
            render: (h) => (
              <div className="flex justify-end items-center gap-x-2">
                <EditIcon
                  size="18"
                  onClick={() => setEditHotel(h)}
                  className="cursor-pointer"
                />
              </div>
            ),
          },
        ]}
      />

      {hasNextPage && (
        <div>
          <button
            className="px-3 py-2 rounded-md border"
            onClick={() => fetchNextPage()}
          >
            {t('common.load_more')}
          </button>
        </div>
      )}
    </div>
  )
}

export default Whatsapp
