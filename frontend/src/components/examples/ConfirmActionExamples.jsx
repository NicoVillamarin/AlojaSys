import React from 'react'
import { useTranslation } from 'react-i18next'
import ConfirmActionButton from 'src/components/ConfirmActionButton'
import TrashIcon from 'src/assets/icons/TrashIcon'

// Ejemplos de uso del componente ConfirmActionButton
const ConfirmActionExamples = () => {
  const { t } = useTranslation()

  const handleDelete = () => {
    console.log('Eliminando...')
  }

  const handleArchive = () => {
    console.log('Archivando...')
  }

  const handlePublish = () => {
    console.log('Publicando...')
  }

  return (
    <div className="space-y-4 p-4">
      <h2 className="text-xl font-semibold">Ejemplos de ConfirmActionButton</h2>
      
      <div className="space-x-2">
        {/* Ejemplo 1: Botón de eliminar (peligroso) */}
        <ConfirmActionButton
          variant="danger"
          size="sm"
          onConfirm={handleDelete}
          confirmTitle="Eliminar Registro"
          confirmMessage="¿Estás seguro que querés eliminar este registro? Esta acción no se puede deshacer."
          confirmText="Eliminar"
          cancelText="Cancelar"
          tone="danger"
          title="Eliminar registro"
        >
          <TrashIcon size="16" />
        </ConfirmActionButton>

        {/* Ejemplo 2: Botón de archivar (advertencia) */}
        <ConfirmActionButton
          variant="secondary"
          size="md"
          onConfirm={handleArchive}
          confirmTitle="Archivar Registro"
          confirmMessage="¿Querés archivar este registro? Podrás restaurarlo más tarde."
          confirmText="Archivar"
          cancelText="Cancelar"
          tone="warning"
          title="Archivar registro"
        >
          Archivar
        </ConfirmActionButton>

        {/* Ejemplo 3: Botón de publicar (éxito) */}
        <ConfirmActionButton
          variant="primary"
          size="lg"
          onConfirm={handlePublish}
          confirmTitle="Publicar Contenido"
          confirmMessage="¿Estás listo para publicar este contenido? Será visible para todos los usuarios."
          confirmText="Publicar"
          cancelText="Cancelar"
          tone="success"
          title="Publicar contenido"
        >
          Publicar
        </ConfirmActionButton>

        {/* Ejemplo 4: Botón deshabilitado */}
        <ConfirmActionButton
          variant="secondary"
          size="md"
          onConfirm={handleDelete}
          disabled={true}
          confirmTitle="Acción Deshabilitada"
          confirmMessage="Esta acción está temporalmente deshabilitada."
          confirmText="OK"
          tone="info"
          title="Acción no disponible"
        >
          Deshabilitado
        </ConfirmActionButton>
      </div>
    </div>
  )
}

export default ConfirmActionExamples
