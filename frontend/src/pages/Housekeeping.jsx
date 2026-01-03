import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { format, parseISO } from 'date-fns'
import Button from 'src/components/Button'
import TableGeneric from 'src/components/TableGeneric'
import Filter from 'src/components/Filter'
import { useList } from 'src/hooks/useList'
import { useUserHotels } from 'src/hooks/useUserHotels'
import SelectAsync from 'src/components/selects/SelectAsync'
import SelectStandalone from 'src/components/selects/SelectStandalone'
import { Formik } from 'formik'
import DeleteButton from 'src/components/DeleteButton'
import HousekeepingModal from 'src/components/modals/HousekeepingModal'
import ChecklistDetailModal from 'src/components/modals/ChecklistDetailModal'
import HousekeepingTaskDetailModal from 'src/components/modals/HousekeepingTaskDetailModal'
import { useDispatchAction } from 'src/hooks/useDispatchAction'
import EditIcon from 'src/assets/icons/EditIcon'
import ClockIcon from 'src/assets/icons/ClockIcon'
import CheckIcon from 'src/assets/icons/CheckIcon'
import CancelIcon from 'src/assets/icons/CancelIcon'
import Tooltip from 'src/components/Tooltip'
import Badge from 'src/components/Badge'
import { usePermissions } from 'src/hooks/usePermissions'
import { usePlanFeatures } from 'src/hooks/usePlanFeatures'

const TASK_STATUS = {
  pending: { labelKey: 'housekeeping.status.pending', variant: 'warning' },
  in_progress: { labelKey: 'housekeeping.status.in_progress', variant: 'info' },
  completed: { labelKey: 'housekeeping.status.completed', variant: 'success' },
  cancelled: { labelKey: 'housekeeping.status.cancelled', variant: 'error' },
}

const ACTIVE_STATUS_KEYS = ['pending', 'in_progress']

