import { useState, useEffect } from 'react'
import ModalLayout from 'src/layouts/ModalLayout'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import { useGet } from 'src/hooks/useGet'
import { Formik, Form, Field } from 'formik'
import * as Yup from 'yup'
import SelectAsync from 'src/components/selects/SelectAsync'
import InputText from 'src/components/inputs/InputText'
import Button from 'src/components/Button'
import SpinnerData from 'src/components/SpinnerData'

const validationSchema = Yup.object({
  type: Yup.string().required('El tipo de factura es requerido'),
  customer_name: Yup.string().required('El nombre del cliente es requerido'),
  customer_document_type: Yup.string().required('El tipo de documento es requerido'),
  customer_document_number: Yup.string().required('El número de documento es requerido'),
  customer_tax_condition: Yup.string().required('La condición fiscal es requerida'),
  customer_address: Yup.string().required('La dirección es requerida'),
  customer_city: Yup.string().required('La ciudad es requerida'),
  customer_postal_code: Yup.string().required('El código postal es requerido'),
  customer_country: Yup.string().required('El país es requerido'),
})

export default function InvoiceModal({ isOpen, onClose, invoice, onSuccess }) {
  const [isEdit, setIsEdit] = useState(false)
  const [loading, setLoading] = useState(false)
  const [invoiceData, setInvoiceData] = useState(null)

  // Cargar datos de la factura si es edición
  const { data: invoiceDetails, isLoading: loadingInvoice } = useGet({
    resource: 'invoices',
    id: invoice?.id,
    enabled: !!invoice?.id && isOpen
  })

  const { mutate: createInvoice } = useCreate({
    resource: 'invoices',
    onSuccess: (data) => {
      onSuccess?.(data)
    }
  })

  const { mutate: updateInvoice } = useUpdate({
    resource: 'invoices',
    onSuccess: (data) => {
      onSuccess?.(data)
    }
  })

  useEffect(() => {
    if (invoice) {
      setIsEdit(true)
      setInvoiceData(invoice)
    } else {
      setIsEdit(false)
      setInvoiceData(null)
    }
  }, [invoice])

  const initialValues = {
    type: invoiceData?.type || 'B',
    customer_name: invoiceData?.customer_name || '',
    customer_document_type: invoiceData?.customer_document_type || 'DNI',
    customer_document_number: invoiceData?.customer_document_number || '',
    customer_tax_condition: invoiceData?.customer_tax_condition || 'CONSUMIDOR_FINAL',
    customer_address: invoiceData?.customer_address || '',
    customer_city: invoiceData?.customer_city || '',
    customer_postal_code: invoiceData?.customer_postal_code || '',
    customer_country: invoiceData?.customer_country || 'Argentina',
    description: invoiceData?.description || '',
  }

  const handleSubmit = async (values, { setSubmitting }) => {
    try {
      setLoading(true)
      
      if (isEdit) {
        updateInvoice({
          id: invoice.id,
          body: values
        })
      } else {
        createInvoice(values)
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setSubmitting(false)
      setLoading(false)
    }
  }

  const documentTypes = [
    { value: 'DNI', label: 'DNI' },
    { value: 'CUIT', label: 'CUIT' },
    { value: 'CUIL', label: 'CUIL' },
    { value: 'PASAPORTE', label: 'Pasaporte' },
  ]

  const taxConditions = [
    { value: 'CONSUMIDOR_FINAL', label: 'Consumidor Final' },
    { value: 'RESPONSABLE_INSCRIPTO', label: 'Responsable Inscripto' },
    { value: 'MONOTRIBUTO', label: 'Monotributo' },
    { value: 'EXENTO', label: 'Exento' },
  ]

  const invoiceTypes = [
    { value: 'A', label: 'Factura A (Responsable Inscripto)' },
    { value: 'B', label: 'Factura B (Consumidor Final)' },
    { value: 'C', label: 'Factura C (Exento)' },
    { value: 'NC', label: 'Nota de Crédito' },
    { value: 'ND', label: 'Nota de Débito' },
  ]

  if (loadingInvoice) {
    return (
      <ModalLayout isOpen={isOpen} onClose={onClose} title="Cargando factura..." size="lg">
        <div className="flex items-center justify-center py-12">
          <SpinnerData size={60} />
        </div>
      </ModalLayout>
    )
  }

  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? 'Editar Factura' : 'Nueva Factura'}
      size="lg"
    >
      <Formik
        initialValues={initialValues}
        validationSchema={validationSchema}
        onSubmit={handleSubmit}
        enableReinitialize
      >
        {({ values, setFieldValue, isSubmitting }) => (
          <Form className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Factura *
                </label>
                <Field
                  as="select"
                  name="type"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  {invoiceTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </Field>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descripción
                </label>
                <Field
                  as={InputText}
                  name="description"
                  placeholder="Descripción de la factura"
                />
              </div>
            </div>

            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Datos del Cliente</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nombre del Cliente *
                  </label>
                  <Field
                    as={InputText}
                    name="customer_name"
                    placeholder="Nombre completo"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tipo de Documento *
                  </label>
                  <Field
                    as="select"
                    name="customer_document_type"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  >
                    {documentTypes.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </Field>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Número de Documento *
                  </label>
                  <Field
                    as={InputText}
                    name="customer_document_number"
                    placeholder="12345678"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Condición Fiscal *
                  </label>
                  <Field
                    as="select"
                    name="customer_tax_condition"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  >
                    {taxConditions.map(condition => (
                      <option key={condition.value} value={condition.value}>
                        {condition.label}
                      </option>
                    ))}
                  </Field>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Dirección *
                  </label>
                  <Field
                    as={InputText}
                    name="customer_address"
                    placeholder="Calle, número, piso, depto"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ciudad *
                  </label>
                  <Field
                    as={InputText}
                    name="customer_city"
                    placeholder="Buenos Aires"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Código Postal *
                  </label>
                  <Field
                    as={InputText}
                    name="customer_postal_code"
                    placeholder="1000"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    País *
                  </label>
                  <Field
                    as={InputText}
                    name="customer_country"
                    placeholder="Argentina"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button
                type="button"
                variant="secondary"
                onClick={onClose}
                disabled={loading}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={isSubmitting || loading}
              >
                {loading ? 'Guardando...' : (isEdit ? 'Actualizar' : 'Crear')}
              </Button>
            </div>
          </Form>
        )}
      </Formik>
    </ModalLayout>
  )
}
