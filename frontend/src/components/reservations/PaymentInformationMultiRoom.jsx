import React, { useEffect, useState, useMemo } from 'react'
import { useFormikContext } from 'formik'
import { useTranslation } from 'react-i18next'
import { format, parseISO } from 'date-fns'
import { es } from 'date-fns/locale'
import SpinnerData from '../SpinnerData'
import WalletIcon from 'src/assets/icons/WalletIcon'
import InputText from 'src/components/inputs/InputText'
// import { useAction } from 'src/hooks/useAction'

/**
 * PaymentInformationMultiRoom
 * 
 * Componente de información de pago para reservas multi-habitación.
 * Calcula precios para cada habitación y muestra un resumen agregado.
 */
const PaymentInformationMultiRoom = () => {
  const { t } = useTranslation()
  const { values, setFieldValue } = useFormikContext()
  const checkIn = values.date_range?.startDate || values.check_in
  const checkOut = values.date_range?.endDate || values.check_out
  const validRooms = (values.rooms || []).filter((r) => r.room && r.guests)

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

  // Acción centralizada para calcular tarifas
  const fetchPricingQuotes = async () => {
    setAppliedPromo(promoDraft)
    setFieldValue('promotion_code', promoDraft)
    setAppliedVoucher(voucherDraft)
    setFieldValue('voucher_code', voucherDraft)
    
    // Por ahora, mostrar un mensaje de que se calculará al crear
    // En el futuro, se pueden hacer llamadas individuales aquí
  }

  const clearPromotion = async () => {
    setPromoDraft('')
    setAppliedPromo('')
    setFieldValue('promotion_code', '')
  }

  const clearVoucher = async () => {
    setVoucherDraft('')
    setAppliedVoucher('')
    setFieldValue('voucher_code', '')
  }

  // Formatear fecha
  const formatDate = (dateStr) => {
    try {
      const date = parseISO(dateStr)
      return format(date, 'EEE dd MMM', { locale: es })
    } catch {
      return dateStr
    }
  }

  // Formatear moneda
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 2,
    }).format(amount)
  }

  // Por ahora, simplificamos la UI
  if (false) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <SpinnerData />
        <p className="mt-4 text-gray-600">{t('payment_information.calculating_prices')}</p>
      </div>
    )
  }

  if (!checkIn || !checkOut || validRooms.length === 0) {
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

  // Calcular total estimado simple (usando room_data que trae base_price desde el select)
  const totals = useMemo(() => {
    if (!checkIn || !checkOut || validRooms.length === 0) {
      return { totalEstimated: 0 }
    }
    
    const nights = Math.ceil((new Date(checkOut) - new Date(checkIn)) / (1000 * 60 * 60 * 24))
    const totalEstimated = validRooms.reduce((sum, room) => {
      // En multi-room guardamos el objeto completo en room.room_data
      const roomData = room.room_data || null
      const basePrice = roomData?.base_price || 0
      return sum + (parseFloat(basePrice) * nights)
    }, 0)
    
    return { totalEstimated }
  }, [checkIn, checkOut, validRooms])

  const anyPromoApplied = !!(appliedPromo || appliedVoucher)

  return (
    <div className="space-y-6">
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
                appliedPromo
                  ? t('payment_information.promotion_applied')
                  : null
              }
              statusType={
                appliedPromo
                  ? "success"
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
              onClick={fetchPricingQuotes}
              disabled={!checkIn || !checkOut || validRooms.length === 0}
              className={`px-4 py-2 rounded-md text-white ${(!checkIn || !checkOut || validRooms.length === 0) ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}
            >
              {t('payment_information.calculate_rate')}
            </button>
          </div>
        </div>
      </div>

      {/* Título */}
      <div className="text-center mb-6">
        <h3 className="text-2xl font-bold text-gray-800 mb-2">{t('payment_information.payment_summary')}</h3>
        <p className="text-gray-600">Resumen de pago para {validRooms.length} habitación(es)</p>
      </div>

      {/* Mensaje informativo */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
        <p className="text-blue-900 font-medium mb-2">
          Los precios se calcularán automáticamente al crear la reserva
        </p>
        <p className="text-sm text-blue-700">
          Los códigos de promoción y voucher ingresados se aplicarán a todas las habitaciones del grupo.
        </p>
      </div>

      {/* Resumen estimado simple */}
      {validRooms.length > 0 && checkIn && checkOut && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">Resumen estimado</h4>
          <div className="space-y-2">
            {validRooms.map((room, idx) => {
              const roomData = room.room_data || null
              const basePrice = roomData?.base_price || 0
              const nights = Math.ceil((new Date(checkOut) - new Date(checkIn)) / (1000 * 60 * 60 * 24))
              const estimatedPrice = parseFloat(basePrice) * nights
              
              return (
                <div key={idx} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">
                    {roomData?.name || `Habitación ${idx + 1}`} - {room.guests} huésped(es)
                  </span>
                  <span className="font-semibold text-gray-900">
                    {formatCurrency(estimatedPrice)}
                    <span className="text-xs text-gray-500 ml-1">
                      ({nights} {nights === 1 ? 'noche' : 'noches'})
                    </span>
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Resumen Total Estimado */}
      {totals.totalEstimated > 0 && (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-lg p-6">
          <div className="space-y-3">
            <div className="border-t-2 border-green-300 pt-3 mt-3">
              <div className="flex items-center justify-between">
                <span className="text-xl font-bold text-gray-800">Total estimado</span>
                <span className="text-3xl font-bold text-green-700">
                  {formatCurrency(totals.totalEstimated)}
                </span>
              </div>
              <p className="text-xs text-gray-600 mt-2">
                💡 Este es un cálculo estimado. El precio final se calculará al crear la reserva aplicando descuentos, impuestos y reglas de tarifa.
              </p>
            </div>
          </div>
        </div>
      )}

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

export default PaymentInformationMultiRoom

