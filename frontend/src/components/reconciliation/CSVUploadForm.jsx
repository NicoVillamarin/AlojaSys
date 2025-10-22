import React, { useState, useRef } from 'react'
import { useCreate } from 'src/hooks/useCreate'
import SpinnerLoading from 'src/components/SpinnerLoading'
import { showSuccess, showErrorConfirm } from 'src/services/toast'
import { Formik, useFormikContext } from 'formik'
import SelectAsync from '../selects/SelectAsync'
import LabelsContainer from '../inputs/LabelsContainer'

// Componente interno que usa useFormikContext
const FormContent = ({ onSuccess, onCancel }) => {
  const { values, setFieldValue } = useFormikContext()
  const { mutate: create, isPending: isCreating } = useCreate({
    resource: 'payments/reconciliations',
    onSuccess: (data) => {
      showSuccess('CSV subido exitosamente. La conciliación se está procesando.')
      onSuccess(data)
    }
  })
  const [formData, setFormData] = useState({
    reconciliationDate: new Date().toISOString().split('T')[0],
    csvFile: null
  })
  const isUploading = isCreating
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef(null)

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      if (!file.name.endsWith('.csv')) {
        showErrorConfirm('El archivo debe ser un CSV')
        return
      }
      if (file.size > 10 * 1024 * 1024) { // 10MB
        showErrorConfirm('El archivo es demasiado grande (máximo 10MB)')
        return
      }
      setFormData(prev => ({
        ...prev,
        csvFile: file
      }))
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    const files = e.dataTransfer.files
    if (files && files[0]) {
      const file = files[0]
      if (!file.name.endsWith('.csv')) {
        showErrorConfirm('El archivo debe ser un CSV')
        return
      }
      if (file.size > 10 * 1024 * 1024) {
        showErrorConfirm('El archivo es demasiado grande (máximo 10MB)')
        return
      }
      setFormData(prev => ({
        ...prev,
        csvFile: file
      }))
    }
  }

  const convertFileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.readAsDataURL(file)
      reader.onload = () => resolve(reader.result)
      reader.onerror = error => reject(error)
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!values.hotelId) {
      showErrorConfirm('Por favor selecciona un hotel')
      return
    }

    if (!formData.csvFile) {
      showErrorConfirm('Por favor selecciona un archivo CSV')
      return
    }

    if (!formData.reconciliationDate) {
      showErrorConfirm('Por favor selecciona una fecha de conciliación')
      return
    }

    try {
      // Convertir archivo a base64
      const fileBase64 = await convertFileToBase64(formData.csvFile)
      
      const reconciliationData = {
        hotel: values.hotelId,
        reconciliation_date: formData.reconciliationDate,
        csv_file_base64: fileBase64,
        csv_filename: formData.csvFile.name
      }

      // Usar useCreate hook con JSON
      create(reconciliationData)
    } catch (error) {
      console.error('Error convirtiendo archivo:', error)
      showErrorConfirm('Error procesando el archivo')
    }
  }

  const handleCancel = () => {
    setFormData({
      reconciliationDate: new Date().toISOString().split('T')[0],
      csvFile: null
    })
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
    onCancel()
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Subir Archivo CSV de Conciliación
      </h3>
      <form onSubmit={handleSubmit} className="space-y-4">
         <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5'>
           <SelectAsync
             title="Hotel"
             name="hotelId"
             resource="hotels"
             getOptionLabel={(h) => h.name}
             getOptionValue={(h) => h.id}
             onChange={(value) => setFieldValue('hotelId', value)}
           />
        {/* Fecha de Conciliación */}
        <div>
          <LabelsContainer title="Fecha de Conciliación">
          <input
            type="date"
            id="reconciliationDate"
            name="reconciliationDate"
            value={formData.reconciliationDate}
            onChange={handleInputChange}
            max={new Date().toISOString().split('T')[0]}
            className="w-full border rounded-md px-3 py-1.5 outline-none transition focus:ring-2 border-gray-200 focus:ring-aloja-navy/30"
            required
          />
          </LabelsContainer>
        </div>
        </div>
        {/* Zona de Drop de Archivo */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Archivo CSV
          </label>
          <div
            className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
              dragActive
                ? 'border-blue-400 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            
            {formData.csvFile ? (
              <div className="space-y-2">
                <div className="flex items-center justify-center">
                  <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-sm text-green-600 font-medium">
                  {formData.csvFile.name}
                </p>
                <p className="text-xs text-gray-500">
                  {(formData.csvFile.size / 1024).toFixed(1)} KB
                </p>
                <button
                  type="button"
                  onClick={() => {
                    setFormData(prev => ({ ...prev, csvFile: null }))
                    if (fileInputRef.current) {
                      fileInputRef.current.value = ''
                    }
                  }}
                  className="text-xs text-red-600 hover:text-red-800"
                >
                  Eliminar archivo
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center justify-center">
                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <p className="text-sm text-gray-600">
                  Arrastra y suelta tu archivo CSV aquí, o{' '}
                  <span className="text-blue-600 font-medium">haz clic para seleccionar</span>
                </p>
                <p className="text-xs text-gray-500">
                  Máximo 10MB, formato CSV
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Información del Formato */}
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
          <h4 className="text-sm font-medium text-blue-800 mb-2">Formato CSV Esperado:</h4>
          <div className="text-xs text-blue-700 space-y-1">
            <p><strong>Columnas:</strong> fecha, descripcion, importe, moneda, referencia</p>
            <p><strong>Separador:</strong> coma (,)</p>
            <p><strong>Encoding:</strong> UTF-8</p>
            <p><strong>Ejemplo:</strong> 2025-10-19, "Transferencia Juan Perez", 23000.00, "ARS", "CBU 28500109...1234"</p>
          </div>
        </div>

        {/* Botones */}
        <div className="flex justify-end space-x-3 pt-4">
          <button
            type="button"
            onClick={handleCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            disabled={isUploading}
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={isUploading || !formData.csvFile || !values.hotelId}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isUploading ? (
              <>
                <SpinnerLoading size="sm" className="mr-2" />
                Subiendo...
              </>
            ) : (
              'Subir CSV'
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

// Componente principal con Formik
const CSVUploadForm = ({ onSuccess, onCancel }) => {
  return (
    <Formik
      initialValues={{ hotelId: null }}
      onSubmit={() => {}} // No usamos onSubmit de Formik, manejamos el submit manualmente
    >
      <FormContent onSuccess={onSuccess} onCancel={onCancel} />
    </Formik>
  )
}

export default CSVUploadForm

