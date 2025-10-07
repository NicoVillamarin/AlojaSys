import React from 'react'
import { useField, useFormikContext } from 'formik'
import LabelsContainer from './LabelsContainer'

const InputText = ({ title, name, placeholder, type = 'text', disabled = false, autoFocus = false, autoComplete = 'off', className = '', inputClassName = '', onChange, onInput, statusMessage, statusType = 'info', ...props }) => {
  const [field, meta] = useField(name)
  const { setFieldValue } = useFormikContext()
  const hasError = meta.touched && !!meta.error

  // Sincroniza valores si el navegador autocompleta sin disparar eventos de React
  React.useEffect(() => {
    const id = setTimeout(() => {
      const el = document.getElementById(name)
      if (el && el.value !== undefined && el.value !== field.value) {
        setFieldValue(name, el.value)
      }
    }, 150)
    return () => clearTimeout(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Determinar estilos del input basado en estado
  const getInputStyles = () => {
    if (hasError) {
      return 'border-red-400 focus:ring-red-300'
    }
    if (statusMessage && statusType === 'success') {
      return 'border-emerald-300 bg-emerald-50 focus:ring-emerald-500'
    }
    if (statusMessage && statusType === 'warning') {
      return 'border-amber-300 bg-amber-50 focus:ring-amber-500'
    }
    return 'border-gray-200 focus:ring-aloja-navy/30'
  }

  // Determinar estilos del mensaje de estado
  const getStatusStyles = () => {
    if (statusType === 'success') {
      return 'text-emerald-700'
    }
    if (statusType === 'warning') {
      return 'text-amber-700'
    }
    return 'text-blue-700'
  }

  return (
    <LabelsContainer title={title}>
      <div className="relative">
        <input
          {...field}
          id={name}
          name={name}
          type={type}
          placeholder={placeholder}
          disabled={disabled}
          autoFocus={autoFocus}
          autoComplete={autoComplete}
          className={`w-full border rounded-md px-3 py-1.5 outline-none transition focus:ring-2 ${getInputStyles()} ${inputClassName}`}
          onChange={(e) => {
            if (onChange) onChange(e)
            else field.onChange(e)
          }}
          onInput={(e) => {
            // Chrome autofill dispara 'input' en algunos casos; actualizamos Formik
            setFieldValue(name, e.target.value)
            if (onInput) onInput(e)
          }}
          {...props}
        />
        {/* Mensaje de error (comportamiento original) */}
        {hasError && (
          <div className="text-xs text-red-600 mt-0.5">{meta.error}</div>
        )}
        {/* Mensaje de estado (nuevo, posicionado absolutamente) */}
        {statusMessage && !hasError && (
          <div className={`absolute top-full left-0 mt-1 text-xs ${getStatusStyles()} flex items-center gap-1 bg-white z-10`}>
            <span className={`w-2 h-2 rounded-full ${
              statusType === 'success' ? 'bg-emerald-500' : 
              statusType === 'warning' ? 'bg-amber-500' : 
              'bg-blue-500'
            }`}></span>
            <span>{statusMessage}</span>
          </div>
        )}
      </div>
    </LabelsContainer>
  )
}

export default InputText