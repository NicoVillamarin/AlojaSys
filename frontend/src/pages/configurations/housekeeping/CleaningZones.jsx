import { useMemo, useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import TableGeneric from 'src/components/TableGeneric'
import { useList } from 'src/hooks/useList'
import { useUserHotels } from 'src/hooks/useUserHotels'
import SelectAsync from 'src/components/selects/SelectAsync'
import { Formik } from 'formik'
import DeleteButton from 'src/components/DeleteButton'
import Button from 'src/components/Button'
import CleaningZoneModal from 'src/components/modals/CleaningZoneModal'
import Filter from 'src/components/Filter'
import EditIcon from 'src/assets/icons/EditIcon'

export default function CleaningZones() {
  const { t } = useTranslation()
  const { hasSingleHotel, singleHotelId } = useUserHotels()
  const [filters, setFilters] = useState({
    hotel: hasSingleHotel ? String(singleHotelId) : '',
  })
  const [showModal, setShowModal] = useState(false)
  const [editZone, setEditZone] = useState(null)
  const didMountRef = useRef(false)

  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: 'housekeeping/zones',
    params: {
      hotel: filters.hotel,
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
  }, [filters.hotel, refetch])

  const displayResults = useMemo(() => results || [], [results])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.configuration')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('housekeeping.zones.title')}</h1>
        </div>
        <Button variant="primary" size="md" onClick={() => { setEditZone(null); setShowModal(true); }}>
          {t('housekeeping.zones.new_zone')}
        </Button>
      </div>

      <CleaningZoneModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        isEdit={!!editZone}
        zone={editZone}
        onSuccess={() => {
          setShowModal(false)
          setEditZone(null)
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
              placeholder={t('common.all')}
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
            { key: 'name', header: t('housekeeping.zones.name'), sortable: true, render: (r) => r.name },
          { key: 'hotel', header: t('common.hotel'), sortable: true, render: (r) => r.hotel_name || r.hotel },
          { key: 'floor', header: t('housekeeping.zones.floor'), sortable: true, render: (r) => r.floor || '-' },
          { key: 'description', header: t('housekeeping.zones.description'), sortable: false, render: (r) => r.description || '-' },
          {
            key: 'actions',
            header: t('dashboard.reservations_management.table_headers.actions'),
            right: true,
            render: (r) => (
              <div className="flex justify-end items-center gap-x-2">
                <EditIcon size="18" onClick={() => { setEditZone(r); setShowModal(true); }} className="cursor-pointer" />
                <DeleteButton resource="housekeeping/zones" id={r.id} onDeleted={refetch} />
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

