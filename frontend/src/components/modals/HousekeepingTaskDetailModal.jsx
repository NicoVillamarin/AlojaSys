import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { format, parseISO } from 'date-fns'
import ModalLayout from 'src/layouts/ModalLayout'
import Badge from 'src/components/Badge'
import { useGet } from 'src/hooks/useGet'
import { useList } from 'src/hooks/useList'

const formatDateTime = (value) => {
  if (!value) return '-'
  try {
    return format(parseISO(value), 'dd/MM/yyyy HH:mm')
  } catch {
    return value
  }
}

const getPriorityLabelKey = (priority) => {
  const p = typeof priority === 'number' ? priority : parseInt(priority ?? '0', 10)
  if (p >= 2) return 'housekeeping.priority_high'
  if (p === 1) return 'housekeeping.priority_medium'
  return 'housekeeping.priority_low'
}

const STATUS_VARIANTS = {
  pending: 'warning',
  in_progress: 'info',
  completed: 'success',
  cancelled: 'error',
}

const HousekeepingTaskDetailModal = ({ isOpen, onClose, taskId }) => {
  const { t } = useTranslation()

  const { results: task, isPending: loadingTask } = useGet({
    resource: 'housekeeping/tasks',
    id: taskId || null,
    enabled: isOpen && !!taskId,
  })

  const { results: checklistCompletionsRaw, isPending: loadingChecklist } = useList({
    resource: 'housekeeping/task-checklist-completions',
    params: { task: taskId },
    enabled: isOpen && !!taskId,
  })

  const checklistCompletions = useMemo(() => {
    if (!Array.isArray(checklistCompletionsRaw)) return []
    return [...checklistCompletionsRaw].sort((a, b) =>
      (a.checklist_item_name || '').localeCompare(b.checklist_item_name || '')
    )
  }, [checklistCompletionsRaw])

  const title = task
    ? `${t('housekeeping.task_type')}: ${t(`housekeeping.types.${task.task_type}`)} · Tarea N° ${task.id}`
    : t('housekeeping.modal.create_title')

  if (!isOpen) return null

  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="lg"
      isDetail={true}
      customFooter={
        <div className="flex justify-end w-full">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm"
          >
            {t('common.close')}
          </button>
        </div>
      }
    >
      {loadingTask ? (
        <div className="py-8 text-center text-gray-500 text-sm">
          {t('common.loading')}
        </div>
      ) : !task ? (
        <div className="py-8 text-center text-gray-500 text-sm">
          {t('common.no_data', 'No hay datos para esta tarea')}
        </div>
      ) : (
        <div className="space-y-6">
          {/* Información principal */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div>
                <div className="text-xs font-medium text-gray-500">{t('common.hotel')}</div>
                <div className="text-sm text-gray-900 font-medium">
                  {task.hotel_name || task.hotel || '-'}
                </div>
              </div>
              <div>
                <div className="text-xs font-medium text-gray-500">{t('housekeeping.room')}</div>
                <div className="text-sm text-gray-900 font-medium">
                  {task.room_name || task.room || '-'}
                </div>
              </div>
              <div>
                <div className="text-xs font-medium text-gray-500">{t('housekeeping.assigned_to')}</div>
                <div className="text-sm text-gray-900">
                  {task.assigned_to_name || t('common.none', 'Sin asignar')}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="text-xs font-medium text-gray-500">{t('housekeeping.status.title')}</div>
                <Badge
                  variant={STATUS_VARIANTS[task.status] || 'default'}
                  size="sm"
                >
                  {t(`housekeeping.status.${task.status}`)}
                </Badge>
                {task.is_overdue && (
                  <Badge variant="error" size="sm">
                    {t('housekeeping.status.overdue')}
                  </Badge>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <div>
                <div className="text-xs font-medium text-gray-500">{t('housekeeping.priority')}</div>
                <div className="text-sm text-gray-900">
                  {t(getPriorityLabelKey(task.priority))}
                </div>
              </div>
              <div>
                <div className="text-xs font-medium text-gray-500">{t('housekeeping.zone')}</div>
                <div className="text-sm text-gray-900">
                  {task.zone || '-'}
                </div>
              </div>
              <div>
                <div className="text-xs font-medium text-gray-500">{t('housekeeping.templates.estimated_minutes')}</div>
                <div className="text-sm text-gray-900">
                  {task.estimated_minutes != null ? `${task.estimated_minutes} min` : '-'}
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs text-gray-600">
                <div>
                  <div className="font-medium">{t('common.created_at')}</div>
                  <div>{formatDateTime(task.created_at)}</div>
                </div>
                <div>
                  <div className="font-medium">{t('housekeeping.history.started_at')}</div>
                  <div>{formatDateTime(task.started_at)}</div>
                </div>
                <div>
                  <div className="font-medium">{t('housekeeping.history.completed_at')}</div>
                  <div>{formatDateTime(task.completed_at)}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Descripción de la tarea */}
          <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
            <div className="text-xs font-semibold text-gray-700 mb-1 uppercase">
              {t('housekeeping.notes')}
            </div>
            <div className="text-sm text-gray-800 whitespace-pre-line">
              {task.notes || t('housekeeping.notes_placeholder')}
            </div>
          </div>

          {/* Checklist (si existe) */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs font-semibold text-gray-700 uppercase">
                {t('housekeeping.checklists.title')}
              </div>
              <div className="text-xs text-gray-500">
                {task.checklist_name
                  ? task.checklist_name
                  : t('housekeeping.checklist.no_checklist')}
              </div>
            </div>

            {loadingChecklist ? (
              <div className="py-4 text-center text-gray-500 text-sm">
                {t('common.loading')}
              </div>
            ) : !task.checklist_name || checklistCompletions.length === 0 ? (
              <p className="text-xs text-gray-500">
                {t(
                  'housekeeping.checklist.no_checklist',
                  'Esta tarea no usa checklist. Se gestiona solo con descripción y estado.'
                )}
              </p>
            ) : (
              <div className="space-y-2">
                {checklistCompletions.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-start justify-between gap-3 border border-gray-100 rounded-lg px-3 py-2"
                  >
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {item.checklist_item_name}
                      </div>
                      {item.notes && (
                        <div className="text-xs text-gray-600 mt-0.5">
                          {item.notes}
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <Badge
                        variant={item.completed ? 'success' : 'default'}
                        size="sm"
                      >
                        {item.completed
                          ? t('housekeeping.status.completed')
                          : t('housekeeping.status.pending')}
                      </Badge>
                      {item.completed_at && (
                        <span className="text-[10px] text-gray-500">
                          {formatDateTime(item.completed_at)}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </ModalLayout>
  )
}

export default HousekeepingTaskDetailModal


