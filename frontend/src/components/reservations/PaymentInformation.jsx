import React, { useEffect, useState } from 'react'
import { useFormikContext } from 'formik'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import { format, parseISO } from 'date-fns'
import { es } from 'date-fns/locale'
import SpinnerData from '../SpinnerData'
import WalletIcon from 'src/assets/icons/WalletIcon'

const PaymentInformation = () => {
  const { values } = useFormikContext()
  const [pricingData, setPricingData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Función para obtener la cotización de precios
  const fetchPricingQuote = async () => {
    if (!values.room || !values.guests || !values.check_in || !values.check_out) {
      setPricingData(null)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams({
        room_id: values.room,
        guests: values.guests,
        check_in: values.check_in,
        check_out: values.check_out,
      })

      const response = await fetchWithAuth(
        `${getApiURL()}/api/reservations/pricing/quote/?${params}`,
        { method: 'GET' }
      )

      setPricingData(response)
    } catch (err) {
      console.error('Error fetching pricing:', err)
      setError('No se pudo obtener la cotización de precios')
    } finally {
      setLoading(false)
    }
  }

  // Cargar cotización cuando cambien los valores relevantes
  useEffect(() => {
    fetchPricingQuote()
  }, [values.room, values.guests, values.check_in, values.check_out])

  // Formatear fecha para mostrar
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

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <SpinnerData />
        <p className="mt-4 text-gray-600">Calculando precios...</p>
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
          Reintentar
        </button>
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
          Completa la información básica
        </p>
        <p className="text-gray-500 text-sm">
          Selecciona hotel, habitación, fechas y número de huéspedes para ver el resumen de pago
        </p>
      </div>
    )
  }

  const roomData = values.room_data

  return (
    <div className="space-y-6">
      {/* Título */}
      <div className="text-center mb-6">
        <h3 className="text-2xl font-bold text-gray-800 mb-2">Resumen de Pago</h3>
        <p className="text-gray-600">Detalle de costos de la reserva</p>
      </div>

      {/* Información de la Habitación */}
      {roomData && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-gray-800 text-lg">{roomData.name}</h4>
              <p className="text-sm text-gray-600">
                Tipo de habitación: {roomData.room_type} • Piso {roomData.floor} • Habitación #{roomData.number}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                Capacidad: {roomData.capacity} huéspedes incluidos (máx. {roomData.max_capacity})
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600">Tarifa base por noche</div>
              <div className="text-xl font-bold text-blue-600">
                {formatCurrency(roomData.base_price)}
              </div>
              {parseFloat(roomData.extra_guest_fee) > 0 && (
                <div className="text-xs text-gray-500 mt-1">
                  + {formatCurrency(roomData.extra_guest_fee)} por huésped extra
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Desglose por Noche */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <h4 className="font-semibold text-gray-800">Desglose por noche</h4>
        </div>
        <div className="divide-y divide-gray-200">
          {pricingData.nights.map((night, index) => {
            const hasExtraGuests = parseFloat(night.extra_guest_fee) > 0
            const hasDiscount = parseFloat(night.discount) > 0
            const hasTax = parseFloat(night.tax) > 0

            return (
              <div key={index} className="px-4 py-3 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <div className="bg-blue-100 text-blue-600 font-semibold text-sm px-3 py-1 rounded-full">
                      Noche {index + 1}
                    </div>
                    <span className="text-gray-700 font-medium">
                      {formatDate(night.date)}
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-gray-800">
                      {formatCurrency(night.total_night)}
                    </div>
                  </div>
                </div>
                
                {/* Detalle de cargos */}
                <div className="ml-20 text-sm text-gray-600 space-y-1">
                  <div className="flex justify-between">
                    <span>Tarifa base</span>
                    <span>{formatCurrency(night.base_rate)}</span>
                  </div>
                  {hasExtraGuests && (
                    <div className="flex justify-between text-blue-600">
                      <span>Huéspedes adicionales</span>
                      <span>+ {formatCurrency(night.extra_guest_fee)}</span>
                    </div>
                  )}
                  {hasDiscount && (
                    <div className="flex justify-between text-green-600">
                      <span>Descuento</span>
                      <span>- {formatCurrency(night.discount)}</span>
                    </div>
                  )}
                  {hasTax && (
                    <div className="flex justify-between">
                      <span>Impuestos</span>
                      <span>+ {formatCurrency(night.tax)}</span>
                    </div>
                  )}
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
            <span className="font-medium">Subtotal ({pricingData.nights.length} {pricingData.nights.length === 1 ? 'noche' : 'noches'})</span>
            <span className="text-lg">
              {formatCurrency(
                pricingData.nights.reduce((sum, n) => sum + parseFloat(n.base_rate), 0)
              )}
            </span>
          </div>
          
          {parseFloat(pricingData.nights.reduce((sum, n) => sum + parseFloat(n.extra_guest_fee), 0)) > 0 && (
            <div className="flex items-center justify-between text-blue-700">
              <span className="font-medium">Cargos por huéspedes adicionales</span>
              <span className="text-lg">
                + {formatCurrency(
                  pricingData.nights.reduce((sum, n) => sum + parseFloat(n.extra_guest_fee), 0)
                )}
              </span>
            </div>
          )}
          
          {parseFloat(pricingData.nights.reduce((sum, n) => sum + parseFloat(n.discount), 0)) > 0 && (
            <div className="flex items-center justify-between text-green-700">
              <span className="font-medium">Descuentos aplicados</span>
              <span className="text-lg">
                - {formatCurrency(
                  pricingData.nights.reduce((sum, n) => sum + parseFloat(n.discount), 0)
                )}
              </span>
            </div>
          )}
          
          {parseFloat(pricingData.nights.reduce((sum, n) => sum + parseFloat(n.tax), 0)) > 0 && (
            <div className="flex items-center justify-between text-gray-700">
              <span className="font-medium">Impuestos</span>
              <span className="text-lg">
                + {formatCurrency(
                  pricingData.nights.reduce((sum, n) => sum + parseFloat(n.tax), 0)
                )}
              </span>
            </div>
          )}
          
          <div className="border-t-2 border-green-300 pt-3 mt-3">
            <div className="flex items-center justify-between">
              <span className="text-xl font-bold text-gray-800">Total a pagar</span>
              <span className="text-3xl font-bold text-green-700">
                {formatCurrency(pricingData.total)}
              </span>
            </div>
          </div>
          
          {/* Información adicional */}
          <div className="text-sm text-gray-600 mt-4 pt-4 border-t border-green-200">
            <div className="flex items-center justify-between">
              <span>Promedio por noche</span>
              <span className="font-semibold">
                {formatCurrency(parseFloat(pricingData.total) / pricingData.nights.length)}
              </span>
            </div>
            <div className="flex items-center justify-between mt-1">
              <span>Huéspedes</span>
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
            <p className="font-medium mb-1">Nota importante:</p>
            <p>
              Este es un resumen preliminar. Los métodos de pago y cargos adicionales
              podrán gestionarse después de crear la reserva.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PaymentInformation