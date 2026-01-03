import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Formik } from 'formik'
import TableGeneric from 'src/components/TableGeneric'
import Filter from 'src/components/Filter'
import { useList } from 'src/hooks/useList'
import { useUserHotels } from 'src/hooks/useUserHotels'
import SelectAsync from 'src/components/selects/SelectAsync'
import SelectStandalone from 'src/components/selects/SelectStandalone'
import ChecklistDetailModal from 'src/components/modals/ChecklistDetailModal'
import HousekeepingTaskDetailModal from 'src/components/modals/HousekeepingTaskDetailModal'
import Badge from 'src/components/Badge'
import { usePermissions } from 'src/hooks/usePermissions'
import { usePlanFeatures } from 'src/hooks/usePlanFeatures'

const TASK_STATUS = {
  pending: { labelKey: 'housekeeping.status.pending', variant: 'warning' },
  in_progress: { labelKey: 'housekeeping.status.in_progress', variant: 'info' },
  completed: { labelKey: 'housekeeping.status.completed', variant: 'success' },
  cancelled: { labelKey: 'housekeeping.status.cancelled', variant: 'error' },
}

const TASK_TYPE_OPTIONS = [
  { value: 'daily', labelKey: 'housekeeping.types.daily' },
  { value: 'checkout', labelKey: 'housekeeping.types.checkout' },
  { value: 'maintenance', labelKey: 'housekeeping.types.maintenance' },
]

const PRIORITY_OPTIONS = [
  { value: '2', labelKey: 'housekeeping.priority_high' },
  { value: '1', labelKey: 'housekeeping.priority_medium' },
  { value: '0', labelKey: 'housekeeping.priority_low' },
]

const STATUS_OPTIONS = ['pending', 'in_progress', 'completed', 'cancelled']

const formatDateTime = (value, locale) => {
  if (!value) return '-'
  try {
    return new Date(value).toLocaleString(locale)
  } catch {
    return value
  }
}

