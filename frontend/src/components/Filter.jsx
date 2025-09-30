import React, { useState } from 'react'
import FilterIcon from 'src/assets/icons/FilterIcon'

const Filter = ({ children, title = "Filtros de búsqueda", className = "" }) => {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className={`w-full ${className}`}>
      {/* Botón compacto - solo el ancho necesario */}
      <div className="flex justify-start">
        <button 
          className="inline-flex items-center gap-2 px-3 py-2 bg-white rounded-xl shadow hover:shadow-md transition-all duration-200 group"
          onClick={() => setIsOpen(!isOpen)}
        >
          <div className="p-1 rounded-md bg-aloja-navy/10 group-hover:bg-aloja-navy/20 transition-colors">
            <FilterIcon />
          </div>
          <span className="text-sm font-medium text-aloja-gray-800">Filtros de búsqueda</span>
          <svg 
            className={`w-3.5 h-3.5 text-aloja-gray-600 transition-transform duration-300 ease-in-out ${isOpen ? 'rotate-180' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Contenido expandido con animación */}
      <div 
        className={`transition-all duration-300 ease-in-out ${
          isOpen 
            ? 'max-h-96 opacity-100 mt-3' 
            : 'max-h-0 opacity-0 mt-0 overflow-hidden'
        }`}
      >
        <div className="bg-white rounded-xl shadow border border-gray-200 px-4 py-3 relative z-50">
          {children}
        </div>
      </div>
    </div>
  )
}

export default Filter