export default function Housekeeping() {
  const { t } = useTranslation()
  const { hasSingleHotel, singleHotelId } = useUserHotels()
  const { housekeepingEnabled } = usePlanFeatures()
  
  // Verificar permisos
  const canAccessHousekeeping = usePermissions("housekeeping.access_housekeeping")
  const canAddTask = usePermissions("housekeeping.add_housekeepingtask")
  const canChangeTask = usePermissions("housekeeping.change_housekeepingtask")
  const canDeleteTask = usePermissions("housekeeping.delete_housekeepingtask")
  
  const [filters, setFilters] = useState({
    hotel: hasSingleHotel ? String(singleHotelId) : '',
    status: '',
    assigned_to: '',
  })
  const [showModal, setShowModal] = useState(false)
  const [editTask, setEditTask] = useState(null)
  const [showChecklistDetail, setShowChecklistDetail] = useState(false)
  const [selectedChecklistId, setSelectedChecklistId] = useState(null)
  const [showTaskDetail, setShowTaskDetail] = useState(false)
  const [selectedTaskId, setSelectedTaskId] = useState(null)

  // Memoizar params para que no cambie en cada render
  const listParams = useMemo(() => ({
    hotel: filters.hotel || undefined,
    status: filters.status ? filters.status : ACTIVE_STATUS_KEYS.join(','),
    assigned_to: filters.assigned_to || undefined,
    page_size: 100,
  }), [filters.hotel, filters.status, filters.assigned_to])

  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'housekeeping/tasks',
    params: listParams,
    enabled: canAccessHousekeeping,
  })

  // Acciones start/complete
  const { mutate: dispatchAction } = useDispatchAction({
    resource: 'housekeeping/tasks',
    onSuccess: () => refetch(),
  })

  const displayResults = useMemo(
    () => (results || []).filter((task) => ACTIVE_STATUS_KEYS.includes(task.status)),
    [results]
  )

  if (!housekeepingEnabled) {
    return (
      <div className="p-6 text-center text-gray-600">
        {t('housekeeping.not_enabled', 'El módulo de housekeeping no está habilitado en tu plan.')}
      </div>
    )
  }

  if (!canAccessHousekeeping) {
    return (
      <div className="p-6 text-center text-gray-600">
        {t('housekeeping.no_permission', 'No tenés permiso para acceder a las tareas de housekeeping.')}
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.housekeeping')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('housekeeping.title')}</h1>
        </div>
        {canAddTask && (
          <Button variant="primary" size="md" onClick={() => { setEditTask(null); setShowModal(true); }}>
            {t('housekeeping.new_task')}
          </Button>
        )}
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
            {ACTIVE_STATUS_KEYS.map((key) => {
              const cfg = TASK_STATUS[key]
              return (
              <button
                key={key}
                className={`px-3 py-1.5 rounded text-xs border ${filters.status === key ? 'bg-aloja-navy text-white border-aloja-navy' : 'bg-white text-aloja-navy border-aloja-navy/30'}`}
                onClick={() => setFilters((f) => ({ ...f, status: key }))}
              >
                {t(cfg.labelKey)}
              </button>
              )
            })}
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
            accessor: (r) => r.id,
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
              return (
                <div className="inline-flex items-center gap-2 flex-wrap">
                  <Badge variant={cfg.variant} size="sm">{t(cfg.labelKey)}</Badge>
                  {r.is_overdue && (
                    <Badge variant="error" size="sm" className="bg-red-100 text-red-700">
                      {t('housekeeping.status.overdue')}
                    </Badge>
                  )}
                </div>
              )
            }
          },
          {
            key: 'created_at',
            header: t('common.created_at'),
            sortable: true,
            accessor: (r) => r.created_at ? format(parseISO(r.created_at), 'dd/MM/yyyy HH:mm') : '',
            render: (r) => r.created_at ? format(parseISO(r.created_at), 'dd/MM/yyyy HH:mm') : '-',
          },
          { 
            key: 'checklist', 
            header: t('housekeeping.checklists.title'), 
            sortable: false, 
            render: (r) => {
              if (!r.checklist_name && !r.checklist) return '-'
              const hasChecklist = !!(r.checklist || r.checklist_id)
              return (
                <div className="flex items-center gap-2">
                  {hasChecklist ? (
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
                  )}
                </div>
              )
            }
          },
          {
            key: 'actions',
            header: t('dashboard.reservations_management.table_headers.actions'),
            right: true,
            render: (r) => {
              // Si no tiene permisos de cambio o eliminación, no mostrar acciones
              if (!canChangeTask && !canDeleteTask) {
                return null
              }
              
              return (
                <div className="flex justify-end items-center gap-x-2">
                  {/* Botón Iniciar: solo cuando está pendiente y tiene permiso de cambio */}
                  {r.status === 'pending' && canChangeTask && (
                    <Tooltip content={t('housekeeping.start_task')} position="bottom">
                      <button
                        onClick={() => dispatchAction({ action: `${r.id}/start`, method: 'POST' })}
                        className="cursor-pointer"
                      >
                        <ClockIcon className="w-5 h-5 text-blue-600 hover:text-blue-800" />
                      </button>
                    </Tooltip>
                  )}
                  {/* Botón Completar: cuando está pendiente o en progreso y tiene permiso de cambio */}
                  {(r.status === 'pending' || r.status === 'in_progress') && canChangeTask && (
                    <Tooltip content={t('housekeeping.complete_task')} position="bottom">
                      <button
                        onClick={() => dispatchAction({ action: `${r.id}/complete`, method: 'POST' })}
                        className="cursor-pointer text-emerald-600 hover:text-emerald-800"
                      >
                        <CheckIcon size="18" />
                      </button>
                    </Tooltip>
                  )}
                  {/* Botón Cancelar: cuando está pendiente o en progreso y tiene permiso de cambio */}
                  {(r.status === 'pending' || r.status === 'in_progress') && canChangeTask && (
                    <Tooltip content={t('housekeeping.cancel_task')} position="bottom">
                      <button
                        onClick={() => dispatchAction({ action: `${r.id}/cancel`, method: 'POST' })}
                        className="cursor-pointer text-rose-600 hover:text-rose-800"
                      >
                        <CancelIcon size="18" />
                      </button>
                    </Tooltip>
                  )}
                  {/* Botón Editar: solo cuando está pendiente y tiene permiso de cambio */}
                  {r.status === 'pending' && canChangeTask && (
                    <Tooltip content={t('common.edit')} position="bottom">
                      <EditIcon 
                        size="18" 
                        onClick={() => { setEditTask(r); setShowModal(true); }} 
                        className="cursor-pointer" 
                      />
                    </Tooltip>
                  )}
                  {/* Botón Eliminar: solo cuando está pendiente y tiene permiso de eliminación */}
                  {r.status === 'pending' && canDeleteTask && (
                    <Tooltip content={t('common.delete')} position="bottom">
                      <div>
                        <DeleteButton resource="housekeeping/tasks" id={r.id} onDeleted={refetch} />
                      </div>
                    </Tooltip>
                  )}
                </div>
              )
            }
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
