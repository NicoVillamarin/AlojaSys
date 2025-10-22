import { useEffect, useMemo, useRef, useState } from 'react'
import { DateRange } from 'react-date-range'
import { parseISO, isValid as isValidDate, format } from 'date-fns'
import es from 'date-fns/locale/es'
import 'react-date-range/dist/styles.css'
import 'react-date-range/dist/theme/default.css'
import Button from './Button'

function toDate(value) {
  if (!value) return new Date()
  if (value instanceof Date) return value
  // Espera YYYY-MM-DD (o ISO). Usar parseISO para evitar desfases TZ
  const d = parseISO(String(value))
  return isValidDate(d) ? d : new Date()
}

function toISODate(d) {
  if (!(d instanceof Date) || !isValidDate(d)) return ''
  // Formato yyyy-MM-dd en local sin aplicar TZ
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
  occupiedDates = [], // Array de fechas ocupadas en formato YYYY-MM-DD
}) => {
  const selection = useMemo(() => ({
    startDate: toDate(startDate),
    endDate: toDate(endDate || startDate),
    key: 'selection',
  }), [startDate, endDate])

  // Crear rangos de fechas ocupadas para que se vean como el rango dorado
  const occupiedRanges = useMemo(() => {
    console.log('DatePickedRange - occupiedDates recibidas:', occupiedDates)
    
    if (!occupiedDates.length) {
      console.log('DatePickedRange - No hay fechas ocupadas')
      return []
    }
    
    // Agrupar fechas consecutivas en rangos
    const ranges = []
    let currentRange = null
    
    occupiedDates.forEach((date, index) => {
      const currentDate = toDate(date)
      const prevDate = index > 0 ? toDate(occupiedDates[index - 1]) : null
      
      if (!prevDate || currentDate.getTime() - prevDate.getTime() !== 24 * 60 * 60 * 1000) {
        // Nueva fecha o no consecutiva, crear nuevo rango
        if (currentRange) {
          ranges.push(currentRange)
        }
        currentRange = {
          startDate: currentDate,
          endDate: currentDate,
          key: `occupied-${index}`,
        }
      } else {
        // Fecha consecutiva, extender rango actual
        if (currentRange) {
          currentRange.endDate = currentDate
        }
      }
    })
    
    if (currentRange) {
      ranges.push(currentRange)
    }
    
    console.log('DatePickedRange - Rangos ocupados creados:', ranges)
    return ranges
  }, [occupiedDates])

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

  // Función para verificar si una fecha está ocupada
  const isDateOccupied = (date) => {
    if (!date || !occupiedDates.length) return false
    const dateStr = toISODate(date)
    return occupiedDates.includes(dateStr)
  }

  return (
    <div className={containerClassName} ref={wrapperRef}>
      <div className="text-sm font-medium text-gray-700 mb-2">{label}</div>
      <div className="relative">
        <div className="flex items-center">
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
            <DateRange
              editableDateInputs={false}
              onChange={(item) => {
                // Solo procesar cambios en el rango de selección, no en los ocupados
                if (item?.selection?.key === 'selection') {
                  let s = item?.selection?.startDate
                  let e = item?.selection?.endDate
                  // Asegurar orden (s <= e)
                  if (s && e && s > e) [s, e] = [e, s]
                  if (onChange) onChange(toISODate(s), toISODate(e))
                }
              }}
              moveRangeOnFirstSelection={false}
              ranges={[selection, ...occupiedRanges]}
              months={months}
              direction="horizontal"
              shownDate={selection.startDate || new Date()}
              locale={es}
              showDateDisplay={false}
              rangeColors={["#D4AF37", "#DC2626"]}
              minDate={minDate ? toDate(minDate) : undefined}
              maxDate={maxDate ? toDate(maxDate) : undefined}
              disabledDates={occupiedDates.map(date => toDate(date))}
            />
            <div className="flex justify-start items-center gap-3 px-4 py-3 bg-gradient-to-r from-gray-50 to-gray-100 border-t border-gray-200">
              <Button
                variant="danger"
                size="sm"
                onClick={() => { onChange && onChange('', ''); setOpen(false) }}
              >
                Limpiar
              </Button>
              <Button variant="success" size="sm"  onClick={() => setOpen(false)}>
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