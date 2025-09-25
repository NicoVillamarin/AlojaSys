import { useField } from 'formik'
import React from 'react'
import LabelsContainer from './labelsContainer'

const InputTextTarea = ({ title, name, placeholder, rows = 3, disabled = false, autoFocus = false, autoComplete = 'off', className = '', textareaClassName = '', ...props }) => {
  const [field, meta] = useField(name)
  const hasError = meta.touched && !!meta.error

  return (
    <LabelsContainer title={title}>
      <textarea
        {...field}
        id={name}
        name={name}
        placeholder={placeholder}
        disabled={disabled}
        autoFocus={autoFocus}
        autoComplete={autoComplete}
        rows={rows}
        className={`w-full border rounded-md px-3 py-2 outline-none transition focus:ring-2 ${hasError ? 'border-red-400 focus:ring-red-300' : 'border-gray-200 focus:ring-aloja-navy/30'} ${textareaClassName}`}
        {...props}
      />
      {hasError && <div className="text-xs text-red-600 mt-0.5">{meta.error}</div>}
    </LabelsContainer>
  )
}

export default InputTextTarea