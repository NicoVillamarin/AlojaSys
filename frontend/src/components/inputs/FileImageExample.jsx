import React from 'react'
import { Formik, Form, Field } from 'formik'
import FileImage from './FileImage'

const FileImageExample = () => {
  const initialValues = {
    logo: null,
    profileImage: null,
    banner: null,
    smallLogo: null
  }

  const handleSubmit = (values) => {
    console.log('Valores del formulario:', values)
    
    // Aquí puedes enviar los archivos al backend
    // Por ejemplo, usando FormData:
    const formData = new FormData()
    if (values.logo) {
      formData.append('logo', values.logo)
    }
    if (values.profileImage) {
      formData.append('profileImage', values.profileImage)
    }
    
    // Enviar al backend...
    console.log('FormData preparado para envío')
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">Ejemplo de uso de FileImage</h2>
      
      <Formik
        initialValues={initialValues}
        onSubmit={handleSubmit}
      >
        {({ values, isSubmitting }) => (
          <Form className="space-y-6">
            {/* Ejemplo 1: Logo del hotel con compresión */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Logo del Hotel (Con Compresión)</h3>
              <FileImage
                name="logo"
                label="Logo del hotel"
                maxSize={2 * 1024 * 1024} // 2MB
                compress={true}
                maxWidth={800}
                maxHeight={600}
                quality={0.9}
                className="mb-4"
              />
            </div>

            {/* Ejemplo 2: Imagen de perfil con compresión alta */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Imagen de Perfil (Compresión Alta)</h3>
              <FileImage
                name="profileImage"
                label="Foto de perfil"
                maxSize={1 * 1024 * 1024} // 1MB
                compress={true}
                maxWidth={500}
                maxHeight={500}
                quality={0.7}
                className="mb-4"
              />
            </div>

            {/* Ejemplo 3: Sin compresión */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Sin Compresión</h3>
              <FileImage
                name="banner"
                label="Banner (sin comprimir)"
                maxSize={10 * 1024 * 1024} // 10MB
                compress={false}
                className="mb-4"
              />
            </div>

            {/* Ejemplo 4: Compresión extrema para logos pequeños */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Logo Pequeño (Compresión Extrema)</h3>
              <FileImage
                name="smallLogo"
                label="Logo pequeño"
                maxSize={500 * 1024} // 500KB
                compress={true}
                maxWidth={200}
                maxHeight={200}
                quality={0.6}
                className="mb-4"
              />
            </div>

            {/* Debug: Mostrar valores actuales */}
            <div className="bg-gray-100 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">Valores actuales:</h4>
              <pre className="text-sm">
                {JSON.stringify({
                  logo: values.logo ? {
                    name: values.logo.name,
                    size: `${Math.round(values.logo.size / 1024)}KB`,
                    type: values.logo.type
                  } : null,
                  profileImage: values.profileImage ? {
                    name: values.profileImage.name,
                    size: `${Math.round(values.profileImage.size / 1024)}KB`,
                    type: values.profileImage.type
                  } : null,
                  banner: values.banner ? {
                    name: values.banner.name,
                    size: `${Math.round(values.banner.size / 1024)}KB`,
                    type: values.banner.type
                  } : null,
                  smallLogo: values.smallLogo ? {
                    name: values.smallLogo.name,
                    size: `${Math.round(values.smallLogo.size / 1024)}KB`,
                    type: values.smallLogo.type
                  } : null
                }, null, 2)}
              </pre>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Enviando...' : 'Enviar Formulario'}
            </button>
          </Form>
        )}
      </Formik>
    </div>
  )
}

export default FileImageExample
