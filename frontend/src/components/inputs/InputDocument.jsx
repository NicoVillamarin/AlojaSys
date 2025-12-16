import React from 'react'
import { useField, useFormikContext } from 'formik'
import LabelsContainer from './LabelsContainer'

/**
 * InputDocument
 * - Restringe a dígitos únicamente.
 * - Aplica longitud máxima (default 15).
 * - Usa inputMode numeric y pattern para teclado numérico en mobile.
 */
const InputDocument = ({
  title,
  name,
  placeholder,
  disabled = false,
  autoFocus = false,
  maxLength = 15,
  className = '',
  inputClassName = '',
  ...props
}) => {
  const [field, meta] = useField(name)
  const { setFieldValue } = useFormikContext()
  const hasError = meta.touched && !!meta.error

  const handleChange = (e) => {
    const raw = e.target.value || ''
    // Solo dígitos, limitado a maxLength
    const sanitized = raw.replace(/\D+/g, '').slice(0, maxLength)
    setFieldValue(name, sanitized)
  }

  return (
    <LabelsContainer title={title}>
      <div className="relative">
        <input
          {...field}
          id={name}
          name={name}
          type="text"
          inputMode="numeric"
          pattern="\d*"
          placeholder={placeholder}
          disabled={disabled}
          autoFocus={autoFocus}
          autoComplete="off"
          maxLength={maxLength}
          className={`w-full border rounded-md px-3 py-1.5 outline-none transition focus:ring-2 ${hasError ? 'border-red-400 focus:ring-red-300' : 'border-gray-200 focus:ring-aloja-navy/30'} ${inputClassName}`}
          value={field.value || ''}
          onChange={handleChange}
          {...props}
        />
        {hasError && <div className="text-xs text-red-600 mt-0.5">{meta.error}</div>}
      </div>
    </LabelsContainer>
  )
}

export default InputDocument



