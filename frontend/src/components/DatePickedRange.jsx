import { useEffect, useMemo, useRef, useState } from 'react'
import { DateRange } from 'react-date-range'
import { parseISO, isValid as isValidDate, format } from 'date-fns'
import es from 'date-fns/locale/es'
import 'react-date-range/dist/styles.css'
import 'react-date-range/dist/theme/default.css'
import Button from './Button'
import LabelsContainer from './inputs/LabelsContainer'

function toDate(value) {
  if (!value) return new Date()
  if (value instanceof Date) return value
  const d = parseISO(String(value))
  return isValidDate(d) ? d : new Date()
}

function toISODate(d) {
  if (!(d instanceof Date) || !isValidDate(d)) return ''
  return format(d, 'yyyy-MM-dd')
}

const DatePickedRange = ({
  label = 'Rango de fechas',
  startDate,
  endDate,
  minDate,
  maxDate,
  onChange,
  months = 1,
  placeholder = 'DD-MM-YYYY — DD-MM-YYYY',
  inputClassName = '',
  displayFormat = 'dd-MM-yyyy',
  containerClassName = 'col-span-2',
  reservationsList = [], // Array de reservas para mostrar en el panel lateral
  occupiedNights = [], // Array de fechas ocupadas en formato 'YYYY-MM-DD' para indicadores visuales
  onApply, // Callback al presionar "Aplicar" (startISO, endISO). Si retorna false, no se cierra.
}) => {
  const [open, setOpen] = useState(false)
  const wrapperRef = useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if (!wrapperRef.current) return
      if (!wrapperRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const display = useMemo(() => {
    const s = startDate ? format(toDate(startDate), displayFormat) : ''
    const e = endDate ? format(toDate(endDate), displayFormat) : ''
    if (s && e) return `${s} — ${e}`
    if (s) return `${s} — `
    return ''
  }, [startDate, endDate, displayFormat])

  const selection = useMemo(() => ({
    startDate: toDate(startDate),
    endDate: toDate(endDate || startDate),
    key: 'selection',
  }), [startDate, endDate])

  // Crear Set de fechas ocupadas para búsqueda rápida
  const occupiedSet = useMemo(() => {
    return new Set(occupiedNights || [])
  }, [occupiedNights])

  // Renderer personalizado para mostrar un punto sutil en fechas ocupadas
  const dayContentRenderer = (day) => {
    const dayISO = format(day, 'yyyy-MM-dd')
    const isOccupied = occupiedSet.has(dayISO)
    
    return (
      <div className="relative w-full h-full flex items-center justify-center" style={{ paddingBottom: '8px' }}>
        <span>{format(day, 'd')}</span>
        {isOccupied && (
          <div 
            className="absolute left-1/2 transform -translate-x-1/2 w-2 h-2 rounded-full bg-red-500"
            title="Fecha ocupada"
            style={{ bottom: '13px', left: '34px' }}
          />
        )}
      </div>
    )
  }

  return (
    <div className={containerClassName} ref={wrapperRef}>
      <div className="relative">
          <LabelsContainer title={label} />
        <div className="flex items-center pt-1">
          <input
            readOnly
            value={display}
            onClick={() => setOpen((v) => !v)}
            placeholder={placeholder}
            className={`w-full border border-gray-300 rounded-md px-3 py-2 pr-10 focus:outline-none focus:ring-2 focus:ring-aloja-navy/20 focus:border-aloja-navy/50 ${inputClassName}`}
          />
          {display && (
            <button
              type="button"
              onClick={() => { onChange && onChange('', ''); setOpen(false) }}
              className="-ml-9 text-gray-500 hover:text-gray-700"
              aria-label="Limpiar rango"
            >
              ✕
            </button>
          )}
        </div>

        {open && (
          <div className="absolute z-50 mt-2 bg-white border-0 rounded-2xl shadow-2xl overflow-hidden backdrop-blur-sm">
            <style jsx>{`
              .rdrDefinedRangesWrapper {
                display: none;
              }
              .rdrDateDisplayWrapper {
                display: none;
              }
            `}</style>
            <div className="flex">
              {/* Panel lateral con reservas existentes */}
              {reservationsList && reservationsList.length > 0 && (
                <div className="w-64 border-r border-gray-200 bg-gray-50 flex flex-col" style={{ minHeight: '380px' }}>
                  <div className="px-4 py-3 border-b border-gray-200 bg-white">
                    <h3 className="text-sm font-semibold text-gray-900">Reservas Existentes</h3>
                    <p className="text-xs text-gray-500 mt-1">{reservationsList.length} reserva{reservationsList.length !== 1 ? 's' : ''}</p>
                  </div>
                  <div className="flex-1 overflow-y-auto" style={{ maxHeight: '340px' }}>
                    <div className="p-3 space-y-2">
                      {reservationsList.map((reservation, index) => {
                        const checkInDate = toDate(reservation.check_in)
                        const checkOutDate = toDate(reservation.check_out)
                        const nights = Math.ceil((checkOutDate - checkInDate) / (1000 * 60 * 60 * 24))
                        const checkInStr = format(checkInDate, 'dd/MM', { locale: es })
                        const checkOutStr = format(checkOutDate, 'dd/MM', { locale: es })
                        
                        return (
                          <div
                            key={reservation.id || index}
                            className="bg-white border border-gray-200 rounded-lg p-3 hover:border-blue-300 transition-colors"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-semibold text-gray-900">Reserva N° {reservation.id || 'N/A'}</span>
                                {reservation.status === 'check_in' && (
                                  <span className="px-1.5 py-0.5 text-[10px] font-medium bg-amber-100 text-amber-800 rounded">
                                    Ocupada
                                  </span>
                                )}
                                {reservation.status === 'confirmed' && (
                                  <span className="px-1.5 py-0.5 text-[10px] font-medium bg-blue-100 text-blue-800 rounded">
                                    Confirmada
                                  </span>
                                )}
                              </div>
                            </div>
                            <div className="text-sm text-gray-900 font-medium mb-1">
                              {checkInStr} → {checkOutStr}
                            </div>
                            <div className="text-xs text-gray-500">
                              {nights} noche{nights !== 1 ? 's' : ''}
                              {reservation.guest_name && (
                                <span className="ml-2">• {reservation.guest_name}</span>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>
              )}
              
              {/* Calendario con indicadores sutiles de ocupación */}
              <div className="flex-1">
                <DateRange
                  editableDateInputs={false}
                  onChange={(item) => {
                    if (item?.selection?.key === 'selection') {
                      let s = item?.selection?.startDate
                      let e = item?.selection?.endDate
                      if (s && e && s > e) [s, e] = [e, s]
                      if (onChange) onChange(toISODate(s), toISODate(e))
                    }
                  }}
                  moveRangeOnFirstSelection={false}
                  ranges={[selection]}
                  months={months}
                  direction="horizontal"
                  locale={es}
                  showDateDisplay={false}
                  rangeColors={["#D4AF37"]}
                  minDate={minDate ? toDate(minDate) : undefined}
                  maxDate={maxDate ? toDate(maxDate) : undefined}
                  dayContentRenderer={occupiedNights.length > 0 ? dayContentRenderer : undefined}
                />
              </div>
            </div>
            <div className="flex justify-start items-center gap-3 px-4 py-3 bg-gradient-to-r from-gray-50 to-gray-100 border-t border-gray-200">
              <Button
                variant="danger"
                size="sm"
                onClick={() => { onChange && onChange('', ''); setOpen(false) }}
              >
                Limpiar
              </Button>
              <Button
                variant="success"
                size="sm"
                onClick={() => {
                  const s = startDate || ''
                  const e = endDate || ''
                  const shouldClose = onApply ? onApply(s, e) : true
                  if (shouldClose !== false) {
                    setOpen(false)
                  }
                }}
              >
                Aplicar
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default DatePickedRange
