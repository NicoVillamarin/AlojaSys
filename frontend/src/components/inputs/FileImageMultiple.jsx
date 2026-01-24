import React, { useState, useRef } from 'react'
import { useField } from 'formik'
import CheckCircleIcon from 'src/assets/icons/CheckCircleIcon'
import XIcon from 'src/assets/icons/Xicon'
import CloudArrowUpIcon from 'src/assets/icons/CloudArrowUpIcon'
import PhotoIcon from 'src/assets/icons/PhotoIcon'

const FileImageMultiple = ({ 
  name, 
  label = "Seleccionar imágenes", 
  accept = "image/*",
  maxSize = 5 * 1024 * 1024, // 5MB por defecto
  className = "",
  preview = true,
  showRemove = true,
  compress = true,
  maxWidth = 1920,
  maxHeight = 1080,
  quality = 0.8,
  maxImages = 10, // Máximo de imágenes
  existingImages = [] // Array de URLs de imágenes existentes para edición
}) => {
  const [field, meta, helpers] = useField(name)
  const [isDragOver, setIsDragOver] = useState(false)
  const [isCompressing, setIsCompressing] = useState(false)
  const fileInputRef = useRef(null)

  // Obtener imágenes actuales (nuevas + existentes)
  // field.value puede ser un array (solo imágenes nuevas) o un objeto con más info
  const fieldValue = field.value || {}
  const currentImages = Array.isArray(fieldValue) ? fieldValue : (fieldValue.images || [])
  const imagesToDelete = Array.isArray(fieldValue) ? [] : (fieldValue.imagesToDelete || [])
  const primaryImageIndex = Array.isArray(fieldValue) ? null : (fieldValue.primaryImageIndex ?? null)
  
  const existingImagesList = existingImages || []
  
  // Filtrar imágenes existentes que no están marcadas para eliminación
  const validExistingImages = existingImagesList
    .map((url, idx) => ({ url, idx }))
    .filter((_, idx) => !imagesToDelete.includes(idx))
  
  // Determinar cuál es la imagen principal
  const primaryIndex = primaryImageIndex !== null ? primaryImageIndex : 0
  
  const allImages = [
    ...validExistingImages.map((urlObj, idx) => {
      const url = urlObj.url || urlObj
      const originalIdx = typeof urlObj === 'string' 
        ? existingImagesList.indexOf(url) 
        : existingImagesList.findIndex(u => u === url || (typeof u === 'object' && u.url === url))
      return {
        url: typeof url === 'string' ? url : (urlObj.url || url),
        isExisting: true,
        id: `existing-${originalIdx >= 0 ? originalIdx : idx}`,
        isPrimary: originalIdx === primaryIndex && currentImages.length === 0
      }
    }),
    ...currentImages.map((img, idx) => ({
      ...img,
      isExisting: false,
      id: img.id || `new-${idx}`,
      isPrimary: validExistingImages.length === 0 && idx === 0 && !img.isPrimary ? true : (img.isPrimary || false)
    }))
  ]

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

  const handleFileSelect = async (files) => {
    if (!files || files.length === 0) return

    const filesArray = Array.from(files)
    const totalImages = allImages.length + filesArray.length

    // Validar cantidad máxima
    if (totalImages > maxImages) {
      helpers.setError(`Máximo ${maxImages} imágenes permitidas. Ya tienes ${allImages.length} imagen(es).`)
      return
    }

    try {
      setIsCompressing(true)
      const processedFiles = []

      for (const file of filesArray) {
        // Validar tipo de archivo
        if (!file.type.startsWith('image/')) {
          helpers.setError('Solo se permiten archivos de imagen')
          continue
        }

        // Validar tamaño inicial
        if (file.size > maxSize) {
          helpers.setError(`El archivo ${file.name} es demasiado grande. Máximo ${Math.round(maxSize / (1024 * 1024))}MB`)
          continue
        }

        let processedFile = file

        // Comprimir imagen si está habilitado
        if (compress) {
          processedFile = await compressImage(file)

          // Verificar tamaño después de la compresión
          if (processedFile.size > maxSize) {
            helpers.setError(`El archivo ${file.name} sigue siendo demasiado grande después de la compresión. Máximo ${Math.round(maxSize / (1024 * 1024))}MB`)
            continue
          }
        }

        // Crear URL de vista previa
        const previewUrl = URL.createObjectURL(processedFile)
        
        const imageData = {
          file: processedFile,
          previewUrl,
          name: processedFile.name,
          size: processedFile.size,
          isPrimary: allImages.length === 0 && processedFiles.length === 0 // Primera imagen es principal
        }
        
        // Verificar que previewUrl se creó correctamente
        if (!previewUrl) {
          console.error('Error: previewUrl no se creó para', processedFile.name)
        }
        
        processedFiles.push(imageData)
      }

      setIsCompressing(false)

      // Agregar nuevas imágenes a las existentes
      // Mantener la estructura si ya existe (con imagesToDelete, etc.)
      if (Array.isArray(fieldValue)) {
        helpers.setValue([...currentImages, ...processedFiles])
      } else {
        helpers.setValue({
          ...fieldValue,
          images: [...currentImages, ...processedFiles]
        })
      }
      helpers.setError(undefined)
    } catch (error) {
      setIsCompressing(false)
      helpers.setError(`Error al procesar las imágenes: ${error.message}`)
    }
  }

  const handleFileChange = (event) => {
    const files = event.target.files
    handleFileSelect(files)
    // Limpiar input para permitir seleccionar el mismo archivo nuevamente
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
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
    
    const files = event.dataTransfer.files
    handleFileSelect(files)
  }

  const handleRemove = (imageId) => {
    const imageIndex = currentImages.findIndex(img => img.id === imageId)
    
    if (imageIndex !== -1) {
      // Es una imagen nueva, eliminar de la lista
      const updatedImages = currentImages.filter((_, idx) => idx !== imageIndex)
      
      // Revocar URL de preview
      const imageToRemove = currentImages[imageIndex]
      if (imageToRemove.previewUrl) {
        URL.revokeObjectURL(imageToRemove.previewUrl)
      }
      
      // Si se eliminó la primera imagen, la siguiente se convierte en principal
      if (imageIndex === 0 && updatedImages.length > 0) {
        updatedImages[0].isPrimary = true
      }
      
      // Mantener estructura si existe
      if (Array.isArray(fieldValue)) {
        helpers.setValue(updatedImages)
      } else {
        helpers.setValue({
          ...fieldValue,
          images: updatedImages
        })
      }
    } else {
      // Es una imagen existente, marcarla para eliminación
      const existingIndex = existingImagesList.findIndex((_, idx) => `existing-${idx}` === imageId)
      if (existingIndex !== -1) {
        const currentToDelete = Array.isArray(fieldValue) ? [] : (fieldValue.imagesToDelete || [])
        if (!currentToDelete.includes(existingIndex)) {
          const newToDelete = [...currentToDelete, existingIndex]
          if (Array.isArray(fieldValue)) {
            helpers.setValue({
              images: currentImages,
              imagesToDelete: newToDelete
            })
          } else {
            helpers.setValue({
              ...fieldValue,
              imagesToDelete: newToDelete
            })
          }
        }
      }
    }
    
    helpers.setError(undefined)
  }

  const handleSetPrimary = (imageId) => {
    // Si es una imagen nueva
    const imageIndex = currentImages.findIndex(img => img.id === imageId)
    if (imageIndex !== -1) {
      const updatedImages = currentImages.map((img, idx) => ({
        ...img,
        isPrimary: idx === imageIndex
      }))
      
      if (Array.isArray(fieldValue)) {
        helpers.setValue(updatedImages)
      } else {
        helpers.setValue({
          ...fieldValue,
          images: updatedImages,
          primaryImageIndex: null // Resetear si se selecciona una nueva como principal
        })
      }
      return
    }

    // Si es una imagen existente, necesitamos reorganizar
    const existingIndex = existingImagesList.findIndex((_, idx) => `existing-${idx}` === imageId)
    if (existingIndex !== -1) {
      // Marcar que esta imagen debe ser la principal
      if (Array.isArray(fieldValue)) {
        helpers.setValue({
          images: currentImages,
          primaryImageIndex: existingIndex
        })
      } else {
        helpers.setValue({
          ...fieldValue,
          primaryImageIndex: existingIndex
        })
      }
    }
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const hasError = meta.touched && meta.error
  const hasImages = allImages.length > 0
  const canAddMore = allImages.length < maxImages

  return (
    <div className={`space-y-2 ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
          {hasImages && (
            <span className="ml-2 text-xs text-gray-500">
              ({allImages.length}/{maxImages})
            </span>
          )}
        </label>
      )}
      
      {/* Área de carga */}
      {canAddMore && (
        <div
          className={`
            relative border-2 border-dashed rounded-lg p-6 transition-all duration-200 cursor-pointer
            ${isDragOver 
              ? 'border-blue-400 bg-blue-50' 
              : hasError 
                ? 'border-red-300 bg-red-50' 
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
            multiple
            onChange={handleFileChange}
            className="hidden"
          />

          {isCompressing ? (
            <div className="text-center">
              <div className="mx-auto w-12 h-12 text-blue-500 mb-4">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
              </div>
              <p className="text-sm font-medium text-blue-600">
                Comprimiendo imágenes...
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Esto puede tomar unos segundos
              </p>
            </div>
          ) : (
            <div className="text-center flex flex-col items-center justify-center min-h-[120px]">
              <div className="mx-auto w-13 h-13 rounded-full shadow-md bg-gray-100 p-2 text-gray-400 mb-4 flex items-center justify-center">
                {isDragOver ? (
                  <CloudArrowUpIcon size='20' />
                ) : (
                  <PhotoIcon size='20'/>
                )}
              </div>
              
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-900">
                  {isDragOver ? 'Suelta las imágenes aquí' : 'Arrastra imágenes aquí'}
                </p>
                <p className="text-xs text-gray-500">
                  o haz clic para seleccionar
                </p>
                <p className="text-xs text-gray-400">
                  PNG, JPG, GIF hasta {Math.round(maxSize / (1024 * 1024))}MB cada una
                </p>
                <p className="text-xs text-gray-400">
                  La primera imagen será la principal
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Galería de imágenes */}
      {hasImages && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mt-4">
          {allImages.map((image, index) => {
            // Verificar si la imagen está marcada para eliminación
            let isMarkedForDeletion = false
            if (image.isExisting) {
              const originalIdx = existingImagesList.indexOf(image.url)
              isMarkedForDeletion = imagesToDelete.includes(originalIdx)
              if (isMarkedForDeletion) return null
            }

            const imageSrc = image.url || image.previewUrl
            
            // Debug: verificar que tenemos una URL válida
            if (!imageSrc) {
              console.warn('Imagen sin URL válida:', image)
            }
            
            return (
              <div
                key={image.id || index}
                className={`
                  relative group rounded-lg overflow-hidden border-2
                  ${image.isPrimary ? 'border-yellow-400 ring-2 ring-yellow-300' : 'border-gray-200'}
                `}
              >
                {/* Imagen */}
                <div className="aspect-square bg-gray-100 relative">
                  {imageSrc ? (
                    <img
                      src={imageSrc}
                      alt={image.name || `Imagen ${index + 1}`}
                      className="w-full h-full object-cover relative z-0"
                      style={{ display: 'block', backgroundColor: 'transparent' }}
                      onLoad={() => {
                        console.log('Imagen cargada correctamente:', imageSrc)
                      }}
                      onError={(e) => {
                        console.error('Error cargando imagen:', {
                          src: imageSrc,
                          image: image,
                          error: e
                        })
                        e.target.style.display = 'none'
                        const parent = e.target.parentElement
                        if (parent && !parent.querySelector('.error-message')) {
                          const errorDiv = document.createElement('div')
                          errorDiv.className = 'error-message w-full h-full flex items-center justify-center bg-gray-200 text-gray-500 text-xs p-2'
                          errorDiv.textContent = 'Error al cargar'
                          parent.appendChild(errorDiv)
                        }
                      }}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gray-200 text-gray-500 text-xs">
                      Sin imagen
                    </div>
                  )}
                </div>

                {/* Badge de imagen principal - siempre visible */}
                {image.isPrimary && (
                  <div className="absolute top-2 left-2 bg-yellow-400 text-yellow-900 px-2 py-1 rounded text-xs font-semibold z-20">
                    Principal
                  </div>
                )}

                {/* Overlay con opciones - solo visible en hover */}
                <div className="absolute inset-0 transition-opacity duration-200 flex items-center justify-center z-10 pointer-events-none group-hover:bg-black/50">
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity flex flex-col gap-2 pointer-events-auto">
                    {/* Botones de acción */}
                    <div className="flex gap-2">
                      {!image.isPrimary && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleSetPrimary(image.id || `existing-${existingImagesList.indexOf(image.url)}`)
                          }}
                          className="bg-white text-gray-700 px-3 py-1 rounded text-xs font-medium hover:bg-gray-100 transition-colors"
                          title="Marcar como principal"
                        >
                          Principal
                        </button>
                      )}
                      
                      {showRemove && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleRemove(image.id || `existing-${existingImagesList.indexOf(image.url)}`)
                          }}
                          className="bg-red-500 text-white px-3 py-1 rounded text-xs font-medium hover:bg-red-600 transition-colors"
                          title="Eliminar"
                        >
                          <XIcon size="12" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Indicador de éxito */}
                <div className="absolute top-2 right-2 bg-green-500 text-white rounded-full p-1">
                  <CheckCircleIcon size="16" />
                </div>
              </div>
            )
          })}
        </div>
      )}

      {hasError && (
        <p className="text-sm text-red-600 flex items-center space-x-1">
          <XIcon />
          <span>{meta.error}</span>
        </p>
      )}
    </div>
  )
}

export default FileImageMultiple
