import React from 'react'

const BedAvailableIcon = ({ className = "w-5 h-5" }) => {
  return (
    <svg 
      className={className} 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Cama de perfil - colchón */}
      <rect 
        x="4" 
        y="12" 
        width="16" 
        height="8" 
        rx="2" 
        fill="currentColor" 
        stroke="currentColor" 
        strokeWidth="1"
      />
      
      {/* Cabecera de la cama */}
      <rect 
        x="2" 
        y="8" 
        width="6" 
        height="12" 
        rx="1" 
        fill="currentColor" 
        stroke="currentColor" 
        strokeWidth="1"
      />
      
      {/* Check verde bien visible */}
      <circle 
        cx="18" 
        cy="6" 
        r="3" 
        fill="#10B981"
        stroke="white" 
        strokeWidth="1"
      />
      <path 
        d="M16.2 6L17.5 7.5L19.8 4.2" 
        stroke="white" 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
    </svg>
  )
}

export default BedAvailableIcon
