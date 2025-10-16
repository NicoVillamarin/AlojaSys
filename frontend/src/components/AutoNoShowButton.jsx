import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import fetchWithAuth from 'src/services/fetchWithAuth'
import { getApiURL } from 'src/services/utils'
import AlertSwal from 'src/components/AlertSwal'
import Button from 'src/components/Button'

const AutoNoShowButton = ({ 
  selectedHotel, 
  hasAutoNoShowEnabled, 
  onSuccess 
}) => {
  const { t } = useTranslation()
  const [showAlert, setShowAlert] = useState(false)
  const [showSuccessAlert, setShowSuccessAlert] = useState(false)
  const [successData, setSuccessData] = useState(null)

  // Hook para auto no-show
  const { mutate: autoNoShowAction, isPending: autoNoShowPending } = useMutation({
    mutationFn: async () => {
      return await fetchWithAuth(`${getApiURL()}/api/reservations/auto-no-show/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      });
    },
    onSuccess: (data) => {
      onSuccess && onSuccess();
      setShowAlert(false)
      setSuccessData(data)
      setShowSuccessAlert(true)
    },
    onError: (error) => {
      // Error handling is now done by AlertSwal
      setShowAlert(false)
    }
  })

  const handleAutoNoShow = async () => {
    try {
      await autoNoShowAction();
    } catch (error) {
      console.error('Error en auto no-show:', error)
    }
  }

  // No mostrar el botón si no hay hotel seleccionado o si ya tiene auto no-show habilitado
  if (!selectedHotel || hasAutoNoShowEnabled) {
    return null
  }

  // Preparar el mensaje de éxito con el count
  const getSuccessMessage = () => {
    let message = t('dashboard.reservations_management.messages.auto_no_show_success', { count: '{{count}}' })
    if (successData && typeof successData === 'object' && successData.updated_count !== undefined) {
      message = message.replace('{{count}}', successData.updated_count)
    }
    return message
  }

  return (
    <>
      <Button 
        variant="secondary" 
        size="md" 
        disabled={autoNoShowPending}
        title={t('dashboard.reservations_management.tooltips.auto_no_show_manual')}
        onClick={() => setShowAlert(true)}
      >
        {autoNoShowPending ? t('common.loading') : t('dashboard.reservations_management.actions.auto_no_show')}
      </Button>

      {/* Modal de confirmación */}
      <AlertSwal
        isOpen={showAlert}
        onClose={() => setShowAlert(false)}
        onConfirm={handleAutoNoShow}
        confirmLoading={autoNoShowPending}
        title={t('dashboard.reservations_management.confirmations.auto_no_show_title')}
        description={t('dashboard.reservations_management.confirmations.auto_no_show')}
        confirmText={t('common.yes')}
        cancelText={t('common.cancel')}
        tone="warning"
      />

      {/* Modal de éxito */}
      <AlertSwal
        isOpen={showSuccessAlert}
        onClose={() => setShowSuccessAlert(false)}
        onConfirm={() => setShowSuccessAlert(false)}
        confirmLoading={false}
        title={t('dashboard.reservations_management.messages.auto_no_show_success_title')}
        description={getSuccessMessage()}
        confirmText={t('common.ok')}
        cancelText=""
        tone="success"
      />
    </>
  )
}

export default AutoNoShowButton
