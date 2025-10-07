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
}) => {
  const selection = useMemo(() => ({
    startDate: toDate(startDate),
    endDate: toDate(endDate || startDate),
    key: 'selection',
  }), [startDate, endDate])

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

  return (
    <div className="col-span-2" ref={wrapperRef}>
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
              .rdrCalendarWrapper {
                background: white;
                border-radius: 16px;
                overflow: hidden;
              }
              .rdrDateRangeWrapper {
                background: white;
              }
              .rdrDefinedRangesWrapper {
                display: none;
              }
              .rdrDateDisplayWrapper {
                display: none;
              }
              .rdrMonths {
                background: white;
              }
              .rdrMonth {
                background: white;
                padding: 8px;
                min-width: 280px;
              }
              .rdrMonthName {
                display: none;
              }
              .rdrWeekDays {
                margin-bottom: 6px;
              }
              .rdrWeekDay {
                font-size: 11px;
                font-weight: 600;
                color: #0A304A;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                padding: 6px 0;
                text-align: center;
              }
              .rdrDays {
                background: white;
                display: grid;
                grid-template-columns: repeat(7, 1fr);
                gap: 3px;
              }
              .rdrDay {
                background: white;
                border: none;
                font-size: 13px;
                font-weight: 500;
                color: #333333;
                height: 36px;
                width: 36px;
                border-radius: 8px;
                margin: 0;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                overflow: hidden;
                padding: 0;
                line-height: 1;
              }
              .rdrDay:hover {
                background: #F5F5F5;
                color: #0A304A;
                transform: scale(1.05);
                box-shadow: 0 2px 8px rgba(10, 48, 74, 0.1);
              }
              .rdrDayInRange:hover {
                background: #B8941F;
                color: white;
                transform: scale(1.05);
                box-shadow: 0 4px 12px rgba(212, 175, 55, 0.4);
              }
              .rdrDayStartOfRange:hover {
                background: #B8941F;
                color: white;
                transform: scale(1.05);
                box-shadow: 0 4px 16px rgba(212, 175, 55, 0.5);
              }
              .rdrDayEndOfRange:hover {
                background: #B8941F;
                color: white;
                transform: scale(1.05);
                box-shadow: 0 4px 16px rgba(212, 175, 55, 0.5);
              }
              .rdrDayNumber {
                color: inherit;
                font-weight: inherit;
                z-index: 1;
                position: static; /* volver al flujo normal para que el subrayado nativo se ubique bien */
                top: auto;
                left: auto;
                transform: none;
                line-height: 1;
                margin: 0;
                padding: 0;
                font-size: 13px;
                display: inline-block;
              }
              .rdrDayPassive {
                color: #EEEEEE;
                opacity: 0.6;
              }
              .rdrDayToday { background: transparent !important; }
              /* Mantener comportamiento por defecto y solo ajustar el color del indicador */
              .rdrDayToday .rdrDayNumber span::after {
                background: #D4AF37 !important; /* igual al color del rango */
              }
              .rdrDayInRange {
                background: #D4AF37;
                color: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(212, 175, 55, 0.3);
                margin: 1px;
                height: 36px;
                width: 36px;
                padding: 0;
                line-height: 1;
              }
              .rdrDayStartOfRange {
                background: #D4AF37;
                color: white;
                border-radius: 8px;
                box-shadow: 0 4px 16px rgba(212, 175, 55, 0.4);
                position: relative;
                margin: 1px;
                height: 36px;
                width: 36px;
                padding: 0;
                line-height: 1;
              }
              .rdrDayStartOfRange::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: #D4AF37;
                border-radius: 8px;
                z-index: -1;
                animation: pulse 2s infinite;
              }
              .rdrDayEndOfRange {
                background: #D4AF37;
                color: white;
                border-radius: 8px;
                box-shadow: 0 4px 16px rgba(212, 175, 55, 0.4);
                margin: 1px;
                height: 36px;
                width: 36px;
                padding: 0;
                line-height: 1;
              }
              .rdrDayInRange:not(.rdrDayStartOfRange):not(.rdrDayEndOfRange) {
                background: rgba(212, 175, 55, 0.2);
                color: #D4AF37;
                border-radius: 8px;
                font-weight: 600;
                margin: 1px;
                height: 36px;
                width: 36px;
                padding: 0;
                line-height: 1;
              }
              .rdrDayStartOfRange:not(.rdrDayEndOfRange) {
                border-top-right-radius: 0;
                border-bottom-right-radius: 0;
              }
              .rdrDayEndOfRange:not(.rdrDayStartOfRange) {
                border-top-left-radius: 0;
                border-bottom-left-radius: 0;
              }
              .rdrDayStartOfRange.rdrDayEndOfRange {
                border-radius: 8px;
              }
              @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.8; }
              }
              .rdrNextPrevButton {
                background: #F5F5F5;
                border: 1px solid #EEEEEE;
                border-radius: 10px;
                width: 28px;
                height: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
              }
              .rdrNextPrevButton:hover {
                background: #0A304A;
                border-color: #0A304A;
                transform: scale(1.1);
                box-shadow: 0 4px 12px rgba(10, 48, 74, 0.3);
                color: white;
              }
              .rdrPprevButton {
                margin-right: 6px;
              }
              .rdrNextButton {
                margin-left: 6px;
              }
              .rdrMonthAndYearWrapper {
                background: white;
                padding: 0 8px;
                margin-bottom: 4px;
              }
              .rdrMonthAndYearPickers {
                font-size: 14px;
                font-weight: 700;
                color: #0A304A;
              }
              .rdrMonthPicker select,
              .rdrYearPicker select {
                background: #F5F5F5;
                border: 1px solid #EEEEEE;
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 13px;
                font-weight: 600;
                color: #333333;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
              }
              .rdrMonthPicker select:hover,
              .rdrYearPicker select:hover {
                border-color: #0A304A;
                box-shadow: 0 0 0 3px rgba(10, 48, 74, 0.1);
                background: #FFFFFF;
              }
            `}</style>
            <DateRange
              editableDateInputs={false}
              onChange={(item) => {
                let s = item?.selection?.startDate
                let e = item?.selection?.endDate
                // Asegurar orden (s <= e)
                if (s && e && s > e) [s, e] = [e, s]
                if (onChange) onChange(toISODate(s), toISODate(e))
              }}
              moveRangeOnFirstSelection={false}
              ranges={[selection]}
              months={months}
              direction="horizontal"
              shownDate={selection.startDate || new Date()}
              locale={es}
              showDateDisplay={false}
              rangeColors={["#D4AF37"]}
              minDate={minDate ? toDate(minDate) : undefined}
              maxDate={maxDate ? toDate(maxDate) : undefined}
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