export default function HousekeepingHistorical() {
  const { t, i18n } = useTranslation()
  const { hasSingleHotel, singleHotelId } = useUserHotels()
  const { housekeepingEnabled } = usePlanFeatures()
  const canViewHousekeeping = usePermissions("housekeeping.access_housekeeping")
  const [filters, setFilters] = useState({
    hotel: hasSingleHotel ? String(singleHotelId) : '',
    status: '',
    assigned_to: '',
    room: '',
    task_type: '',
    priority: '',
    created_from: '',
    created_to: '',
    completed_from: '',
    completed_to: '',
  })
  const [showChecklistDetail, setShowChecklistDetail] = useState(false)
  const [selectedChecklistId, setSelectedChecklistId] = useState(null)
  const [showTaskDetail, setShowTaskDetail] = useState(false)
  const [selectedTaskId, setSelectedTaskId] = useState(null)

  const listParams = useMemo(
    () => ({
      hotel: filters.hotel || undefined,
      status: filters.status || undefined,
      assigned_to: filters.assigned_to || undefined,
      room: filters.room || undefined,
      task_type: filters.task_type || undefined,
      priority: filters.priority || undefined,
      created_from: filters.created_from || undefined,
      created_to: filters.created_to || undefined,
      completed_from: filters.completed_from || undefined,
      completed_to: filters.completed_to || undefined,
      page_size: 100,
    }),
    [filters]
  )

  const { results, isPending, hasNextPage, fetchNextPage } = useList({
    resource: 'housekeeping/tasks',
    params: listParams,
    enabled: canViewHousekeeping,
  })

  const displayResults = useMemo(() => results || [], [results])

  const handleDateChange = (field) => (event) => {
    setFilters((prev) => ({ ...prev, [field]: event.target.value }))
  }

  if (!housekeepingEnabled) {
    return (
      <div className="p-6 text-center text-gray-600">
        {t('housekeeping.not_enabled', 'El módulo de housekeeping no está habilitado en tu plan.')}
      </div>
    )
  }

  if (!canViewHousekeeping) {
    return (
      <div className="p-6 text-center text-gray-600">
        {t('housekeeping.no_permission_history', 'No tenés permiso para ver el histórico de housekeeping.')}
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div>
        <div className="text-xs text-aloja-gray-800/60">{t('sidebar.housekeeping_historical')}</div>
        <h1 className="text-2xl font-semibold text-aloja-navy">{t('housekeeping.history.title')}</h1>
        <p className="text-sm text-aloja-gray-700 mt-1">{t('housekeeping.history.description')}</p>
      </div>

      <ChecklistDetailModal
        isOpen={showChecklistDetail}
        onClose={() => {
          setShowChecklistDetail(false)
          setSelectedChecklistId(null)
        }}
        checklistId={selectedChecklistId}
      />

      <HousekeepingTaskDetailModal
        isOpen={showTaskDetail}
        onClose={() => {
          setShowTaskDetail(false)
          setSelectedTaskId(null)
        }}
        taskId={selectedTaskId}
      />

      <Filter>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          <Formik enableReinitialize initialValues={{}} onSubmit={() => {}}>
            <SelectAsync
              title={t('common.hotel')}
              name="hotel"
              resource="hotels"
              placeholder={t('common.all')}
              getOptionLabel={(h) => h?.name}
              getOptionValue={(h) => h?.id}
              onValueChange={(opt, val) => setFilters((f) => ({ ...f, hotel: String(val || '') }))}
              autoSelectSingle
            />
          </Formik>
          <Formik enableReinitialize initialValues={{}} onSubmit={() => {}}>
            <SelectAsync
              title={t('housekeeping.assigned_to')}
              name="assigned_to"
              resource="housekeeping/staff"
              placeholder={t('common.all')}
              extraParams={{ hotel: filters.hotel || undefined }}
              getOptionLabel={(s) => `${s.first_name}${s.last_name ? ' ' + s.last_name : ''}`}
              getOptionValue={(s) => s.id}
              onValueChange={(opt, val) => setFilters((f) => ({ ...f, assigned_to: String(val || '') }))}
              isClearable
            />
          </Formik>
          <Formik enableReinitialize initialValues={{}} onSubmit={() => {}}>
            <SelectAsync
              title={t('housekeeping.filters.room')}
              name="room"
              resource="rooms"
              placeholder={t('common.all')}
              extraParams={{ hotel: filters.hotel || undefined }}
              getOptionLabel={(room) => `${room?.name ?? ''}${room?.floor ? ` · Piso ${room.floor}` : ''}`}
              getOptionValue={(room) => room?.id}
              onValueChange={(opt, val) => setFilters((f) => ({ ...f, room: String(val || '') }))}
              isClearable
            />
          </Formik>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 mt-4">
          <SelectStandalone
            title={t('housekeeping.status.title')}
            value={
              filters.status
                ? { value: filters.status, label: t(`housekeeping.status.${filters.status}`) }
                : null
            }
            onChange={(opt) => setFilters((f) => ({ ...f, status: opt ? opt.value : '' }))}
            options={STATUS_OPTIONS.map((value) => ({
              value,
              label: t(`housekeeping.status.${value}`),
            }))}
            placeholder={t('common.select_placeholder')}
            isClearable
            isSearchable={false}
          />
          <SelectStandalone
            title={t('housekeeping.filters.task_type')}
            value={
              filters.task_type
                ? { value: filters.task_type, label: t(`housekeeping.types.${filters.task_type}`) }
                : null
            }
            onChange={(opt) => setFilters((f) => ({ ...f, task_type: opt ? opt.value : '' }))}
            options={TASK_TYPE_OPTIONS.map(({ value, labelKey }) => ({
              value,
              label: t(labelKey),
            }))}
            placeholder={t('common.select_placeholder')}
            isClearable
            isSearchable={false}
          />
          <SelectStandalone
            title={t('housekeeping.filters.priority')}
            value={
              filters.priority
                ? {
                    value: filters.priority,
                    label:
                      filters.priority === '2'
                        ? t('housekeeping.priority_high')
                        : filters.priority === '1'
                        ? t('housekeeping.priority_medium')
                        : t('housekeeping.priority_low'),
                  }
                : null
            }
            onChange={(opt) => setFilters((f) => ({ ...f, priority: opt ? opt.value : '' }))}
            options={PRIORITY_OPTIONS.map(({ value, labelKey }) => ({
              value,
              label: t(labelKey),
            }))}
            placeholder={t('common.select_placeholder')}
            isClearable
            isSearchable={false}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mt-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label className="flex flex-col text-sm text-aloja-gray-700">
              {t('housekeeping.filters.created_from')}
              <input
                type="date"
                className="mt-1 rounded-md border border-gray-200 px-3 py-2 text-sm text-aloja-gray-900 focus:border-aloja-navy focus:outline-none"
                value={filters.created_from}
                onChange={handleDateChange('created_from')}
              />
            </label>
            <label className="flex flex-col text-sm text-aloja-gray-700">
              {t('housekeeping.filters.created_to')}
              <input
                type="date"
                className="mt-1 rounded-md border border-gray-200 px-3 py-2 text-sm text-aloja-gray-900 focus:border-aloja-navy focus:outline-none"
                value={filters.created_to}
                onChange={handleDateChange('created_to')}
              />
            </label>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label className="flex flex-col text-sm text-aloja-gray-700">
              {t('housekeeping.filters.completed_from')}
              <input
                type="date"
                className="mt-1 rounded-md border border-gray-200 px-3 py-2 text-sm text-aloja-gray-900 focus:border-aloja-navy focus:outline-none"
                value={filters.completed_from}
                onChange={handleDateChange('completed_from')}
              />
            </label>
            <label className="flex flex-col text-sm text-aloja-gray-700">
              {t('housekeeping.filters.completed_to')}
              <input
                type="date"
                className="mt-1 rounded-md border border-gray-200 px-3 py-2 text-sm text-aloja-gray-900 focus:border-aloja-navy focus:outline-none"
                value={filters.completed_to}
                onChange={handleDateChange('completed_to')}
              />
            </label>
          </div>
        </div>
      </Filter>

      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          {
            key: 'id',
            header: 'ID',
            sortable: true,
            render: (r) => (
              <button
                type="button"
                className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
                onClick={() => {
                  setSelectedTaskId(r.id)
                  setShowTaskDetail(true)
                }}
              >
                {`Tarea N° ${r.id}`}
              </button>
            ),
          },
          { key: 'hotel', header: t('common.hotel'), sortable: true, render: (r) => r.hotel_name || r.hotel },
          { key: 'room', header: t('housekeeping.room'), sortable: true, render: (r) => r.room_name || r.room },
          {
            key: 'task_type',
            header: t('housekeeping.task_type'),
            sortable: true,
            render: (r) => t(`housekeeping.types.${r.task_type}`),
          },
          { key: 'assigned_to', header: t('housekeeping.assigned_to'), sortable: true, render: (r) => r.assigned_to_name || '-' },
          {
            key: 'status',
            header: t('housekeeping.status.title'),
            sortable: true,
            render: (r) => {
              const cfg = TASK_STATUS[r.status] || TASK_STATUS.pending
              return (
                <Badge variant={cfg.variant} size="sm">
                  {t(cfg.labelKey)}
                </Badge>
              )
            },
          },
          {
            key: 'checklist',
            header: t('housekeeping.checklists.title'),
            sortable: false,
            render: (r) => {
              if (!r.checklist_name && !r.checklist) return '-'
              const hasChecklist = !!(r.checklist || r.checklist_id)
              return hasChecklist ? (
                <button
                  onClick={() => {
                    setSelectedChecklistId(r.checklist || r.checklist_id)
                    setShowChecklistDetail(true)
                  }}
                  className="text-sm text-blue-600 hover:text-blue-800 hover:underline transition-colors cursor-pointer"
                >
                  {r.checklist_name || '-'}
                </button>
              ) : (
                <span className="text-sm text-gray-700">{r.checklist_name || '-'}</span>
              )
            },
          },
          {
            key: 'priority',
            header: t('housekeeping.priority'),
            sortable: true,
            render: (r) => {
              const p = typeof r.priority === 'number' ? r.priority : parseInt(r.priority ?? '0', 10)
              if (p >= 2) return t('housekeeping.priority_high')
              if (p === 1) return t('housekeeping.priority_medium')
              return t('housekeeping.priority_low')
            },
          },
          {
            key: 'created_at',
            header: t('common.created_at'),
            sortable: true,
            render: (r) => formatDateTime(r.created_at, i18n.language),
          },
          {
            key: 'started_at',
            header: t('housekeeping.history.started_at'),
            sortable: true,
            render: (r) => formatDateTime(r.started_at, i18n.language),
          },
          {
            key: 'completed_at',
            header: t('housekeeping.history.completed_at'),
            sortable: true,
            render: (r) => formatDateTime(r.completed_at, i18n.language),
          },
        ]}
      />

      {hasNextPage && (
        <div className="mt-3">
          <button className="px-3 py-2 rounded-md border" onClick={() => fetchNextPage()}>
            {t('common.load_more')}
          </button>
        </div>
      )}
    </div>
  )
}