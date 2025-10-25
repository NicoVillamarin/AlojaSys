import React, { useState, useEffect } from 'react'
import ModalLayout from 'src/layouts/ModalLayout'
import Button from 'src/components/Button'
import { useGet } from 'src/hooks/useGet'

export default function CertificatesListModal({ isOpen, onClose, onSelectCertificate, onSelectKey }) {
  const [selectedCert, setSelectedCert] = useState('')
  const [selectedKey, setSelectedKey] = useState('')

  const { data: certificates, isLoading } = useGet({
    resource: 'invoicing/certificates/list/',
    enabled: isOpen
  })

  const handleSelectCertificate = () => {
    if (selectedCert) {
      onSelectCertificate(selectedCert)
    }
  }

  const handleSelectKey = () => {
    if (selectedKey) {
      onSelectKey(selectedKey)
    }
  }

  const handleClose = () => {
    setSelectedCert('')
    setSelectedKey('')
    onClose()
  }

  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={handleClose}
      title="Certificados Disponibles"
      size="lg"
      showFooter={false}
    >
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Certificados (.crt)</h3>
          {isLoading ? (
            <div className="text-center py-4">Cargando certificados...</div>
          ) : (
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {certificates?.certificates?.map((cert, index) => (
                <div key={index} className="flex items-center justify-between p-2 border rounded">
                  <code className="text-sm text-gray-700">{cert}</code>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setSelectedCert(cert)}
                    disabled={selectedCert === cert}
                  >
                    {selectedCert === cert ? 'Seleccionado' : 'Seleccionar'}
                  </Button>
                </div>
              ))}
            </div>
          )}
          {selectedCert && (
            <div className="mt-2">
              <Button
                size="sm"
                variant="primary"
                onClick={handleSelectCertificate}
              >
                Usar Certificado Seleccionado
              </Button>
            </div>
          )}
        </div>

        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Claves Privadas (.key)</h3>
          {isLoading ? (
            <div className="text-center py-4">Cargando claves...</div>
          ) : (
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {certificates?.private_keys?.map((key, index) => (
                <div key={index} className="flex items-center justify-between p-2 border rounded">
                  <code className="text-sm text-gray-700">{key}</code>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setSelectedKey(key)}
                    disabled={selectedKey === key}
                  >
                    {selectedKey === key ? 'Seleccionado' : 'Seleccionar'}
                  </Button>
                </div>
              ))}
            </div>
          )}
          {selectedKey && (
            <div className="mt-2">
              <Button
                size="sm"
                variant="primary"
                onClick={handleSelectKey}
              >
                Usar Clave Seleccionada
              </Button>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="secondary" onClick={handleClose}>
            Cerrar
          </Button>
        </div>
      </div>
    </ModalLayout>
  )
}