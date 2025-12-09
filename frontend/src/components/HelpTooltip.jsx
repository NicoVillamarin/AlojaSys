import React, { useState } from 'react'
import QuestionIcon from 'src/assets/icons/QuestionIcon'

/**
 * Componente de tooltip de ayuda con icono de pregunta
 * Muestra un tooltip al pasar el mouse sobre el icono
 */
const HelpTooltip = ({ text, className = '' }) => {
  const [isVisible, setIsVisible] = useState(false)

  if (!text) return null

  return (
    <div className={`relative inline-flex items-center ${className}`}>
      <div
        className="cursor-help group"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
      >
        <QuestionIcon size="16" className="text-gray-400 group-hover:text-gray-600 transition-colors" />
      </div>
      
      {isVisible && (
        <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 z-50 w-72 pointer-events-none">
          <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2.5 shadow-xl">
            <div className="whitespace-pre-line leading-relaxed">{text}</div>
            {/* Flecha del tooltip */}
            <div className="absolute left-1/2 -translate-x-1/2 bottom-full w-0 h-0 border-l-[6px] border-r-[6px] border-b-[6px] border-transparent border-b-gray-900"></div>
          </div>
        </div>
      )}
    </div>
  )
}

export default HelpTooltip

