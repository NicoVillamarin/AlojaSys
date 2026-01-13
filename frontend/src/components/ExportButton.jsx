import React from 'react'
import Button from 'src/components/Button'
import SaveIcon from 'src/assets/icons/SaveIcon'

/**
 * Botón reutilizable para acciones de exportación.
 * - Usa el componente Button del sistema (spinner vía isPending)
 * - Incluye icono por defecto (SaveIcon)
 */
export default function ExportButton({
  onClick,
  isPending = false,
  disabled = false,
  children = 'Exportar Excel',
  loadingText = 'Exportando...',
  variant = 'success',
  size = 'sm',
  leftIcon,
  className = '',
}) {
  return (
    <Button
      onClick={onClick}
      isPending={isPending}
      disabled={disabled}
      loadingText={loadingText}
      variant={variant}
      size={size}
      leftIcon={leftIcon ?? <SaveIcon size="18" />}
      className={className}
    >
      {children}
    </Button>
  )
}

