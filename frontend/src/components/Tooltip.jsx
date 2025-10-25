import { useState, useRef, useEffect } from 'react'

const Tooltip = ({ 
  children, 
  content, 
  position = 'bottom',
  maxWidth = '320px',
  className = '',
  disabled = false
}) => {
  const [isVisible, setIsVisible] = useState(false)
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 })
  const triggerRef = useRef(null)

  const updatePosition = () => {
    if (!triggerRef.current) return

    const triggerRect = triggerRef.current.getBoundingClientRect()
    const scrollY = window.scrollY || document.documentElement.scrollTop

    let top = 0
    let left = 0

    // Calcular la posición del centro del elemento trigger
    const triggerCenterX = triggerRect.left + (triggerRect.width / 2)

    switch (position) {
      case 'bottom':
        top = triggerRect.bottom + scrollY + 8
        left = triggerCenterX
        break
      case 'top':
        top = triggerRect.top + scrollY - 8
        left = triggerCenterX
        break
      case 'left':
        top = triggerRect.top + scrollY + (triggerRect.height / 2)
        left = triggerRect.left - 8
        break
      case 'right':
        top = triggerRect.top + scrollY + (triggerRect.height / 2)
        left = triggerRect.right + 8
        break
      default:
        top = triggerRect.bottom + scrollY + 8
        left = triggerCenterX
    }

    setTooltipPosition({ top, left })
  }

  const showTooltip = () => {
    if (!disabled) {
      setIsVisible(true)
      // Actualizar posición después de que se renderice
      setTimeout(() => {
        updatePosition()
      }, 0)
    }
  }

  const hideTooltip = () => {
    setIsVisible(false)
  }

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
        className="inline-block"
      >
        {children}
      </div>

      {isVisible && (
        <div
          className={`fixed z-50 px-3 py-2 text-sm text-white bg-gray-900 rounded-lg shadow-xl border border-gray-700 ${className}`}
          style={{
            top: `${tooltipPosition.top}px`,
            left: `${tooltipPosition.left}px`,
            maxWidth: maxWidth,
            pointerEvents: 'none',
            transform: 'translateX(-50%)'
          }}
        >
          {content}
          
          {/* Flecha del tooltip */}
          <div
            className={`absolute w-2 h-2 bg-gray-900 border-gray-700 transform rotate-45 ${
              position === 'top' ? 'top-full left-1/2 -translate-x-1/2 -mt-1 border-r border-b' :
              position === 'bottom' ? 'bottom-full left-1/2 -translate-x-1/2 -mb-1 border-l border-t' :
              position === 'left' ? 'left-full top-1/2 -translate-y-1/2 -ml-1 border-t border-r' :
              'right-full top-1/2 -translate-y-1/2 -mr-1 border-b border-l'
            }`}
          />
        </div>
      )}
    </>
  )
}

export default Tooltip
