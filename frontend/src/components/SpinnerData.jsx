import React from 'react'
import PropTypes from 'prop-types'

/**
 * SpinnerData: spinner chico para cargas de datos (llamadas), temática hotelera
 * Icono: llavero con llave
 * Props:
 * - size: px (default 24)
 * - label: texto opcional (default null)
 * - inline: si true, alinea en fila
 */
const SpinnerData = ({ size = 24, label = null, inline = true, className = '' }) => {
  const px = typeof size === 'number' ? size : 24
  return (
    <div className={`${inline ? 'inline-flex items-center gap-2' : 'flex flex-col items-center gap-2'} ${className}`} role="status" aria-live="polite">
      <svg viewBox="0 0 64 64" width={px} height={px} aria-hidden="true" className="block">
        <defs>
          <linearGradient id="keyGrad" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#d4af37" />
            <stop offset="100%" stopColor="#b48a1f" />
          </linearGradient>
        </defs>
        {/* aro */}
        <circle cx="24" cy="24" r="10" fill="none" stroke="url(#keyGrad)" strokeWidth="4" className="origin-center animate-[spin_1200ms_linear_infinite]" />
        {/* llave */}
        <g transform="translate(30,30)">
          <path d="M0 0 l16 0 l0 4 l-4 0 l0 4 l-4 0 l0 4 l-8 0 z" fill="url(#keyGrad)" opacity="0.9" />
        </g>
      </svg>
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


