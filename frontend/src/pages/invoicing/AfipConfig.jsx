import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useList } from 'src/hooks/useList'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import { useDispatchAction } from 'src/hooks/useDispatchAction'
import { useUserHotels } from 'src/hooks/useUserHotels'
import TableGeneric from 'src/components/TableGeneric'
import Button from 'src/components/Button'
import Badge from 'src/components/Badge'
import ModalLayout from 'src/layouts/ModalLayout'
import { Formik, Form, Field } from 'formik'
import * as Yup from 'yup'
import SelectAsync from 'src/components/selects/SelectAsync'
import InputText from 'src/components/inputs/InputText'
import { useGet } from 'src/hooks/useGet'
import EditIcon from 'src/assets/icons/EditIcon'
import TestIcon from 'src/assets/icons/TestIcon'
import DeleteButton from 'src/components/DeleteButton'
import CertificatesListModal from 'src/components/invoicing/CertificatesListModal'

const validationSchema = Yup.object({
  hotel: Yup.string().required('El hotel es requerido'),
  cuit: Yup.string()
    .required('El CUIT es requerido')
    .matches(/^\d{11}$/, 'El CUIT debe tener 11 dígitos'),
  point_of_sale: Yup.number()
    .required('El punto de venta es requerido')
    .min(1, 'El punto de venta debe ser mayor a 0')
    .max(9999, 'El punto de venta debe ser menor a 10000'),
  tax_condition: Yup.string().required('La condición fiscal es requerida'),
  environment: Yup.string().required('El ambiente es requerido'),
  certificate_path: Yup.string().required('La ruta del certificado es requerida'),
  private_key_path: Yup.string().required('La ruta de la clave privada es requerida'),
})

