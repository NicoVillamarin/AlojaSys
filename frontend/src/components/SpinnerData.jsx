import React from 'react'
import PropTypes from 'prop-types'
import logoImage from '../assets/img/logo_new_alone.png'

/**
 * SpinnerData: spinner mejorado con dos líneas giratorias y logo central
 * Diseño: dos líneas que giran en direcciones opuestas con logo en el centro
 * Props:
 * - size: px (default 64)
 * - label: texto opcional (default null)
 * - inline: si true, alinea en fila
 */
const SpinnerData = ({ size = 64, label = null, inline = true, className = '' }) => {
  const px = typeof size === 'number' ? size : 64
  const logoSize = Math.max(px * 0.5, 24) // Logo será 50% del tamaño del spinner
  
  return (
    <div className={`${inline ? 'inline-flex items-center gap-2' : 'flex flex-col items-center gap-2'} ${className}`} role="status" aria-live="polite">
      <div className="relative" style={{ width: px, height: px }}>
        {/* Círculo exterior - gira en sentido horario */}
        <div 
          className="absolute inset-0 border-2 border-gray-200 rounded-full"
        ></div>
        
        {/* Círculo de carga principal - exterior */}
        <div 
          className="absolute inset-0 border-2 border-transparent border-t-yellow-400 rounded-full animate-spin"
          style={{ animationDuration: '2s' }}
        ></div>
        
        {/* Círculo interior - gira en sentido antihorario */}
        <div 
          className="absolute inset-2 border border-transparent border-r-yellow-300 rounded-full animate-spin"
          style={{ animationDuration: '3s', animationDirection: 'reverse' }}
        ></div>
        
        {/* Logo central */}
        <div 
          className="absolute inset-0 flex items-center justify-center"
          style={{ 
            width: logoSize, 
            height: logoSize,
            left: '50%',
            top: '50%',
            transform: 'translate(-50%, -50%)'
          }}
        >
          <img 
            src={logoImage} 
            alt="AlojaSys" 
            className="w-full h-full object-contain"
            style={{ width: logoSize, height: logoSize }}
          />
        </div>
      </div>
      {!!label && <span className="text-xs text-aloja-gray-800/70 select-none">{label}</span>}
    </div>
  )
}

SpinnerData.propTypes = {
  size: PropTypes.number,
  label: PropTypes.node,
  inline: PropTypes.bool,
  className: PropTypes.string,
}

export default SpinnerData


