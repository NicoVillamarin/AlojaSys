import React from 'react'
import PropTypes from 'prop-types'

/**
 * Button: botón reutilizable con variantes y spinner de carga
 * Props principales:
 * - variant: 'primary' | 'success' | 'danger' | 'neutral' | 'outline' | 'ghost'
 * - size: 'sm' | 'md' | 'lg'
 * - isPending: muestra spinner y deshabilita el botón
 * - leftIcon / rightIcon: nodos opcionales (iconos)
 * - fullWidth: ocupar 100% del ancho
 */
export default function Button({
  children,
  type = 'button',
  variant = 'primary',
  size = 'md',
  isPending = false,
  disabled = false,
  fullWidth = false,
  leftIcon,
  rightIcon,
  className = '',
  onClick,
  loadingText,
}) {
  const base = `relative overflow-hidden cursor-pointer group inline-flex items-center justify-center gap-2 font-medium rounded-md transition focus:outline-none focus:ring-2 focus:ring-offset-1 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 ${
    fullWidth ? 'w-full' : ''
  }`

  const variants = {
    primary: 'text-white bg-gradient-to-b from-aloja-navy to-aloja-navy2 hover:from-aloja-navy2 hover:to-aloja-navy2 shadow-sm',
    success: 'text-white bg-gradient-to-b from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 shadow-sm',
    danger: 'text-white bg-gradient-to-b from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 shadow-sm',
    neutral: 'text-aloja-gray-800 bg-gray-100 hover:bg-gray-200',
    outline: 'text-aloja-navy bg-white border border-gray-300 hover:bg-gray-50',
    ghost: 'text-aloja-navy bg-transparent hover:bg-gray-100',
  }

  const sizes = {
    sm: 'text-sm px-3 py-1.5',
    md: 'text-sm px-3.5 py-2',
    lg: 'text-base px-4 py-2.5',
  }

  const isDisabled = disabled || isPending

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      className={`${base} ${variants[variant] ?? variants.primary} ${sizes[size] ?? sizes.md} ${className}`}
    >
      {/* Sheen hover effect */}
      <span aria-hidden className="pointer-events-none absolute inset-0 z-0">
        <span className="absolute -inset-y-6 -left-1/2 w-1/2 bg-white/20 blur-md -skew-x-12 translate-x-[-120%] group-hover:translate-x-[220%] transition-transform duration-700 ease-out" />
      </span>

      <span className="relative z-[1] inline-flex items-center">
        {isPending && <Spinner className={variant === 'outline' || variant === 'neutral' || variant === 'ghost' ? 'text-aloja-navy' : 'text-white'} />}
        {leftIcon && !isPending ? <span className="shrink-0 mr-1.5">{leftIcon}</span> : null}
        <span>{isPending && loadingText ? loadingText : children}</span>
        {rightIcon && !isPending ? <span className="shrink-0 ml-1.5">{rightIcon}</span> : null}
      </span>
    </button>
  )
}

function Spinner({ className = '' }) {
  return (
    <svg
      className={`animate-spin ${className}`}
      width="16"
      height="16"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" fill="none" opacity="0.25" />
      <path d="M21 12a9 9 0 0 1-9 9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" fill="none" />
    </svg>
  )
}

Spinner.propTypes = {
  className: PropTypes.string,
}

Button.propTypes = {
  children: PropTypes.node,
  type: PropTypes.oneOf(['button', 'submit', 'reset']),
  variant: PropTypes.oneOf(['primary', 'success', 'danger', 'neutral', 'outline', 'ghost']),
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  isPending: PropTypes.bool,
  disabled: PropTypes.bool,
  fullWidth: PropTypes.bool,
  leftIcon: PropTypes.node,
  rightIcon: PropTypes.node,
  className: PropTypes.string,
  onClick: PropTypes.func,
  loadingText: PropTypes.node,
}