export default function AfipConfig() {
  const { t } = useTranslation()
  const [showModal, setShowModal] = useState(false)
  const [editingConfig, setEditingConfig] = useState(null)
  const [testingConnection, setTestingConnection] = useState(null)
  const { hotelIdsString, isSuperuser, hotelIds } = useUserHotels()

  const { results, isPending, refetch } = useList({
    resource: 'invoicing/afip-configs',
    params: !isSuperuser && hotelIdsString ? { hotel_ids: hotelIdsString } : {}
  })

  const { mutate: createConfig } = useCreate({
    resource: 'invoicing/afip-configs',
    onSuccess: () => {
      setShowModal(false)
      setEditingConfig(null)
      refetch()
    }
  })

  const { mutate: updateConfig } = useUpdate({
    resource: 'invoicing/afip-configs',
    onSuccess: () => {
      setShowModal(false)
      setEditingConfig(null)
      refetch()
    }
  })

  const { mutate: testConnection, isPending: testing } = useDispatchAction({
    resource: 'invoicing/afip-configs',
    onSuccess: (data) => {
      setTestingConnection({
        success: data.success,
        message: data.message,
        environment: data.environment,
        has_token: data.has_token,
        has_sign: data.has_sign
      })
      setTimeout(() => setTestingConnection(null), 5000)
    }
  })

  const handleEdit = (config) => {
    setEditingConfig(config)
    setShowModal(true)
  }

  const handleTestConnection = (configId) => {
    testConnection({ action: `${configId}/test_connection`, body: {}, method: 'POST' })
  }

  const handleTestPDFGeneration = async () => {
    try {
      setTestingConnection(true)
      const response = await fetch('/api/invoicing/test/pdf/generate/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({})
      })
      
      const data = await response.json()
      
      if (data.success) {
        alert(`✅ PDF generado exitosamente!\n\nFactura ID: ${data.invoice_id}\nRuta: ${data.pdf_path}`)
      } else {
        alert(`❌ Error generando PDF: ${data.error}`)
      }
    } catch (error) {
      console.error('Error generating PDF:', error)
      alert(`❌ Error generando PDF: ${error.message}`)
    } finally {
      setTestingConnection(false)
    }
  }

  const taxConditions = [
    { value: '5', label: 'Consumidor Final' },
    { value: '1', label: 'Responsable Inscripto' },
    { value: '8', label: 'Monotributo' },
    { value: '6', label: 'Exento' },
    { value: '7', label: 'No Responsable' },
    { value: '9', label: 'Monotributo Social' },
  ]

  const environments = [
    { value: 'test', label: 'Homologación (Test)' },
    { value: 'production', label: 'Producción' },
  ]

  const columns = [
    { key: 'hotel_name', header: 'Hotel', sortable: true },
    { key: 'cuit', header: 'CUIT', sortable: true },
    { key: 'point_of_sale', header: 'Punto de Venta', sortable: true },
    { key: 'tax_condition', header: 'Condición Fiscal', sortable: true, render: (r) => {
      const condition = taxConditions.find(c => c.value === r.tax_condition)
      return condition?.label || r.tax_condition
    }},
    { key: 'environment', header: 'Ambiente', sortable: true, render: (r) => (
      <Badge variant={r.environment === 'production' ? 'afip-production' : 'afip-test'} size="sm">
        {r.environment === 'production' ? 'Producción' : 'Test'}
      </Badge>
    )},
    { key: 'is_active', header: 'Estado', sortable: true, render: (r) => (
      <Badge variant={r.is_active ? 'afip-active' : 'afip-inactive'} size="sm">
        {r.is_active ? 'Activo' : 'Inactivo'}
      </Badge>
    )},
    { key: 'last_invoice_number', header: 'Última Factura', sortable: true, render: (r) => r.last_invoice_number || '0' },
    {
      key: 'actions',
      header: 'Acciones',
      sortable: false,
      right: true,
      render: (r) => (
        <div className="flex justify-end items-center gap-x-2">
          <EditIcon size="18" onClick={() => handleEdit(r)} className="cursor-pointer" />
          <TestIcon 
            size="16" 
            onClick={() => handleTestConnection(r.id)} 
            className={`cursor-pointer ${testing ? 'opacity-50' : 'hover:opacity-70'} text-green-600`}
            title="Probar Conexión"
          />
          <DeleteButton resource="invoicing/afip-configs" id={r.id} onDeleted={refetch} className="cursor-pointer" />
        </div>
      )
    },
  ]

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Configuración Fiscal</h2>
          <p className="text-sm text-gray-600">Gestiona las configuraciones de facturación electrónica ARCA</p>
        </div>
        <Button
          variant="primary"
          size="md"
          onClick={() => setShowModal(true)}
        >
          Nueva Configuración
        </Button>
      </div>

      {/* Resultado de prueba de conexión */}
      {testingConnection && (
        <div className={`p-4 rounded-lg ${
          testingConnection.success 
            ? 'bg-green-50 border border-green-200' 
            : 'bg-red-50 border border-red-200'
        }`}>
          <div className="flex items-center">
            <div className={`text-lg mr-2 ${
              testingConnection.success ? 'text-green-600' : 'text-red-600'
            }`}>
              {testingConnection.success ? '✅' : '❌'}
            </div>
            <div>
              <p className={`font-medium ${
                testingConnection.success ? 'text-green-800' : 'text-red-800'
              }`}>
                {testingConnection.success ? 'Conexión exitosa' : 'Error de conexión'}
              </p>
              <p className={`text-sm ${
                testingConnection.success ? 'text-green-600' : 'text-red-600'
              }`}>
                {testingConnection.message}
              </p>
              {testingConnection.success && (
                <div className="text-xs text-green-600 mt-1">
                  <div>Ambiente: {testingConnection.environment}</div>
                  <div>Token: {testingConnection.has_token ? '✅' : '❌'}</div>
                  <div>Firma: {testingConnection.has_sign ? '✅' : '❌'}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <TableGeneric
        isLoading={isPending}
        data={results || []}
        getRowId={(r) => r.id}
        columns={columns}
        emptyMessage="No hay configuraciones AFIP"
      />

      {/* Modal de configuración */}
      <AfipConfigModal
        isOpen={showModal}
        onClose={() => {
          setShowModal(false)
          setEditingConfig(null)
        }}
        config={editingConfig}
        onSuccess={() => {
          setShowModal(false)
          setEditingConfig(null)
          refetch()
        }}
        onTestPDFGeneration={handleTestPDFGeneration}
      />
    </div>
  )
}

function AfipConfigModal({ isOpen, onClose, config, onSuccess, onTestPDFGeneration }) {
  const isEdit = !!config
  const [showCertificatesModal, setShowCertificatesModal] = useState(false)
  const [selectedCertificate, setSelectedCertificate] = useState('')
  const [selectedKey, setSelectedKey] = useState('')

  const { mutate: createConfig, isPending: creating } = useCreate({
    resource: 'invoicing/afip-configs',
    onSuccess: onSuccess
  })

  const { mutate: updateConfig, isPending: updating } = useUpdate({
    resource: 'invoicing/afip-configs',
    onSuccess: onSuccess
  })

  const initialValues = {
    hotel: config?.hotel || '',
    cuit: config?.cuit || '',
    point_of_sale: config?.point_of_sale || 1,
    tax_condition: config?.tax_condition || '1',
    environment: config?.environment || 'test',
    certificate_path: config?.certificate_path || selectedCertificate,
    private_key_path: config?.private_key_path || selectedKey,
    is_active: config?.is_active ?? true,
  }



  const handleSubmit = (values) => {
    if (isEdit) {
      updateConfig({
        id: config.id,
        body: values
      })
    } else {
      createConfig(values)
    }
  }

  const taxConditions = [
    { value: '5', label: 'Consumidor Final' },
    { value: '1', label: 'Responsable Inscripto' },
    { value: '8', label: 'Monotributo' },
    { value: '6', label: 'Exento' },
    { value: '7', label: 'No Responsable' },
    { value: '9', label: 'Monotributo Social' },
  ]

  const environments = [
    { value: 'test', label: 'Homologación (Test)' },
    { value: 'production', label: 'Producción' },
  ]

  return (
    <>
      <Formik
        initialValues={initialValues}
        validationSchema={validationSchema}
        onSubmit={handleSubmit}
        enableReinitialize
      >
        {({ handleSubmit, values, setFieldValue }) => {
          // Actualizar campos cuando se seleccionen certificados
          useEffect(() => {
            if (selectedCertificate) {
              setFieldValue('certificate_path', selectedCertificate)
              setSelectedCertificate('')
            }
            if (selectedKey) {
              setFieldValue('private_key_path', selectedKey)
              setSelectedKey('')
            }
          }, [selectedCertificate, selectedKey, setFieldValue])

          return (
            <ModalLayout
              isOpen={isOpen}
              onClose={onClose}
              title={isEdit ? 'Editar Configuración ARCA' : 'Nueva Configuración ARCA'}
              onSubmit={handleSubmit}
              submitText={isEdit ? 'Actualizar' : 'Crear'}
              cancelText="Cancelar"
              submitDisabled={creating || updating}
              submitLoading={creating || updating}
              size="lg"
            >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Hotel *
                </label>
                <SelectAsync
                  name="hotel"
                  resource="hotels"
                  placeholder="Seleccionar hotel"
                  getOptionLabel={(h) => h?.name}
                  getOptionValue={(h) => h?.id}
                  onValueChange={(opt, val) => setFieldValue('hotel', val)}
                  value={values.hotel}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CUIT *
                </label>
                <Field
                  as={InputText}
                  name="cuit"
                  placeholder="20123456789"
                  maxLength="11"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Punto de Venta *
                </label>
                <Field
                  as={InputText}
                  name="point_of_sale"
                  type="number"
                  placeholder="1"
                  min="1"
                  max="9999"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Condición Fiscal *
                </label>
                <Field
                  as="select"
                  name="tax_condition"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  {taxConditions.map(condition => (
                    <option key={condition.value} value={condition.value}>
                      {condition.label}
                    </option>
                  ))}
                </Field>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Ambiente *
                </label>
                <Field
                  as="select"
                  name="environment"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  {environments.map(env => (
                    <option key={env.value} value={env.value}>
                      {env.label}
                    </option>
                  ))}
                </Field>
              </div>

              <div className="flex items-center">
                <Field
                  type="checkbox"
                  name="is_active"
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-700">
                  Configuración activa
                </label>
              </div>
            </div>

            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Certificados Digitales</h3>
              
              {/* Información de rutas actuales */}
              {isEdit && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
                  <h4 className="text-sm font-medium text-blue-900 mb-2">Rutas Actuales en el Servidor</h4>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="font-medium text-blue-700">Certificado:</span>
                      <code className="ml-2 bg-blue-100 px-2 py-1 rounded text-blue-800">
                        {config?.certificate_path || 'No configurado'}
                      </code>
                    </div>
                    <div>
                      <span className="font-medium text-blue-700">Clave Privada:</span>
                      <code className="ml-2 bg-blue-100 px-2 py-1 rounded text-blue-800">
                        {config?.private_key_path || 'No configurado'}
                      </code>
                    </div>
                  </div>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ruta del Certificado (.crt) *
                  </label>
                  <Field
                    as={InputText}
                    name="certificate_path"
                    placeholder="/app/certs/afip_certificate.crt"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Ruta completa del archivo de certificado en el servidor
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ruta de la Clave Privada (.key) *
                  </label>
                  <Field
                    as={InputText}
                    name="private_key_path"
                    placeholder="/app/certs/afip_private_key.key"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Ruta completa del archivo de clave privada en el servidor
                  </p>
                </div>
              </div>

              {/* Botón para listar certificados */}
              <div className="mt-4">
                <button
                  type="button"
                  onClick={() => setShowCertificatesModal(true)}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  📁 Ver Certificados Disponibles
                </button>
                
                <button
                  type="button"
                  onClick={onTestPDFGeneration}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 ml-2"
                >
                  📄 Probar Generación PDF
                </button>
              </div>

              {/* Información de ayuda */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mt-4">
                <h4 className="text-sm font-medium text-yellow-900 mb-2">ℹ️ Información Importante</h4>
                <ul className="text-xs text-yellow-800 space-y-1">
                  <li>• Los certificados deben estar en el servidor Docker</li>
                  <li>• Las rutas deben ser absolutas (empezar con /app/certs/)</li>
                  <li>• El certificado y la clave privada deben coincidir</li>
                  <li>• Para homologación, usa certificados de AFIP WSASS</li>
                </ul>
              </div>
            </div>

            </ModalLayout>
          )
        }}
      </Formik>
      
      {/* Modal de certificados */}
      <CertificatesListModal
        isOpen={showCertificatesModal}
        onClose={() => setShowCertificatesModal(false)}
        onSelectCertificate={(path) => {
          setSelectedCertificate(path)
          setShowCertificatesModal(false)
        }}
        onSelectKey={(path) => {
          setSelectedKey(path)
          setShowCertificatesModal(false)
        }}
      />
    </>
  )
}
