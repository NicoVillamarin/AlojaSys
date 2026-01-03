import { useMemo, useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useUserHotels } from 'src/hooks/useUserHotels'
import SelectAsync from 'src/components/selects/SelectAsync'
import { Formik } from 'formik'
import Button from 'src/components/Button'
import Filter from 'src/components/Filter'
import { useAction } from 'src/hooks/useAction'
import { useUpdate } from 'src/hooks/useUpdate'
import { Link } from 'react-router-dom'
import HelpTooltip from 'src/components/HelpTooltip'
import { usePlanFeatures } from 'src/hooks/usePlanFeatures'

export default function HousekeepingConfig() {
  const { t } = useTranslation()
  const { hasSingleHotel, singleHotelId } = useUserHotels()
  const { housekeepingEnabled } = usePlanFeatures()
  const [selectedHotel, setSelectedHotel] = useState(hasSingleHotel ? String(singleHotelId) : '')
  const didMountRef = useRef(false)

  const { results: hkConfig, isPending: hkLoading, refetch: refetchHK } = useAction({
    resource: 'housekeeping/config',
    action: selectedHotel ? `by-hotel/${selectedHotel}` : undefined,
    enabled: housekeepingEnabled && !!selectedHotel,
  })

  const [hkValues, setHkValues] = useState(null)
  useEffect(() => {
    if (!hkConfig) return
    setHkValues((prev) => {
      // Si ya tenemos la misma config (por id), no volver a setear para evitar loops
      if (prev && prev.id === hkConfig.id) {
        return prev
      }
      return hkConfig
    })
  }, [hkConfig])

  const { mutate: updateHK, isPending: savingHK } = useUpdate({
    resource: 'housekeeping/config',
    onSuccess: () => {
      refetchHK && refetchHK()
    },
    method: 'PATCH',
  })

  if (!housekeepingEnabled) {
    return (
      <div className="p-6 text-center text-gray-600">
        {t('housekeeping.not_enabled', 'El módulo de housekeeping no está habilitado en tu plan.')}
      </div>
    )
  }

  const handleSaveHK = () => {
    if (!hkValues?.id) return
    const payload = {
      use_checklists: hkValues.use_checklists !== false,
      enable_auto_assign: !!hkValues.enable_auto_assign,
      create_daily_tasks: !!hkValues.create_daily_tasks,
      daily_for_all_rooms: !!hkValues.daily_for_all_rooms,
      daily_generation_time: hkValues.daily_generation_time || null,
      skip_service_on_checkin: !!hkValues.skip_service_on_checkin,
      skip_service_on_checkout: !!hkValues.skip_service_on_checkout,
      linens_every_n_nights: Number(hkValues.linens_every_n_nights ?? 3),
      towels_every_n_nights: Number(hkValues.towels_every_n_nights ?? 1),
      morning_window_start: hkValues.morning_window_start || null,
      morning_window_end: hkValues.morning_window_end || null,
      afternoon_window_start: hkValues.afternoon_window_start || null,
      afternoon_window_end: hkValues.afternoon_window_end || null,
      quiet_hours_start: hkValues.quiet_hours_start || null,
      quiet_hours_end: hkValues.quiet_hours_end || null,
      prefer_by_zone: !!hkValues.prefer_by_zone,
      rebalance_every_minutes: Number(hkValues.rebalance_every_minutes ?? 5),
      checkout_priority: Number(hkValues.checkout_priority ?? 2),
      daily_priority: Number(hkValues.daily_priority ?? 1),
      alert_checkout_unstarted_minutes: Number(hkValues.alert_checkout_unstarted_minutes ?? 30),
      max_task_duration_minutes: Number(hkValues.max_task_duration_minutes ?? 120),
      auto_complete_overdue: !!hkValues.auto_complete_overdue,
      overdue_grace_minutes: Number(hkValues.overdue_grace_minutes ?? 30),
    }
    updateHK({ id: hkValues.id, body: payload })
  }

  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true
      return
    }
    if (selectedHotel) {
      refetchHK()
    }
  }, [selectedHotel, refetchHK])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">{t('sidebar.configuration')}</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">{t('housekeeping.config.title')}</h1>
        </div>
      </div>

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
              onValueChange={(opt, val) => setSelectedHotel(String(val || ''))}
              autoSelectSingle
            />
          </Formik>
        </div>
      </Filter>

      {selectedHotel && (
        <div className="space-y-5">
          {/* Enlaces rápidos a recursos */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-aloja-gray-800 mb-3">{t('housekeeping.config.manage_resources')}</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Link
                to="/settings/housekeeping/zones"
                className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="text-sm font-medium text-aloja-gray-800">{t('housekeeping.zones.title')}</div>
                <div className="text-xs text-aloja-gray-600 mt-1">{t('housekeeping.config.manage_zones_desc')}</div>
              </Link>
              <Link
                to="/settings/housekeeping/templates"
                className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="text-sm font-medium text-aloja-gray-800">{t('housekeeping.templates.title')}</div>
                <div className="text-xs text-aloja-gray-600 mt-1">{t('housekeeping.config.manage_templates_desc')}</div>
              </Link>
              <Link
                to="/settings/housekeeping/checklists"
                className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="text-sm font-medium text-aloja-gray-800">{t('housekeeping.checklists.title')}</div>
                <div className="text-xs text-aloja-gray-600 mt-1">{t('housekeeping.config.manage_checklists_desc')}</div>
              </Link>
            </div>
          </div>

          {/* Configuración del hotel */}
          {hkLoading ? (
            <div className="text-center py-8 text-gray-500">{t('common.loading')}</div>
          ) : hkValues ? (
            <div className="bg-white border border-gray-200 rounded-lg p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-aloja-gray-800">{t('housekeeping.config.settings')}</h3>
                <Button
                  variant="primary"
                  size="sm"
                  disabled={savingHK}
                  onClick={handleSaveHK}
                  loadingText={savingHK}
                >
                  {t('common.save')}
                </Button>
              </div>

              <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5'>
                {/* Activación y generación */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <h4 className="text-xs font-semibold text-aloja-gray-800/70 uppercase">{t('housekeeping.config.automation')}</h4>
                    <HelpTooltip text={t('housekeeping.config.automation_help')} />
                  </div>
                  <label className='flex items-center gap-2 cursor-pointer'>
                    <input
                      type='checkbox'
                      className='rounded border-gray-300'
                      checked={!!hkValues?.enable_auto_assign}
                      onChange={(e) => setHkValues((v) => ({ ...v, enable_auto_assign: e.target.checked }))}
                    />
                    <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.housekeeping.enable_auto_assign')}</span>
                  </label>
                  {/* Modo de uso: simple vs avanzado */}
                  <div className="flex items-center gap-2 mt-2">
                    <h4 className="text-xs font-semibold text-aloja-gray-800/70 uppercase">{t('housekeeping.config.mode')}</h4>
                    <HelpTooltip text={t('housekeeping.config.mode_help')} />
                  </div>
                  <label className='flex items-start gap-2 cursor-pointer'>
                    <input
                      type='checkbox'
                      className='mt-1 rounded border-gray-300'
                      checked={hkValues?.use_checklists !== false}
                      onChange={(e) => setHkValues((v) => ({ ...v, use_checklists: e.target.checked }))}
                    />
                    <div className="flex flex-col">
                      <span className='text-sm text-aloja-gray-800/80'>
                        {t('hotels_modal.housekeeping.use_checklists')}
                      </span>
                    </div>
                  </label>
              <label className='flex items-center gap-2 cursor-pointer'>
                <input
                  type='checkbox'
                  className='rounded border-gray-300'
                  checked={!!hkValues?.daily_for_all_rooms}
                  onChange={(e) => setHkValues((v) => ({ ...v, daily_for_all_rooms: e.target.checked }))}
                />
                <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.housekeeping.daily_for_all_rooms')}</span>
                  </label>
                  <label className='flex items-center gap-2 cursor-pointer'>
                    <input
                      type='checkbox'
                      className='rounded border-gray-300'
                      checked={!!hkValues?.create_daily_tasks}
                      onChange={(e) => setHkValues((v) => ({ ...v, create_daily_tasks: e.target.checked }))}
                    />
                    <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.housekeeping.create_daily_tasks')}</span>
                  </label>
                  <div>
                    <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.daily_generation_time')}</label>
                    <input
                      type='time'
                      className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                      value={hkValues?.daily_generation_time || ''}
                      onChange={(e) => setHkValues((v) => ({ ...v, daily_generation_time: e.target.value }))}
                    />
                  </div>
                </div>

                {/* Reglas de servicio */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                  <h4 className="text-xs font-semibold text-aloja-gray-800/70 uppercase">{t('housekeeping.config.service_rules')}</h4>
                    <HelpTooltip text={t('housekeeping.config.service_rules_help')} />
                  </div>
                  <label className='flex items-center gap-2 cursor-pointer'>
                    <input
                      type='checkbox'
                      className='rounded border-gray-300'
                      checked={!!hkValues?.skip_service_on_checkin}
                      onChange={(e) => setHkValues((v) => ({ ...v, skip_service_on_checkin: e.target.checked }))}
                    />
                    <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.housekeeping.skip_service_on_checkin')}</span>
                  </label>
                  <label className='flex items-center gap-2 cursor-pointer'>
                    <input
                      type='checkbox'
                      className='rounded border-gray-300'
                      checked={!!hkValues?.skip_service_on_checkout}
                      onChange={(e) => setHkValues((v) => ({ ...v, skip_service_on_checkout: e.target.checked }))}
                    />
                    <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.housekeeping.skip_service_on_checkout')}</span>
                  </label>
                  <div>
                    <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.linens_every')}</label>
                    <input
                      type='number'
                      className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                      value={hkValues?.linens_every_n_nights ?? 3}
                      onChange={(e) => setHkValues((v) => ({ ...v, linens_every_n_nights: e.target.value }))}
                      placeholder='3'
                    />
                  </div>
                  <div>
                    <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.towels_every')}</label>
                    <input
                      type='number'
                      className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                      value={hkValues?.towels_every_n_nights ?? 1}
                      onChange={(e) => setHkValues((v) => ({ ...v, towels_every_n_nights: e.target.value }))}
                      placeholder='1'
                    />
                  </div>
                </div>

                {/* Ventanas de tiempo */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                  <h4 className="text-xs font-semibold text-aloja-gray-800/70 uppercase">{t('housekeeping.config.time_windows')}</h4>
                    <HelpTooltip text={t('housekeeping.config.time_windows_help')} />
                  </div>
                  <div>
                    <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.morning_window_start')}</label>
                    <input
                      type='time'
                      className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                      value={hkValues?.morning_window_start || ''}
                      onChange={(e) => setHkValues((v) => ({ ...v, morning_window_start: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.morning_window_end')}</label>
                    <input
                      type='time'
                      className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                      value={hkValues?.morning_window_end || ''}
                      onChange={(e) => setHkValues((v) => ({ ...v, morning_window_end: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.afternoon_window_start')}</label>
                    <input
                      type='time'
                      className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                      value={hkValues?.afternoon_window_start || ''}
                      onChange={(e) => setHkValues((v) => ({ ...v, afternoon_window_start: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.afternoon_window_end')}</label>
                    <input
                      type='time'
                      className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                      value={hkValues?.afternoon_window_end || ''}
                      onChange={(e) => setHkValues((v) => ({ ...v, afternoon_window_end: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.quiet_hours_start')}</label>
                    <input
                      type='time'
                      className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                      value={hkValues?.quiet_hours_start || ''}
                      onChange={(e) => setHkValues((v) => ({ ...v, quiet_hours_start: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.quiet_hours_end')}</label>
                    <input
                      type='time'
                      className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                      value={hkValues?.quiet_hours_end || ''}
                      onChange={(e) => setHkValues((v) => ({ ...v, quiet_hours_end: e.target.value }))}
                    />
                  </div>
                </div>

                {/* Asignación y prioridades */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                  <h4 className="text-xs font-semibold text-aloja-gray-800/70 uppercase">{t('housekeeping.config.assignment_priorities')}</h4>
                    <HelpTooltip text={t('housekeeping.config.assignment_priorities_help')} />
                  </div>
                  <label className='flex items-center gap-2 cursor-pointer'>
                    <input
                      type='checkbox'
                      className='rounded border-gray-300'
                      checked={!!hkValues?.prefer_by_zone}
                      onChange={(e) => setHkValues((v) => ({ ...v, prefer_by_zone: e.target.checked }))}
                    />
                    <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.housekeeping.prefer_by_zone')}</span>
                  </label>
                  <div>
                    <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.rebalance_every_minutes')}</label>
                    <input
                      type='number'
                      className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                      value={hkValues?.rebalance_every_minutes ?? 5}
                      onChange={(e) => setHkValues((v) => ({ ...v, rebalance_every_minutes: e.target.value }))}
                      placeholder='5'
                    />
                  </div>
                  <div>
                    <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.checkout_priority')}</label>
                    <select
                      className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                      value={hkValues?.checkout_priority ?? 2}
                      onChange={(e) => setHkValues((v) => ({ ...v, checkout_priority: Number(e.target.value) }))}
                    >
                      <option value={2}>{t('housekeeping.priority_high')}</option>
                      <option value={1}>{t('housekeeping.priority_medium')}</option>
                      <option value={0}>{t('housekeeping.priority_low')}</option>
                    </select>
                  </div>
                  <div>
                    <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.daily_priority')}</label>
                    <select
                      className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                      value={hkValues?.daily_priority ?? 1}
                      onChange={(e) => setHkValues((v) => ({ ...v, daily_priority: Number(e.target.value) }))}
                    >
                      <option value={2}>{t('housekeeping.priority_high')}</option>
                      <option value={1}>{t('housekeeping.priority_medium')}</option>
                      <option value={0}>{t('housekeeping.priority_low')}</option>
                    </select>
                  </div>
                  <div>
                    <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.alert_checkout_unstarted_minutes')}</label>
                    <input
                      type='number'
                      className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                      value={hkValues?.alert_checkout_unstarted_minutes ?? 30}
                      onChange={(e) => setHkValues((v) => ({ ...v, alert_checkout_unstarted_minutes: e.target.value }))}
                      placeholder='30'
                    />
                  </div>
                </div>

                {/* Vencimiento de tareas */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                  <h4 className="text-xs font-semibold text-aloja-gray-800/70 uppercase">{t('housekeeping.config.task_timeout')}</h4>
                    <HelpTooltip text={t('housekeeping.config.task_timeout_help')} />
                  </div>
                  <div>
                    <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.max_task_duration_minutes')}</label>
                    <input
                      type='number'
                      className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                      value={hkValues?.max_task_duration_minutes ?? 120}
                      onChange={(e) => setHkValues((v) => ({ ...v, max_task_duration_minutes: e.target.value }))}
                      placeholder='120'
                    />
                    <p className='text-xs text-gray-500 mt-1'>{t('hotels_modal.housekeeping.max_task_duration_help')}</p>
                  </div>
                  <label className='flex items-center gap-2 cursor-pointer'>
                    <input
                      type='checkbox'
                      className='rounded border-gray-300'
                      checked={!!hkValues?.auto_complete_overdue}
                      onChange={(e) => setHkValues((v) => ({ ...v, auto_complete_overdue: e.target.checked }))}
                    />
                    <span className='text-sm text-aloja-gray-800/80'>{t('hotels_modal.housekeeping.auto_complete_overdue')}</span>
                  </label>
                  {hkValues?.auto_complete_overdue && (
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800/70 mb-1'>{t('hotels_modal.housekeeping.overdue_grace_minutes')}</label>
                      <input
                        type='number'
                        className='w-full border border-gray-200 rounded-lg px-3 py-2 text-sm'
                        value={hkValues?.overdue_grace_minutes ?? 30}
                        onChange={(e) => setHkValues((v) => ({ ...v, overdue_grace_minutes: e.target.value }))}
                        placeholder='30'
                      />
                      <p className='text-xs text-gray-500 mt-1'>{t('hotels_modal.housekeeping.overdue_grace_help')}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">{t('housekeeping.config.no_config')}</div>
          )}
        </div>
      )}
    </div>
  )
}

