import React from 'react'
import { badgeVariants, badgeSizes } from 'src/utils/badgeVariants'

const Badge = ({ 
  variant = 'default', 
  size = 'md', 
  icon = null, 
  children, 
  className = '',
  ...props 
}) => {
  const variantConfig = badgeVariants[variant] || badgeVariants.default
  const sizeConfig = badgeSizes[size] || badgeSizes.md

  // Icono a mostrar
  const IconComponent = icon || variantConfig.icon

  return (
    <span
      className={`
        inline-flex items-center justify-center
        ${sizeConfig.container}
        ${sizeConfig.spacing}
        ${variantConfig.bg}
        ${variantConfig.text}
        ${variantConfig.border}
        border rounded-full font-medium
        transition-all duration-200
        hover:shadow-sm
        ${className}
      `}
      {...props}
    >
      {IconComponent && (
        <IconComponent 
          className={`${sizeConfig.icon} ${variantConfig.iconColor} flex-shrink-0`}
        />
      )}
      {children && (
        <span className="truncate">
          {children}
        </span>
      )}
    </span>
  )
}

export default Badge
