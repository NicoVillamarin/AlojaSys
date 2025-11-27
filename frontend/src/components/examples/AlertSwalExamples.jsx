import React from 'react'
import { useTranslation } from 'react-i18next'
import AlertSwal from 'src/components/AlertSwal'
import TrashIcon from 'src/assets/icons/TrashIcon'
import Button from 'src/components/Button'

// Ejemplos de uso del componente AlertSwal
const AlertSwalExamples = () => {
  const { t } = useTranslation()

  const handleDelete = async () => {
    // Simular resultado
    return { updated_count: 5 }
  }

  const handleArchive = async () => {
    return { updated_count: 1 }
  }

  return (
    <div className="space-y-4 p-4">
      <h2 className="text-xl font-semibold">Ejemplos de AlertSwal</h2>
      
      <div className="space-x-2">
        {/* Ejemplo 1: Como DeleteButton (icono de basura) */}
        <AlertSwal
          onConfirm={handleDelete}
          confirmTitle="Eliminar Registro"
          confirmMessage="¿Estás seguro que querés eliminar este registro? Esta acción no se puede deshacer."
          confirmText="Eliminar"
          cancelText="Cancelar"
          tone="danger"
          successTitle="Eliminado"
          successMessage="Se eliminaron {{count}} registros exitosamente."
          className="text-red-500"
        >
          <TrashIcon size="20" />
        </AlertSwal>

        {/* Ejemplo 2: Botón personalizado */}
        <AlertSwal
          onConfirm={handleArchive}
          confirmTitle="Archivar Registro"
          confirmMessage="¿Querés archivar este registro? Podrás restaurarlo más tarde."
          confirmText="Archivar"
          cancelText="Cancelar"
          tone="warning"
          successTitle="Archivado"
          successMessage="El registro fue archivado exitosamente."
        >
          <Button variant="secondary" size="sm">
            Archivar
          </Button>
        </AlertSwal>

        {/* Ejemplo 3: Texto simple */}
        <AlertSwal
          onConfirm={handleDelete}
          confirmTitle="Confirmar Acción"
          confirmMessage="¿Estás seguro de realizar esta acción?"
          confirmText="Sí"
          cancelText="No"
          tone="info"
          successTitle="Completado"
          successMessage="La acción se completó exitosamente."
          className="text-blue-600 underline cursor-pointer"
        >
          Hacer algo
        </AlertSwal>
      </div>
    </div>
  )
}

export default AlertSwalExamples
