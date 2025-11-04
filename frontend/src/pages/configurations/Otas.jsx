import { useMemo, useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import Button from 'src/components/Button'
import DeleteButton from 'src/components/DeleteButton'
import { useList } from 'src/hooks/useList'
import OtaConfigModal from 'src/components/modals/OtaConfigModal'
import { useDispatchAction } from 'src/hooks/useDispatchAction'
import EditIcon from 'src/assets/icons/EditIcon'
import Tooltip from 'src/components/Tooltip'
import SelectStandalone from 'src/components/selects/SelectStandalone'
import { getApiURL } from 'src/services/utils'
import { showSuccess, showErrorConfirm } from 'src/services/toast'
import CopyIcon from 'src/assets/icons/CopyIcon'
import fetchWithAuth from 'src/services/fetchWithAuth'
import CheckIcon from 'src/assets/icons/CheckIcon'
import XIcon from 'src/assets/icons/Xicon'

export default function Otas() {
    const { t } = useTranslation()
    const [showModal, setShowModal] = useState(false)
    const [editItem, setEditItem] = useState(null)
    const [filters, setFilters] = useState({ search: '', provider: '', is_active: '' })
    const [hotelFilter, setHotelFilter] = useState('')
    const [syncingId, setSyncingId] = useState(null)
    const didMountRef = useRef(false)

    const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
        resource: 'otas/configs',
        params: { 
            search: filters.search, 
            hotel: hotelFilter || undefined,
            provider: filters.provider || undefined,
            is_active: filters.is_active || undefined,
        },
    })
    const { results: hotelOptions } = useList({ resource: 'hotels' })
    const { results: jobs, refetch: refetchJobs } = useList({ resource: 'otas/jobs' })

    // Obtener el último job de sincronización para cada configuración
    const getLastSyncJobForConfig = (configId, provider, hotelId) => {
        return (jobs || [])
            .filter(j => j.hotel === hotelId && j.provider === provider)
            .sort((a, b) => new Date(b.started_at || 0) - new Date(a.started_at || 0))[0] || null
    }

    const handleSyncNow = async (config) => {
        setSyncingId(config.id)
        try {
            const response = await fetchWithAuth(`${getApiURL()}/api/otas/sync/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    provider: config.provider,
                    hotel_id: config.hotel 
                }),
            })
            
            if (response.status === 'ok' || response.status === 'running') {
                showSuccess(t('ota.sync_started'))
                setTimeout(() => {
                    refetch()
                    refetchJobs()
                }, 1000)
            } else {
                showErrorConfirm(response.message || t('ota.sync_error'))
            }
        } catch (error) {
            showErrorConfirm(error?.message || t('ota.sync_error'))
        } finally {
            setTimeout(() => setSyncingId(null), 2000)
        }
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
    }, [filters.search, filters.provider, filters.is_active, hotelFilter, refetch])

    // Recargar jobs periódicamente si hay alguna sincronización en curso
    useEffect(() => {
        const interval = setInterval(() => {
            if (syncingId || (jobs || []).some(j => j.status === 'running')) {
                refetchJobs()
            }
        }, 3000)
        return () => clearInterval(interval)
    }, [syncingId, jobs, refetchJobs])

    return (
        <div className="space-y-5">
            <div className="flex items-center justify-between">
                <div>
                    <div className="text-xs text-aloja-gray-800/60">{t('sidebar.configuration')}</div>
                    <h1 className="text-2xl font-semibold text-aloja-navy">{t('ota.title')}</h1>
                </div>
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
                            placeholder={t('common.search')}
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
                    <div className="min-w-[180px]">
                        <SelectStandalone
                            title={t('ota.filters.provider')}
                            options={[
                                { value: 'ical', label: 'iCal' },
                                { value: 'booking', label: 'Booking' },
                                { value: 'airbnb', label: 'Airbnb' },
                                { value: 'expedia', label: 'Expedia' },
                                { value: 'other', label: t('common.other') },
                            ]}
                            placeholder={t('ota.filters.provider_placeholder')}
                            value={filters.provider ? { value: filters.provider, label: filters.provider } : null}
                            onChange={(opt) => setFilters((f) => ({ ...f, provider: opt ? opt.value : '' }))}
                            getOptionLabel={(opt) => opt.label}
                            getOptionValue={(opt) => opt.value}
                            isClearable={true}
                        />
                    </div>
                    <div className="min-w-[150px]">
                        <SelectStandalone
                            title={t('ota.filters.status')}
                            options={[
                                { value: 'true', label: t('common.active') },
                                { value: 'false', label: t('common.inactive') },
                            ]}
                            placeholder={t('ota.filters.status_placeholder')}
                            value={filters.is_active ? { value: filters.is_active, label: filters.is_active === 'true' ? t('common.active') : t('common.inactive') } : null}
                            onChange={(opt) => setFilters((f) => ({ ...f, is_active: opt ? opt.value : '' }))}
                            getOptionLabel={(opt) => opt.label}
                            getOptionValue={(opt) => opt.value}
                            isClearable={true}
                        />
                    </div>
                </div>
            </div>

            <TableGeneric
                isLoading={isPending}
                data={displayResults}
                getRowId={(c) => c.id}
                columns={[
                    { key: 'hotel_name', header: t('ota.table.hotel'), sortable: true },
                    { key: 'provider', header: t('ota.table.provider'), sortable: true },
                    { key: 'label', header: t('ota.table.label'), sortable: true },
                    { 
                        key: 'is_active', 
                        header: t('ota.table.active'), 
                        sortable: true, 
                        render: (c) => c.is_active ? <CheckIcon color="green" /> : <XIcon color="red" />
                    },
                    {
                        key: 'ical_out_token', 
                        header: t('ota.table.token'), 
                        sortable: false, 
                        render: (c) => {
                            const token_masked = String(c.ical_out_token_masked || c.ical_out_token || '')
                            return (
                                <div className="flex items-center gap-2">
                                    <span className="font-mono text-sm">{token_masked || '—'}</span>
                                </div>
                            )
                        }
                    },
                    {
                        key: 'verified', 
                        header: t('ota.table.verified'), 
                        sortable: false, 
                        render: (c) => {
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
                        key: 'last_sync', 
                        header: t('ota.table.last_sync'), 
                        sortable: false, 
                        render: (c) => {
                            const job = getLastSyncJobForConfig(c.id, c.provider, c.hotel)
                            if (!job) return <span className="text-gray-400">—</span>
                            
                            const statusColors = {
                                'success': 'bg-green-100 text-green-800',
                                'failed': 'bg-red-100 text-red-800',
                                'running': 'bg-blue-100 text-blue-800',
                                'pending': 'bg-gray-100 text-gray-600',
                            }
                            
                            const statusLabels = {
                                'success': t('ota.sync_success'),
                                'failed': t('ota.sync_failed'),
                                'running': t('ota.sync_running'),
                                'pending': t('ota.sync_pending'),
                            }
                            
                            const date = new Date(job.started_at)
                            return (
                                <div className="flex flex-col gap-1">
                                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusColors[job.status] || statusColors.pending}`}>
                                        {statusLabels[job.status] || job.status}
                                    </span>
                                    <span className="text-xs text-gray-500">
                                        {date.toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' })}
                                    </span>
                                </div>
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
                                <Tooltip content={t('ota.sync_now')}>
                                    <button
                                        disabled={syncingId === c.id}
                                        onClick={() => handleSyncNow(c)}
                                        className={`cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed p-1 rounded hover:bg-gray-100 ${syncingId === c.id ? 'animate-spin' : ''}`}
                                        aria-label={t('ota.sync_now')}
                                    >
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                        </svg>
                                    </button>
                                </Tooltip>
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

