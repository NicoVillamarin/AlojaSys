import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import { useGet } from 'src/hooks/useGet'
import { useList } from 'src/hooks/useList'
import SpinnerData from 'src/components/SpinnerData'

const ChecklistDetailModal = ({ isOpen, onClose, checklistId }) => {
  const { t } = useTranslation()

  // Obtener el checklist completo
  const { results: checklistData, isPending: loadingChecklist } = useGet({
    resource: 'housekeeping/checklists',
    id: checklistId || null,
    enabled: isOpen && !!checklistId,
  })

  // Obtener los items del checklist
  const { results: checklistItems } = useList({
    resource: 'housekeeping/checklist-items',
    params: { checklist: checklistId },
    enabled: isOpen && !!checklistId,
  })

  const sortedItems = useMemo(() => {
    if (!checklistItems || !Array.isArray(checklistItems)) return []
    return [...checklistItems].sort((a, b) => (a.order || 0) - (b.order || 0))
  }, [checklistItems])

  if (!checklistId) {
    return (
      <ModalLayout isOpen={isOpen} onClose={onClose} title={t('housekeeping.checklist.detail_title')} size="lg">
        <div className="text-center py-8">
          <p className="text-gray-600">{t('housekeeping.checklist.no_checklist')}</p>
        </div>
      </ModalLayout>
    )
  }

  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={onClose}
      title={checklistData?.name || t('housekeeping.checklist.detail_title')}
      size="lg"
      customFooter={
        <div className="flex justify-end w-full">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
          >
            {t('common.close')}
          </button>
        </div>
      }
    >
      {loadingChecklist ? (
        <div className="flex justify-center py-8">
          <SpinnerData />
        </div>
      ) : (
        <div className="space-y-4">
          {checklistData?.description && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">{checklistData.description}</p>
            </div>
          )}

          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">
              {t('housekeeping.checklist.items')} ({sortedItems.length})
            </h3>
            {sortedItems.length > 0 ? (
              sortedItems.map((item, index) => (
                <div
                  key={item.id}
                  className="p-3 border border-gray-200 rounded-lg bg-white hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-semibold">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">{item.name}</span>
                        {item.is_required && (
                          <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded">
                            {t('housekeeping.checklist.required')}
                          </span>
                        )}
                      </div>
                      {item.description && (
                        <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-center text-gray-500 py-4">{t('housekeeping.checklists.no_items')}</p>
            )}
          </div>

          {checklistData && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="grid grid-cols-2 gap-4 text-sm">
                {checklistData.room_type && (
                  <div>
                    <span className="text-gray-600">{t('housekeeping.checklists.room_type')}:</span>
                    <span className="ml-2 font-medium">{t(`rooms_modal.room_types.${checklistData.room_type}`)}</span>
                  </div>
                )}
                {checklistData.task_type && (
                  <div>
                    <span className="text-gray-600">{t('housekeeping.task_type')}:</span>
                    <span className="ml-2 font-medium">{t(`housekeeping.types.${checklistData.task_type}`)}</span>
                  </div>
                )}
                <div>
                  <span className="text-gray-600">{t('housekeeping.checklists.is_default')}:</span>
                  <span className="ml-2 font-medium">{checklistData.is_default ? t('common.yes') : t('common.no')}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </ModalLayout>
  )
}

export default ChecklistDetailModal

