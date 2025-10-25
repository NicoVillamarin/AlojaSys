import React from 'react'
import ModalLayout from 'src/layouts/ModalLayout'

export default function InvoicePDFViewer({ isOpen, onClose, pdfUrl }) {
  if (!pdfUrl) return null

  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={onClose}
      title="Vista de Factura PDF"
      size="xl"
      showFooter={false}
    >
      <div className="w-full h-96">
        <iframe
          src={pdfUrl}
          className="w-full h-full border-0"
          title="Factura PDF"
        />
      </div>
    </ModalLayout>
  )
}