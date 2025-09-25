import React, { useState } from 'react'
import PropTypes from 'prop-types'
import { useDelete } from 'src/hooks/useDelete'
import TrashIcon from 'src/assets/icons/TrashIcon'
import ValidateAction from 'src/components/ValidateAction'


const DeleteButton = ({ resource, id, onDeleted, confirmMessage = '¿Estás seguro que querés eliminar este registro?' , title = 'Eliminar registro'}) => {
  const { mutate: doDelete, isPending } = useDelete({ resource })
  const [open, setOpen] = useState(false)

  const handleConfirm = () => {
    doDelete(id, {
      onSuccess: (data) => {
        setOpen(false)
        onDeleted && onDeleted(data)
      },
    })
  }

  return (
    <>
      <span className="cursor-pointer text-red-500" onClick={() => setOpen(true)} aria-label="Eliminar" title="Eliminar">
        <TrashIcon size="20" />
      </span>
      <ValidateAction
        isOpen={open}
        onClose={() => setOpen(false)}
        title={title}
        description={confirmMessage}
        confirmText="Eliminar"
        tone="danger"
        confirmLoading={isPending}
        onConfirm={handleConfirm}
      />
    </>
  )
}

DeleteButton.propTypes = {
    resource: PropTypes.string.isRequired,
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    onDeleted: PropTypes.func,
    confirmMessage: PropTypes.string,
    title: PropTypes.string,
}

export default DeleteButton