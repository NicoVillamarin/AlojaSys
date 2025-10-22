import React, { useState, useRef } from 'react'
import { useField } from 'formik'
import CheckCircleIcon from 'src/assets/icons/CheckCircleIcon'
import XIcon from 'src/assets/icons/Xicon'
import CloudArrowUpIcon from 'src/assets/icons/CloudArrowUpIcon'
import PhotoIcon from 'src/assets/icons/PhotoIcon'

const FileImage = ({ 
  name, 
  label = "Seleccionar imagen", 
  accept = "image/*",
  maxSize = 5 * 1024 * 1024, // 5MB por defecto
  className = "",
  preview = true,
  showRemove = true,
  compress = true,
  maxWidth = 1920,
  maxHeight = 1080,
  quality = 0.8,
  existingImageUrl = null // URL de imagen existente para edición
}) => {
  const [field, meta, helpers] = useField(name)
  const [isDragOver, setIsDragOver] = useState(false)
  const [previewUrl, setPreviewUrl] = useState(field.value || null)
  const [isCompressing, setIsCompressing] = useState(false)
  const fileInputRef = useRef(null)

  // Función para comprimir imagen usando Canvas
  const compressImage = (file) => {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      const img = new Image()

      img.onload = () => {
        // Calcular nuevas dimensiones manteniendo la proporción
        let { width, height } = img
        
        if (width > maxWidth || height > maxHeight) {
          const ratio = Math.min(maxWidth / width, maxHeight / height)
          width = width * ratio
          height = height * ratio
        }

        // Configurar canvas
        canvas.width = width
        canvas.height = height

        // Dibujar imagen redimensionada
        ctx.drawImage(img, 0, 0, width, height)

        // Convertir a blob con compresión
        canvas.toBlob(
          (blob) => {
            if (blob) {
              // Crear nuevo archivo con el blob comprimido
              const compressedFile = new File([blob], file.name, {
                type: file.type,
                lastModified: Date.now()
              })
              resolve(compressedFile)
            } else {
              reject(new Error('Error al comprimir la imagen'))
            }
          },
          file.type,
          quality
        )
      }

      img.onerror = () => reject(new Error('Error al cargar la imagen'))
      img.src = URL.createObjectURL(file)
    })
  }

  const handleFileSelect = async (file) => {
    console.log('📁 FileImage: Archivo seleccionado:', {
      name: file?.name,
      size: file?.size,
      type: file?.type
    })
    
    if (!file) return

    // Validar tipo de archivo
    if (!file.type.startsWith('image/')) {
      console.log('❌ FileImage: Tipo de archivo inválido:', file.type)
      helpers.setError('Solo se permiten archivos de imagen')
      return
    }

    // Validar tamaño inicial
    if (file.size > maxSize) {
      console.log('❌ FileImage: Archivo demasiado grande:', file.size, 'bytes')
      helpers.setError(`El archivo es demasiado grande. Máximo ${Math.round(maxSize / (1024 * 1024))}MB`)
      return
    }

    try {
      let processedFile = file

      // Comprimir imagen si está habilitado
      if (compress) {
        console.log('🗜️ FileImage: Comprimiendo imagen...')
        setIsCompressing(true)
        processedFile = await compressImage(file)
        setIsCompressing(false)
        console.log('✅ FileImage: Imagen comprimida:', {
          originalSize: file.size,
          compressedSize: processedFile.size,
          reduction: `${Math.round((1 - processedFile.size / file.size) * 100)}%`
        })

        // Verificar tamaño después de la compresión
        if (processedFile.size > maxSize) {
          console.log('❌ FileImage: Archivo sigue siendo demasiado grande después de compresión')
          helpers.setError(`El archivo sigue siendo demasiado grande después de la compresión. Máximo ${Math.round(maxSize / (1024 * 1024))}MB`)
          return
        }
      }

      // Crear URL de vista previa
      const url = URL.createObjectURL(processedFile)
      setPreviewUrl(url)
      
      // Actualizar Formik
      console.log('✅ FileImage: Archivo procesado y asignado a Formik:', {
        name: processedFile.name,
        size: processedFile.size,
        type: processedFile.type
      })
      helpers.setValue(processedFile)
      helpers.setError(undefined)
    } catch (error) {
      console.log('❌ FileImage: Error al procesar imagen:', error)
      setIsCompressing(false)
      helpers.setError(`Error al procesar la imagen: ${error.message}`)
    }
  }

  const handleFileChange = (event) => {
    const file = event.target.files?.[0]
    handleFileSelect(file)
  }

  const handleDragOver = (event) => {
    event.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (event) => {
    event.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (event) => {
    event.preventDefault()
    setIsDragOver(false)
    
    const file = event.dataTransfer.files?.[0]
    handleFileSelect(file)
  }

  const handleRemove = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }
    setPreviewUrl(null)
    helpers.setValue(null)
    helpers.setError(undefined)
    
    // Limpiar input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const hasError = meta.touched && meta.error
  const hasFile = field.value || previewUrl
  const hasExistingImage = existingImageUrl && !field.value && !previewUrl
  const displayImageUrl = previewUrl || (hasExistingImage ? existingImageUrl : null)

  return (
    <div className={`space-y-2 ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-6 transition-all duration-200 cursor-pointer
          ${isDragOver 
            ? 'border-blue-400 bg-blue-50' 
            : hasError 
              ? 'border-red-300 bg-red-50' 
              : hasFile 
                ? 'border-green-300 bg-green-50'
                : 'border-gray-300 hover:border-gray-400'
          }
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileChange}
          className="hidden"
        />

        {isCompressing ? (
          <div className="text-center">
            <div className="mx-auto w-12 h-12 text-blue-500 mb-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
            <p className="text-sm font-medium text-blue-600">
              Comprimiendo imagen...
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Esto puede tomar unos segundos
            </p>
          </div>
        ) : (hasFile || hasExistingImage) ? (
          <div className="relative w-full h-full min-h-[200px] flex flex-col items-center justify-center">
            {preview && displayImageUrl && (
              <>
                {/* Imagen de fondo */}
                <img
                  src={displayImageUrl}
                  alt={hasExistingImage ? "Imagen actual" : "Vista previa"}
                  className="absolute inset-0 w-full h-full object-cover rounded-lg"
                />
                
                {/* Overlay con opciones */}
                <div className="absolute inset-0 bg-black bg-opacity-40 rounded-lg flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity duration-200">
                  <div className="flex space-x-3">
                    {/* Botón de cambiar */}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleClick()
                      }}
                      className="bg-white text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-100 transition-colors flex items-center space-x-2"
                    >
                      <PhotoIcon size="16" />
                      <span>Cambiar</span>
                    </button>
                    
                    {/* Botón de eliminar */}
                    {showRemove && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleRemove()
                        }}
                        className="bg-red-500 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-600 transition-colors flex items-center space-x-2"
                      >
                        <XIcon />
                        <span>Eliminar</span>
                      </button>
                    )}
                  </div>
                </div>
                
                {/* Información del archivo en la esquina */}
                <div className="absolute top-2 left-2 bg-white bg-opacity-90 px-2 py-1 rounded text-xs text-gray-700">
                  {hasExistingImage ? 'Imagen actual' : (field.value?.name || 'Imagen seleccionada')}
                </div>
                
                {/* Indicador de éxito */}
                <div className="absolute top-2 right-2 bg-green-500 text-white rounded-full p-1">
                  <CheckCircleIcon />
                </div>
              </>
            )}
          </div>
        ) : (
          <div className="text-center flex flex-col items-center justify-center min-h-[200px]">
            <div className="mx-auto w-13 h-13 rounded-full shadow-md bg-gray-100 p-2 text-gray-400 mb-4 flex items-center justify-center">
              {isDragOver ? (
                <CloudArrowUpIcon size='20' />
              ) : (
                <PhotoIcon size='20'/>
              )}
            </div>
            
            <div className="space-y-1">
              <p className="text-sm font-medium text-gray-900">
                {isDragOver ? 'Suelta la imagen aquí' : 'Arrastra una imagen aquí'}
              </p>
              <p className="text-xs text-gray-500">
                o haz clic para seleccionar
              </p>
              <p className="text-xs text-gray-400">
                PNG, JPG, GIF hasta {Math.round(maxSize / (1024 * 1024))}MB
              </p>
            </div>
          </div>
        )}
      </div>

      {hasError && (
        <p className="text-sm text-red-600 flex items-center space-x-1">
          <XIcon />
          <span>{meta.error}</span>
        </p>
      )}
    </div>
  )
}

export default FileImage