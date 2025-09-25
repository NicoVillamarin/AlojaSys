import React from 'react'
import PropTypes from 'prop-types'

/**
 * SpinnerLoading: spinner animado con temática hotelera (campana de conserjería)
 * Props:
 * - size: número en px (default 80 para vistas completas)
 * - label: texto accesible/visible (default "Cargando…"). Si null/'' no se muestra.
 * - inline: si true, renderiza en fila (útil para botones/indicadores pequeños)
 * - className: clases extras del contenedor
 */
const SpinnerLoading = ({ size = 80, label = 'Cargando…', inline = false, className = '' }) => {
  const px = typeof size === 'number' ? size : 56

  return (
    <div
      role="status"
      aria-live="polite"
      className={`${inline ? 'inline-flex items-center gap-2' : 'flex flex-col items-center gap-3'} ${className}`}
    >
      <div className="relative" style={{ width: px, height: px }} aria-hidden="true">
        {/* halo */}
        <span
          className="absolute inset-0 rounded-full bg-aloja-navy/10 animate-ping"
          style={{ filter: 'blur(0.5px)' }}
        />

        {/* campana */}
        <svg
          viewBox="0 0 64 64"
          width={px}
          height={px}
          className="relative block"
        >
          <defs>
            <linearGradient id="bellGrad" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#1d2b53" />
              <stop offset="100%" stopColor="#233a7a" />
            </linearGradient>
            <linearGradient id="baseGrad" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#e5e7eb" />
              <stop offset="100%" stopColor="#c7ccd4" />
            </linearGradient>
          </defs>

          {/* sombra */}
          <ellipse cx="32" cy="54" rx="16" ry="3" fill="rgba(0,0,0,0.12)" />

          {/* grupo animado de la campana */}
          <g className="aloja-bell" style={{ transformOrigin: '32px 44px' }}>
            {/* botón superior */}
            <circle cx="32" cy="18" r="3" fill="url(#baseGrad)" />

            {/* cúpula */}
            <path d="M16 40a16 16 0 0132 0v2H16v-2z" fill="url(#bellGrad)" />

            {/* brillo */}
            <path d="M24 32c2-6 14-8 16-6" fill="none" stroke="#9fb4ff" strokeOpacity="0.6" strokeWidth="2" strokeLinecap="round" />

            {/* base */}
            <rect x="18" y="42" width="28" height="6" rx="3" fill="url(#baseGrad)" />
          </g>

          {/* estrellas decorativas */}
          <g className="aloja-stars" fill="#ffcc66">
            <circle cx="8" cy="10" r="1.2" />
            <circle cx="58" cy="14" r="1.6" />
            <circle cx="10" cy="28" r="1" />
          </g>
        </svg>

        <style>{`
@keyframes alojaBellRing {
  0% { transform: rotate(0deg); }
  10% { transform: rotate(-12deg); }
  20% { transform: rotate(9deg); }
  30% { transform: rotate(-6deg); }
  40% { transform: rotate(4deg); }
  50% { transform: rotate(-2deg); }
  60% { transform: rotate(1deg); }
  70%, 100% { transform: rotate(0deg); }
}
@keyframes alojaStarTwinkle {
  0%, 100% { opacity: 0.25; transform: scale(0.9) translateY(0); }
  50% { opacity: 1; transform: scale(1.05) translateY(-1px); }
}
.aloja-bell { animation: alojaBellRing 1200ms ease-in-out infinite; }
.aloja-stars > circle { animation: alojaStarTwinkle 1600ms ease-in-out infinite; }
.aloja-stars > circle:nth-child(2) { animation-delay: 300ms; }
.aloja-stars > circle:nth-child(3) { animation-delay: 600ms; }
        `}</style>
      </div>
    </div>
  )
}

SpinnerLoading.propTypes = {
  size: PropTypes.number,
  label: PropTypes.node,
  inline: PropTypes.bool,
  className: PropTypes.string,
}

export default SpinnerLoading