import { useState } from 'react'
import { useDispatchAction } from 'src/hooks/useDispatchAction'
import Button from 'src/components/Button'
import { useGet } from 'src/hooks/useGet'
import SpinnerData from 'src/components/SpinnerData'

export default function InvoiceGenerationButton({ paymentId, onSuccess, disabled = false }) {
  const [isGenerating, setIsGenerating] = useState(false)
  
  // Verificar si ya existe una factura para este pago
  const { data: existingInvoice, isLoading: checkingInvoice } = useGet({
    resource: 'invoicing/invoices',
    params: { payment: paymentId },
    enabled: !!paymentId
  })

  const { mutate: generateInvoice } = useDispatchAction({
    resource: 'invoicing/invoices',
    onSuccess: (data) => {
      setIsGenerating(false)
      onSuccess?.(data)
    },
    onError: (error) => {
      setIsGenerating(false)
      console.error('Error generando factura:', error)
    }
  })

  const handleGenerateInvoice = async () => {
    if (!paymentId) return
    
    setIsGenerating(true)
    generateInvoice({
      action: 'generate_from_payment',
      body: { payment_id: paymentId },
      method: 'POST'
    })
  }

  if (checkingInvoice) {
    return (
      <div className="flex items-center gap-2">
        <SpinnerData size={16} />
        <span className="text-sm text-gray-600">Verificando...</span>
      </div>
    )
  }

  // Si ya existe una factura, mostrar información
  if (existingInvoice && existingInvoice.length > 0) {
    const invoice = existingInvoice[0]
    return (
      <div className="flex items-center gap-2">
        <span className="text-sm text-green-600">✓ Factura generada</span>
        <span className="text-xs text-gray-500">#{invoice.number}</span>
      </div>
    )
  }

  return (
    <Button
      size="sm"
      variant="secondary"
      onClick={handleGenerateInvoice}
      disabled={disabled || isGenerating}
    >
      {isGenerating ? (
        <>
          <SpinnerData size={16} className="mr-2" />
          Generando...
        </>
      ) : (
        'Generar Factura'
      )}
    </Button>
  )
}
