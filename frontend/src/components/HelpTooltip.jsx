import React, { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import QuestionIcon from 'src/assets/icons/QuestionIcon'

/**
 * Componente de tooltip de ayuda con icono de pregunta
 * Muestra un tooltip al pasar el mouse sobre el icono
 */
const HelpTooltip = ({ text, className = '' }) => {
  const [isVisible, setIsVisible] = useState(false)
  const iconRef = useRef(null)
  const tooltipRef = useRef(null)
  const [pos, setPos] = useState(null) // { left, top, placement }

  if (!text) return null

  const TOOLTIP_MAX_WIDTH = 288 // ~ w-72
  const VIEWPORT_MARGIN = 12

  const computePosition = () => {
    const el = iconRef.current
    if (!el) return

    const rect = el.getBoundingClientRect()
    const tipRect = tooltipRef.current?.getBoundingClientRect()
    const width = tipRect?.width || TOOLTIP_MAX_WIDTH
    const height = tipRect?.height || 90

    // Centrar respecto al ícono, con clamp al viewport
    let left = rect.left + rect.width / 2
    left = Math.min(
      Math.max(left, VIEWPORT_MARGIN + width / 2),
      window.innerWidth - VIEWPORT_MARGIN - width / 2
    )

    // Preferir abajo, pero si no entra, mostrar arriba
    const spaceBelow = window.innerHeight - rect.bottom
    const spaceAbove = rect.top
    const offset = 10

    let placement = 'bottom'
    let top = rect.bottom + offset
    if (spaceBelow < height + offset && spaceAbove > height + offset) {
      placement = 'top'
      top = rect.top - offset
    }

    setPos({ left, top, placement })
  }

  // Reposicionar cuando se muestra y ante scroll/resize
  useEffect(() => {
    if (!isVisible) return
    const raf = requestAnimationFrame(() => computePosition())
    const onReflow = () => computePosition()

    window.addEventListener('scroll', onReflow, true)
    window.addEventListener('resize', onReflow)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('scroll', onReflow, true)
      window.removeEventListener('resize', onReflow)
    }
  }, [isVisible])

  const portalTarget = useMemo(() => (typeof document !== 'undefined' ? document.body : null), [])

  return (
    <div className={`relative inline-flex items-center ${className}`}>
      <div
        className="cursor-help group"
        ref={iconRef}
        onMouseEnter={() => {
          setIsVisible(true)
          // 2 ticks: primero renderiza el tooltip, luego medimos tamaño real
          requestAnimationFrame(() => computePosition())
          requestAnimationFrame(() => computePosition())
        }}
        onMouseLeave={() => setIsVisible(false)}
      >
        <QuestionIcon size="16" className="text-gray-400 group-hover:text-gray-600 transition-colors" />
      </div>
      
      {isVisible && portalTarget && pos && createPortal(
        <div
          ref={tooltipRef}
          className="fixed z-[9999] w-72 pointer-events-none"
          style={{
            left: `${pos.left}px`,
            top: `${pos.top}px`,
            transform: pos.placement === 'top' ? 'translate(-50%, -100%)' : 'translateX(-50%)'
          }}
        >
          <div className="relative bg-gray-900 text-white text-xs rounded-lg px-3 py-2.5 shadow-xl">
            <div className="whitespace-pre-line leading-relaxed">{text}</div>
            {/* Flecha del tooltip */}
            {pos.placement === 'bottom' ? (
              <div className="absolute left-1/2 -translate-x-1/2 bottom-full w-0 h-0 border-l-[6px] border-r-[6px] border-b-[6px] border-transparent border-b-gray-900"></div>
            ) : (
              <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-transparent border-t-gray-900"></div>
            )}
          </div>
        </div>,
        portalTarget
      )}
    </div>
  )
}

export default HelpTooltip

