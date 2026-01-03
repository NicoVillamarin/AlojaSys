import { useMemo, useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import { useUserHotels } from 'src/hooks/useUserHotels'
import SelectAsync from 'src/components/selects/SelectAsync'
import { Formik } from 'formik'
import DeleteButton from 'src/components/DeleteButton'
import Button from 'src/components/Button'
import CleaningStaffModal from 'src/components/modals/CleaningStaffModal'
import Filter from 'src/components/Filter'
import EditIcon from 'src/assets/icons/EditIcon'
import { usePlanFeatures } from 'src/hooks/usePlanFeatures'

export default function CleaningStaff() {
  const { t } = useTranslation()
  const { hasSingleHotel, singleHotelId } = useUserHotels()
  const { housekeepingEnabled } = usePlanFeatures()
  const [filters, setFilters] = useState({
    hotel: hasSingleHotel ? String(singleHotelId) : '',
  })
  const [showModal, setShowModal] = useState(false)
  const [editStaff, setEditStaff] = useState(null)
  const didMountRef = useRef(false)

  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'housekeeping/staff',
    params: {
      hotel: filters.hotel || undefined,
      page_size: 100,
    },
    enabled: housekeepingEnabled,
  })

  if (!housekeepingEnabled) {
    return (
      <div className="p-6 text-center text-gray-600">
        {t('housekeeping.not_enabled', 'El módulo de housekeeping no está habilitado en tu plan.')}
      </div>
    )
  }

  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true
      return
    }
    const id = setTimeout(() => refetch(), 350)
    return () => clearTimeout(id)
  }, [filters.hotel, refetch])

  const displayResults = useMemo(() => results || [], [results])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.configuration')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('housekeeping.staff.title')}</h1>
        </div>
        <Button variant="primary" size="md" onClick={() => { setEditStaff(null); setShowModal(true); }}>
          {t('housekeeping.staff.new_staff')}
        </Button>
      </div>

      <CleaningStaffModal
        isOpen={showModal}
        onClose={() => {
          setShowModal(false)
          setEditStaff(null)
        }}
        isEdit={!!editStaff}
        staff={editStaff}
        onSuccess={() => {
          setShowModal(false)
          setEditStaff(null)
          refetch()
        }}
      />

      <Filter>
        <div className="grid grid-cols-1 lg:grid-cols-1 gap-3">
          <Formik enableReinitialize initialValues={{}} onSubmit={() => {}}>
            <SelectAsync
              title={t('common.hotel')}
              name="hotel"
              resource="hotels"
              placeholder={t('common.select_placeholder')}
              getOptionLabel={(h) => h?.name}
              getOptionValue={(h) => h?.id}
              onValueChange={(opt, val) => setFilters((f) => ({ ...f, hotel: String(val || '') }))}
              autoSelectSingle
            />
          </Formik>
        </div>
      </Filter>

      <TableGeneric
        isLoading={isPending}
        data={displayResults}
        getRowId={(r) => r.id}
        columns={[
          { key: 'id', header: 'ID', sortable: true, accessor: (r) => r.id },
          { key: 'first_name', header: t('housekeeping.staff.first_name'), sortable: true, render: (r) => r.first_name },
          { key: 'last_name', header: t('housekeeping.staff.last_name'), sortable: true, render: (r) => r.last_name || '-' },
          { key: 'hotel', header: t('common.hotel'), sortable: true, render: (r) => r.hotel_name || r.hotel },
          { 
            key: 'shift', 
            header: t('housekeeping.staff.shift'), 
            sortable: true, 
            render: (r) => r.shift_display || r.shift || '-' 
          },
          {
            key: 'work_hours',
            header: t('housekeeping.staff.work_hours'),
            sortable: false,
            render: (r) => {
              if (r.work_start_time && r.work_end_time) {
                return `${r.work_start_time} - ${r.work_end_time}`
              }
              return '-'
            }
          },
          {
            key: 'zones',
            header: t('housekeeping.staff.zones'),
            sortable: false,
            render: (r) => {
              if (r.cleaning_zones && r.cleaning_zones.length > 0) {
                return r.cleaning_zones.map(z => z.name).join(', ')
              }
              return r.zone || '-'
            }
          },
          {
            key: 'is_active',
            header: t('common.active'),
            sortable: true,
            render: (r) => (
              <span className={`px-2 py-1 rounded ${r.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-700'}`}>
                {r.is_active ? t('common.yes') : t('common.no')}
              </span>
            )
          },
          {
            key: 'actions',
            header: t('dashboard.reservations_management.table_headers.actions'),
            right: true,
            render: (r) => (
              <div className="flex justify-end items-center gap-x-2">
                <EditIcon size="18" onClick={() => { setEditStaff(r); setShowModal(true); }} className="cursor-pointer" />
                <DeleteButton resource="housekeeping/staff" id={r.id} onDeleted={refetch} />
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

