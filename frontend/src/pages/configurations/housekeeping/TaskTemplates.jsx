import { useMemo, useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import { useUserHotels } from 'src/hooks/useUserHotels'
import SelectAsync from 'src/components/selects/SelectAsync'
import SelectStandalone from 'src/components/selects/SelectStandalone'
import { Formik } from 'formik'
import DeleteButton from 'src/components/DeleteButton'
import Button from 'src/components/Button'
import TaskTemplateModal from 'src/components/modals/TaskTemplateModal'
import Filter from 'src/components/Filter'
import EditIcon from 'src/assets/icons/EditIcon'

export default function TaskTemplates() {
  const { t } = useTranslation()
  const { hasSingleHotel, singleHotelId } = useUserHotels()
  const [filters, setFilters] = useState({
    hotel: hasSingleHotel ? String(singleHotelId) : '',
    room_type: '',
    task_type: '',
  })
  const [showModal, setShowModal] = useState(false)
  const [editTemplate, setEditTemplate] = useState(null)
  const didMountRef = useRef(false)

  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'housekeeping/templates',
    params: {
      hotel: filters.hotel,
      room_type: filters.room_type || undefined,
      task_type: filters.task_type || undefined,
      page_size: 100,
    },
  })

  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true
      return
    }
    const id = setTimeout(() => refetch(), 350)
    return () => clearTimeout(id)
  }, [filters.hotel, filters.room_type, filters.task_type, refetch])

  const displayResults = useMemo(() => results || [], [results])

  const ROOM_TYPES = [
    { value: 'single', label: t('rooms_modal.room_types.single') },
    { value: 'double', label: t('rooms_modal.room_types.double') },
    { value: 'triple', label: t('rooms_modal.room_types.triple') },
    { value: 'suite', label: t('rooms_modal.room_types.suite') },
  ]

  const TASK_TYPES = [
    { value: 'daily', label: t('housekeeping.types.daily') },
    { value: 'checkout', label: t('housekeeping.types.checkout') },
    { value: 'maintenance', label: t('housekeeping.types.maintenance') },
  ]

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.configuration')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('housekeeping.templates.title')}</h1>
          <p className="mt-1 text-xs text-aloja-gray-800/70">
            {t('housekeeping.config.manage_templates_desc')}
          </p>
        </div>
        <Button variant="primary" size="md" onClick={() => { setEditTemplate(null); setShowModal(true); }}>
          {t('housekeeping.templates.new_template')}
        </Button>
      </div>

      <TaskTemplateModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        isEdit={!!editTemplate}
        template={editTemplate}
        onSuccess={() => {
          setShowModal(false)
          setEditTemplate(null)
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
          <SelectStandalone
            title={t('housekeeping.templates.room_type')}
            value={
              filters.room_type
                ? ROOM_TYPES.find((rt) => rt.value === filters.room_type)
                : null
            }
            onChange={(opt) => setFilters((f) => ({ ...f, room_type: opt ? opt.value : '' }))}
            options={ROOM_TYPES}
            placeholder={t('common.all')}
            isClearable
            isSearchable={false}
          />
          <SelectStandalone
            title={t('housekeeping.task_type')}
            value={
              filters.task_type
                ? TASK_TYPES.find((tt) => tt.value === filters.task_type)
                : null
            }
            onChange={(opt) => setFilters((f) => ({ ...f, task_type: opt ? opt.value : '' }))}
            options={TASK_TYPES}
            placeholder={t('common.all')}
            isClearable
            isSearchable={false}
          />
        </div>
      </Filter>

      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          { key: 'id', header: 'ID', sortable: true, accessor: (r) => r.id },
          { key: 'hotel', header: t('common.hotel'), sortable: true, render: (r) => r.hotel_name || r.hotel },
          { key: 'room_type', header: t('housekeeping.templates.room_type'), sortable: true, render: (r) => t(`rooms_modal.room_types.${r.room_type}`) },
          { key: 'task_type', header: t('housekeeping.task_type'), sortable: true, render: (r) => t(`housekeeping.types.${r.task_type}`) },
          { key: 'name', header: t('housekeeping.templates.name'), sortable: true, render: (r) => r.name },
          { key: 'estimated_minutes', header: t('housekeeping.templates.estimated_minutes'), sortable: true, render: (r) => `${r.estimated_minutes} min` },
          { key: 'is_required', header: t('housekeeping.templates.is_required'), sortable: true, render: (r) => r.is_required ? t('common.yes') : t('common.no') },
          {
            key: 'actions',
            header: t('dashboard.reservations_management.table_headers.actions'),
            right: true,
            render: (r) => (
              <div className="flex justify-end items-center gap-x-2">
                <EditIcon size="18" onClick={() => { setEditTemplate(r); setShowModal(true); }} className="cursor-pointer" />
                <DeleteButton resource="housekeeping/templates" id={r.id} onDeleted={refetch} />
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

