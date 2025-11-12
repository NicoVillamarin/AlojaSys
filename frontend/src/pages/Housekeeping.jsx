import { useMemo, useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import Button from 'src/components/Button'
import TableGeneric from 'src/components/TableGeneric'
import Filter from 'src/components/Filter'
import { useList } from 'src/hooks/useList'
import { useUserHotels } from 'src/hooks/useUserHotels'
import SelectAsync from 'src/components/selects/SelectAsync'
import SelectBasic from 'src/components/selects/SelectBasic'
import SelectStandalone from 'src/components/selects/SelectStandalone'
import { Formik } from 'formik'
import DeleteButton from 'src/components/DeleteButton'
import HousekeepingModal from 'src/components/modals/HousekeepingModal'
import { useDispatchAction } from 'src/hooks/useDispatchAction'

const TASK_STATUS = {
  pending: { labelKey: 'housekeeping.status.pending', color: 'bg-amber-100 text-amber-700' },
  in_progress: { labelKey: 'housekeeping.status.in_progress', color: 'bg-blue-100 text-blue-700' },
  completed: { labelKey: 'housekeeping.status.completed', color: 'bg-emerald-100 text-emerald-700' },
  cancelled: { labelKey: 'housekeeping.status.cancelled', color: 'bg-rose-100 text-rose-700' },
}

export default function Housekeeping() {
  const { t } = useTranslation()
  const { hasSingleHotel, singleHotelId } = useUserHotels()
  const [filters, setFilters] = useState({
    hotel: hasSingleHotel ? String(singleHotelId) : '',
    status: '',
    assigned_to: '',
  })
  const [showModal, setShowModal] = useState(false)
  const [editTask, setEditTask] = useState(null)
  const didMountRef = useRef(false)

  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'housekeeping/tasks',
    params: {
      hotel: filters.hotel,
      status: filters.status,
      assigned_to: filters.assigned_to,
      page_size: 100,
    },
  })

  // Acciones start/complete
  const { mutate: dispatchAction } = useDispatchAction({
    resource: 'housekeeping/tasks',
    onSuccess: () => refetch(),
  })

  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true
      return
    }
    const id = setTimeout(() => refetch(), 350)
    return () => clearTimeout(id)
  }, [filters.hotel, filters.status, filters.assigned_to, refetch])

  const displayResults = useMemo(() => results || [], [results])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.housekeeping')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('housekeeping.title')}</h1>
        </div>
        <Button variant="primary" size="md" onClick={() => { setEditTask(null); setShowModal(true); }}>
          {t('housekeeping.new_task')}
        </Button>
      </div>

      <HousekeepingModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        isEdit={!!editTask}
        task={editTask}
        onSuccess={() => {
          setShowModal(false)
          setEditTask(null)
          refetch()
        }}
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
          <SelectStandalone
            title={t('housekeeping.status.title')}
            value={
              filters.status
                ? { value: filters.status, label: t(`housekeeping.status.${filters.status}`) }
                : null
            }
            onChange={(opt) => setFilters((f) => ({ ...f, status: opt ? opt.value : '' }))}
            options={[
              { value: 'pending', label: t('housekeeping.status.pending') },
              { value: 'in_progress', label: t('housekeeping.status.in_progress') },
              { value: 'completed', label: t('housekeeping.status.completed') },
              { value: 'cancelled', label: t('housekeeping.status.cancelled') },
            ]}
            placeholder={t('common.select_placeholder')}
            isClearable
            isSearchable={false}
          />
        </div>
        <div className="mt-3">
          <div className="flex gap-2">
            <button
              className={`px-3 py-1.5 rounded text-xs border ${!filters.status ? 'bg-aloja-navy text-white border-aloja-navy' : 'bg-white text-aloja-navy border-aloja-navy/30'}`}
              onClick={() => setFilters((f) => ({ ...f, status: '' }))}
            >
              {t('common.all')}
            </button>
            {Object.entries(TASK_STATUS).map(([key, cfg]) => (
              <button
                key={key}
                className={`px-3 py-1.5 rounded text-xs border ${filters.status === key ? 'bg-aloja-navy text-white border-aloja-navy' : 'bg-white text-aloja-navy border-aloja-navy/30'}`}
                onClick={() => setFilters((f) => ({ ...f, status: key }))}
              >
                {t(cfg.labelKey)}
              </button>
            ))}
          </div>
        </div>
      </Filter>

      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          { key: 'id', header: 'ID', sortable: true, accessor: (r) => r.id },
          { key: 'hotel', header: t('common.hotel'), sortable: true, render: (r) => r.hotel_name || r.hotel },
          { key: 'room', header: t('housekeeping.room'), sortable: true, render: (r) => r.room_name || r.room },
          { key: 'task_type', header: t('housekeeping.task_type'), sortable: true, render: (r) => t(`housekeeping.types.${r.task_type}`) },
          { key: 'assigned_to', header: t('housekeeping.assigned_to'), sortable: true, render: (r) => r.assigned_to_name || '-' },
          { key: 'priority', header: t('housekeeping.priority'), sortable: true, render: (r) => {
              const p = typeof r.priority === 'number' ? r.priority : parseInt(r.priority ?? '1', 10)
              if (p >= 2) return t('housekeeping.priority_high')
              if (p === 1) return t('housekeeping.priority_medium')
              return t('housekeeping.priority_low')
            }
          },
          { key: 'status', header: t('housekeeping.status.title'), sortable: true, render: (r) => {
              const cfg = TASK_STATUS[r.status] || TASK_STATUS.pending
              return <span className={`px-2 py-1 rounded ${cfg.color}`}>{t(cfg.labelKey)}</span>
            }
          },
          {
            key: 'actions',
            header: t('dashboard.reservations_management.table_headers.actions'),
            right: true,
            render: (r) => (
              <div className="flex justify-end items-center gap-x-2">
                {r.status !== 'completed' && r.status !== 'cancelled' && (
                  <button
                    className="px-2 py-1 text-xs rounded bg-blue-600 text-white hover:bg-blue-700"
                    onClick={() => dispatchAction({ action: `housekeeping/tasks/${r.id}/start`, method: 'POST' })}
                    disabled={r.status === 'in_progress'}
                    title={t('housekeeping.start_task')}
                  >
                    {t('housekeeping.start')}
                  </button>
                )}
                {r.status !== 'completed' && r.status !== 'cancelled' && (
                  <button
                    className="px-2 py-1 text-xs rounded bg-emerald-600 text-white hover:bg-emerald-700"
                    onClick={() => dispatchAction({ action: `housekeeping/tasks/${r.id}/complete`, method: 'POST' })}
                    title={t('housekeeping.complete_task')}
                  >
                    {t('housekeeping.complete')}
                  </button>
                )}
                <button
                  className="px-2 py-1 text-xs rounded bg-gray-600 text-white hover:bg-gray-700"
                  onClick={() => { setEditTask(r); setShowModal(true); }}
                >
                  {t('common.edit')}
                </button>
                <DeleteButton resource="housekeeping/tasks" id={r.id} onDeleted={refetch} />
              </div>
            )
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