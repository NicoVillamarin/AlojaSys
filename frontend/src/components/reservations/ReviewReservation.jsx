import React, { useMemo } from 'react'
import { useFormikContext } from 'formik'
import { useTranslation } from 'react-i18next'
import { format, parseISO, isValid } from 'date-fns'
import { es } from 'date-fns/locale'
import CheckCircleIcon from 'src/assets/icons/CheckCircleIcon'
import CandelarClock from 'src/assets/icons/CandelarClock'
import PeopleIcon from 'src/assets/icons/PeopleIcon'
import { useAction } from 'src/hooks/useAction'

const ReviewReservation = () => {
  const { t } = useTranslation()
  const { values } = useFormikContext()

  // Función helper para formatear fechas correctamente
  const formatDate = (dateString, formatStr = 'dd MMM') => {
    if (!dateString) return ''
    try {
      // Si es una fecha en formato ISO, usar parseISO
      if (dateString.includes('T') || dateString.includes('Z')) {
        const parsed = parseISO(dateString)
        return isValid(parsed) ? format(parsed, formatStr, { locale: es }) : ''
      }
      // Si es una fecha en formato YYYY-MM-DD, crear Date directamente
      const date = new Date(dateString + 'T00:00:00')
      return isValid(date) ? format(date, formatStr, { locale: es }) : ''
    } catch (error) {
      console.error('Error formatting date:', error)
      return ''
    }
  }

  // Calcular duración de la estadía
  const calculateStayDuration = (checkIn, checkOut) => {
    if (!checkIn || !checkOut) return 0
    try {
      const checkInDate = checkIn.includes('T') ? parseISO(checkIn) : new Date(checkIn + 'T00:00:00')
      const checkOutDate = checkOut.includes('T') ? parseISO(checkOut) : new Date(checkOut + 'T00:00:00')
      
      if (!isValid(checkInDate) || !isValid(checkOutDate)) return 0
      
      const diffTime = checkOutDate - checkInDate
      return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    } catch (error) {
      console.error('Error calculating stay duration:', error)
      return 0
    }
  }

  const stayDuration = calculateStayDuration(values.check_in, values.check_out)

  // ----- Resumen de pago (cotización) -----
  const ready = Boolean(values.room && values.check_in && values.check_out && (values.guests || 1))
  const quoteParams = useMemo(() => ({
    room_id: values.room,
    check_in: values.check_in,
    check_out: values.check_out,
    guests: values.guests || 1,
    channel: 'direct', // Siempre DIRECT para reservas creadas desde el sistema
    price_source: values.price_source || 'primary',
    ...(values.promotion_code ? { promotion_code: values.promotion_code } : {}),
    ...(values.voucher_code ? { voucher_code: values.voucher_code } : {}),
  }), [values.room, values.check_in, values.check_out, values.guests, values.promotion_code, values.voucher_code, values.price_source])

  const { results: quoteRes, isPending: quotePending } = useAction({
    resource: 'reservations',
    action: 'quote-range',
    params: quoteParams,
    enabled: ready,
  })

  const paymentSummary = useMemo(() => {
    if (!quoteRes || quoteRes.ok === false) return null
    const nights = (quoteRes.days || []).map(d => d.pricing || {})
    const sum = (arr, key) => arr.reduce((s, n) => s + Number(n[key] || 0), 0)
    const base = sum(nights, 'base_rate')
    const extra = sum(nights, 'extra_guest_fee')
    const discount = sum(nights, 'discount')
    const tax = sum(nights, 'tax')
    const total = Number(quoteRes.total || 0)
    return { base, extra, discount, tax, total, nightsCount: nights.length }
  }, [quoteRes])

  const currencyCode = quoteRes?.currency_code || 'ARS'
  const formatCurrency = (amount) =>
    new Intl.NumberFormat('es-AR', { style: 'currency', currency: currencyCode, minimumFractionDigits: 2 }).format(amount)

  return (
    <div className="space-y-6">
      {/* Resumen Principal */}
      <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-xl border border-green-200 shadow-sm">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 bg-green-100 rounded-lg">
            <CheckCircleIcon className="w-6 h-6 text-green-600" />
          </div>
          <h3 className="text-xl font-bold text-green-900">{t('review_reservation.reservation_summary')}</h3>
        </div>

        {/* Rango de fechas destacado */}
        <div className="bg-white p-6 rounded-lg border border-green-200 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="text-center">
                <div className="text-sm font-medium text-gray-600 mb-2">{t('review_reservation.check_in')}</div>
                <div className="text-2xl font-bold text-green-600">
                  {formatDate(values.check_in, 'dd MMM')}
                </div>
                <div className="text-sm text-gray-500">
                  {formatDate(values.check_in, 'EEEE, yyyy')}
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <div className="w-12 h-0.5 bg-green-300"></div>
                <div className="bg-green-100 px-3 py-1 rounded-full">
                  <span className="text-green-700 font-bold text-sm">
                    {stayDuration} {stayDuration === 1 ? t('reservations_modal.night') : t('reservations_modal.nights')}
                  </span>
                </div>
                <div className="w-12 h-0.5 bg-green-300"></div>
              </div>
              
              <div className="text-center">
                <div className="text-sm font-medium text-gray-600 mb-2">{t('review_reservation.check_out')}</div>
                <div className="text-2xl font-bold text-green-600">
                  {formatDate(values.check_out, 'dd MMM')}
                </div>
                <div className="text-sm text-gray-500">
                  {formatDate(values.check_out, 'EEEE, yyyy')}
                </div>
              </div>
            </div>
            
            <div className="text-right">
              <div className="text-sm text-gray-600 mb-1">{t('review_reservation.total_duration')}</div>
              <div className="text-3xl font-bold text-green-600">{stayDuration}</div>
              <div className="text-sm text-gray-500">{t('review_reservation.nights')}</div>
            </div>
          </div>
        </div>

        {/* Información de la habitación y huéspedes */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-4 rounded-lg border border-green-200">
            <div className="flex items-center space-x-2 mb-3">
              <CandelarClock className="w-5 h-5 text-green-600" />
              <h4 className="font-semibold text-gray-800">{t('review_reservation.room')}</h4>
            </div>
            <div className="space-y-2">
              <div>
                <span className="text-sm text-gray-600">{t('review_reservation.hotel')} </span>
                <span className="font-medium">{values.hotel || t('review_reservation.not_selected')}</span>
              </div>
              <div>
                <span className="text-sm text-gray-600">{t('review_reservation.room_name')} </span>
                <span className="font-medium">
                  {values.room_data?.name || values.room || t('review_reservation.not_selected_room')}
                </span>
              </div>
              {values.room_data && (
                <div>
                  <span className="text-sm text-gray-600">{t('review_reservation.type')} </span>
                  <span className="font-medium">{values.room_data.room_type}</span>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-green-200">
            <div className="flex items-center space-x-2 mb-3">
              <PeopleIcon className="w-5 h-5 text-green-600" />
              <h4 className="font-semibold text-gray-800">{t('review_reservation.guests')}</h4>
            </div>
            <div className="space-y-2">
              <div>
                <span className="text-sm text-gray-600">{t('review_reservation.total')} </span>
                <span className="font-medium text-lg">{values.guests || 0}</span>
                {values.room_data && (
                  <span className="text-sm text-gray-500 ml-1">
                    / {values.room_data.max_capacity} {t('guest_information.max_capacity')}
                  </span>
                )}
              </div>
              <div>
                <span className="text-sm text-gray-600">{t('review_reservation.principal')} </span>
                <span className="font-medium">{values.guest_name || t('review_reservation.not_specified')}</span>
              </div>
              {values.other_guests && values.other_guests.length > 0 && (
                <div>
                  <span className="text-sm text-gray-600">{t('review_reservation.additional')} </span>
                  <span className="font-medium">{values.other_guests.length}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Información del huésped principal */}
      {values.guest_name && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200 shadow-sm">
          <h4 className="text-lg font-bold text-blue-900 mb-4">{t('review_reservation.primary_guest')}</h4>
          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-600">{t('review_reservation.name')} </span>
                <span className="font-medium">{values.guest_name}</span>
              </div>
              <div>
                <span className="text-sm text-gray-600">{t('review_reservation.email')} </span>
                <span className="font-medium">{values.guest_email}</span>
              </div>
              <div>
                <span className="text-sm text-gray-600">{t('review_reservation.phone')} </span>
                <span className="font-medium">{values.guest_phone}</span>
              </div>
              <div>
                <span className="text-sm text-gray-600">{t('review_reservation.document')} </span>
                <span className="font-medium">{values.guest_document}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Resumen de Pago (incluye impuestos si aplican) */}
      {ready && (
        <div className="bg-gradient-to-br from-emerald-50 to-green-50 p-6 rounded-xl border border-emerald-200 shadow-sm">
          <h4 className="text-lg font-bold text-emerald-900 mb-4">{t('review_reservation.payment_summary')}</h4>
          <div className="bg-white p-4 rounded-lg border border-emerald-200">
            {quotePending && (
              <div className="text-sm text-gray-600">{t('review_reservation.calculating_prices')}</div>
            )}
            {!quotePending && paymentSummary && (
              <div className="space-y-2 text-gray-800">
                <div className="flex items-center justify-between">
                  <span>{t('review_reservation.subtotal')} ({paymentSummary.nightsCount} {paymentSummary.nightsCount === 1 ? t('reservations_modal.night') : t('reservations_modal.nights')})</span>
                  <span className="font-medium">
                    {formatCurrency(paymentSummary.base)}
                  </span>
                </div>
                {paymentSummary.extra > 0 && (
                  <div className="flex items-center justify-between text-blue-700">
                    <span>{t('review_reservation.extra_guests')}</span>
                    <span className="font-medium">+ {formatCurrency(paymentSummary.extra)}</span>
                  </div>
                )}
                {paymentSummary.discount > 0 && (
                  <div className="flex items-center justify-between text-green-700">
                    <span>{t('review_reservation.discounts')}</span>
                    <span className="font-medium">- {formatCurrency(paymentSummary.discount)}</span>
                  </div>
                )}
                {paymentSummary.tax > 0 && (
                  <div className="flex items-center justify-between">
                    <span>{t('review_reservation.taxes')}</span>
                    <span className="font-medium">+ {formatCurrency(paymentSummary.tax)}</span>
                  </div>
                )}
                <div className="border-t border-emerald-200 pt-2 mt-2 flex items-center justify-between">
                  <span className="text-lg font-bold">{t('review_reservation.total')}</span>
                  <span className="text-2xl font-extrabold text-emerald-700">
                    {formatCurrency(paymentSummary.total)}
                  </span>
                </div>
              </div>
            )}
            {!quotePending && !paymentSummary && (
              <div className="text-sm text-gray-600">{t('review_reservation.could_not_calculate')}</div>
            )}
          </div>
        </div>
      )}

      {/* Notas */}
      {values.notes && (
        <div className="bg-gradient-to-br from-gray-50 to-slate-50 p-6 rounded-xl border border-gray-200 shadow-sm">
          <h4 className="text-lg font-bold text-gray-900 mb-4">{t('review_reservation.additional_notes')}</h4>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <p className="text-gray-700">{values.notes}</p>
          </div>
        </div>
      )}

      {/* Validación final */}
      <div className="bg-gradient-to-br from-yellow-50 to-orange-50 p-4 rounded-xl border border-yellow-200">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-yellow-100 rounded-lg">
            <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h4 className="font-bold text-yellow-900">{t('review_reservation.final_verification')}</h4>
            <p className="text-yellow-700 text-sm">
              {t('review_reservation.review_before_confirm')}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ReviewReservation