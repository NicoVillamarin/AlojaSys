import { useMemo, useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import Button from 'src/components/Button'
import DeleteButton from 'src/components/DeleteButton'
import { useList } from 'src/hooks/useList'
import OtaConfigModal from 'src/components/modals/OtaConfigModal'
import OtaRoomMappingModal from 'src/components/modals/OtaRoomMappingModal'
import OtaRoomTypeMappingModal from 'src/components/modals/OtaRoomTypeMappingModal'
import OtaRatePlanMappingModal from 'src/components/modals/OtaRatePlanMappingModal'
import OtaAriPushModal from 'src/components/modals/OtaAriPushModal'
import { useDispatchAction } from 'src/hooks/useDispatchAction'
import EditIcon from 'src/assets/icons/EditIcon'
import Tooltip from 'src/components/Tooltip'
import DownloadIcon from 'src/assets/icons/DownloadIcon'
import EyeIcon from 'src/assets/icons/EyeIcon'
import EyeSlashIcon from 'src/assets/icons/EyeSlashIcon'
import SelectStandalone from 'src/components/selects/SelectStandalone'
import Tabs from 'src/components/Tabs'
import { getApiURL } from 'src/services/utils'
import { showSuccess } from 'src/services/toast'
import CopyIcon from 'src/assets/icons/CopyIcon'

export default function OtaConfig() {
    const { t } = useTranslation()
    const [showModal, setShowModal] = useState(false)
    const [editItem, setEditItem] = useState(null)
    const [filters, setFilters] = useState({ search: '' })
    const [hotelFilter, setHotelFilter] = useState('')
    const [revealed, setRevealed] = useState({})
    const [activeTab, setActiveTab] = useState('configs')
    const didMountRef = useRef(false)
    const [showMappingModal, setShowMappingModal] = useState(false)
    const [editMapping, setEditMapping] = useState(null)
    const [selectedHotelForMapping, setSelectedHotelForMapping] = useState(null)
    const [showRoomTypeModal, setShowRoomTypeModal] = useState(false)
    const [editRoomType, setEditRoomType] = useState(null)
    const [showRatePlanModal, setShowRatePlanModal] = useState(false)
    const [editRatePlan, setEditRatePlan] = useState(null)
    const [showAriModal, setShowAriModal] = useState(false)

    const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
        resource: 'otas/configs',
        params: { search: filters.search, hotel: hotelFilter || undefined },
    })
    const { results: hotelOptions } = useList({ resource: 'hotels' })

    const { results: mappings, isPending: loadingMappings, refetch: refetchMappings } = useList({
        resource: 'otas/mappings',
        params: { hotel: hotelFilter || undefined },
    })
  const { results: roomTypes, isPending: loadingRoomTypes, refetch: refetchRoomTypes } = useList({ resource: 'otas/room-type-mappings', params: { hotel: hotelFilter || undefined } })
  const { results: ratePlans, isPending: loadingRatePlans, refetch: refetchRatePlans } = useList({ resource: 'otas/rate-plan-mappings', params: { hotel: hotelFilter || undefined } })

    const { mutate: dispatchMappingAction } = useDispatchAction({ resource: 'otas/mappings' })
    const { results: jobs, refetch: refetchJobs } = useList({ resource: 'otas/jobs' })
    const [importingId, setImportingId] = useState(null)

    const getLastJobForMapping = (mappingId) => {
        return (jobs || []).find(j => (j?.stats?.mapping_id === mappingId) && j.job_type === 'import_ics') || null
    }

    const displayResults = useMemo(() => {
        const q = (filters.search || '').trim().toLowerCase()
        if (!q) return results
        return (results || []).filter((c) => {
            const hotelStr = String(c.hotel_name ?? '')
            const providerStr = String(c.provider ?? '')
            const labelStr = String(c.label ?? '')
            return (
                hotelStr.toLowerCase().includes(q) ||
                providerStr.toLowerCase().includes(q) ||
                labelStr.toLowerCase().includes(q)
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
                    <div className="text-xs text-aloja-gray-800/60">{t('sidebar.configuration')}</div>
                    <h1 className="text-2xl font-semibold text-aloja-navy">{t('ota.config.title')}</h1>
                </div>
                <Button variant="primary" size="md" onClick={() => setShowModal(true)}>
                    {t('ota.config.create_button')}
                </Button>
            </div>

            <OtaConfigModal isOpen={showModal} onClose={() => setShowModal(false)} isEdit={false} onSuccess={refetch} />
            <OtaConfigModal isOpen={!!editItem} onClose={() => setEditItem(null)} isEdit={true} config={editItem} onSuccess={refetch} />

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
                            placeholder={t('common.search_placeholder')}
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
                    <div className="min-w-[260px]">
                        <SelectStandalone
                            title={t('ota.filters.hotel')}
                            options={hotelOptions}
                            placeholder={t('ota.filters.hotel_placeholder')}
                            value={hotelOptions.find(h => String(h.id) === String(hotelFilter)) || null}
                            onChange={(opt) => setHotelFilter(opt ? opt.id : '')}
                            getOptionLabel={(h) => h?.name}
                            getOptionValue={(h) => h?.id}
                            isClearable={true}
                        />
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <Tabs
              className="mt-2"
              tabs={[
                { id: 'configs', label: t('ota.config.title') },
                { id: 'room_mappings', label: t('ota.mappings.title') },
                { id: 'room_types', label: t('ota.room_types.title') },
                { id: 'rate_plans', label: t('ota.rate_plans.title') },
              ]}
              activeTab={activeTab}
              onTabChange={setActiveTab}
            />

            {activeTab === 'configs' && (
              <TableGeneric
                isLoading={isPending}
                data={displayResults}
                getRowId={(c) => c.id}
                columns={[
                  { key: 'hotel_name', header: t('ota.config.table.hotel'), sortable: true },
                  { key: 'provider', header: t('ota.config.table.provider'), sortable: true },
                  { key: 'label', header: t('ota.config.table.label'), sortable: true },
                  { key: 'is_active', header: t('ota.config.table.active'), sortable: true, render: (c) => (c.is_active ? '✓' : '—') },
                  {
                    key: 'ical_out_token', header: t('ota.config.table.token'), sortable: false, render: (c) => {
                      const token_masked =
                        c.provider === 'smoobu'
                          ? String(c.smoobu_api_key_masked || '')
                          : String(c.ical_out_token_masked || c.ical_out_token || '')
                      return (
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm">{token_masked || '—'}</span>
                        </div>
                      )
                    }
                  },
                  {
                    key: 'verified', header: t('ota.config.table.verified'), sortable: false, render: (c) => {
                      return c.verified ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          {t('common.verified')}
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                          {t('common.not_verified')}
                        </span>
                      )
                    }
                  },
                  {
                    key: 'actions',
                    header: t('dashboard.reservations_management.table_headers.actions'),
                    sortable: false,
                    right: true,
                    render: (c) => (
                      <div className="flex justify-end items-center gap-x-2">
                        <EditIcon size="18" onClick={() => setEditItem(c)} className="cursor-pointer" />
                        {c.ical_hotel_url && (
                          <Tooltip content={t('ota.config.copy_hotel_ical')}>
                            <CopyIcon
                              size="18"
                              className="cursor-pointer"
                              onClick={() => {
                                navigator.clipboard.writeText(c.ical_hotel_url)
                                showSuccess(t('common.copied'))
                              }}
                            />
                          </Tooltip>
                        )}
                        <DeleteButton resource="otas/configs" id={c.id} onDeleted={refetch} className="cursor-pointer" />
                      </div>
                    ),
                  },
                ]}
              />
            )}

            {/* --- MAPEOS POR HABITACIÓN --- */}
            {activeTab === 'room_mappings' && (
            <>
            <div className="flex items-center justify-between mt-8">
                <div>
                    <h2 className="text-xl font-semibold text-aloja-navy">{t('ota.mappings.title')}</h2>
                    <div className="text-xs text-aloja-gray-800/60">{t('ota.mappings.subtitle')}</div>
                </div>
                <div className="flex items-center gap-3">
                  <Button variant="secondary" size="md" onClick={() => setShowAriModal(true)}>
                    {t('ota.ari.push_title')}
                  </Button>
                  <Button variant="secondary" size="md" onClick={() => { setSelectedHotelForMapping(null); setEditMapping(null); setShowMappingModal(true) }}>
                      {t('ota.mappings.create_button')}
                  </Button>
                </div>
            </div>

            <OtaRoomMappingModal
                isOpen={showMappingModal}
                onClose={() => setShowMappingModal(false)}
                isEdit={!!editMapping}
                mapping={editMapping}
                defaultHotelId={selectedHotelForMapping}
                onSuccess={() => { refetchMappings(); setShowMappingModal(false) }}
            />
            <OtaAriPushModal isOpen={showAriModal} onClose={() => setShowAriModal(false)} defaultHotelId={hotelFilter || undefined} onQueued={() => { setShowAriModal(false) }} />

            <TableGeneric
                isLoading={loadingMappings}
                data={mappings}
                getRowId={(m) => m.id}
                columns={[
                    { key: 'hotel_name', header: t('ota.mappings.table.hotel'), sortable: true },
                    { key: 'room_name', header: t('ota.mappings.table.room'), sortable: true },
                    { key: 'provider', header: t('ota.mappings.table.provider'), sortable: true },
                    { key: 'external_id', header: t('ota.mappings.table.external_id'), sortable: true },
                    { key: 'ical_in_url', header: t('ota.mappings.table.ical_in_url'), sortable: false },
                    { key: 'sync_direction', header: t('ota.mappings.table.sync_direction'), sortable: true, render: (m) => {
                        const dir = m.sync_direction || 'both'
                        if (dir === 'both') return t('ota.mappings.sync_direction_both')
                        if (dir === 'import') return t('ota.mappings.sync_direction_import')
                        return t('ota.mappings.sync_direction_export')
                    }},
                    { key: 'is_active', header: t('ota.mappings.table.active'), sortable: true, render: (m) => (m.is_active ? '✓' : '—') },
                    { key: 'last_synced', header: t('ota.mappings.table.last_synced'), sortable: true, render: (m) => {
                        if (!m.last_synced) return '—'
                        const d = new Date(m.last_synced)
                        return d.toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' })
                    }},
                    {
                        key: 'last_import', header: t('ota.mappings.table.last_import'), sortable: false, render: (m) => {
                            const job = getLastJobForMapping(m.id)
                            if (!job) return '—'
                            const s = job.stats || {}
                            const base = job.status
                            const detail = (s.processed != null) ? ` • ${s.processed}/${(s.created || 0)}+${(s.updated || 0)}+${(s.skipped || 0)}` : ''
                            return base + detail
                        }
                    },
                    {
                        key: 'actions',
                        header: t('dashboard.reservations_management.table_headers.actions'),
                        sortable: false,
                        right: true,
                        render: (m) => (
                            <div className="flex justify-end items-center gap-x-2">
                                <EditIcon size="18" onClick={() => { setEditMapping(m); setShowMappingModal(true) }} className="cursor-pointer" />
                                <Tooltip content={t('ota.mappings.import_now')}>
                                    <button
                                        disabled={importingId === m.id}
                                        onClick={() => {
                                            setImportingId(m.id)
                                            dispatchMappingAction({ action: `${m.id}/import_now`, body: {}, method: 'POST' })
                                            setTimeout(() => { setImportingId(null); refetchJobs() }, 1200)
                                        }}
                                        className="cursor-pointer disabled:opacity-50"
                                        aria-label={t('ota.mappings.import_now')}
                                    >
                                        <DownloadIcon size="20" />
                                    </button>
                                </Tooltip>
                                <Tooltip content={t('ota.mappings.copy_room_ical')}>
                                    <CopyIcon
                                        onClick={() => {
                                            const cfg = (results || []).find(c => c.hotel === m.hotel && c.provider === 'ical' && c.is_active)
                                            // Usar ical_hotel_url si está disponible, o construir manualmente
                                            if (cfg?.ical_hotel_url) {
                                              // Reemplazar hotel con room en la URL
                                              const roomUrl = cfg.ical_hotel_url.replace(`/hotel/${cfg.hotel}.ics`, `/room/${m.room}.ics`)
                                              navigator.clipboard.writeText(roomUrl)
                                            } else {
                                              // Fallback: construir manualmente (requiere token real)
                                              const base = getApiURL()
                                              // Nota: esto requiere que el token esté disponible
                                              // En producción, siempre usar ical_hotel_url
                                              return
                                            }
                                            showSuccess(t('common.copied'))
                                        }}
                                        size="18"
                                        className="cursor-pointer"
                                    />
                                </Tooltip>
                                <DeleteButton resource="otas/mappings" id={m.id} onDeleted={refetchMappings} className="cursor-pointer" />
                            </div>
                        ),
                    },
                ]}
            />
            </>
            )}

            {hasNextPage && (
                <div>
                    <button className="px-3 py-2 rounded-md border" onClick={() => fetchNextPage()}>
                        {t('common.load_more')}
                    </button>
                </div>
            )}

            {/* --- ROOM TYPE MAPPINGS --- */}
            {activeTab === 'room_types' && (
            <>
            <div className="flex items-center justify-between mt-10">
              <div>
                <h2 className="text-xl font-semibold text-aloja-navy">{t('ota.room_types.title')}</h2>
                <div className="text-xs text-aloja-gray-800/60">{t('ota.room_types.subtitle')}</div>
              </div>
              <Button variant="secondary" size="md" onClick={() => { setEditRoomType(null); setShowRoomTypeModal(true) }}>
                {t('ota.room_types.create_button')}
              </Button>
            </div>
            <OtaRoomTypeMappingModal
              isOpen={showRoomTypeModal}
              onClose={() => setShowRoomTypeModal(false)}
              isEdit={!!editRoomType}
              mapping={editRoomType}
              defaultHotelId={hotelFilter || undefined}
              onSuccess={() => { refetchRoomTypes(); setShowRoomTypeModal(false) }}
            />
            <TableGeneric
              isLoading={loadingRoomTypes}
              data={roomTypes}
              getRowId={(r) => r.id}
              columns={[
                { key: 'hotel_name', header: t('ota.room_types.table.hotel'), sortable: true },
                { key: 'provider', header: t('ota.room_types.table.provider'), sortable: true },
                { key: 'room_type_code', header: t('ota.room_types.table.room_type_code'), sortable: true },
                { key: 'provider_code', header: t('ota.room_types.table.provider_code'), sortable: true },
                { key: 'name', header: t('ota.room_types.table.name'), sortable: true },
                { key: 'is_active', header: t('ota.room_types.table.active'), sortable: true, render: (r) => (r.is_active ? '✓' : '—') },
                {
                  key: 'actions', header: t('dashboard.reservations_management.table_headers.actions'), right: true, render: (r) => (
                    <div className="flex justify-end items-center gap-x-2">
                      <EditIcon size="18" onClick={() => { setEditRoomType(r); setShowRoomTypeModal(true) }} className="cursor-pointer" />
                      <DeleteButton resource="otas/room-type-mappings" id={r.id} onDeleted={refetchRoomTypes} className="cursor-pointer" />
                    </div>
                  )
                }
              ]}
            />
            </>
            )}

            {/* --- RATE PLAN MAPPINGS --- */}
            {activeTab === 'rate_plans' && (
            <>
            <div className="flex items-center justify-between mt-10">
              <div>
                <h2 className="text-xl font-semibold text-aloja-navy">{t('ota.rate_plans.title')}</h2>
                <div className="text-xs text-aloja-gray-800/60">{t('ota.rate_plans.subtitle')}</div>
              </div>
              <Button variant="secondary" size="md" onClick={() => { setEditRatePlan(null); setShowRatePlanModal(true) }}>
                {t('ota.rate_plans.create_button')}
              </Button>
            </div>
            <OtaRatePlanMappingModal
              isOpen={showRatePlanModal}
              onClose={() => setShowRatePlanModal(false)}
              isEdit={!!editRatePlan}
              mapping={editRatePlan}
              defaultHotelId={hotelFilter || undefined}
              onSuccess={() => { refetchRatePlans(); setShowRatePlanModal(false) }}
            />
            <TableGeneric
              isLoading={loadingRatePlans}
              data={ratePlans}
              getRowId={(r) => r.id}
              columns={[
                { key: 'hotel_name', header: t('ota.rate_plans.table.hotel'), sortable: true },
                { key: 'provider', header: t('ota.rate_plans.table.provider'), sortable: true },
                { key: 'rate_plan_code', header: t('ota.rate_plans.table.rate_plan_code'), sortable: true },
                { key: 'provider_code', header: t('ota.rate_plans.table.provider_code'), sortable: true },
                { key: 'currency', header: t('ota.rate_plans.table.currency'), sortable: true },
                { key: 'is_active', header: t('ota.rate_plans.table.active'), sortable: true, render: (r) => (r.is_active ? '✓' : '—') },
                {
                  key: 'actions', header: t('dashboard.reservations_management.table_headers.actions'), right: true, render: (r) => (
                    <div className="flex justify-end items-center gap-x-2">
                      <EditIcon size="18" onClick={() => { setEditRatePlan(r); setShowRatePlanModal(true) }} className="cursor-pointer" />
                      <DeleteButton resource="otas/rate-plan-mappings" id={r.id} onDeleted={refetchRatePlans} className="cursor-pointer" />
                    </div>
                  )
                }
              ]}
            />
            </>
            )}
        </div>
    )
}
