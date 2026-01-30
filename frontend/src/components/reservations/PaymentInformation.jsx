import React, { useEffect, useMemo, useState } from 'react'
import { useFormikContext } from 'formik'
import { useTranslation } from 'react-i18next'
import { format, parseISO } from 'date-fns'
import { es } from 'date-fns/locale'
import SpinnerData from '../SpinnerData'
import WalletIcon from 'src/assets/icons/WalletIcon'
import InputText from 'src/components/inputs/InputText'
import { useAction } from 'src/hooks/useAction'

const PaymentInformation = () => {
  const { t } = useTranslation()
  const { values, setFieldValue } = useFormikContext()
  const [pricingData, setPricingData] = useState(null)
  const [error, setError] = useState(null)
  const [canBookIssue, setCanBookIssue] = useState(null)

  // Usar el canal actual (si la reserva viene de OTA, mantenerlo)

  // Función para obtener la cotización de precios
  const ready = !!(values.room && values.guests && values.check_in && values.check_out)
  // IMPORTANTE: memoizar params para evitar loops de react-query (queryKey cambia por referencia)
  const canParams = useMemo(
    () => ({
      room_id: values.room,
      check_in: values.check_in,
      check_out: values.check_out,
      channel: values.channel || 'direct',
    }),
    [values.room, values.check_in, values.check_out, values.channel]
  )
  const { results: canBookRes, isPending: canPending, refetch: refetchCanBook } = useAction({
    resource: 'reservations',
    action: 'can-book',
    params: canParams,
    enabled: ready,
  })

  const [promoDraft, setPromoDraft] = useState(values.promotion_code || '')
  const [appliedPromo, setAppliedPromo] = useState(values.promotion_code || '')
  const [voucherDraft, setVoucherDraft] = useState(values.voucher_code || '')
  const [appliedVoucher, setAppliedVoucher] = useState(values.voucher_code || '')
  useEffect(() => {
    setPromoDraft(values.promotion_code || '')
    setAppliedPromo(values.promotion_code || '')
    setVoucherDraft(values.voucher_code || '')
    setAppliedVoucher(values.voucher_code || '')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const quoteParams = useMemo(
    () => ({
      room_id: values.room,
      check_in: values.check_in,
      check_out: values.check_out,
      guests: values.guests || 1,
      channel: values.channel || 'direct',
      price_source: values.price_source || 'primary',
      ...(appliedPromo ? { promotion_code: appliedPromo } : {}),
      ...(appliedVoucher ? { voucher_code: appliedVoucher } : {}),
    }),
    [
      values.room,
      values.check_in,
      values.check_out,
      values.guests,
      values.channel,
      values.price_source,
      appliedPromo,
      appliedVoucher,
    ]
  )
  const { results: quoteRes, isPending: quotePending, refetch: refetchQuote } = useAction({
    resource: 'reservations',
    action: 'quote-range',
    params: quoteParams,
    enabled: ready && canBookRes?.ok === true,
  })

  // proyectar resultados en el estado de UI
  useEffect(() => {
    setError(null)
    if (!ready) {
      setPricingData(null)
      setCanBookIssue(null)
      return
    }
    if (canBookRes && canBookRes.ok === false) {
      setCanBookIssue(canBookRes)
      setPricingData(null)
      return
    }
    setCanBookIssue(null)
    if (quoteRes && quoteRes.ok !== false) {
      const nights = (quoteRes?.days || []).map(d => ({
        date: d.date,
        base_rate: d.pricing?.base_rate ?? 0,
        extra_guest_fee: d.pricing?.extra_guest_fee ?? 0,
        discount: d.pricing?.discount ?? 0,
        tax: d.pricing?.tax ?? 0,
        total_night: d.pricing?.total_night ?? 0,
        applied_promos: d.pricing?.applied_promos || [],
        applied_promos_detail: d.pricing?.applied_promos_detail || [],
        applied_taxes_detail: d.pricing?.applied_taxes_detail || [],
        rule: d.rule || null,
      }))
      setPricingData({ nights, total: quoteRes?.total ?? 0 })
    } else if (quoteRes && quoteRes.ok === false) {
      setCanBookIssue(quoteRes)
      setPricingData(null)
    }
  }, [ready, canBookRes, quoteRes])

  // Cargar cotización cuando cambien los valores relevantes
  useEffect(() => {
    // refetch on demand button triggers
  }, [])

  // Acción centralizada para calcular tarifa (botón y reintentos)
  const fetchPricingQuote = async () => {
    await refetchCanBook()
    setAppliedPromo(promoDraft)
    setFieldValue('promotion_code', promoDraft)
    setAppliedVoucher(voucherDraft)
    setFieldValue('voucher_code', voucherDraft)
    await refetchQuote()
  }

  const clearPromotion = async () => {
    setPromoDraft('')
    setAppliedPromo('')
    setFieldValue('promotion_code', '')
    await refetchQuote()
  }

  const clearVoucher = async () => {
    setVoucherDraft('')
    setAppliedVoucher('')
    setFieldValue('voucher_code', '')
    await refetchQuote()
  }

  // Formatear fecha para mostrar
  const formatDate = (dateStr) => {
    try {
      const date = parseISO(dateStr)
      return format(date, 'EEE dd MMM', { locale: es })
    } catch {
      return dateStr
    }
  }

  const roomData = values.room_data
  const secondaryAvailable = roomData?.secondary_price != null && !!roomData?.secondary_currency_code
  const selectedPriceSource = values.price_source || 'primary'
  const quoteCurrencyCode = quoteRes?.currency_code || (selectedPriceSource === 'secondary' ? roomData?.secondary_currency_code : roomData?.base_currency_code) || 'ARS'
  const selectedBasePrice = selectedPriceSource === 'secondary' && secondaryAvailable ? roomData?.secondary_price : roomData?.base_price

  // Si cambió la habitación y no hay tarifa secundaria, volver a principal
  useEffect(() => {
    if (roomData && selectedPriceSource === 'secondary' && !secondaryAvailable) {
      setFieldValue('price_source', 'primary')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [values.room, secondaryAvailable])

  // Formatear moneda (dinámica según la tarifa elegida)
  const formatCurrency = (amount, currencyCode = quoteCurrencyCode) => {
    const code = currencyCode || 'ARS'
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: code,
      minimumFractionDigits: 2,
    }).format(amount)
  }

  if (canPending || quotePending) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <SpinnerData />
        <p className="mt-4 text-gray-600">{t('payment_information.calculating_prices')}</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <div className="text-red-600 mb-2">⚠️ {error}</div>
        <button
          onClick={fetchPricingQuote}
          className="text-sm text-red-700 hover:text-red-900 underline"
        >
          {t('payment_information.retry')}
        </button>
      </div>
    )
  }

  if (canBookIssue) {
    const mapReason = (issue) => {
      if (!issue) return ''
      const r = issue.reason
      if (r === 'closed_to_arrival') return 'La fecha de llegada no permite check-in (CTA).'
      if (r === 'closed_to_departure') return 'La fecha de salida no permite check-out (CTD).'
      if (r === 'min_stay') return `La estadía es menor al mínimo requerido (${issue.value} noches).`
      if (r === 'max_stay') return `La estadía supera el máximo permitido (${issue.value} noches).`
      if (r === 'closed') return `Hay días cerrados a la venta (p.ej., ${issue.date}).`
      if (r === 'capacity_exceeded') return `Capacidad máxima superada (${issue.max_capacity}).`
      if (r === 'overlap') return 'La habitación ya tiene una reserva en el rango.'
      if (r === 'room_block') return 'La habitación está bloqueada en el rango.'
      return 'No es posible reservar en el rango seleccionado.'
    }
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="text-yellow-800 font-medium mb-2">{t('payment_information.cannot_book')}</div>
        <div className="text-sm text-yellow-800 mb-4">{mapReason(canBookIssue)}</div>
        <button onClick={fetchPricingQuote} className="text-sm text-yellow-700 hover:text-yellow-900 underline">{t('payment_information.retry')}</button>
      </div>
    )
  }

  if (!pricingData) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
        <div className="text-gray-400 mb-2">
          <WalletIcon className="w-16 h-16 mx-auto mb-4" />
        </div>
        <p className="text-gray-600 text-lg font-medium mb-2">
          {t('payment_information.complete_basic_info')}
        </p>
        <p className="text-gray-500 text-sm">
          {t('payment_information.select_hotel_room_dates')}
        </p>
      </div>
    )
  }

  const anyPromoApplied = !!(pricingData?.nights?.some(n => (
    (Array.isArray(n.applied_promos) && n.applied_promos.length > 0) ||
    (Array.isArray(n.applied_promos_detail) && n.applied_promos_detail.length > 0) ||
    (parseFloat(n.discount || 0) > 0)
  )))
  const totalDiscountApplied = pricingData ? pricingData.nights.reduce((sum, n) => sum + (parseFloat(n.discount || 0) || 0), 0) : 0

  return (
    <div className="space-y-6">
      {/* Selección de tarifa (principal / secundaria) */}
      {roomData && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm font-semibold text-gray-800 mb-3">Tarifa a aplicar</div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setFieldValue('price_source', 'primary')}
              className={`w-full text-left rounded-lg border px-4 py-3 transition-colors ${
                selectedPriceSource === 'primary'
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 bg-white hover:bg-gray-50'
              }`}
            >
              <div className="text-sm font-medium text-gray-900">Tarifa principal</div>
              <div className="text-xs text-gray-600 mt-1">
                {roomData?.base_currency_code ? `${roomData.base_currency_code} • ` : ''}
                {formatCurrency(roomData?.base_price || 0, roomData?.base_currency_code || quoteCurrencyCode)}
                {' '}por noche
              </div>
            </button>
            <button
              type="button"
              disabled={!secondaryAvailable}
              onClick={() => setFieldValue('price_source', 'secondary')}
              className={`w-full text-left rounded-lg border px-4 py-3 transition-colors ${
                !secondaryAvailable
                  ? 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed'
                  : selectedPriceSource === 'secondary'
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 bg-white hover:bg-gray-50'
              }`}
              title={!secondaryAvailable ? 'La habitación no tiene tarifa secundaria configurada' : undefined}
            >
              <div className="text-sm font-medium">Tarifa secundaria</div>
              <div className="text-xs mt-1">
                {secondaryAvailable ? (
                  <>
                    {roomData?.secondary_currency_code ? `${roomData.secondary_currency_code} • ` : ''}
                    {formatCurrency(roomData?.secondary_price || 0, roomData?.secondary_currency_code || quoteCurrencyCode)}
                    {' '}por noche
                  </>
                ) : (
                  'No configurada para esta habitación'
                )}
              </div>
            </button>
          </div>
          <div className="text-xs text-gray-500 mt-2">
            La moneda del resumen y del cálculo se ajusta según la tarifa elegida.
          </div>
        </div>
      )}
      {/* Controles de código promo y voucher */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 items-end">
          <div className="relative">
            <InputText
              name="promotion_code_draft"
              title={t('payment_information.promotion_code')}
              placeholder={t('payment_information.promotion_code_placeholder')}
              value={promoDraft}
              onChange={(e) => setPromoDraft(e.target.value)}
              statusMessage={
                appliedPromo && totalDiscountApplied > 0
                  ? t('payment_information.promotion_applied')
                  : appliedPromo && totalDiscountApplied === 0
                  ? t('payment_information.promotion_not_applied')
                  : null
              }
              statusType={
                appliedPromo && totalDiscountApplied > 0
                  ? "success"
                  : appliedPromo && totalDiscountApplied === 0
                  ? "warning"
                  : "info"
              }
              inputClassName="pr-10"
            />
            {appliedPromo && anyPromoApplied && (
              <div className="absolute right-2 top-6 z-20">
                <button
                  type="button"
                  onClick={clearPromotion}
                  className="text-emerald-600 hover:text-emerald-800 font-bold text-lg leading-none flex items-center justify-center w-6 h-6"
                  title={t('payment_information.remove_promotion')}
                >
                  ×
                </button>
              </div>
            )}
          </div>
          <div className="relative">
            <InputText
              name="voucher_code_draft"
              title={t('payment_information.voucher_code')}
              placeholder={t('payment_information.voucher_code_placeholder')}
              value={voucherDraft}
              onChange={(e) => setVoucherDraft(e.target.value)}
              statusMessage={
                appliedVoucher
                  ? t('payment_information.voucher_applied')
                  : null
              }
              statusType={
                appliedVoucher
                  ? "success"
                  : "info"
              }
              inputClassName="pr-10"
            />
            {appliedVoucher && (
              <div className="absolute right-2 top-6 z-20">
                <button
                  type="button"
                  onClick={clearVoucher}
                  className="text-emerald-600 hover:text-emerald-800 font-bold text-lg leading-none flex items-center justify-center w-6 h-6"
                  title={t('payment_information.remove_voucher')}
                >
                  ×
                </button>
              </div>
            )}
          </div>
          <div className="flex items-end">
            <button
              onClick={fetchPricingQuote}
              disabled={!ready || canPending || quotePending}
              className={`px-4 py-2 rounded-md text-white ${(!ready || canPending || quotePending) ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}
            >
              {quotePending || canPending ? t('payment_information.calculating') : t('payment_information.calculate_rate')}
            </button>
          </div>
        </div>
      </div>
      {/* Título */}
      <div className="text-center mb-6">
        <h3 className="text-2xl font-bold text-gray-800 mb-2">{t('payment_information.payment_summary')}</h3>
        <p className="text-gray-600">{t('payment_information.payment_summary_subtitle')}</p>
      </div>

      {/* Información de la Habitación */}
      {roomData && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-gray-800 text-lg">{roomData.name}</h4>
              <p className="text-sm text-gray-600">
                {t('payment_information.room_type')} {roomData.room_type} • {t('payment_information.floor')} {roomData.floor} • {t('payment_information.room_number')}{roomData.number}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                {t('payment_information.capacity')} {roomData.capacity} {t('payment_information.guests_included')} {roomData.max_capacity})
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600">{t('payment_information.base_rate_per_night')}</div>
              <div className="text-xl font-bold text-blue-600">
                {formatCurrency(selectedBasePrice || 0)}
              </div>
              {parseFloat(roomData.extra_guest_fee) > 0 && (
                <div className="text-xs text-gray-500 mt-1">
                  + {formatCurrency(roomData.extra_guest_fee)} {t('payment_information.extra_per_guest')}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Desglose por Noche */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <h4 className="font-semibold text-gray-800">{t('payment_information.breakdown_by_night')}</h4>
        </div>
        <div className="divide-y divide-gray-200">
          {pricingData.nights.map((night, index) => {
            const hasExtraGuests = parseFloat(night.extra_guest_fee) > 0
            const hasDiscount = parseFloat(night.discount) > 0
            const hasTax = parseFloat(night.tax) > 0

            return (
              <div key={index} className="px-4 py-3 hover:bg-gray-50 transition-colors">
                <div className="flex items-center mb-2">
                  <div className="flex items-center space-x-3">
                    <div className="bg-blue-100 text-blue-600 font-semibold text-sm px-3 py-1 rounded-full">
                      {t('payment_information.night')} {index + 1}
                    </div>
                    <span className="text-gray-700 font-medium">
                      {formatDate(night.date)}
                    </span>
                  </div>
                </div>
                
                {/* Detalle de cargos */}
                <div className="ml-20 text-sm text-gray-600 space-y-1">
                  {/* Tarifa base de la habitación */}
                  <div className="flex justify-between">
                    <span>{t('payment_information.base_rate')}</span>
                    <span>{formatCurrency(selectedBasePrice || 0)}</span>
                  </div>
                  
                  {/* Regla aplicada (si existe) */}
                  {night.rule && (
                    <div className="flex justify-between text-blue-600">
                      <span>
                        {t('payment_information.rate_rule')} ({night.rule.name || t('payment_information.rule_applied')})
                        {night.rule.price_mode === 'absolute' ? '' : ''}
                      </span>
                      <span>
                        {night.rule.price_mode === 'absolute' 
                          ? formatCurrency(night.base_rate)
                          : `+ ${formatCurrency(night.base_rate - (selectedBasePrice || 0))}`
                        }
                      </span>
                    </div>
                  )}
                  {hasExtraGuests && (
                    <div className="flex justify-between text-blue-600">
                      <span>{t('payment_information.extra_guests')}</span>
                      <span>+ {formatCurrency(night.extra_guest_fee)}</span>
                    </div>
                  )}
                  {hasDiscount && (
                    <div className="flex justify-between text-green-600">
                      <span>
                        {t('payment_information.discount')}
                        {night.applied_promos_detail && night.applied_promos_detail.length > 0 && (
                          <span className="text-green-500 font-medium">
                            {' '}({night.applied_promos_detail.map(p => p.code).join(', ')})
                          </span>
                        )}
                      </span>
                      <span>- {formatCurrency(night.discount)}</span>
                    </div>
                  )}
                  {appliedPromo && (Array.isArray(night.applied_promos) ? night.applied_promos.length > 0 : false) && (
                    <div className="flex justify-between text-emerald-700">
                      <span>{t('payment_information.promo_applied')}</span>
                      <span>{Array.isArray(night.applied_promos) ? night.applied_promos.length : 1}</span>
                    </div>
                  )}
                  {hasTax && (
                    <div className="flex justify-between">
                      <span>
                        {t('payment_information.taxes')}
                        {night.applied_taxes_detail && night.applied_taxes_detail.length > 0 && (
                          <span className="text-gray-500 font-medium">{' '}(
                            {night.applied_taxes_detail.map(t => t.name).join(', ')}
                          )</span>
                        )}
                      </span>
                      <span>+ {formatCurrency(night.tax)}</span>
                    </div>
                  )}
                </div>
                
                {/* Total de la noche con línea separadora */}
                <div className="ml-20 mt-3 pt-2 border-t border-gray-200">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-gray-800">{t('payment_information.total_night')}</span>
                    <span className="text-lg font-bold text-gray-800">
                      {formatCurrency(night.total_night)}
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Resumen Total */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-lg p-6">
        <div className="space-y-3">
          <div className="flex items-center justify-between text-gray-700">
            <span className="font-medium">{t('payment_information.subtotal')} ({pricingData.nights.length} {pricingData.nights.length === 1 ? t('reservations_modal.night') : t('reservations_modal.nights')})</span>
            <span className="text-lg">
              {formatCurrency(
                pricingData.nights.reduce((sum, n) => sum + parseFloat(n.base_rate), 0)
              )}
            </span>
          </div>
          
          {parseFloat(pricingData.nights.reduce((sum, n) => sum + parseFloat(n.extra_guest_fee), 0)) > 0 && (
            <div className="flex items-center justify-between text-blue-700">
              <span className="font-medium">{t('payment_information.extra_guest_charges')}</span>
              <span className="text-lg">
                + {formatCurrency(
                  pricingData.nights.reduce((sum, n) => sum + parseFloat(n.extra_guest_fee), 0)
                )}
              </span>
            </div>
          )}
          
          {parseFloat(pricingData.nights.reduce((sum, n) => sum + parseFloat(n.discount), 0)) > 0 && (
            <div className="flex items-center justify-between text-green-700">
              <span className="font-medium">{t('payment_information.applied_discounts')}</span>
              <span className="text-lg">
                - {formatCurrency(
                  pricingData.nights.reduce((sum, n) => sum + parseFloat(n.discount), 0)
                )}
              </span>
            </div>
          )}
          
          {parseFloat(pricingData.nights.reduce((sum, n) => sum + parseFloat(n.tax), 0)) > 0 && (
            <div className="flex items-center justify-between text-gray-700">
              <span className="font-medium">{t('payment_information.taxes')}</span>
              <span className="text-lg">
                + {formatCurrency(
                  pricingData.nights.reduce((sum, n) => sum + parseFloat(n.tax), 0)
                )}
              </span>
            </div>
          )}
          
          <div className="border-t-2 border-green-300 pt-3 mt-3">
            <div className="flex items-center justify-between">
              <span className="text-xl font-bold text-gray-800">{t('payment_information.total_to_pay')}</span>
              <span className="text-3xl font-bold text-green-700">
                {formatCurrency(pricingData.total)}
              </span>
            </div>
          </div>
          
          {/* Información adicional */}
          <div className="text-sm text-gray-600 mt-4 pt-4 border-t border-green-200">
            <div className="flex items-center justify-between">
              <span>{t('payment_information.average_per_night')}</span>
              <span className="font-semibold">
                {formatCurrency(parseFloat(pricingData.total) / pricingData.nights.length)}
              </span>
            </div>
            <div className="flex items-center justify-between mt-1">
              <span>{t('payment_information.guests')}</span>
              <span className="font-semibold">{values.guests}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Nota informativa */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <span className="text-yellow-600 text-xl">💡</span>
          <div className="text-sm text-yellow-800">
            <p className="font-medium mb-1">{t('payment_information.important_note')}</p>
            <p>
              {t('payment_information.preliminary_summary')}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PaymentInformation