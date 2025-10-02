import React from 'react'
import { useField, useFormikContext } from 'formik'
import LabelsContainer from './LabelsContainer'

const InputText = ({ title, name, placeholder, type = 'text', disabled = false, autoFocus = false, autoComplete = 'off', className = '', inputClassName = '', onChange, onInput, ...props }) => {
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

  return (
    <LabelsContainer title={title}>
      <input
        {...field}
        id={name}
        name={name}
        type={type}
        placeholder={placeholder}
        disabled={disabled}
        autoFocus={autoFocus}
        autoComplete={autoComplete}
        className={`w-full border rounded-md px-3 py-1.5 outline-none transition focus:ring-2 ${hasError ? 'border-red-400 focus:ring-red-300' : 'border-gray-200 focus:ring-aloja-navy/30'} ${inputClassName}`}
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
      {hasError && (
        <div className="text-xs text-red-600 mt-0.5">{meta.error}</div>
      )}
    </LabelsContainer>
  )
}

export default InputText