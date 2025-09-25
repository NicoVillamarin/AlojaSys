import React from 'react'
import { useField } from 'formik'
import LabelsContainer from './labelsContainer'

const InputText = ({ title, name, placeholder, type = 'text', disabled = false, autoFocus = false, autoComplete = 'off', className = '', inputClassName = '', ...props }) => {
  const [field, meta] = useField(name)
  const hasError = meta.touched && !!meta.error

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
        {...props}
      />
      {hasError && (
        <div className="text-xs text-red-600 mt-0.5">{meta.error}</div>
      )}
    </LabelsContainer>
  )
}

export default InputText